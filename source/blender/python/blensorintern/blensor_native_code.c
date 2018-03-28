#include "DNA_image_types.h"
#include "DNA_node_types.h"
#include "DNA_camera_types.h"
#include "DNA_object_types.h"
#include "DNA_material_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"
#include "DNA_userdef_types.h"
#include "DNA_property_types.h"
 
#include "MEM_guardedalloc.h"
 
#include "BKE_scene.h"
#include "BKE_sequencer.h"
#include "BKE_property.h"
#include "BKE_idprop.h"

#include "PIL_time.h"
#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
 
#include "intern/openexr/openexr_multi.h"
#include "rayintersection.h"
#include "rayobject.h"
#include "RNA_access.h"
#include "RE_engine.h"
#include "RE_pipeline.h"
#include "RE_shader_ext.h"

#include "blensor_native_code.h"

/* This is needed because the shading functions in shadeoutput.c use a local copy 
 * to speed up the processing. Without setting this here, shade_ray will segfault
 */
extern struct Render R;

extern int blensor_initialize_from_main(Render *re, RenderData *rd, Main *bmain, Scene *scene, SceneRenderLayer *srl,
                                       Object *camera_override, unsigned int lay_override, int anim, int anim_init);
extern void shade_ray(struct Isect *is, struct ShadeInput *shi, struct ShadeResult *shr);


//How many fields are returned from the cast rays function
#define BLENSOR_INTERSECTION_RETURNS 15
#define BLENSOR_ELEMENTS_PER_RETURN 8

/* Return the value of the id property or the defaultvalue if the id property
 * does not exist
 */
double Blensor_GetIDPropertyValue_Double(struct ID *root, const char *name, double default_value)
{
    struct IDProperty *prop;
    struct IDProperty *rindex;
    double retVal=default_value;

    if (root)
    {
        prop = IDP_GetProperties(root, 0);
        if (prop)
        {
            rindex = IDP_GetPropertyFromGroup(prop, name);
            if (rindex)
            {
                int *rtmp = (int *)&retVal;
                rtmp[0] = rindex->data.val;
                rtmp[1] = rindex->data.val2;
            }
        }
    }
    return retVal;
}

/* Return the value of theproperty or the defaultvalue if the id property
 * does not exist
 */
double Blensor_GetPropertyValue_Double(struct Object *root, const char *name, double default_value)
{
    struct bProperty *prop;    
    double retVal=default_value;

    if (root)
    {
            prop = BKE_bproperty_object_get(root,name);
            
            if (prop)
            {
                retVal = prop->data;
            }
    }
    return retVal;
}



/* Setup a single ray and cast it onto the raytree */
static int cast_ray(RayObject *tree, float sx, float sy, float sz, float vx, float vy, float vz, float *ret, void **hit_ob, void **hit_face, Render *re, SceneRenderLayer *srl, int shading)
{
    struct Isect isect;
    int res=0;
    float veclen = sqrt( pow(vx,2) + pow(vy,2) +pow(vz,2));
    ret[5] = 1.0; //Transmission
    ret[6] = 0.0; //Reflection
    ret[10] = 1.0; //Refractive Index of the material
    ret[11] = 1.0; //Diffuse reflectivity
    ret[12] = 1.0; //R-Value
    ret[13] = 1.0; //G-Value
    ret[14] = 1.0; //B-Value

   if (hit_ob && *hit_ob)
    {
        isect.orig.ob = *hit_ob;
    }
    if (hit_face && *hit_face)
    {
        isect.orig.face = *hit_face;
    }

    if (veclen)
    {
        isect.start[0]=sx;
        isect.start[1]=sy;
        isect.start[2]=sz;

        isect.dir[0]=vx/veclen;
        isect.dir[1]=vy/veclen;
        isect.dir[2]=vz/veclen;


        isect.dist = RE_RAYTRACE_MAXDIST;
  	    isect.mode= RE_RAY_MIRROR;
	      isect.check = RE_CHECK_VLR_RENDER;
	      isect.skip = RE_SKIP_VLR_NEIGHBOUR;
	      isect.hint = 0;

        res = RE_rayobject_raycast( (RayObject*) tree, &isect );


        ret[0] = isect.dist;
        ret[1] = isect.dist * isect.dir[0] + isect.start[0];    
        ret[2] = isect.dist * isect.dir[1] + isect.start[1];
        ret[3] = isect.dist * isect.dir[2] + isect.start[2];
        ret[4] = 0.0;
        
        if (isect.dist < 1000)
        {
            /* Object is defined in: source/blender/makesdna/DNA_object_types.h */
          	ObjectInstanceRen *obi = (ObjectInstanceRen*)isect.hit.ob;

            /* Retrieve the information from the intersected face */
            VlakRen *face = (VlakRen *) isect.hit.face;

            *hit_ob = isect.hit.ob;
            *hit_face = isect.hit.face;


            if (face)
            {
                 //#TODO get all necessary information from the Shaderesult
                ShadeInput shi =  {0};
                ShadeResult shr = {{0}};
                int saved_render_mode;
                int saved_material_mode;
                struct Material *m = face->mat;
                
                if (shading)
                {
                  memset(&shi, 0, sizeof(ShadeInput));
                  shi.lay = re->scene->lay; //#TODO get the layers that are really active
                  shi.depth = isect.dist;
                  shi.volume_depth = 0;
                  shi.passflag |= SCE_PASS_RGBA | SCE_PASS_COMBINED | SCE_PASS_DIFFUSE | SCE_PASS_SPEC;
                  shi.mat_override= NULL;
                  shi.light_override= NULL;
                  shi.combinedflag= 0xFFFF;

                  saved_render_mode = re->r.mode;
                  re->r.mode = ~(R_RAYTRACE); //Disable raytracing
                  saved_material_mode = m->mode;
                  m->mode |= MA_SHLESS; //Enable shadeless mode (disables lighting shaders)
                  shade_ray(&isect, &shi, &shr);
                  /* Restore parameters */
                  m->mode = saved_material_mode;
                  re->r.mode = saved_render_mode;
                }
                ret[5] = m->alpha;
                ret[6] = m->ray_mirror;
                ret[7] = face->n[0];
                ret[8] = face->n[1];
                ret[9] = face->n[2];
                ret[10] = Blensor_GetIDPropertyValue_Double(&face->mat->id,"refractive_index", 1.0);

                if (m->mapto & MAP_REF && shading)
                {
                  ret[11] = (shr.diff[0] +  shr.diff[1] + shr.diff[2])/3.0;
                } else
                {
                   ret[11] = m->ref;
                }

                if (shading)                
                {
                  ret[12] = shr.col[0]; 
                  ret[13] = shr.col[1];
                  ret[14] = shr.col[2];
                }
                else 
                {
                  ret[12] = m->r; 
                  ret[13] = m->g;
                  ret[14] = m->b;
                }
            }
              
            if (obi->ob->id.name != NULL)
            {
                int idx;
                char *bytes = (char *)(&ret[4]);
                bytes[0]=0;
                bytes[1]=0;
                bytes[2]=0;
                bytes[3]=0;

                /* We have a name 
                 * They are usually OB<name>. For example "OBCube" 
                 * Extract 4 characters after OB 
                */
                 for (idx = 0; idx < 4 && obi->ob->id.name[idx+2] != 0; idx++)
                 {  
                    bytes[idx] = obi->ob->id.name[idx+2];
                 }
            }
       }
    }
    return res;
}


/* Calculate the Outgoing ray based on the surface normal and the refractive indices
 * (n1,n2) of the two materials
 * Returns 0 if the ray is reflected
 */
int blensor_dispersion(float *ray, float *surface_normal, float n1, float n2, float *out_ray)
{
    float incident_angle = angle_v3v3(ray, surface_normal);
    int reflected = 0;
    /* Check for numerical problems. We can not calculate a rotation axis if 
     * the ray is close to parallel to the surface normal
     * If the ray is parallel to the surface_normal the change in direction 
     * due to dispersion is minimal and the ray passes along in the same direction
     */
    if (fabs(n1) < 0.0 && (fabs(incident_angle) < 0.002 || 
                           fabs(incident_angle-M_PI) < 0.02) )
    {
        float rotation_axis[3];
      
        float r = n2/n1;
        float sin_theta2 = incident_angle*r;


        cross_v3_v3v3(rotation_axis,ray,surface_normal);

        /* If the angle is below the critical angle we get a total-reflection */
        if (sin_theta2 > 1.0)
        {
            reflect_v3_v3v3(out_ray, ray, surface_normal);
            reflected = 1;
        }
        else
        {
            float exit_angle;
            float tmp[3];
            exit_angle = asin(sin_theta2);

            normalize_v3_v3(tmp, surface_normal); //This is probably already normalized
            rotate_v3_v3v3fl(out_ray, tmp, rotation_axis, -exit_angle);            
        }
    }
    else 
    {
       out_ray[0]=ray[0];
       out_ray[1]=ray[1];
       out_ray[2]=ray[2];
    }
    return reflected;
}


/* Calculate the minimal reflectivty that will cause a reflection */
double blensor_calculate_reflectivity_limit(double dist, 
                                            double reflectivity_distance,    
                                            double reflectivity_limit,
                                            double reflectivity_slope)
{
    double min_reflectivity = -1.0;
    if (dist >= reflectivity_distance)
    {
        min_reflectivity = reflectivity_limit + reflectivity_slope * (dist-reflectivity_distance);
    }
    
    return min_reflectivity;
}


/*
 * TODO: implement a threaded blensor
 * 
static void threaded_blensor_processor(Render *re)
{
	ListBase threads;
	RenderPart *pa, *nextpa;
	int rendering=1, counter= 1, drawtimer=0, hasdrawn, minx=0;
	
//?//	initparts(re);

	
	BLI_init_threads(&threads, do_part_blensor, re->r.threads);
	
	// assuming no new data gets added to dbase... 
	R= *re;
	
	// set threadsafe break 
//?//	R.test_break= thread_break;

	nextpa= find_next_part(re, 0);
	
	while (rendering) {
		
		if (BLI_available_threads(&threads)) {
			BLI_insert_thread(&threads, [[DATA]]);
		}

		
		for (pa= re->parts.first; pa; pa= pa->next) {
			if (pa->ready) {
				BLI_remove_thread(&threads, pa);
			}
		}
	}
	
	// unset threadsafety 
	g_break= 0;
	
	BLI_end_threads(&threads);
//?//	freeparts(re);
}
*/


/* cast all rays specified in *rays and return the result via *returns */
static void do_blensor(Render *re, float *rays, int raycount, int elements_per_ray, float *returns, float maximum_distance,
                       Main *bmain, Scene *scene, SceneRenderLayer *srl, int shading)
{
    int idx;
    float refractive_index = 1.0;
    double reflectivity_distance = 50;  //Minimum distance at which the reflectivity
                                          //of the object influences the distance measuremet
    double reflectivity_limit = 0.1;  
    double reflectivity_slope = 0.01;  
    double min_reflectivity = -1.0;
    int reflection_enabled = 0;
    struct bProperty *tprop;
    Camera *cam;
    PointerRNA rna_cam;
    PropertyRNA *rna_cam_prop;
    PropertyType pt;
    

    cam = (Camera *)re->scene->camera->data;
    RNA_pointer_create(&(re->scene->camera->id), &RNA_Object, re->scene->camera, &rna_cam);

    rna_cam_prop = RNA_struct_find_property(&rna_cam, "ref_dist");
    reflectivity_distance = RNA_property_float_get(&rna_cam, rna_cam_prop);

    rna_cam_prop = RNA_struct_find_property(&rna_cam, "ref_limit");
    reflectivity_limit = RNA_property_float_get(&rna_cam, rna_cam_prop);

    rna_cam_prop = RNA_struct_find_property(&rna_cam, "ref_slope");
    reflectivity_slope = RNA_property_float_get(&rna_cam, rna_cam_prop);

    rna_cam_prop = RNA_struct_find_property(&rna_cam, "ref_enabled");
    reflection_enabled = RNA_property_boolean_get(&rna_cam, rna_cam_prop);

    /* This is necessary, see explanation at the point of declaration */
    R = *re;

    refractive_index = Blensor_GetIDPropertyValue_Double(&re->scene->world->id,"refractive_index", 1.0);
    printf ("The refractive index of the world is: %.6f\n",refractive_index);
    printf ("reflectivity_distance: %.6f  reflectivity_limit: %.6f\n",reflectivity_distance, reflectivity_limit);

    for (idx = 0; idx < raycount ;  idx ++)
    {
        double maxdist = maximum_distance;
        int valid_signal = 0;


        float sx = 0.0, sy=0.0, sz=0.0;
        float vx = rays[idx*elements_per_ray], vy=rays[idx*elements_per_ray+1], vz=rays[idx*elements_per_ray+2];
        float intersection[BLENSOR_INTERSECTION_RETURNS];
        //Transmission threshold and reflection threshold should be set for
        //every ray from within python

        float raydistance = 0.0;
        int reflection = 0;
        int transmission = 0;
        void *hit_ob = NULL;
        void *hit_face = NULL;

        /* If we got 6 elements per ray the scan interface also supplied
           start coordinates for every ray
         */
        if (elements_per_ray >= 6)
        {
          sx = rays[idx*elements_per_ray+3];
          sy = rays[idx*elements_per_ray+4];
          sz = rays[idx*elements_per_ray+5];;
        }

    
        do
        {
            double min_reflectivity = -1.0;
            double reflected_energy = 0.0;
            reflection = 0;
            transmission = 0;
            cast_ray(re->raytree, sx, sy, sz, vx, vy, vz, intersection, &hit_ob, &hit_face, re, srl, shading);
  
            raydistance += intersection[0];

            min_reflectivity = blensor_calculate_reflectivity_limit(raydistance, 
                                            reflectivity_distance, reflectivity_limit, reflectivity_slope);
    
            //TODO: We would neeed to cast the ray through the material and
            //      also reflect it, but this could get really messy if a ray
            //      is split many times.
            //      reflectivity tells how much light is reflected this is further
            //      split into diffuse and specular reflection. A certain amount of
            //      the specular reflection is added to the reflected_energy.
            //      If the remaining amount of energy that is emitted through reflection/transmission
            //      is below the threshold for a detection we can stop

            if (intersection[6] > 0.0 && reflection_enabled != 0) //if reflection instead of transmission
            {
                    /* Check if the ray is reflected and calculate the
                     * the new vector
                     */                        
                    float out_ray[3];
                    float in_ray[] = {vx,vy,vz};
                    float v1[3];
                    float angle;

                    reflection = 1;
                    reflect_v3_v3v3(out_ray, in_ray, &intersection[7]);

                    v1[0] = sx-intersection[1];
                    v1[1] = sy-intersection[2];
                    v1[2] = sz-intersection[3];

                    angle = angle_v3v3(v1,&intersection[7]);
                    
                    vx=out_ray[0];
                    vy=out_ray[1];
                    vz=out_ray[2];

                    valid_signal=0; //Reflection means we have not hit a correct target
            } 
            else if (intersection[11] > min_reflectivity )
            {
               valid_signal = 1;
               //We have a signal
               reflection=0;
               transmission=0; 
            }
            else if ( (1==0) && intersection[5] > 0.0 ) //Refraction is currently [DISABLED]
            {
                float out_ray[3];
                float in_ray[] = {vx,vy,vz};
                
                transmission = 1;
                transmission = !blensor_dispersion(in_ray, &intersection[7], refractive_index, intersection[10], out_ray);

                vx=out_ray[0];
                vy=out_ray[1];
                vz=out_ray[2];
            
                valid_signal = 0;
            } else
            {
                valid_signal = 0;
            }

            sx = intersection[1];  //And set up the new starting point            
            sy = intersection[2];
            sz = intersection[3];
        } while((reflection || transmission) && raydistance <= maxdist && !valid_signal);

        returns[idx*BLENSOR_ELEMENTS_PER_RETURN+5] = intersection[12]; //r-value
        returns[idx*BLENSOR_ELEMENTS_PER_RETURN+6] = intersection[13]; //g-value
        returns[idx*BLENSOR_ELEMENTS_PER_RETURN+7] = intersection[14]; //b-value
        
        if (raydistance <= maxdist && valid_signal != 0)
        {   
            intersection[0] = raydistance;
            memcpy(&returns[idx*BLENSOR_ELEMENTS_PER_RETURN], intersection, 5*sizeof(float));
        }
        else 
        {
            intersection[0] = FLT_MAX;
        }
    }

}



/* ****************************** render invoking ***************** */


static uintptr_t convert_str_to_ptr(char *ptr_str)
{
  int idx=0;
  uintptr_t ptr=0;
  for (idx=0; idx < 16; idx++)
  {
    ptr = ptr << 4;  
    switch(ptr_str[idx])
    {
      case 'F': 
      case 'f': ptr += 15; break;
      case 'E': 
      case 'e': ptr += 14; break;
      case 'D': 
      case 'd': ptr += 13; break;
      case 'C': 
      case 'c': ptr += 12; break;
      case 'B': 
      case 'b': ptr += 11; break;
      case 'A': 
      case 'a': ptr += 10; break;
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9': ptr += ptr_str[idx]-'0';
            break;
      default:
        //You have some ugly data here
        break;
    }
    
  }
  return ptr;
}

/* for exec() when there is no render job
 * note: this wont check for the escape key being pressed, but doing so isnt threadsafe */
static int render_break(void *UNUSED(rjv))
{
	if (G.is_break)
		return 1;
	return 0;
}


/* #TODO@mgschwan: There is a memory leak somewhere in the raycasting code. Find it! */
/* Setup the evnironment and call the raycaster function */
void RE_BlensorFrame(Render *re, Main *bmain, Scene *scene, SceneRenderLayer *srl, Object *camera_override, unsigned int lay, int frame, const short write_still, float *rays, int raycount, int elements_per_ray, float *returns, float maximum_distance, int keep_setup, int shading)
{
  static int render_still_available = 0; //If this is 1 the raycasting is still setup from
                                         //previous renders, and can be reused
  double refractive_index = 1.0; //Vacuum
	/* ugly global still... is to prevent preview events and signal subsurfs etc to make full resol */
	G.is_rendering= true;
	
	printf ("Do Blensor processing: %d\n", frame);

	scene->r.cfra= frame;

	if(blensor_initialize_from_main(re, &scene->r, bmain, scene, srl, camera_override, lay, 0, 0)) {
    MEM_reset_peak_memory();

    BKE_scene_camera_switch_update(re->scene);
    
    //BLI_callback_exec(re->main, (ID *)scene, BLI_CB_EVT_RENDER_PRE);

    re->pool = BKE_image_pool_new();

    // moved here from the do_blensor function 
    re->scene->r.subframe = re->mblur_offs + re->field_offs;
    RE_Database_FromScene(re, re->main, re->scene, re->lay, 1); //Sets up all the stuff
		RE_Database_Preprocess(re);

    do_blensor(re, rays, raycount, elements_per_ray, returns, maximum_distance, bmain, scene, srl, shading);
	
    // moved here from the end of do_blensor 
    // free all render verts etc 
    RE_Database_Free(re);

	BKE_image_pool_free(re->pool);
    re->pool = NULL;

    re->scene->r.subframe = 0.f;
    render_still_available = 0;

    //BLI_callback_exec(re->main, (ID *)scene, BLI_CB_EVT_RENDER_POST); 
  }

  //BLI_callback_exec(re->main, (ID *)scene, G.afbreek ? BLI_CB_EVT_RENDER_CANCEL : BLI_CB_EVT_RENDER_COMPLETE);

	/* UGLY WARNING */
	G.is_rendering= false;
}

/* executes blocking blensor */
int screen_blensor_exec(bContext *C, int raycount, int elements_per_ray, int keep_render_setup, int shading, float maximum_distance, char *ray_ptr_str, char *return_ptr_str)
{
	Scene *scene= CTX_data_scene(C);
    SceneRenderLayer *srl = NULL;
	static Render *re=NULL;
	Image *ima;
	View3D *v3d= CTX_wm_view3d(C);
	Main *mainp= CTX_data_main(C);
	unsigned int lay= (v3d)? v3d->lay: scene->lay;
    float *rays;
    float *returns;

	struct Object *camera_override= v3d ? V3D_CAMERA_LOCAL(v3d) : NULL;


    rays = (float *)convert_str_to_ptr(ray_ptr_str);
    returns = (float *)convert_str_to_ptr(return_ptr_str);
      
    if (raycount > 0)
    {
            
        printf ("Raycount: %d\n",raycount);
        
            if(re==NULL) {
                re = RE_NewSceneRender(scene);
            }
        
    
        G.is_break = false;
        RE_test_break_cb(re, NULL, render_break);

        ima= BKE_image_verify_viewer(IMA_TYPE_R_RESULT, "Render Result");
        BKE_image_signal(ima, NULL, IMA_SIGNAL_FREE);
        BKE_image_backup_render(scene, ima, true);

        /* cleanup sequencer caches before starting user triggered render.
        * otherwise, invalidated cache entries can make their way into
        * the output rendering. We can't put that into RE_BlenderFrame,
        * since sequence rendering can call that recursively... (peter) */
        BKE_sequencer_cache_cleanup();

        //RE_SetReports(re, op->reports);

        BLI_threaded_malloc_begin();

        RE_BlensorFrame(re, mainp, scene, NULL, camera_override, lay, scene->r.cfra, 0, rays, raycount, elements_per_ray, returns, maximum_distance, keep_render_setup, shading);

        BLI_threaded_malloc_end();

        RE_SetReports(re, NULL);

            // no redraw needed, we leave state as we entered it
        ED_update_for_newframe(mainp, scene, 1);

        WM_event_add_notifier(C, NC_SCENE|ND_RENDER_RESULT, scene);
        if (keep_render_setup == 0)
        {
            re = NULL;
        }

     }
	return OPERATOR_FINISHED;
}

/* Return the floating point zbuffer */
void blensor_Image_copy_zbuf(Image *image, bContext *C, int *outbuffer_len, float **outbuffer)
{
  ImageUser iuser;
	void *lock;
  Scene *scene;
	ImBuf *ibuf;
  int idx=0;
  
  scene = CTX_data_scene(C);

  *outbuffer_len=0;

	iuser.scene = scene;
	iuser.ok = 1;

	ibuf = BKE_image_acquire_ibuf(image, &iuser, &lock);

	if (ibuf == NULL) {
			printf ("Couldn't acquire buffer from image");
	}
	else {
        *outbuffer = (float *) MEM_mallocN(ibuf->x * ibuf->y * sizeof(float),"rna_Image_zbuf");
        if (*outbuffer == NULL)
        {
           printf("Couldn't allocate buffer for zbuffer output");
        }
        else
        {
            memcpy((void *)*outbuffer, (const void *)ibuf->zbuf_float, ibuf->x * ibuf->y* sizeof(float));
            *outbuffer_len = ibuf->x * ibuf->y;
        }

	}
	BKE_image_release_ibuf(image, ibuf, lock);
}




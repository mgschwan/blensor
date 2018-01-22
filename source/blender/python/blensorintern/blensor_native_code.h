#include <math.h>
#include <string.h>
#include <stddef.h>

#include "DNA_image_types.h"
#include "DNA_node_types.h"
#include "DNA_camera_types.h"
#include "DNA_object_types.h"
#include "DNA_material_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"
#include "DNA_userdef_types.h"
#include "DNA_property_types.h"
#include "DNA_view3d_types.h"

#include "MEM_guardedalloc.h"
 
#include "BKE_property.h"
#include "BKE_idprop.h"
#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_colortools.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_sequencer.h"
#include "BKE_screen.h"
#include "BKE_scene.h"
#include "BKE_animsys.h"  /* <------ should this be here?, needed for sequencer update */
#include "BKE_camera.h"
#include "BKE_modifier.h"
#include "BKE_pointcache.h"


#include "PIL_time.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "RE_pipeline.h"
#include "RE_engine.h"
#include "RE_shader_ext.h"

#include "ED_object.h"
#include "ED_render.h"
#include "ED_screen.h"
#include "ED_util.h"
#include "ED_view3d.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_math.h"
#include "BLI_rect.h"
#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_path_util.h"
#include "BLI_fileops.h"
#include "BLI_threads.h"
#include "BLI_rand.h"
#include "BLI_callbacks.h"


//#include "BLF_translation.h"
 
#include "intern/openexr/openexr_multi.h"
#include "rayintersection.h"
#include "rayobject.h"

#include "WM_api.h"
#include "WM_types.h"
#include "GPU_extensions.h"
#include "wm_window.h"
#include "render_intern.h"

/* internal */
#include "render_result.h"
#include "render_types.h"
#include "renderpipeline.h"
#include "renderdatabase.h"
#include "rendercore.h"
#include "initrender.h"
#include "shadbuf.h"
#include "pixelblending.h"
#include "zbuf.h"


int screen_blensor_exec(bContext *C, int raycount, int elements_per_ray, int keep_render_setup, int shading, float maximum_distance, char *ray_ptr_str, char *return_ptr_str);
void blensor_Image_copy_zbuf(Image *image, bContext *C, int *outbuffer_len, float **outbuffer);


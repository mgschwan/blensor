/**
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "LOD_decimation.h"
#include "ply/ply.h"
#include "MEM_SmartPtr.h"
#include "common/GlutDrawer.h"
#include "GlutMeshDrawer.h"
#include "MyGlutKeyHandler.h"
#include "MyGlutMouseHandler.h"
#include "MT_Vector3.h"
#include "LOD_GhostTestApp.h"

#include <memory>

#define DEBUG_PRINT 0

struct LoadVertex {
  float x,y,z;             /* the usual 3-space position of a vertex */
};

struct LoadFace {
  unsigned char intensity; /* this user attaches intensity to faces */
  unsigned char nverts;    /* number of vertex indices in list */
  int *verts;              /* vertex index list */
};

 
	 LOD_Decimation_InfoPtr 
NewVertsFromFile(
	char * file_name,
	MT_Vector3 &min,
	MT_Vector3 &max
) {

	min = MT_Vector3(MT_INFINITY,MT_INFINITY,MT_INFINITY);
	max = MT_Vector3(-MT_INFINITY,-MT_INFINITY,-MT_INFINITY);

	
	PlyProperty vert_props[] = { /* list of property information for a vertex */
	  {"x", PLY_FLOAT, PLY_FLOAT, offsetof(LoadVertex,x), 0, 0, 0, 0},
	  {"y", PLY_FLOAT, PLY_FLOAT, offsetof(LoadVertex,y), 0, 0, 0, 0},
	  {"z", PLY_FLOAT, PLY_FLOAT, offsetof(LoadVertex,z), 0, 0, 0, 0},
	};

	PlyProperty face_props[] = { /* list of property information for a vertex */
	  {"intensity", PLY_UCHAR, PLY_UCHAR, offsetof(LoadFace,intensity), 0, 0, 0, 0},
	  {"vertex_indices", PLY_INT, PLY_INT, offsetof(LoadFace,verts),
	   1, PLY_UCHAR, PLY_UCHAR, offsetof(LoadFace,nverts)},
	};
#if 0
	MEM_SmartPtr<std::vector<float> > verts = new std::vector<float>;
	MEM_SmartPtr<std::vector<float> > vertex_normals = new std::vector<float>;

	MEM_SmartPtr<std::vector<int> > faces = new std::vector<int>;
#else
	std::vector<float>* verts = new std::vector<float>;
	std::vector<float>*  vertex_normals = new std::vector<float>;

	std::vector<int> * faces = new std::vector<int>;
#endif

  int i,j;
  PlyFile *ply;
  int nelems;
  char **elist;
  int file_type;
  float version;
  int nprops;
  int num_elems;
  PlyProperty **plist;

  char *elem_name;

	LoadVertex load_vertex;
	LoadFace load_face;

  /* open a PLY file for reading */
  ply = ply_open_for_reading(file_name, &nelems, &elist, &file_type, &version);

 if (ply == NULL) return NULL;
  /* go through each kind of element that we learned is in the file */
  /* and read them */

  for (i = 0; i < nelems; i++) {

    /* get the description of the first element */

    elem_name = elist[i];
    plist = ply_get_element_description (ply, elem_name, &num_elems, &nprops);

    /* print the name of the element, for debugging */

    /* if we're on vertex elements, read them in */
    if (equal_strings ("vertex", elem_name)) {

      /* set up for getting vertex elements */

      ply_get_property (ply, elem_name, &vert_props[0]);
      ply_get_property (ply, elem_name, &vert_props[1]);
      ply_get_property (ply, elem_name, &vert_props[2]);

		// make some memory for the vertices		
  		verts->reserve(num_elems);

      /* grab all the vertex elements */
      for (j = 0; j < num_elems; j++) {

        /* grab and element from the file */
        ply_get_element (ply, (void *)&load_vertex);
		// pass the vertex into the mesh builder.
			
	
		if (load_vertex.x < min.x()) {
			min.x() = load_vertex.x;
		} else
		if (load_vertex.x > max.x()) {
			max.x()= load_vertex.x;
		}

		if (load_vertex.y < min.y()) {
			min.y() = load_vertex.y;
		} else
		if (load_vertex.y > max.y()) {
			max.y()= load_vertex.y;
		}

		if (load_vertex.z < min.z()) {
			min.z() = load_vertex.z;
		} else
		if (load_vertex.z > max.z()) {
			max.z()= load_vertex.z;
		}

		verts->push_back(load_vertex.x);
		verts->push_back(load_vertex.y);
		verts->push_back(load_vertex.z);

		vertex_normals->push_back(1.0f);
		vertex_normals->push_back(0.0f);
		vertex_normals->push_back(0.0f);


      }
    }

    /* if we're on face elements, read them in */
    if (equal_strings ("face", elem_name)) {

      /* set up for getting face elements */

 //     ply_get_property (ply, elem_name, &face_props[0]);
      ply_get_property (ply, elem_name, &face_props[1]);

      /* grab all the face elements */
      for (j = 0; j < num_elems; j++) {

        ply_get_element (ply, (void *)&load_face);

		faces->push_back(load_face.verts[0]);
		faces->push_back(load_face.verts[1]);
		faces->push_back(load_face.verts[2]);

		// free up the memory this pile of shit used to allocate the polygon's vertices

		free (load_face.verts);
      }

    }
  }
  /* close the PLY file */
  ply_close (ply);

  LOD_Decimation_InfoPtr output = new LOD_Decimation_Info;

  output->vertex_buffer = verts->begin();
  output->vertex_num = verts->size()/3;

  output->triangle_index_buffer = faces->begin();
  output->face_num = faces->size()/3;
  output->intern = NULL;
  output->vertex_normal_buffer = vertex_normals->begin();

  // memory leaks 'r' us	
#if 0
  verts.Release();
  vertex_normals.Release();
  faces.Release();
#endif
  return output;
}
	

void
init(MT_Vector3 min,MT_Vector3 max)
{
 
	GLfloat light_diffuse0[] = {1.0, 0.0, 0.0, 0.5};  /* Red diffuse light. */
	GLfloat light_position0[] = {1.0, 1.0, 1.0, 0.0};  /* Infinite light location. */

	GLfloat light_diffuse1[] = {1.0, 1.0, 1.0, 0.5};  /* Red diffuse light. */
	GLfloat light_position1[] = {1.0, 0, 0, 0.0};  /* Infinite light location. */

  /* Enable a single OpenGL light. */
  glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse0);
  glLightfv(GL_LIGHT0, GL_POSITION, light_position0);

  glLightfv(GL_LIGHT1, GL_DIFFUSE, light_diffuse1);
  glLightfv(GL_LIGHT1, GL_POSITION, light_position1);

  glEnable(GL_LIGHT0);
//  glEnable(GL_LIGHT1);
  glEnable(GL_LIGHTING);

	// use two sided lighting model
	
	glLightModeli(GL_LIGHT_MODEL_TWO_SIDE,GL_TRUE);

  /* Use depth buffering for hidden surface elimination. */
  glEnable(GL_DEPTH_TEST);

  /* Setup the view of the cube. */
  glMatrixMode(GL_PROJECTION);

	// center of the box + 3* depth of box

  MT_Vector3 center = (min + max) * 0.5;
  MT_Vector3 diag = max - min;

	float depth = diag.length();
	float distance = 2;

  gluPerspective( 
	/* field of view in degree */ 40.0,
    /* aspect ratio */ 1.0,
    /* Z near */ 1.0, 
	/* Z far */ distance * depth * 2
  );
  glMatrixMode(GL_MODELVIEW);	


  gluLookAt(
	center.x(), center.y(), center.z() + distance*depth,  /* eye is at (0,0,5) */
    center.x(), center.y(), center.z(),      /* center is at (0,0,0) */
    0.0, 1.0, 0.);      /* up is in positive Y direction */

  glPushMatrix();	


}

int
main(int argc, char **argv)
{

// load in the mesh

	MT_Vector3 mesh_min,mesh_max;

	LOD_Decimation_InfoPtr LOD_info = NewVertsFromFile("beethoven.ply",mesh_min,mesh_max);

	// load the mesh data 

	int load_result = LOD_LoadMesh(LOD_info);
	int preprocess_result = LOD_PreprocessMesh(LOD_info);

	if (!(load_result && preprocess_result)) {
		cout << " could not load mesh! \n";
		return 0;
	}

	// make and install a mouse handler

	MEM_SmartPtr<MyGlutMouseHandler> mouse_handler(MyGlutMouseHandler::New());
	GlutMouseManager::Instance()->InstallHandler(mouse_handler);

	// instantiate the drawing class	

	MEM_SmartPtr<GlutMeshDrawer> drawer(GlutMeshDrawer::New());
	GlutDrawManager::Instance()->InstallDrawer(drawer);
	drawer->SetLODInfo(LOD_info);	
	drawer->SetMouseHandler(mouse_handler);

	// make and install a keyhandler

	MEM_SmartPtr<MyGlutKeyHandler> key_handler(MyGlutKeyHandler::New(LOD_info));
	GlutKeyboardManager::Instance()->InstallHandler(key_handler);


	LOD_GhostTestApp LOD_app;

	LOD_app.InitApp();
	init(mesh_min,mesh_max);

	LOD_app.Run();


	return 0;             /* ANSI C requires main to return int. */
}

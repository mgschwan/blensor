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

#ifndef __GLUTMESHDRAWER_H__
#define __GLUTMESHDRAWER_H__

#include "common/GlutDrawer.h"
#include "LOD_decimation.h"
#include "MyGlutMouseHandler.h"
#include <math.h>
#include <iostream>
#include <iterator>
#if defined(WIN32) || defined(__APPLE__)
#ifdef WIN32
#include <windows.h>
#include <GL/gl.h>
#include <GL/glu.h>
#else // WIN32
// __APPLE__ is defined
#include <AGL/gl.h>
#endif // WIN32
#else // defined(WIN32) || defined(__APPLE__)
#include <GL/gl.h>
#include <GL/glu.h>
#endif // defined(WIN32) || defined(__APPLE__)
#include <vector>
// a concrete mesh drawer

class GlutMeshDrawer : public GlutDrawer
{
public :
	static
		GlutMeshDrawer *
	New(
	) {
		return new GlutMeshDrawer();
	}

	// set the mesh to draw

		void
	SetLODInfo( 
		LOD_Decimation_InfoPtr info
	){
		m_info = info;
	}
	
		void
	SetMouseHandler(
		MyGlutMouseHandler *mouse_handler
	) {
		m_mouse_handler = mouse_handler;
	}


	// inherited from GlutDrawer
		void
	Draw(
	) {
	  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
		  glPopMatrix();
		  glPushMatrix();
		  glRotatef(m_mouse_handler->AngleX(), 0.0, 1.0, 0.0);
		  glRotatef(m_mouse_handler->AngleY(), 1.0, 0.0, 0.0);
			
	  DrawScene();
	}

	~GlutMeshDrawer(
	){
		// nothing to do
	};		
	
private :

		void
	DrawScene(
	){
		
		float * verts = m_info->vertex_buffer;
		const int num_verts = m_info->vertex_num;

		float * vertex_normals = m_info->vertex_normal_buffer;


		int * index = m_info->triangle_index_buffer;
		const int num_faces = m_info->face_num;

		glBegin(GL_TRIANGLES);

		float mat_spec1[] = {1.0,1.0,1.0,1.0};
		float mat_spec2[] = {1.0,0.0,1.0,1.0};
		float mat_spec3[] = {1.0,1.0,0.0,1.0};
		float mat_spec4[] = {0.0,0.0,1.0,1.0};

	

		int i;
		for (i= 0; i < num_faces; i++) {
#if 0
			int col = i%4;
			if (col == 0) {
				glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,mat_spec1);
			} else 
			if (col == 1) {
				glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,mat_spec2);
			} else 
			if (col == 2) {
				glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,mat_spec3);
			} else 
			if (col == 3) {
				glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,mat_spec4);
			}
#endif
			glNormal3fv(vertex_normals + 3*index[3*i]);		
			glVertex3fv(verts + 3*index[3*i]);

			glNormal3fv(vertex_normals + 3*index[3*i + 1]);
			glVertex3fv(verts + 3*index[3*i + 1]);

			glNormal3fv(vertex_normals + 3*index[3*i + 2]);
			glVertex3fv(verts + 3*index[3*i + 2]);

		}
		glEnd();


	};



private :

	LOD_Decimation_InfoPtr m_info;

	MyGlutMouseHandler * m_mouse_handler;

	GlutMeshDrawer (
	) : m_info (NULL) {
	};
	
};


#endif


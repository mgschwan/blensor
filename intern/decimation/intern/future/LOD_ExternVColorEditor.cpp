/*
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

/** \file decimation/intern/future/LOD_ExternVColorEditor.cpp
 *  \ingroup decimation
 */


#include "LOD_ExternVColorEditor.h"

#include <vector>

using namespace std;


LOD_ExternVColorEditor::
LOD_ExternVColorEditor(
	LOD_Decimation_InfoPtr extern_info
) :
	m_extern_info (extern_info)
{
}

	LOD_ExternVColorEditor *
LOD_ExternVColorEditor::
New(
	LOD_Decimation_InfoPtr extern_info
){
	if (extern_info == NULL) return NULL;
	
	NanPtr<LOD_ExternVColorEditor> output(new LOD_ExternVColorEditor(extern_info));

	return output.Release();
};
	

// vertex normals
/////////////////

	void
LOD_ExternVColorEditor::
RemoveVertexColors(
	const vector<LOD_VertexInd> &sorted_verts
){

	float * vertex_colors = m_extern_info->vertex_color_buffer;

	// assumption here that the vertexs normal number corresponds with 
	// the number of vertices !

	int vertex_color_num = m_extern_info->vertex_num; 

	vector<LOD_VertexInd>::const_iterator it_start = sorted_verts.begin();
	vector<LOD_VertexInd>::const_iterator it_end = sorted_verts.end();

	for (; it_start != it_end; ++it_start) {

		if (vertex_color_num > 0) {

			float * vertex_color = vertex_colors + int(*it_start)*3;
			float * last_color = vertex_colors + ((vertex_color_num-1)*3);

			MT_Vector3 last_c(last_color);
			last_c.getValue(vertex_color);

			vertex_color_num--;
		}

		// FIXME - throw exception
	}
};

// Return the color for vertex v

	MT_Vector3
LOD_ExternVColorEditor::
IndexColor(
	const LOD_VertexInd &v
) const {
	return MT_Vector3(m_extern_info->vertex_color_buffer + int(v)*3);
}


// Set the color for vertex v

	void
LOD_ExternVColorEditor::
SetColor(
	MT_Vector3 c,
	const LOD_VertexInd &v
) {
	c.getValue(m_extern_info->vertex_color_buffer + int(v)*3);
}






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

/** \file decimation/intern/future/LOD_NdQSDecimator.h
 *  \ingroup decimation
 */


#ifndef __LOD_NDQSDECIMATOR_H__
#define __LOD_NDQSDECIMATOR_H__

#include "common/NonCopyable.h"
#include "LOD_ManMesh2.h"

#include "LOD_EdgeCollapser.h"
#include "LOD_NdQuadricEditor.h"

class LOD_ExternBufferEditor;
class LOD_ExternVColorEditor;
class LOD_ExternNormalEditor;

class LOD_NdQSDecimator : public NonCopyable {

public :

	static
		LOD_NdQSDecimator *
	New(
		LOD_ManMesh2 &mesh,
		LOD_ExternNormalEditor &face_editor,
		LOD_ExternVColorEditor &color_editor,
		LOD_ExternBufferEditor &extern_editor
	);


		bool
	Arm(
	);


		bool
	Step(
	);

private :

	LOD_NdQSDecimator(
		LOD_ManMesh2 &mesh,
		LOD_ExternNormalEditor &face_editor,
		LOD_ExternVColorEditor &color_editor,
		LOD_ExternBufferEditor &extern_editor
	);

		bool
	CollapseEdge(
	);

		bool
	BuildHeap(
	);

		void
	UpdateHeap(
		std::vector<LOD_EdgeInd> &deg_edges,
		std::vector<LOD_EdgeInd> &new_edges
	);	

		void
	DeletePrimitives(
		const std::vector<LOD_EdgeInd> & degenerate_edges,
		const std::vector<LOD_FaceInd> & degenerate_faces,
		const std::vector<LOD_VertexInd> & degenerate_vertices
	);

	// Iterate through the face set 
	// for each property of the face vertices 
	// compute a quadric for that property.
	// Add it to the quadric array.	
	
		void
	ComputePropertyQuadrics(
	);


private :	

		
	// owned by this class
	//////////////////////

	NanPtr<LOD_EdgeCollapser> m_collapser;
	NanPtr<Heap<LOD_Edge> > m_heap;
	NanPtr<LOD_NdQuadricEditor> m_quadric_editor;

	bool m_is_armed;

	// arguments to New(...)
	////////////////////////

	LOD_ManMesh2 & m_mesh;
	LOD_ExternNormalEditor & m_face_editor;
	LOD_ExternBufferEditor & m_extern_editor;
	LOD_ExternVColorEditor & m_color_editor;	

	// temporary buffers
	////////////////////

	std::vector<LOD_FaceInd> m_deg_faces;
	std::vector<LOD_EdgeInd> m_deg_edges;
	std::vector<LOD_VertexInd> m_deg_vertices;

	std::vector<LOD_FaceInd> m_update_faces;
	std::vector<LOD_EdgeInd> m_new_edges;
	std::vector<LOD_VertexInd> m_update_vertices;


};

#endif


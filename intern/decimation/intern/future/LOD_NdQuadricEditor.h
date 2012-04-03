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

/** \file decimation/intern/future/LOD_NdQuadricEditor.h
 *  \ingroup decimation
 */


#ifndef __LOD_NDQUADRICEDITOR_H__
#define __LOD_NDQUADRICEDITOR_H__

#include "common/NonCopyable.h"
#include "LOD_ManMesh2.h"
#include "MT_Vector3.h"
#include "LOD_NdQuadric.h"

class LOD_ExternNormalEditor;
class LOD_ExternVColorEditor;


class LOD_NdQuadricEditor
{

public : 

	// Creation
	///////////

	static
		LOD_NdQuadricEditor *
	New(
		LOD_ManMesh2 &mesh
	); 

	// Property editor interface
	////////////////////////////

		void
	Remove(
		const std::vector<LOD_VertexInd> &sorted_vertices
	);

		std::vector<LOD_NdQuadric> &
	Quadrics(
	) const {
		return *m_quadrics;
	};


	// Editor specific methods
	//////////////////////////

		bool
	BuildQuadrics(
		const LOD_ExternNormalEditor& normal_editor,
		bool preserve_boundaries
	);	

		void
	InitializeHeapKeys(
		const LOD_ExternVColorEditor & color_editor
	);


		void
	ComputeEdgeCosts(
		const std::vector<LOD_EdgeInd> &edges,
		const LOD_ExternVColorEditor & color_editor
	); 	

		void 
	TargetVertex(
		const LOD_Edge & e,
		TNT::Vector<MT_Scalar> &result,
		const LOD_ExternVColorEditor & color_editor
	) const;

	~LOD_NdQuadricEditor(
	 ){
		delete(m_quadrics);
	};

		
private :

	std::vector<LOD_NdQuadric> * m_quadrics;

	LOD_ManMesh2 &m_mesh;

private :
	
	LOD_NdQuadricEditor(LOD_ManMesh2 &mesh);



};

#endif


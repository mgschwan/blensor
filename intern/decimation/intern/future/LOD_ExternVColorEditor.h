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

/** \file decimation/intern/future/LOD_ExternVColorEditor.h
 *  \ingroup decimation
 */


#ifndef __LOD_EXTERNVCOLOREDITOR_H__
#define __LOD_EXTERNVCOLOREDITOR_H__

#include "common/NonCopyable.h"
#include "LOD_ManMesh2.h"
#include "MT_Vector3.h"
#include "../extern/LOD_decimation.h"

class LOD_ExternVColorEditor : public NonCopyable
{

public : 

	// Creation
	///////////

	static
		LOD_ExternVColorEditor *
	New(
		LOD_Decimation_InfoPtr
	); 	

	// vertex colors
	/////////////////

		void
	RemoveVertexColors(
		const std::vector<LOD_VertexInd> &sorted_verts
	);

	// Return the color for vertex v

		MT_Vector3
	IndexColor(
		const LOD_VertexInd &v
	) const;

	// Set the color for vertex v

		void
	SetColor(
		MT_Vector3 c,
		const LOD_VertexInd &v
	);
		

private :

	LOD_Decimation_InfoPtr m_extern_info;

private :
	
		
	LOD_ExternVColorEditor(
		LOD_Decimation_InfoPtr extern_info
	);

};

#endif


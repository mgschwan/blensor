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

/** \file decimation/intern/future/LOD_NdQuadric.h
 *  \ingroup decimation
 */


#ifndef __LOD_NDQUADRIC_H__
#define __LOD_NDQUADRIC_H__

// An N dimensional quadric form.
///////////////////////////////////

#include "TNT/cmat.h"
#include "TNT/vec.h"
#include "MT_Matrix3x3.h"
#include "LOD_Quadric.h"


class LOD_NdQuadric {

private :

	LOD_Quadric m_q;

	// For space efficiency we should not use
	// TNT matrices to hold variables in. Use
	// fixed sized arrays based on template size
	// and load them into the quadric only when
	// needed for computation.

	TNT::Vector<MT_Scalar> m_prop_grad1;
	TNT::Vector<MT_Scalar> m_prop_grad2;
	TNT::Vector<MT_Scalar> m_prop_grad3;
	TNT::Vector<MT_Scalar> m_bbottom;

	// Not essential but makes it easier to debug if keep an
	// explicit version of the diagonal.
#if 1
	TNT::Vector<MT_Scalar> m_diag;
#else
	MT_Scalar m_diag;
#endif
public :

	// The general idea of these 2 constructors
	// is that first you build a quadric Qg from the
	// geometric properties of a vertex v. Then for
	// each of the properties i construct a property
	// quadric Qpi. Then sum them altogether to get
	// the final combined geomeetry and property quadric
	// Qv = Qg + Qpi

	// Initialize a quadric with a default geometric plane

    LOD_NdQuadric(
		const MT_Vector3 & vec,
		const MT_Scalar & offset
	); 

	// Initialize a quadric from a linear functional describing
	// the property gradient.pos is the position where this
	// functional is placed in the array.

	LOD_NdQuadric(
		const MT_Vector3 & vec,
		const MT_Scalar & offset,
		int pos
	);

	// Make sure the internal vectors are of the correct size.

	LOD_NdQuadric(
	);

	// This class also has the default copy constructors
	// available.

	~LOD_NdQuadric(
	){
		//nothing to do
	};

		void
	Tensor(
		TNT::Matrix<MT_Scalar> & 		
	) const; 

		void
	Vector(
		TNT::Vector<MT_Scalar> &
	) const; 

		void 
	Clear(
		MT_Scalar val=0.0
	);

		LOD_NdQuadric & 
	operator=(
		const LOD_NdQuadric& Q
	); 
		
		LOD_NdQuadric& 
	operator+=(
		const LOD_NdQuadric& Q
	);

	// You can increase or decrease the relative importance
	// of a quadric prior the summation by multiplying it
	// with a scalar value s.

		LOD_NdQuadric& 
	operator*=(
		const MT_Scalar & s
	); 

		MT_Scalar 
	Evaluate(
		const TNT::Vector<MT_Scalar> & vec
	) const;
 
		bool 
	Optimize(
		TNT::Vector<MT_Scalar> & vec
	) const;

	
};

#endif


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

/** \file decimation/intern/future/LOD_NdQuadric.cpp
 *  \ingroup decimation
 */


#include "LOD_NdQuadric.h"

#include <iostream>

// for Lower Upper decompostion code.
#include "TNT/lu.h"

//soon to be template parameter.
#define MAT_SIZE 3

LOD_NdQuadric::
LOD_NdQuadric(
	const MT_Vector3 & vec,
	const MT_Scalar & offset
):
	m_q(vec,offset),
	m_prop_grad1(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad2(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad3(int(MAT_SIZE),MT_Scalar(0)),
	m_bbottom(int(MAT_SIZE),MT_Scalar(0)),
	m_diag (int(MAT_SIZE),MT_Scalar(0))
{
	// nothing to do
}
// Initialize a quadric from a linear functional describing
// the property gradient.pos is the position where this
// functional is placed in the array.

LOD_NdQuadric::
LOD_NdQuadric(
	const MT_Vector3 & vec,
	const MT_Scalar & offset,
	int pos
):
	m_q(vec,offset),
	m_prop_grad1(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad2(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad3(int(MAT_SIZE),MT_Scalar(0)),
	m_bbottom(int(MAT_SIZE),MT_Scalar(0)),
	m_diag (int(MAT_SIZE),MT_Scalar(0))
{
	m_prop_grad1[pos] = -vec[0];
	m_prop_grad2[pos] = -vec[1];
	m_prop_grad3[pos] = -vec[2];
	
	m_bbottom[pos] = -offset;
	m_diag[pos] = MT_Scalar(1);
}


LOD_NdQuadric::
LOD_NdQuadric(
):
	m_prop_grad1(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad2(int(MAT_SIZE),MT_Scalar(0)),
	m_prop_grad3(int(MAT_SIZE),MT_Scalar(0)),
	m_bbottom(int(MAT_SIZE),MT_Scalar(0)),
	m_diag (int(MAT_SIZE),MT_Scalar(0)),
	m_q()
{
}



// This class also has the default copy constructors
// available.

	void
LOD_NdQuadric::
Tensor(
	TNT::Matrix<MT_Scalar> &tensor 		
) const {
	
	// Set the matrix to zero
	tensor = 0;
	
	// Fill in the matrix values from d variables.

	MT_Matrix3x3 tensor3x3 = m_q.Tensor();
	int i,j;

	for (j=0; j<=2; j++) {
		for (i=0; i<=2; i++) {
			tensor[j][i] = tensor3x3[j][i];
		}
	}

	// now the diagonal entry.

	for (i=3;i <3+MAT_SIZE;++i) {
		tensor[i][i] = m_diag[i-3];
	}

	// now the property gradients rows and symmetrical columns

	for (i=3; i < 3+MAT_SIZE; i++) {
		tensor[0][i] = m_prop_grad1[i-3];
		tensor[i][0] = m_prop_grad1[i-3];

		tensor[1][i] = m_prop_grad2[i-3];
		tensor[i][1] = m_prop_grad2[i-3];

		tensor[2][i] = m_prop_grad3[i-3];
		tensor[i][2] = m_prop_grad3[i-3];
	}


}
		
	void
LOD_NdQuadric::
Vector(
	TNT::Vector<MT_Scalar> &vector
) const {
	int i;

	MT_Vector3 q_vec = m_q.Vector();

	vector[0] = q_vec[0];	
	vector[1] = q_vec[1];
	vector[2] = q_vec[2];

	for (i = 3; i < 3 + MAT_SIZE; ++i) {
		vector[i] = m_bbottom[i-3];
	}
}		 

	void 
LOD_NdQuadric::
Clear(
	MT_Scalar val
) {
	m_q.Clear(val);
	m_prop_grad1 = val;
	m_prop_grad2 = val;
	m_prop_grad3 = val;
	m_bbottom = val;
	m_diag = val;
};

	LOD_NdQuadric & 
LOD_NdQuadric::
operator=(
	const LOD_NdQuadric& Q
){

	m_q = Q.m_q;
	m_prop_grad1 = Q.m_prop_grad1;
	m_prop_grad2 = Q.m_prop_grad2;
	m_prop_grad3 = Q.m_prop_grad3;
	m_bbottom = Q.m_bbottom;
	m_diag = Q.m_diag;

	return (*this);
}
	
	LOD_NdQuadric& 
LOD_NdQuadric::
operator+=(
	const LOD_NdQuadric& Q
){	
	m_q += Q.m_q;
	TNT::vectoradd(m_prop_grad1,Q.m_prop_grad1);
	TNT::vectoradd(m_prop_grad2,Q.m_prop_grad2);
	TNT::vectoradd(m_prop_grad3,Q.m_prop_grad3);
	TNT::vectoradd(m_bbottom,Q.m_bbottom);
	TNT::vectoradd(m_diag,Q.m_diag);

	return (*this);
}

	LOD_NdQuadric& 
LOD_NdQuadric::
operator*=(
	const MT_Scalar & s
){
	// multiply everything by s

	m_q *= s;
	TNT::vectorscale(m_prop_grad1,s);
	TNT::vectorscale(m_prop_grad2,s);
	TNT::vectorscale(m_prop_grad3,s);
	TNT::vectorscale(m_bbottom,s);
	TNT::vectorscale(m_diag,s);

	return (*this);
}

	MT_Scalar 
LOD_NdQuadric::
Evaluate(
	const TNT::Vector<MT_Scalar> & vec
) const {
	// compute the quadric error cost for the vector.

	//FIXME very inefficient memory usage here 
	//Way to many computations-these are symmetric!

	TNT::Matrix<MT_Scalar> 	Atensor(3+MAT_SIZE,3+MAT_SIZE,MT_Scalar(0));
	Tensor(Atensor);
	
	TNT::Vector<MT_Scalar>	Bvector(3+MAT_SIZE);
	Vector(Bvector);

	TNT::Vector<MT_Scalar> temp1(3+MAT_SIZE);

	TNT::matmult(temp1,Atensor,vec);

	return TNT::dot_prod(vec,temp1) + 2*TNT::dot_prod(Bvector,vec) + m_q.Scalar();
} 	


	bool 
LOD_NdQuadric::
Optimize(
	TNT::Vector<MT_Scalar> & vec
) const {
	
	// Return the solution to Tensor().invers() * Vector();
	// Use lower upper decomposition --again we're creating
	// heap memory for this function.
	
	TNT::Vector<TNT::Subscript> pivots(3+MAT_SIZE,0);
	TNT::Matrix<MT_Scalar> Atensor(3+MAT_SIZE,3+MAT_SIZE,MT_Scalar(0));
	
	Tensor(Atensor);
	Vector(vec);

	// Find the decomposition of the matrix. If none available 
	// matrix is singular return false.

	if (TNT::LU_factor(Atensor,pivots)) {
		return false;
	}

	if (TNT::LU_solve(Atensor,pivots,vec)) {
		return false;
	}
	
	// Now we should return -Ainv(B)!
	
	TNT::Vector<MT_Scalar>::iterator start = vec.begin();
	TNT::Vector<MT_Scalar>::const_iterator end = vec.end();

	while (start != end) {
		*start = -(*start);
		++start;
	}

#if 0
	std::cout << vec << "\n";
#endif
	return true;
};


#undef MAT_SIZE

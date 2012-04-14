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
 * Contributor(s): Michael Gschwandtner
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/python/mathutils/mathutils_eigen.h
 *  \ingroup mathutils
 */

#ifndef __MATHUTILS_EIGEN_H__
#define __MATHUTILS_EIGEN_H__

#include "mathutils.h"

/* List of available solvers */
#define EIGEN_INVALID_SOLVER          0x0000
#define EIGEN_COL_PIV_HOUSEHOLDER     0x0001
#define EIGEN_FULL_PIV_HOUSEHOLDER    0x0002
#define EIGEN_JACOBI_SVD              0x0003

PyMODINIT_FUNC PyInit_mathutils_eigen(void);
PyMODINIT_FUNC PyInit_mathutils_eigen_solvers(void);

#endif // __MATHUTILS_EIGEN_H__

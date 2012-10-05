# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# The Original Code is Copyright (C) 2006, Blender Foundation
# All rights reserved.
#
# The Original Code is: all of this file.
#
# Contributor(s): Jacques Beaurai, Erwin Coumans
#
# ***** END GPL LICENSE BLOCK *****

set(INC
	.
	common
	eltopo3d
	common/meshes
	common/newsparse
	common/tunicate
)

set(INC_SYS

)

set(SRC
	eltopo-capi.cpp
	common/bfstream.cpp
	common/ccd_wrapper.cpp
	common/clamped_spline.cpp
	common/collisionqueries.cpp
	common/cubic_ccd_wrapper.cpp
	common/fe_ccd_wrapper.cpp
	common/fileio.cpp
	common/levelset.cpp
	common/makelevelset2.cpp
	common/makelevelset3.cpp
	common/marching_triangles.cpp
	common/predicates.cpp
	common/runstats.cpp
	common/sos_ccd_wrapper.cpp
	common/wallclocktime.cpp
	eltopo3d/accelerationgrid.cpp
	eltopo3d/broadphasegrid.cpp
	eltopo3d/collisionpipeline.cpp
	eltopo3d/dynamicsurface.cpp
	eltopo3d/edgecollapser.cpp
	eltopo3d/edgeflipper.cpp
	eltopo3d/edgesplitter.cpp
	eltopo3d/eltopo.cpp
	eltopo3d/impactzonesolver.cpp
	eltopo3d/meshmerger.cpp
	eltopo3d/meshsmoother.cpp
	eltopo3d/meshpincher.cpp
	eltopo3d/nondestructivetrimesh.cpp
	eltopo3d/subdivisionscheme.cpp
	eltopo3d/surftrack.cpp
	eltopo3d/trianglequality.cpp
	common/newsparse/dense_matrix.cpp
	common/newsparse/krylov_solvers.cpp
	common/newsparse/sparse_matrix.cpp
	common/sparse/incomplete_qr.cpp
	common/tunicate/expansion.cpp
	common/tunicate/intersection.cpp
	common/tunicate/neg.cpp
	common/tunicate/orientation.cpp
	common/tunicate/sos_intersection.cpp
	common/tunicate/sos_orientation.cpp

	eltopo-capi.h
	common/array1.h
	common/array2.h
	common/array3.h
	common/array3_utils.h
	common/bfstream.h
	common/blas_wrapper.h
	common/ccd_wrapper.h
	common/clamped_spline.h
	common/collisionqueries.h
	common/fileio.h
	common/grid3.h
	common/hashtable.h
	common/lapack_wrapper.h
	common/levelset.h
	common/makelevelset2.h
	common/makelevelset3.h
	common/marching_triangles.h
	common/mat.h
	common/matlapack.h
	common/openglutils.h
	common/predicates.h
	common/util.h
	common/vec.h
	common/vector_math.h
	common/wallclocktime.h
	eltopo3d/accelerationgrid.h
	eltopo3d/broadphase.h
	eltopo3d/broadphasegrid.h
	eltopo3d/dynamicsurface.h
	eltopo3d/eltopo.h
	eltopo3d/nondestructivetrimesh.h
	eltopo3d/options.h
	eltopo3d/subdivisionscheme.h
	eltopo3d/surftrack.h
	common/newsparse/dense_matrix.h
	common/newsparse/krylov_solvers.h
	common/newsparse/linear_operator.h
	common/newsparse/sparse_matrix.h
	common/sparse/cgsolver.h
	common/sparse/crsolver.h
	common/sparse/incomplete_qr.h
	common/sparse/sparseilu.h
	common/sparse/sparsematrix.h
	common/sparse/sparsemilu.h
	common/tunicate/expansion.h
	common/tunicate/neg.h
	common/tunicate/tunicate.h
	)

add_definitions(-DNO_GUI)
add_definitions(-DUSE_FORTRAN_BLAS)

blender_add_lib(extern_eltopo "${SRC}" "${INC}" "${INC_SYS}")

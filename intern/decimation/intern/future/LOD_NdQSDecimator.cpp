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

/** \file decimation/intern/future/LOD_NdQSDecimator.cpp
 *  \ingroup decimation
 */


#include "LOD_NdQSDecimator.h"

#include "LOD_ExternBufferEditor.h"
#include "LOD_ExternNormalEditor.h"
#include "LOD_ExternVColorEditor.h"
#include "TNT/lu.h"

#include <iostream>

using namespace std;

	LOD_NdQSDecimator *
LOD_NdQSDecimator::
New(
	LOD_ManMesh2 &mesh,
	LOD_ExternNormalEditor &face_editor,
	LOD_ExternVColorEditor &color_editor,
	LOD_ExternBufferEditor &extern_editor
){

	NanPtr<LOD_NdQSDecimator> output 
		= new LOD_NdQSDecimator(mesh,face_editor,color_editor,extern_editor);

	NanPtr<LOD_EdgeCollapser > collapser(LOD_EdgeCollapser::New());
	NanPtr<LOD_NdQuadricEditor> q_editor(LOD_NdQuadricEditor::New(mesh));

	if (
		output == NULL ||
		collapser == NULL ||
		q_editor == NULL 
	) {
		return NULL;
	}
	output->m_collapser = collapser.Release();
	output->m_quadric_editor = q_editor.Release();
	return output.Release();
}	



	bool
LOD_NdQSDecimator::
Arm(
){
	MT_assert(!m_is_armed);
	bool heap_result = BuildHeap();
	if (!heap_result) {
		return false;
	}
	m_is_armed = true;
	return true;
}
	
	bool
LOD_NdQSDecimator::
Step(
){
	return CollapseEdge();
}


LOD_NdQSDecimator::
LOD_NdQSDecimator(
	LOD_ManMesh2 &mesh,
	LOD_ExternNormalEditor &face_editor,
	LOD_ExternVColorEditor &color_editor,
	LOD_ExternBufferEditor &extern_editor
) :
	m_mesh(mesh),
	m_face_editor(face_editor),
	m_color_editor(color_editor),
	m_extern_editor(extern_editor),
	m_is_armed (false)
{	
	m_deg_edges.reserve(32);
	m_deg_faces.reserve(32);
	m_deg_vertices.reserve(32);
	m_update_faces.reserve(32);
	m_new_edges.reserve(32);
	m_update_vertices.reserve(32);
};

	bool
LOD_NdQSDecimator::
CollapseEdge(
){
	
	// find an edge to collapse
	
	// FIXME force an edge collapse
	// or return false

	vector<LOD_Edge> & edges = m_mesh.EdgeSet();
	vector<LOD_Vertex> & verts = m_mesh.VertexSet();
	vector<LOD_NdQuadric> & quadrics = m_quadric_editor->Quadrics();
	int size = edges.size();

	if (size == 0) return false;

	const int heap_top = m_heap->Top();

	if (heap_top == -1 || edges[heap_top].HeapKey() <= -MT_INFINITY) {
		return false;
	}
	
	// compute the target position

	TNT::Vector<MT_Scalar> new_vector(6,MT_Scalar(0)); 

	m_quadric_editor->TargetVertex(edges[heap_top],new_vector,m_color_editor);


	MT_Vector3 new_vertex(
		new_vector[0],
		new_vector[1],
		new_vector[2]
	);
	for (int i = 3; i < 6;i++) {
		if (new_vector[i] > MT_Scalar(1)) {
			new_vector[i] = MT_Scalar(1);
		} else 
		if (new_vector[i] < MT_Scalar(0)) {
			new_vector[i] = MT_Scalar(0);
		}
	}
	MT_Vector3 new_color(
		new_vector[3],
		new_vector[4],
		new_vector[5]
	);

	// bounds check?

		
	LOD_NdQuadric & q0 = quadrics[edges[heap_top].m_verts[0]];
	LOD_NdQuadric & q1 = quadrics[edges[heap_top].m_verts[1]];

	const LOD_VertexInd v0ind = edges[heap_top].m_verts[0];
	const LOD_VertexInd v1ind = edges[heap_top].m_verts[1];

	LOD_Vertex &v0 = verts[v0ind];
	LOD_Vertex &v1 = verts[v1ind];

	LOD_NdQuadric sum = q0;
	sum += q1;


	if (m_collapser->CollapseEdge(
			heap_top,
			m_mesh,
			m_deg_edges,
			m_deg_faces,
			m_deg_vertices,
			m_new_edges,
			m_update_faces,
			m_update_vertices
	)) {

		// assign new vertex position

		v0.pos = new_vertex;
		v1.pos = new_vertex;

		// assign the new vertex color
			
		m_color_editor.SetColor(new_color,v0ind);
		m_color_editor.SetColor(new_color,v1ind);

		// sum the quadrics of v0 and v1
		q0 = sum;
		q1 = sum;

		// ok update the primitive properties

		m_face_editor.Update(m_update_faces);	
		m_face_editor.UpdateVertexNormals(m_update_vertices);

		// update the external vertex buffer 
		m_extern_editor.CopyModifiedVerts(m_mesh,m_update_vertices);

		// update the external face buffer
		m_extern_editor.CopyModifiedFaces(m_mesh,m_update_faces);

		// update the edge heap
		UpdateHeap(m_deg_edges,m_new_edges);

		m_quadric_editor->Remove(m_deg_vertices);
		m_face_editor.Remove(m_deg_faces);
		m_face_editor.RemoveVertexNormals(m_deg_vertices);		
		m_color_editor.RemoveVertexColors(m_deg_vertices);
				
		// delete the primitives

		DeletePrimitives(m_deg_edges,m_deg_faces,m_deg_vertices);

	} else {
		// the edge could not be collapsed at the moment - so
		// we adjust it's priority and add it back to the heap.
		m_heap->Remove(edges.begin(),0);
		edges[heap_top].HeapKey() = - MT_INFINITY;
		m_heap->Insert(edges.begin(),heap_top);
	}

	//clear all the temporary buffers

	m_deg_faces.clear();
	m_deg_edges.clear();
	m_deg_vertices.clear();
	
	m_update_faces.clear();
	m_update_vertices.clear();
	m_new_edges.clear();

	return true;

}	

	void
LOD_NdQSDecimator::
DeletePrimitives(
	const vector<LOD_EdgeInd> & degenerate_edges,
	const vector<LOD_FaceInd> & degenerate_faces,
	const vector<LOD_VertexInd> & degenerate_vertices
) {

	// assumes that the 3 vectors are sorted in descending order.

	// Delete Degnerate primitives
	//////////////////////////////


	// delete the old edges - we have to be very careful here
	// mesh.delete() swaps edges to be deleted with the last edge in 
	// the edge buffer. However the next edge to be deleted may have
	// been the last edge in the buffer!

	// One way to solve this is to sort degenerate_edges in descending order.
	// And then delete them in that order.
	
	// it is also vital that degenerate_edges contains no duplicates

	vector<LOD_EdgeInd>::const_iterator edge_it = degenerate_edges.begin();
	vector<LOD_EdgeInd>::const_iterator edge_end = degenerate_edges.end();

	for (; edge_it != edge_end; ++edge_it) {
		m_mesh.DeleteEdge(*edge_it,m_heap);
	}



	vector<LOD_FaceInd>::const_iterator face_it = degenerate_faces.begin();
	vector<LOD_FaceInd>::const_iterator face_end = degenerate_faces.end();
	
	for (;face_it != face_end; ++face_it) {
		m_mesh.DeleteFace(m_extern_editor,*face_it);
	}

	vector<LOD_VertexInd>::const_iterator vertex_it = degenerate_vertices.begin();
	vector<LOD_VertexInd>::const_iterator vertex_end = degenerate_vertices.end();
	
	for (;vertex_it != vertex_end; ++vertex_it) {
		m_mesh.DeleteVertex(m_extern_editor,*vertex_it);
	}
}


	bool
LOD_NdQSDecimator::
BuildHeap(
){
	// build the geometric quadrics 

	if (m_quadric_editor->BuildQuadrics(m_face_editor,true) == false) return false;

	// add in the property quadrics.
	ComputePropertyQuadrics();

	m_quadric_editor->InitializeHeapKeys(m_color_editor);

	m_heap = Heap<LOD_Edge>::New();
	// load in edge pointers to the heap

	vector<LOD_Edge> & edge_set= m_mesh.EdgeSet();
	vector<LOD_Edge>::const_iterator edge_end = edge_set.end();
	vector<LOD_Edge>::iterator edge_start = edge_set.begin();

	vector<int> & heap_vector = m_heap->HeapVector();

	for (int i = 0; i < edge_set.size(); ++i) {
		edge_set[i].HeapPos() = i;
		heap_vector.push_back(i);
	}
	
	m_heap->MakeHeap(edge_set.begin());

	return true;
}

	void
LOD_NdQSDecimator::
UpdateHeap(
	vector<LOD_EdgeInd> &deg_edges,
	vector<LOD_EdgeInd> &new_edges
){
	// first of all compute values for the new edges 
	// and bung them on the heap.

	vector<LOD_Edge>  & edge_set= m_mesh.EdgeSet();

	vector<LOD_EdgeInd>::const_iterator edge_it = new_edges.begin();
	vector<LOD_EdgeInd>::const_iterator end_it = new_edges.end();


	// insert all the new edges		
	///////////////////////////

	// compute edge costs ffor the new edges

	m_quadric_editor->ComputeEdgeCosts(new_edges,m_color_editor);

	// inser the new elements into the heap

	for (; edge_it != end_it; ++edge_it) {		
		m_heap->Insert(edge_set.begin(),*edge_it);
	}


	// remove all the old values from the heap

	edge_it = deg_edges.begin();
	end_it = deg_edges.end();

	for (; edge_it != end_it; ++edge_it) {
		LOD_Edge &e = edge_set[*edge_it];
		m_heap->Remove(edge_set.begin(),e.HeapPos());

		e.HeapPos() = 0xffffffff;

	}
}
	
	void
LOD_NdQSDecimator::
ComputePropertyQuadrics(
){

	vector<LOD_TriFace> & faces = m_mesh.FaceSet();
	vector<LOD_Vertex> & verts = m_mesh.VertexSet();
	vector<LOD_NdQuadric> & quadrics = m_quadric_editor->Quadrics();
	const vector<MT_Vector3> &face_normals = m_face_editor.Normals();

	// compute the linear functionals for each face

	// For each property associated with that face we compute
	// a property gradient, construct a quadric based on this and add
	// it to each of the face's vertex quadrics.

	vector<LOD_TriFace>::const_iterator f_start = faces.begin();
	vector<LOD_TriFace>::const_iterator f_end = faces.end();
	vector<LOD_TriFace>::iterator f = faces.begin();

	// we need a little matrix space to help us with the
	// linear functional computation.

	TNT::Matrix<MT_Scalar> mat(4,4,MT_Scalar(0));
	TNT::Vector<MT_Scalar> vec(4,MT_Scalar(1));

	// some pivots.

	TNT::Vector<TNT::Subscript> pivots(4,int(0));

	// Quadrics now consume heap memory so let's
	// reuse one in the following loop rather than 
	// making one each iteration.

	LOD_NdQuadric qp;


	for (;f != f_end; ++f) {
		
		// collect the coordinates of the face
		// and the normal into a matrix
	
		const LOD_VertexInd * f_verts= f->m_verts;

		const MT_Vector3 & p0 = verts[f_verts[0]].pos;
		const MT_Vector3 & p1 = verts[f_verts[1]].pos;
		const MT_Vector3 & p2 = verts[f_verts[2]].pos;
	
		const MT_Vector3 c0 = m_color_editor.IndexColor(f_verts[0]);
		const MT_Vector3 c1 = m_color_editor.IndexColor(f_verts[1]);
		const MT_Vector3 c2 = m_color_editor.IndexColor(f_verts[2]);

		// get the face normal	

		const MT_Vector3 & fn = face_normals[int(f - f_start)];

		// load into mat

		int i;
		for (i = 0; i < 3; i++) {
			mat[0][i] = p0[i];
			mat[1][i] = p1[i];
			mat[2][i] = p2[i];
			mat[3][i] = fn[i];
		}
		mat[0][3] = MT_Scalar(1);
		mat[1][3] = MT_Scalar(1);
		mat[2][3] = MT_Scalar(1);
		mat[3][3] = MT_Scalar(0);

		// Compute the pivots

		if (TNT::LU_factor(mat,pivots)) {
			// bad face!
			continue;
		}	

		// compute red linear functional

		vec[0] = c0[0];				
		vec[1] = c1[0];
		vec[2] = c2[0];
		vec[3] = MT_Scalar(0);

		TNT::LU_solve(mat,pivots,vec);

		// construct a quadric based on this functional

		qp = LOD_NdQuadric(
			MT_Vector3(vec[0],vec[1],vec[2]),
			vec[3],
			0
		);			
		// compute green functional

		vec[0] = c0[1];				
		vec[1] = c1[1];
		vec[2] = c2[1];
		vec[3] = MT_Scalar(0);

		TNT::LU_solve(mat,pivots,vec);

		// construct a quadric based on this functional

		qp += LOD_NdQuadric(
			MT_Vector3(vec[0],vec[1],vec[2]),
			vec[3],
			1
		);			
		
		// compute blue functional

		vec[0] = c0[2];				
		vec[1] = c1[2];
		vec[2] = c2[2];
		vec[3] = MT_Scalar(0);

		TNT::LU_solve(mat,pivots,vec);

		// construct a quadric based on this functional

		qp += LOD_NdQuadric(
			MT_Vector3(vec[0],vec[1],vec[2]),
			vec[3],
			2
		);			
	
		// add to the geometric quadrics of each of the 
		// vertices of f
		
		qp *= MT_Scalar(50);	


		quadrics[f_verts[0]] += qp;
		quadrics[f_verts[1]] += qp;
		quadrics[f_verts[2]] += qp;
	
		qp.Clear();

	}
}




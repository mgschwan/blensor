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

/** \file decimation/intern/future/LOD_NdQuadricEditor.cpp
 *  \ingroup decimation
 */


#include "LOD_NdQuadricEditor.h"
#include "LOD_ExternNormalEditor.h"
#include "LOD_ExternVColorEditor.h"

// Creation
///////////

using namespace std;


LOD_NdQuadricEditor::
LOD_NdQuadricEditor(
	LOD_ManMesh2 &mesh
) :
	m_quadrics(NULL),
	m_mesh(mesh)
{
};

	LOD_NdQuadricEditor *
LOD_NdQuadricEditor::
New(
	LOD_ManMesh2 &mesh
){
	//same number of quadrics as vertices in the mesh

	NanPtr<LOD_NdQuadricEditor> output(new LOD_NdQuadricEditor(mesh));

	if (output == NULL) {
		return NULL;
	}
	return output.Release();
}


// Property editor interface
////////////////////////////

	void
LOD_NdQuadricEditor::
Remove(
	const std::vector<LOD_VertexInd> &sorted_vertices
){
	vector<LOD_NdQuadric> & quadrics = *m_quadrics;

	vector<LOD_VertexInd>::const_iterator it_start = sorted_vertices.begin();
	vector<LOD_VertexInd>::const_iterator it_end = sorted_vertices.end();

	for (; it_start != it_end; ++it_start) {

		if (quadrics.size() > 0) {
			LOD_NdQuadric temp = quadrics[*it_start];
		
			quadrics[*it_start] = quadrics.back();
			quadrics.back() = temp;

			quadrics.pop_back();
		}
	}
};


// Editor specific methods
//////////////////////////

	bool
LOD_NdQuadricEditor::
BuildQuadrics(
	const LOD_ExternNormalEditor& normal_editor,
	bool preserve_boundaries
){
	if (m_quadrics != NULL) delete(m_quadrics);		

	m_quadrics =new vector<LOD_NdQuadric> (m_mesh.VertexSet().size());
	if (m_quadrics == NULL) return false;

	// iterate through the face set of the mesh
	// compute a quadric based upon that face and 
	// add it to each of it's vertices quadrics.

	const vector<LOD_TriFace> &faces = m_mesh.FaceSet();
	const vector<LOD_Vertex> &verts = m_mesh.VertexSet();
	vector<LOD_Edge> &edges = m_mesh.EdgeSet();	

	const vector<MT_Vector3> &normals = normal_editor.Normals();
	vector<MT_Vector3>::const_iterator normal_it = normals.begin();
	
	vector<LOD_TriFace>::const_iterator face_it = faces.begin();
	vector<LOD_TriFace>::const_iterator face_end = faces.end();

	vector<LOD_NdQuadric> & quadrics = *m_quadrics;


	for (; face_it != face_end; ++face_it, ++normal_it) {
				
		MT_Vector3 normal = *normal_it;
		MT_Scalar offset = -normal.dot(verts[face_it->m_verts[0]].pos);	

		LOD_NdQuadric q(normal,offset);

#if 0
		// try something with the size of the face.

		MT_Vector3 vec1 = 
			verts[face_it->m_verts[1]].pos - 
			verts[face_it->m_verts[0]].pos;

		MT_Vector3 vec2 = 
			verts[face_it->m_verts[2]].pos - 
			verts[face_it->m_verts[1]].pos;

		vec1 = vec1.cross(vec2);

		q *= vec1.length();
#endif
		quadrics[face_it->m_verts[0]] += q;
		quadrics[face_it->m_verts[1]] += q;
		quadrics[face_it->m_verts[2]] += q;
	}

	if (preserve_boundaries) {

		// iterate through the edge set and add a boundary quadric to 
		// each of the boundary edges vertices.
	
		vector<LOD_Edge>::const_iterator edge_it = edges.begin();
		vector<LOD_Edge>::const_iterator edge_end = edges.end();	

		for (; edge_it != edge_end; ++edge_it) {
			if (edge_it->BoundaryEdge()) {

				// compute a plane perpendicular to the edge and the normal
				// of the edges single polygon.
				const MT_Vector3 & v0 = verts[edge_it->m_verts[0]].pos;
				const MT_Vector3 & v1 = verts[edge_it->m_verts[1]].pos;
	
				MT_Vector3 edge_vector = v1 - v0;

				LOD_FaceInd edge_face = edge_it->OpFace(LOD_EdgeInd::Empty());
				edge_vector = edge_vector.cross(normals[edge_face]);

				if (!edge_vector.fuzzyZero()) {
					edge_vector.normalize();
				
					LOD_NdQuadric boundary_q(edge_vector, - edge_vector.dot(v0));	
					boundary_q *= 100;				

					quadrics[edge_it->m_verts[0]] += boundary_q;
					quadrics[edge_it->m_verts[1]] += boundary_q;
				}
			}
		}
	}

	return true;

};

	void
LOD_NdQuadricEditor::
InitializeHeapKeys(
	const LOD_ExternVColorEditor & color_editor
){
	// initiate the heap keys of the edges by computing the edge costs.

	vector<LOD_Edge> &edges = m_mesh.EdgeSet();	
	vector<LOD_NdQuadric> & quadrics = *m_quadrics;

	vector<LOD_Edge>::iterator edge_it = edges.begin();
	vector<LOD_Edge>::const_iterator edge_end = edges.end();

	
	TNT::Vector<MT_Scalar> target(6,MT_Scalar(0));

	for (; edge_it != edge_end; ++edge_it) {
		
		TargetVertex(*edge_it,target,color_editor);
		LOD_Edge &e = *edge_it;
		const LOD_NdQuadric &q0 = quadrics[e.m_verts[0]];
		const LOD_NdQuadric &q1 = quadrics[e.m_verts[1]];

#if 0
		// testing print out target colors.
		
		std::cout << color_editor.IndexColor(e.m_verts[0]) << "\n";
		std::cout << color_editor.IndexColor(e.m_verts[1]) << "\n";

		MT_Vector3 target_color(target[3],target[4],target[5]);

		std::cout << target_color << "\n\n";
#endif

		
		e.HeapKey() = -float(q0.Evaluate(target) + q1.Evaluate(target));
	}
}






	void 
LOD_NdQuadricEditor::
TargetVertex(
	const LOD_Edge & e,
	TNT::Vector<MT_Scalar> &result,
	const LOD_ExternVColorEditor & color_editor
) const {

	// compute an edge contration target for edge ei
	// this is computed by summing it's vertices quadrics and 
	// optimizing the result.
	vector<LOD_Vertex> &verts = m_mesh.VertexSet();
	vector<LOD_NdQuadric> &quadrics = *m_quadrics;

	LOD_VertexInd v0 = e.m_verts[0];
	LOD_VertexInd v1 = e.m_verts[1];

	LOD_NdQuadric q0 = quadrics[v0];
	q0 += quadrics[v1];

	if (q0.Optimize(result)) {
		return;
	} else {
		// the quadric was degenerate -> just take the average of 
		// v0 and v1

		MT_Vector3 t_result = ((verts[v0].pos + verts[v1].pos) * 0.5);
		result[0] = t_result[0];
		result[1] = t_result[1];
		result[2] = t_result[2];
		
		// do the same for the colors

		MT_Vector3 c0 = color_editor.IndexColor(v0);
		MT_Vector3 c1 = color_editor.IndexColor(v0);

		c0 = (c0 + c1) *0.5;
		result[3] = c0[0];
		result[4] = c0[1];
		result[5] = c0[2];

		return;
	}
};

	void
LOD_NdQuadricEditor::
ComputeEdgeCosts(
	const vector<LOD_EdgeInd> &edges,
	const LOD_ExternVColorEditor & color_editor
){ 	
	
	// for each we compute the target vertex and then compute
	// the quadric error e = Q1(v') + Q2(v')
	vector<LOD_Edge> &edge_set = m_mesh.EdgeSet();

	vector<LOD_NdQuadric> &quadrics = *m_quadrics;

	vector<LOD_EdgeInd>::const_iterator edge_it = edges.begin();
	vector<LOD_EdgeInd>::const_iterator edge_end = edges.end();

	TNT::Vector<MT_Scalar> target(6,MT_Scalar(0));

	for (; edge_it != edge_end; ++edge_it) {
		
		TargetVertex(edge_set[*edge_it],target,color_editor);

		LOD_Edge &e = edge_set[*edge_it];
		const LOD_NdQuadric &q0 = quadrics[e.m_verts[0]];
		const LOD_NdQuadric &q1 = quadrics[e.m_verts[1]];
		
		e.HeapKey() = -float(q0.Evaluate(target) + q1.Evaluate(target));
	}
};
	
		


		





	





















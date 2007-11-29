/**
 * BKE_cloth.h
 *
 * $Id: BKE_cloth.h,v 1.1 2007/08/01 02:07:27 daniel Exp $
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef BKE_COLLISIONS_H
#define BKE_COLLISIONS_H

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* types */
#include "BLI_linklist.h"
#include "BKE_DerivedMesh.h"
#include "BKE_object.h"

#include "DNA_modifier_types.h"

// used in kdop.c and collision.c
typedef struct CollisionTree
{
	struct CollisionTree *nodes[4]; // 4 children --> quad-tree
	struct CollisionTree *parent;
	struct CollisionTree *nextLeaf;
	struct CollisionTree *prevLeaf;
	float	bv[26]; // Bounding volume of all nodes / we have 7 axes on a 14-DOP
	int point_index[4]; // supports up to 4 points in a leaf
	int	count_nodes; // how many nodes are used
	int	traversed;  // how many nodes already traversed until this level?
	int	isleaf;
}
CollisionTree;

typedef struct CollisionTree TreeNode;

typedef struct BVH
{
	unsigned int 	numfaces;
	unsigned int 	numverts;
	MVert	 	*xnew; // position of verts at time n 
	MVert	 	*x; // position of verts at time n-1
	MFace 		*mfaces; // just a pointer to the original datastructure
	struct LinkNode *tree;
	CollisionTree 	*root; // TODO: saving the root --> is this really needed? YES!
	CollisionTree 	*leaf_tree; /* Tail of the leaf linked list.	*/
	CollisionTree 	*leaf_root;	/* Head of the leaf linked list.	*/
	float 		epsilon; /* epslion is used for inflation of the k-dop	   */
	int 		flags; /* bvhFlags */
	
}
BVH;

/* used for collisions in kdop.c and also collision.c*/
typedef struct CollisionPair
{
	int point_indexA[4], point_indexB[4];
	float vector[3];
	float normal[3]; // has to be calculated from vector
	float distance;
	float pa[3], pb[3];
}
CollisionPair;


/////////////////////////////////////////////////
// forward declarations
/////////////////////////////////////////////////

// NOTICE: mvert-routines for building + update the BVH are the most native ones

// builds bounding volume hierarchy
BVH *bvh_build_from_mvert (MFace *mfaces, unsigned int numfaces, MVert *x, unsigned int numverts, float epsilon);
BVH *bvh_build_from_float3 (MFace *mfaces, unsigned int numfaces, float (*x)[3], unsigned int numverts, float epsilon);
BVH *bvh_build_from_float4 (MFace *mfaces, unsigned int numfaces, float (*x)[4], unsigned int numverts, float epsilon);

// frees the same
void bvh_free ( BVH *bvh );

// checks two bounding volume hierarchies for potential collisions and returns some list with those
int bvh_traverse(CollisionTree *tree1, CollisionTree *tree2, LinkNode **collision_list);

// update bounding volumes, needs updated positions in bvh->x
void bvh_update_from_mvert(BVH * bvh, MVert *x, unsigned int numverts, MVert *xnew, int moving);
void bvh_update_from_float3(BVH * bvh, float (*x)[3], unsigned int numverts, float (*xnew)[3], int moving);
void bvh_update_from_float4(BVH * bvh, float (*x)[4], unsigned int numverts, float (*xnew)[4], int moving);

LinkNode *BLI_linklist_append_fast (LinkNode **listp, void *ptr);

// move Collision modifier object inter-frame with step = [0,1]
// defined in collisions.c
void collision_move_object(CollisionModifierData *collmd, float step, float prevstep);

// interface for collision functions
void collisions_compute_barycentric (float pv[3], float p1[3], float p2[3], float p3[3], float *w1, float *w2, float *w3);
void interpolateOnTriangle(float to[3], float v1[3], float v2[3], float v3[3], double w1, double w2, double w3);

/////////////////////////////////////////////////

#endif


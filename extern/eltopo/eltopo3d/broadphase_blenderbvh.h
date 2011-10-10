#if 0
// ---------------------------------------------------------
//
//  broadphase_blenderbvh.h
//  Joseph Eagar 2011
//  
//  Broad phase collision detection culling using a K-DOP bvh structure
//
// ---------------------------------------------------------

#ifndef BROADPHASEGRID_H
#define BROADPHASEGRID_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <broadphase.h>
#include "../../../source/blender/blenlib/BLI_kdopbvh.h"

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

class DynamicSurface;

// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Broad phase collision detector using three regular grids: one grid each for vertices, edges and triangles.
///
// --------------------------------------------------------

class BroadPhaseBVH : public BroadPhase
{
private:
	BVHTree *v_bvhtree;
	BVHTree *e_bvhtree;
	BVHTree *t_bvhtree;

public:
   
	BroadPhaseBVH() {
		m_bvhtree = NULL;
	}
  
   ~BroadPhaseGrid();
   
   /// Rebuild the broad phase using current vertex positions
   ///
   void update_broad_phase_static( const DynamicSurface& surface );
   
   /// Rebuild the broad phase using current and predicted vertex positions
   ///
   void update_broad_phase_continuous( const DynamicSurface& surface );

   inline void add_vertex( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high ); 
   inline void add_edge( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high ); 
   inline void add_triangle( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high );   
   
   inline void update_vertex( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high ); 
   inline void update_edge( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high ); 
   inline void update_triangle( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high ); 
   
   inline void remove_vertex( unsigned int index ); 
   inline void remove_edge( unsigned int index ); 
   inline void remove_triangle( unsigned int index ); 
   
   /// Get the set of vertices whose bounding volumes overlap the specified bounding volume
   ///
   inline void get_potential_vertex_collisions( const Vec3d& aabb_low, 
                                                const Vec3d& aabb_high, 
                                                std::vector<unsigned int>& overlapping_vertices );
   
   /// Get the set of edges whose bounding volumes overlap the specified bounding volume
   ///
   inline void get_potential_edge_collisions( const Vec3d& aabb_low, 
                                              const Vec3d& aabb_high, 
                                              std::vector<unsigned int>& overlapping_edges );
   
   /// Get the set of triangles whose bounding volumes overlap the specified bounding volume
   ///
   inline void get_potential_triangle_collisions( const Vec3d& aabb_low, 
                                                  const Vec3d& aabb_high, 
                                                  std::vector<unsigned int>& overlapping_triangles );

   /// Rebuild one of the grids
   ///
   void build_acceleration_grid( AccelerationGrid& grid, 
                                 std::vector<Vec3d>& xmins, 
                                 std::vector<Vec3d>& xmaxs, 
                                 double length_scale, 
                                 double grid_padding );
   
   /// Regular grids
   ///
   AccelerationGrid m_vertex_grid;
   AccelerationGrid m_edge_grid;
   AccelerationGrid m_triangle_grid;  
   
};

// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Add a vertex to the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::add_vertex( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_vertex_grid.add_element( index, aabb_low, aabb_high );
}

// --------------------------------------------------------
///
/// Add an edge to the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::add_edge( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_edge_grid.add_element( index, aabb_low, aabb_high );
}

// --------------------------------------------------------
///
/// Add a triangle to the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::add_triangle( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_triangle_grid.add_element( index, aabb_low, aabb_high );
}


inline void BroadPhaseGrid::update_vertex( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_vertex_grid.update_element( index, aabb_low, aabb_high );
}

inline void BroadPhaseGrid::update_edge( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_edge_grid.update_element( index, aabb_low, aabb_high );   
}

inline void BroadPhaseGrid::update_triangle( unsigned int index, const Vec3d& aabb_low, const Vec3d& aabb_high )
{
   m_triangle_grid.update_element( index, aabb_low, aabb_high );   
}


// --------------------------------------------------------
///
/// Remove a vertex from the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::remove_vertex( unsigned int index )
{
   m_vertex_grid.remove_element( index );
}

// --------------------------------------------------------
///
/// Remove an edge from the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::remove_edge( unsigned int index )
{
   m_edge_grid.remove_element( index );
}

// --------------------------------------------------------
///
/// Remove a triangle from the broad phase
///
// --------------------------------------------------------

inline void BroadPhaseGrid::remove_triangle( unsigned int index )
{
   m_triangle_grid.remove_element( index );
}

// --------------------------------------------------------
///
/// Query the broad phase to get the set of all vertices overlapping the given AABB
///
// --------------------------------------------------------

inline void BroadPhaseGrid::get_potential_vertex_collisions( const Vec3d& aabb_low, const Vec3d& aabb_high, std::vector<unsigned int>& overlapping_vertices )
{
   m_vertex_grid.find_overlapping_elements( aabb_low, aabb_high, overlapping_vertices );
}

// --------------------------------------------------------
///
/// Query the broad phase to get the set of all edges overlapping the given AABB
///
// --------------------------------------------------------

inline void BroadPhaseGrid::get_potential_edge_collisions( const Vec3d& aabb_low, const Vec3d& aabb_high, std::vector<unsigned int>& overlapping_edges )
{
   m_edge_grid.find_overlapping_elements( aabb_low, aabb_high, overlapping_edges );
}

// --------------------------------------------------------
///
/// Query the broad phase to get the set of all triangles overlapping the given AABB
///
// --------------------------------------------------------

inline void BroadPhaseGrid::get_potential_triangle_collisions( const Vec3d& aabb_low, const Vec3d& aabb_high, std::vector<unsigned int>& overlapping_triangles )
{
   m_triangle_grid.find_overlapping_elements( aabb_low, aabb_high, overlapping_triangles );
}

#endif



#endif

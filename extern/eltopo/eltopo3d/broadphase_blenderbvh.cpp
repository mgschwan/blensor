#if 0
// ---------------------------------------------------------
//
//  broadphase_blenderbvh.cpp
//  Joseph Eagar 2010
//  
//  Broad phase collision detection culling using blender's kdop bvh.
//
// ---------------------------------------------------------

// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <broadphasegrid.h>
#include <dynamicsurface.h>

// ---------------------------------------------------------
// Global externs
// ---------------------------------------------------------

// ---------------------------------------------------------
// Local constants, typedefs, macros
// ---------------------------------------------------------

// ---------------------------------------------------------
// Static function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------


// --------------------------------------------------------
///
/// Rebuild acceleration grids according to the given triangle mesh
///
// --------------------------------------------------------

static void build_bvh_tree
void BroadPhaseGrid::update_broad_phase_static( const DynamicSurface& surface )
{
   double grid_scale = surface.get_average_edge_length();
   
   {
      unsigned int num_vertices = surface.m_positions.size();
      std::vector<Vec3d> vertex_xmins(num_vertices), vertex_xmaxs(num_vertices);
      for(unsigned int i = 0; i < num_vertices; i++)
      {
         surface.vertex_static_bounds(i, vertex_xmins[i], vertex_xmaxs[i]);
      }      
      build_acceleration_grid( m_vertex_grid, vertex_xmins, vertex_xmaxs, grid_scale, surface.m_proximity_epsilon );
   }
   
   {
      unsigned int num_edges = surface.m_mesh.m_edges.size();
      std::vector<Vec3d> edge_xmins(num_edges), edge_xmaxs(num_edges);
      for(unsigned int i = 0; i < num_edges; i++)
      {
         surface.edge_static_bounds(i, edge_xmins[i], edge_xmaxs[i]);
      }      
      if (num_edges)
		  build_acceleration_grid( m_edge_grid, edge_xmins, edge_xmaxs, grid_scale, surface.m_proximity_epsilon );
   }
   
   {
      unsigned int num_triangles = surface.m_mesh.m_tris.size();
      std::vector<Vec3d> tri_xmins(num_triangles), tri_xmaxs(num_triangles);
      for(unsigned int i = 0; i < num_triangles; i++)
      {
         surface.triangle_static_bounds(i, tri_xmins[i], tri_xmaxs[i]);
      }   
	  
      if (num_triangles)
		  build_acceleration_grid( m_triangle_grid, tri_xmins, tri_xmaxs, grid_scale, surface.m_proximity_epsilon );  
   }
   
}



// --------------------------------------------------------
///
/// Rebuild acceleration grids according to the given triangle mesh
///
// --------------------------------------------------------

void BroadPhaseGrid::update_broad_phase_continuous( const DynamicSurface& surface )
{
   double grid_scale = surface.get_average_edge_length();
   
   {
      unsigned int num_vertices = surface.m_positions.size();
      std::vector<Vec3d> vertex_xmins(num_vertices), vertex_xmaxs(num_vertices);
      for(unsigned int i = 0; i < num_vertices; i++)
      {           
         surface.vertex_continuous_bounds(i, vertex_xmins[i], vertex_xmaxs[i]);
      }
	  
      build_acceleration_grid( m_vertex_grid, vertex_xmins, vertex_xmaxs, grid_scale, surface.m_proximity_epsilon );
   }
   
   {
      unsigned int num_edges = surface.m_mesh.m_edges.size();
      std::vector<Vec3d> edge_xmins(num_edges), edge_xmaxs(num_edges);
      for(unsigned int i = 0; i < num_edges; i++)
      {
         surface.edge_continuous_bounds(i, edge_xmins[i], edge_xmaxs[i]);
      }
      if (num_edges)
		  build_acceleration_grid( m_edge_grid, edge_xmins, edge_xmaxs, grid_scale, surface.m_proximity_epsilon );
   }
   
   {
      unsigned int num_triangles = surface.m_mesh.m_tris.size();
      std::vector<Vec3d> tri_xmins(num_triangles), tri_xmaxs(num_triangles);
      for(unsigned int i = 0; i < num_triangles; i++)
      {            
         surface.triangle_continuous_bounds(i, tri_xmins[i], tri_xmaxs[i]);
      }
      if (num_triangles)
		  build_acceleration_grid( m_triangle_grid, tri_xmins, tri_xmaxs, grid_scale, surface.m_proximity_epsilon );  
   }
   
}

#endif

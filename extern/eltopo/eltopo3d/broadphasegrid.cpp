// ---------------------------------------------------------
//
//  broadphasegrid.cpp
//  Tyson Brochu 2008
//  
//  Broad phase collision detection culling using three regular, volumetric grids.
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
/// Construct one grid from the given set of AABBs, using the given length scale as the cell size, with the given padding
///
// --------------------------------------------------------

void BroadPhaseGrid::build_acceleration_grid( AccelerationGrid& grid, 
                                              std::vector<Vec3d>& xmins, 
                                              std::vector<Vec3d>& xmaxs, 
                                              double length_scale, 
                                              double grid_padding )
{

   Vec3d xmax = xmaxs[0];
   Vec3d xmin = xmins[0];
   double maxdistance = 0;
   
   unsigned int n = xmins.size();
   
   for(unsigned int i = 0; i < n; i++)
   {
      update_minmax(xmins[i], xmin, xmax);
      update_minmax(xmaxs[i], xmin, xmax);
      maxdistance = std::max(maxdistance, mag(xmaxs[i] - xmins[i]));
   }
   
   for(unsigned int i = 0; i < 3; i++)
   {
      xmin[i] -= 2*maxdistance + grid_padding;
      xmax[i] += 2*maxdistance + grid_padding;
   }
   
   Vec3ui dims(1,1,1);
          
   if(mag(xmax-xmin) > grid_padding)
   {
      for(unsigned int i = 0; i < 3; i++)
      {
         unsigned int d = (unsigned int)ceil((xmax[i] - xmin[i])/length_scale);
         
         if(d < 1) d = 1;
         if(d > n) d = n;
         dims[i] = d;
      }
   }
      
   grid.set(dims, xmin, xmax);
   
   for(unsigned int i = n; i > 0; i--)
   {
      unsigned int index = i - 1;
      
      // don't add inside-out AABBs
      if ( xmins[index][0] > xmaxs[index][0] )  { continue; }
      
      grid.add_element(index, xmins[index], xmaxs[index]);
   }
}


// --------------------------------------------------------
///
/// Rebuild acceleration grids according to the given triangle mesh
///
// --------------------------------------------------------

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


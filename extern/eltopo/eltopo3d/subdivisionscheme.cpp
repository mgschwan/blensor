// ---------------------------------------------------------
//
//  subdivisionscheme.cpp
//  Tyson Brochu 2008
//  
//  A collection of interpolation schemes for generating vertex locations.
//
// ---------------------------------------------------------

// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <subdivisionscheme.h>
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
/// Midpoint scheme: simply places the new vertex at the midpoint of the edge
///
// --------------------------------------------------------

void MidpointScheme::generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point )
{
   const NonDestructiveTriMesh& mesh = surface.m_mesh;
   const std::vector<Vec3d>& positions = surface.m_positions;
   unsigned int p1_index = mesh.m_edges[edge_index][0];
	unsigned int p2_index = mesh.m_edges[edge_index][1];   
   
   new_point = 0.5 * ( positions[ p1_index ] + positions[ p2_index ] );
}


// --------------------------------------------------------
///
/// Butterfly scheme: uses a defined weighting of nearby vertices to determine the new vertex location
///
// --------------------------------------------------------

void ButterflyScheme::generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point )
{
   const NonDestructiveTriMesh& mesh = surface.m_mesh;
   const std::vector<Vec3d>& positions = surface.m_positions;
   
   unsigned int p1_index = mesh.m_edges[edge_index][0];
	unsigned int p2_index = mesh.m_edges[edge_index][1];
	
   unsigned int tri0 = mesh.m_edgetri[edge_index][0];
   unsigned int tri1 = mesh.m_edgetri[edge_index][1];
   
	unsigned int p3_index = mesh.get_third_vertex( mesh.m_edges[edge_index][0], mesh.m_edges[edge_index][1], mesh.m_tris[tri0] );
	unsigned int p4_index = mesh.get_third_vertex( mesh.m_edges[edge_index][0], mesh.m_edges[edge_index][1], mesh.m_tris[tri1] );
	
	unsigned int adj_edges[4] = { mesh.get_edge( p1_index, p3_index ),
      mesh.get_edge( p2_index, p3_index ),
      mesh.get_edge( p1_index, p4_index ),
      mesh.get_edge( p2_index, p4_index ) };
   
	unsigned int q_indices[4];
	
	for ( unsigned int i = 0; i < 4; ++i )
	{
		const std::vector<unsigned int>& adj_tris = mesh.m_edgetri[ adj_edges[i] ];
		if ( adj_tris.size() != 2 )
		{
         // abort
			new_point = 0.5 * ( positions[ p1_index ] + positions[ p2_index ] );
         return;
		}
		
		if ( adj_tris[0] == tri0 || adj_tris[0] == tri1 )
		{
			q_indices[i] = mesh.get_third_vertex( mesh.m_edges[ adj_edges[i] ][0], mesh.m_edges[ adj_edges[i] ][1], mesh.m_tris[ adj_tris[1] ] );
		}
		else
		{
			q_indices[i] = mesh.get_third_vertex( mesh.m_edges[ adj_edges[i] ][0], mesh.m_edges[ adj_edges[i] ][1], mesh.m_tris[ adj_tris[0] ] );
		}
	}
   
	new_point =   8. * positions[ p1_index ] + 8. * positions[ p2_index ] + 2. * positions[ p3_index ] + 2. * positions[ p4_index ]
                       - positions[ q_indices[0] ] - positions[ q_indices[1] ] - positions[ q_indices[2] ] - positions[ q_indices[3] ];
   
	new_point *= 0.0625;
   
}


// --------------------------------------------------------
///
/// Quadric error minimization scheme: places the new vertex at the location that minimizes the change in the quadric metric tensor along the edge.
///
// --------------------------------------------------------

void QuadraticErrorMinScheme::generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point )
{
   const NonDestructiveTriMesh& mesh = surface.m_mesh;
   const std::vector<Vec3d>& positions = surface.m_positions;

   unsigned int v0 = mesh.m_edges[edge_index][0];
   unsigned int v1 = mesh.m_edges[edge_index][1];
   
   Mat33d Q;
   zero(Q);
   Vec3d b;
   zero(b);
   
   std::vector<unsigned int> triangles_counted;
   
   Mat<1,1,double> constant_dist;
   constant_dist.a[0] = 0;
   
   for ( unsigned int i = 0; i < mesh.m_vtxtri[v0].size(); ++i )
   {
      unsigned int t = mesh.m_vtxtri[v0][i];
      const Vec3d& plane_normal = surface.get_triangle_normal( t );
      Q += outer( plane_normal, plane_normal );
      b += dot( positions[v0], plane_normal ) * plane_normal;
      constant_dist.a[0] += dot( plane_normal, positions[v0] ) * dot( plane_normal, positions[v0] );
      triangles_counted.push_back(t);
   }
   
   for ( unsigned int i = 0; i < mesh.m_vtxtri[v1].size(); ++i )
   {
      unsigned int t = mesh.m_vtxtri[v1][i];
      
      bool already_counted = false;
      for ( unsigned int j = 0; j < triangles_counted.size(); ++j ) 
      {
         if ( t == triangles_counted[j] )
         {
            already_counted = true;
         }
      }
      
      if ( !already_counted )
      {
         const Vec3d& plane_normal = surface.get_triangle_normal( t );
         Q += outer( plane_normal, plane_normal );
         b += dot( positions[v1], plane_normal ) * plane_normal;
         constant_dist.a[0] += dot( plane_normal, positions[v1] ) * dot( plane_normal, positions[v1] );
      }
   }
   
   // Compute normal direction
   Vec3d normal = 0.5 * (surface.get_vertex_normal(v0) + surface.get_vertex_normal(v1));
   normalize(normal);
   
   Mat<3,1,double> n;
   n(0,0) = normal[0];
   n(1,0) = normal[1];
   n(2,0) = normal[2];
   
   // Compute edge midpoint
   Vec3d midpoint = 0.5 * (positions[v0] + positions[v1]);   
   Mat<3,1,double> m;
   m(0,0) = midpoint[0];
   m(1,0) = midpoint[1];
   m(2,0) = midpoint[2]; 
   
   Mat<3,1,double> d;
   d(0,0) = b[0];
   d(1,0) = b[1];
   d(2,0) = b[2];
   
   double LHS = 2.0 * (n.transpose()*Q*n).a[0];              // result of multiplication is Mat<1,1,double>, hence the .a[0]
   double RHS = ( 2.0 * (n.transpose()*d) - (n.transpose()*Q*m) - (m.transpose()*Q*n) ).a[0];
   
   double a;
   if ( fabs(LHS) > 1e-10 )
   {
      a = RHS / LHS;
   }
   else
   {
      a = 0.0;
   }
   
   Mat<3,1,double> v = m + (a * n);
   
   double v_error = (v.transpose() * Q * v - 2.0 * (v.transpose() * d) + constant_dist).a[0];
   double m_error = (m.transpose() * Q * m - 2.0 * (m.transpose() * d) + constant_dist).a[0];
   
   //assert( v_error < m_error + 1e-8 );
   
   if ( surface.m_verbose )
   {
      std::cout << "a: " << a << std::endl;
      std::cout << "error at v: " << v_error << std::endl;
      std::cout << "error at midpoint: " << m_error << std::endl;
   }
   
   new_point = Vec3d( v.a[0], v.a[1], v.a[2] );
      
}

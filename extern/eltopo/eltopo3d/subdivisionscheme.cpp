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

#include <mat.h>
#include <surftrack.h>

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

void MidpointScheme::generate_new_midpoint( size_t edge_index, const SurfTrack& surface, Vec3d& new_point )
{
    const NonDestructiveTriMesh& mesh = surface.m_mesh;
    const std::vector<Vec3d>& positions = surface.get_positions();
    size_t p1_index = mesh.m_edges[edge_index][0];
	size_t p2_index = mesh.m_edges[edge_index][1];   
    
    new_point = 0.5 * ( positions[ p1_index ] + positions[ p2_index ] );
}


// --------------------------------------------------------
///
/// Butterfly scheme: uses a defined weighting of nearby vertices to determine the new vertex location
///
// --------------------------------------------------------

void ButterflyScheme::generate_new_midpoint( size_t edge_index, const SurfTrack& surface, Vec3d& new_point )
{
    const NonDestructiveTriMesh& mesh = surface.m_mesh;
    const std::vector<Vec3d>& positions = surface.get_positions();
    
    size_t p1_index = mesh.m_edges[edge_index][0];
	size_t p2_index = mesh.m_edges[edge_index][1];
	
    size_t tri0 = mesh.m_edge_to_triangle_map[edge_index][0];
    size_t tri1 = mesh.m_edge_to_triangle_map[edge_index][1];
    
	size_t p3_index = mesh.get_third_vertex( mesh.m_edges[edge_index][0], mesh.m_edges[edge_index][1], mesh.get_triangle(tri0) );
	size_t p4_index = mesh.get_third_vertex( mesh.m_edges[edge_index][0], mesh.m_edges[edge_index][1], mesh.get_triangle(tri1) );
	
	size_t adj_edges[4] = { mesh.get_edge_index( p1_index, p3_index ),
        mesh.get_edge_index( p2_index, p3_index ),
        mesh.get_edge_index( p1_index, p4_index ),
        mesh.get_edge_index( p2_index, p4_index ) };
    
	size_t q_indices[4];
	
	for ( size_t i = 0; i < 4; ++i )
	{
		const std::vector<size_t>& adj_tris = mesh.m_edge_to_triangle_map[ adj_edges[i] ];
		if ( adj_tris.size() != 2 )
		{
            // abort
			new_point = 0.5 * ( positions[ p1_index ] + positions[ p2_index ] );
            return;
		}
		
		if ( adj_tris[0] == tri0 || adj_tris[0] == tri1 )
		{
			q_indices[i] = mesh.get_third_vertex( mesh.m_edges[ adj_edges[i] ][0], mesh.m_edges[ adj_edges[i] ][1], mesh.get_triangle( adj_tris[1] ) );
		}
		else
		{
			q_indices[i] = mesh.get_third_vertex( mesh.m_edges[ adj_edges[i] ][0], mesh.m_edges[ adj_edges[i] ][1], mesh.get_triangle( adj_tris[0] ) );
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

void QuadraticErrorMinScheme::generate_new_midpoint( size_t edge_index, const SurfTrack& surface, Vec3d& new_point )
{
    const NonDestructiveTriMesh& mesh = surface.m_mesh;
    const std::vector<Vec3d>& positions = surface.get_positions();
    
    size_t v0 = mesh.m_edges[edge_index][0];
    size_t v1 = mesh.m_edges[edge_index][1];
    
    Mat33d Q;
    zero(Q);
    Vec3d b;
    zero(b);
    
    std::vector<size_t> triangles_counted;
    
    Mat<1,1,double> constant_dist;
    constant_dist.a[0] = 0;
    
    for ( size_t i = 0; i < mesh.m_vertex_to_triangle_map[v0].size(); ++i )
    {
        size_t t = mesh.m_vertex_to_triangle_map[v0][i];
        const Vec3d& plane_normal = surface.get_triangle_normal( t );
        Q += outer( plane_normal, plane_normal );
        b += dot( positions[v0], plane_normal ) * plane_normal;
        constant_dist.a[0] += dot( plane_normal, positions[v0] ) * dot( plane_normal, positions[v0] );
        triangles_counted.push_back(t);
    }
    
    for ( size_t i = 0; i < mesh.m_vertex_to_triangle_map[v1].size(); ++i )
    {
        size_t t = mesh.m_vertex_to_triangle_map[v1][i];
        
        bool already_counted = false;
        for ( size_t j = 0; j < triangles_counted.size(); ++j ) 
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

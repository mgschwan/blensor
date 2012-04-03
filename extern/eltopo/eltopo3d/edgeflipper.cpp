// ---------------------------------------------------------
//
//  edgeflipper.cpp
//  Tyson Brochu 2011
//  
//  Functions supporting the "edge flip" operation: replacing non-delaunay edges with their dual edge.
//
// ---------------------------------------------------------

#include <edgeflipper.h>

#include <broadphase.h>
#include <collisionqueries.h>
#include <nondestructivetrimesh.h>
#include <runstats.h>
#include <surftrack.h>
#include <trianglequality.h>

// ---------------------------------------------------------
//  Extern globals
// ---------------------------------------------------------

extern RunStats g_stats;

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Check whether the new triangles created by flipping an edge introduce any intersection
///
// --------------------------------------------------------

bool EdgeFlipper::flip_introduces_collision( size_t edge_index, 
                                            const Vec2st& new_edge, 
                                            const Vec3st& new_triangle_a, 
                                            const Vec3st& new_triangle_b )
{  
    
    NonDestructiveTriMesh& m_mesh = m_surf.m_mesh;
    const std::vector<Vec3d>& xs = m_surf.get_positions();
    
    if ( !m_surf.m_collision_safety )
    {
        return false;
    }
    
    const Vec2st& old_edge = m_mesh.m_edges[edge_index];
    
    size_t tet_vertex_indices[4] = { old_edge[0], old_edge[1], new_edge[0], new_edge[1] };
    
    const Vec3d tet_vertex_positions[4] = { xs[ tet_vertex_indices[0] ], 
        xs[ tet_vertex_indices[1] ], 
        xs[ tet_vertex_indices[2] ], 
        xs[ tet_vertex_indices[3] ] };
    
    Vec3d low, high;
    minmax( tet_vertex_positions[0], tet_vertex_positions[1], tet_vertex_positions[2], tet_vertex_positions[3], low, high );
    
    std::vector<size_t> overlapping_vertices;
    m_surf.m_broad_phase->get_potential_vertex_collisions( low, high, true, true, overlapping_vertices );
    
    // do point-in-tet tests
    for ( size_t i = 0; i < overlapping_vertices.size(); ++i ) 
    { 
        if ( (overlapping_vertices[i] == old_edge[0]) || (overlapping_vertices[i] == old_edge[1]) || 
            (overlapping_vertices[i] == new_edge[0]) || (overlapping_vertices[i] == new_edge[1]) ) 
        {
            continue;
        }
        
        if ( point_tetrahedron_intersection( xs[overlapping_vertices[i]], overlapping_vertices[i],
                                            tet_vertex_positions[0], tet_vertex_indices[0],
                                            tet_vertex_positions[1], tet_vertex_indices[1],
                                            tet_vertex_positions[2], tet_vertex_indices[2],
                                            tet_vertex_positions[3], tet_vertex_indices[3] ) ) 
        {
            return true;
        }
    }
    
    //
    // Check new triangle A vs existing edges
    //
    
    minmax( xs[new_triangle_a[0]], xs[new_triangle_a[1]], xs[new_triangle_a[2]], low, high );
    std::vector<size_t> overlapping_edges;
    m_surf.m_broad_phase->get_potential_edge_collisions( low, high, true, true, overlapping_edges );
    
    for ( size_t i = 0; i < overlapping_edges.size(); ++i )
    {
        size_t overlapping_edge_index = overlapping_edges[i];
        const Vec2st& edge = m_mesh.m_edges[overlapping_edge_index];
        
        if ( check_edge_triangle_intersection_by_index( edge[0], edge[1], 
                                                       new_triangle_a[0], new_triangle_a[1], new_triangle_a[2], 
                                                       xs, m_surf.m_verbose ) )
        {
            return true;
        }      
    }
    
    //
    // Check new triangle B vs existing edges
    //
    
    minmax( xs[new_triangle_b[0]], xs[new_triangle_b[1]], xs[new_triangle_b[2]], low, high );
    
    overlapping_edges.clear();
    m_surf.m_broad_phase->get_potential_edge_collisions( low, high, true, true, overlapping_edges );
    
    for ( size_t i = 0; i < overlapping_edges.size(); ++i )
    {
        size_t overlapping_edge_index = overlapping_edges[i];
        const Vec2st& edge = m_mesh.m_edges[overlapping_edge_index];
        
        if ( check_edge_triangle_intersection_by_index( edge[0], edge[1], 
                                                       new_triangle_b[0], new_triangle_b[1], new_triangle_b[2], 
                                                       xs, m_surf.m_verbose ) )
        {
            return true;
        }      
    }
    
    //
    // Check new edge vs existing triangles
    //   
    
    minmax( xs[new_edge[0]], xs[new_edge[1]], low, high );
    std::vector<size_t> overlapping_triangles;
    m_surf.m_broad_phase->get_potential_triangle_collisions( low, high, true, true, overlapping_triangles );
    
    for ( size_t i = 0; i <  overlapping_triangles.size(); ++i )
    {
        const Vec3st& tri = m_mesh.get_triangle(overlapping_triangles[i]);
        
        if ( check_edge_triangle_intersection_by_index( new_edge[0], new_edge[1],
                                                       tri[0], tri[1], tri[2],
                                                       xs, m_surf.m_verbose ) )
        {         
            return true;
        }                                              
    }
    
    return false;
    
}


// --------------------------------------------------------
///
/// Flip an edge: remove the edge and its incident triangles, then add a new edge and two new triangles
///
// --------------------------------------------------------

bool EdgeFlipper::flip_edge( size_t edge, 
                            size_t tri0, 
                            size_t tri1, 
                            size_t third_vertex_0, 
                            size_t third_vertex_1 )
{  
    
    g_stats.add_to_int( "EdgeFlipper:edge_flip_attempt", 1 );
    
    NonDestructiveTriMesh& m_mesh = m_surf.m_mesh;
    const std::vector<Vec3d>& xs = m_surf.get_positions();
    
    Vec2st& edge_vertices = m_mesh.m_edges[edge];
    
    // Find the vertices which will form the new edge
    Vec2st new_edge( third_vertex_0, third_vertex_1);
    
    // --------------
    
    // Control volume change
    double vol = fabs( signed_volume( xs[edge_vertices[0]], 
                                     xs[edge_vertices[1]], 
                                     xs[new_edge[0]], 
                                     xs[new_edge[1]] ) ); 
    
    if ( vol > m_surf.m_max_volume_change )
    {
        g_stats.add_to_int( "EdgeFlipper:edge_flip_volume_change", 1 );
        if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: volume change = " << vol << std::endl; }
        return false;
    }
    
    // --------------
    
    // Prevent non-manifold surfaces if we're not allowing them
    if ( false == m_surf.m_allow_non_manifold )
    {
        for ( size_t i = 0; i < m_mesh.m_vertex_to_edge_map[ third_vertex_0 ].size(); ++i )
        {
            if ( ( m_mesh.m_edges[ m_mesh.m_vertex_to_edge_map[third_vertex_0][i] ][0] == third_vertex_1 ) ||
                ( m_mesh.m_edges[ m_mesh.m_vertex_to_edge_map[third_vertex_0][i] ][1] == third_vertex_1 ) )
            {
                // edge already exists
                if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: edge exists" << std::endl;             }
                
                g_stats.add_to_int( "EdgeFlipper:edge_flip_would_be_nonmanifold", 1 );
                
                return false;
            }
        }
    }
    
    // --------------
    
    // Don't flip edge on a degenerate tet
    if ( third_vertex_0 == third_vertex_1 )
    {
        if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: degenerate tet" << std::endl; }
        g_stats.add_to_int( "EdgeFlipper:edge_flip_on_degenerate_tet", 1 );
        return false;
    }
    
    // --------------
    
    // Create the new triangles
    // new edge winding order == winding order of old triangle0 == winding order of new triangle0
    
    size_t new_triangle_third_vertex_0, new_triangle_third_vertex_1;
    if ( m_mesh.oriented( m_mesh.m_edges[edge][0], m_mesh.m_edges[edge][1], m_mesh.get_triangle(tri0) ) ) 
    {
		assert( m_mesh.oriented( m_mesh.m_edges[edge][1], m_mesh.m_edges[edge][0], m_mesh.get_triangle(tri1) ) );
        new_triangle_third_vertex_0 = m_mesh.m_edges[edge][1];
        new_triangle_third_vertex_1 = m_mesh.m_edges[edge][0];
    }
    else
    {
		assert( m_mesh.oriented( m_mesh.m_edges[edge][0], m_mesh.m_edges[edge][1], m_mesh.get_triangle(tri1) ) );
		assert( m_mesh.oriented( m_mesh.m_edges[edge][1], m_mesh.m_edges[edge][0], m_mesh.get_triangle(tri0) ) );
        new_triangle_third_vertex_0 = m_mesh.m_edges[edge][0];
        new_triangle_third_vertex_1 = m_mesh.m_edges[edge][1];
    }
    
    Vec3st new_triangle0( new_edge[0], new_edge[1], new_triangle_third_vertex_0 );
    Vec3st new_triangle1( new_edge[1], new_edge[0], new_triangle_third_vertex_1 );
    
    if ( m_surf.m_verbose )
    {
        std::cout << "flip --- new triangle 0: " << new_triangle0 << std::endl;
        std::cout << "flip --- new triangle 1: " << new_triangle1 << std::endl;
    }
    
    // --------------
    
    // if both triangle normals agree before flipping, make sure they agree after flipping
    if ( dot( m_surf.get_triangle_normal(tri0), m_surf.get_triangle_normal(tri1) ) > 0.0 ) 
    {
        if ( dot( m_surf.get_triangle_normal(new_triangle0), m_surf.get_triangle_normal(new_triangle1) ) < 0.0 )
        {
            if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: normal inversion" << std::endl; }
            g_stats.add_to_int( "EdgeFlipper:edge_flip_normal_inversion", 1 );
            return false;
        }
        
        if ( dot( m_surf.get_triangle_normal(new_triangle0), m_surf.get_triangle_normal(tri0) ) < 0.0 )
        {
            if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: normal inversion" << std::endl; }
            g_stats.add_to_int( "EdgeFlipper:edge_flip_normal_inversion", 1 );         
            return false;
        }
        
        if ( dot( m_surf.get_triangle_normal(new_triangle1), m_surf.get_triangle_normal(tri1) ) < 0.0 )
        {
            if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: normal inversion" << std::endl; }
            g_stats.add_to_int( "EdgeFlipper:edge_flip_normal_inversion", 1 );         
            return false;
        }
        
        if ( dot( m_surf.get_triangle_normal(new_triangle0), m_surf.get_triangle_normal(tri1) ) < 0.0 )
        {
            if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: normal inversion" << std::endl; }
            g_stats.add_to_int( "EdgeFlipper:edge_flip_normal_inversion", 1 );         
            return false;
        }
        
        if ( dot( m_surf.get_triangle_normal(new_triangle1), m_surf.get_triangle_normal(tri0) ) < 0.0 )
        {
            if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: normal inversion" << std::endl; }
            g_stats.add_to_int( "EdgeFlipper:edge_flip_normal_inversion", 1 );         
            return false;
        }
    }
    
    // --------------
    
    // Prevent intersection
    if ( m_surf.m_collision_safety && flip_introduces_collision( edge, new_edge, new_triangle0, new_triangle1 ) )
    {
        if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: intersection" << std::endl; }
        
        g_stats.add_to_int( "EdgeFlipper:edge_flip_collision", 1 );
        
        return false;
    }
    
    // --------------
    
    // Prevent degenerate triangles
    if ( triangle_area( xs[new_triangle0[0]], xs[new_triangle0[1]], xs[new_triangle0[2]] ) < m_surf.m_min_triangle_area )
    {
        if ( m_surf.m_verbose ) { std::cout << "edge flip rejected: area too small" << std::endl;    }
        g_stats.add_to_int( "EdgeFlipper:edge_flip_new_area_too_small", 1 );      
        return false;
    }
    
    if ( triangle_area( xs[new_triangle1[0]], xs[new_triangle1[1]], xs[new_triangle1[2]] ) < m_surf.m_min_triangle_area )
    {
        if ( m_surf.m_verbose ) {std::cout << "edge flip rejected: area too small" << std::endl; }
        g_stats.add_to_int( "EdgeFlipper:edge_flip_new_area_too_small", 1 );            
        return false;
    }
    
    
    // --------------
    
    // Control change in area
    
    double old_area = m_surf.get_triangle_area( tri0 ) + m_surf.get_triangle_area( tri1 );
    double new_area = triangle_area( xs[new_triangle0[0]], xs[new_triangle0[1]], xs[new_triangle0[2]] ) 
    + triangle_area( xs[new_triangle1[0]], xs[new_triangle1[1]], xs[new_triangle1[2]] );
    
    if ( fabs( old_area - new_area ) > 0.1 * old_area )
    {
        if ( m_surf.m_verbose ) {std::cout << "edge flip rejected: area change too great" << std::endl; }
        g_stats.add_to_int( "EdgeFlipper:edge_flip_area_change_too_large", 1 );            
        return false;
    }
    
    // --------------
    
    // Don't flip unless both vertices are on a smooth patch
    if ( ( m_surf.vertex_primary_space_rank( edge_vertices[0] ) > 1 ) || ( m_surf.vertex_primary_space_rank( edge_vertices[1] ) > 1 ) )
    {
        if ( m_surf.m_verbose ) {std::cout << "edge flip rejected: vertices not on smooth patch" << std::endl;  }
        g_stats.add_to_int( "EdgeFlipper:edge_flip_not_smooth", 1 );                  
        return false;
    }        
    
    
    // --------------
    
    // Don't introduce a large or small angle
    
    double min_angle = min_triangle_angle( xs[new_triangle0[0]], xs[new_triangle0[1]], xs[new_triangle0[2]] );
    min_angle = min( min_angle, min_triangle_angle( xs[new_triangle1[0]], xs[new_triangle1[1]], xs[new_triangle1[2]] ) );
    
    if ( rad2deg(min_angle) < m_surf.m_min_triangle_angle )
    {
        g_stats.add_to_int( "EdgeFlipper:edge_flip_bad_angle", 1 );                  
        return false;
    }
    
    double max_angle = max_triangle_angle( xs[new_triangle0[0]], xs[new_triangle0[1]], xs[new_triangle0[2]] );
    max_angle = max( max_angle, max_triangle_angle( xs[new_triangle1[0]], xs[new_triangle1[1]], xs[new_triangle1[2]] ) );
    
    if ( rad2deg(max_angle) > m_surf.m_max_triangle_angle )
    {
        g_stats.add_to_int( "EdgeFlipper:edge_flip_bad_angle", 1 );                  
        return false;
    }
    
    // --------------
    
    // Okay, now do the actual operation
    
    Vec3st old_tri0 = m_mesh.get_triangle(tri0);
    Vec3st old_tri1 = m_mesh.get_triangle(tri1);
    
    m_surf.remove_triangle( tri0 );
    m_surf.remove_triangle( tri1 );
    
    size_t new_triangle_index_0 = m_surf.add_triangle( new_triangle0 );
    size_t new_triangle_index_1 = m_surf.add_triangle( new_triangle1 );
    
    if ( m_surf.m_collision_safety )
    {
        if ( m_surf.check_triangle_vs_all_triangles_for_intersection( new_triangle_index_0 ) )
        {
            std::cout << "missed an intersection.  New triangles: " << new_triangle0 << ", " << new_triangle1 << std::endl;
            std::cout << "old triangles: " << old_tri0 << ", " << old_tri1 << std::endl;
            assert(0);
        }
        
        if ( m_surf.check_triangle_vs_all_triangles_for_intersection( new_triangle_index_1 ) )
        {
            std::cout << "missed an intersection.  New triangles: " << new_triangle0 << ", " << new_triangle1 << std::endl;
            std::cout << "old triangles: " << old_tri0 << ", " << old_tri1 << std::endl;      
            assert(0);
        }
    }
    
    m_surf.m_dirty_triangles.push_back( new_triangle_index_0 );
    m_surf.m_dirty_triangles.push_back( new_triangle_index_1 );   
    
    if ( m_surf.m_verbose ) { std::cout << "edge flip: ok" << std::endl; }
    
    g_stats.add_to_int( "EdgeFlipper:edge_flip_success", 1 );
    
    return true;
    
}



// --------------------------------------------------------
///
/// Flip all non-delaunay edges
///
// --------------------------------------------------------

bool EdgeFlipper::flip_pass( )
{
    
    if ( m_surf.m_verbose )
    {
        std::cout << "---------------------- EdgeFlipper: flipping ----------------------" << std::endl;
    }
	
    //   if ( m_surf.m_collision_safety )
    //   {
    //      m_surf.check_continuous_broad_phase_is_up_to_date();
    //   }
    
    m_surf.m_dirty_triangles.clear();
    
    bool flip_occurred_ever = false;          // A flip occurred in this function call
    bool flip_occurred = true;                // A flip occurred in the current loop iteration
    
    static unsigned int MAX_NUM_FLIP_PASSES = 5;
    unsigned int num_flip_passes = 0;
    
    NonDestructiveTriMesh& m_mesh = m_surf.m_mesh;
    const std::vector<Vec3d>& xs = m_surf.get_positions();
    
    //
    // Each "pass" is once over the entire set of edges (ignoring edges created during the current pass)
    //
    
    while ( flip_occurred && num_flip_passes++ < MAX_NUM_FLIP_PASSES )
    {
        if ( m_surf.m_verbose )
        {
            std::cout << "---------------------- El Topo: flipping ";
            std::cout << "pass " << num_flip_passes << "/" << MAX_NUM_FLIP_PASSES;
            std::cout << "----------------------" << std::endl;
        }
        
        flip_occurred = false;
        
        size_t number_of_edges = m_mesh.m_edges.size();      // don't work on newly created edges
        
        for( size_t i = 0; i < number_of_edges; i++ )
        {
            if ( m_mesh.m_edges[i][0] == m_mesh.m_edges[i][1] )   { continue; }
            if ( m_mesh.m_edge_to_triangle_map[i].size() > 4 || m_mesh.m_edge_to_triangle_map[i].size() < 2 )   { continue; }
            if ( m_mesh.m_is_boundary_vertex[ m_mesh.m_edges[i][0] ] || m_mesh.m_is_boundary_vertex[ m_mesh.m_edges[i][1] ] )  { continue; }  // skip boundary vertices
            
            size_t triangle_a = (size_t)~0, triangle_b =(size_t)~0;
            
            if ( m_mesh.m_edge_to_triangle_map[i].size() == 2 )
            {    
                triangle_a = m_mesh.m_edge_to_triangle_map[i][0];
                triangle_b = m_mesh.m_edge_to_triangle_map[i][1];         
                assert (    m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.get_triangle(triangle_a) ) 
                        != m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.get_triangle(triangle_b) ) );
            }
            else if ( m_mesh.m_edge_to_triangle_map[i].size() == 4 )
            {           
                triangle_a = m_mesh.m_edge_to_triangle_map[i][0];
                
                // Find first triangle with orientation opposite triangle_a's orientation
                unsigned int j = 1;
                for ( ; j < 4; ++j )
                {
                    triangle_b = m_mesh.m_edge_to_triangle_map[i][j];
                    if (    m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.get_triangle(triangle_a) ) 
                        != m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.get_triangle(triangle_b) ) )
                    {
                        break;
                    }
                }
                assert ( j < 4 );
            }
            else
            {
                std::cout << m_mesh.m_edge_to_triangle_map[i].size() << " triangles incident to an edge" << std::endl;
                assert(0);
            }
            
            // Don't flip edge on a degenerate triangle
            const Vec3st& tri_a = m_mesh.get_triangle( triangle_a );
            const Vec3st& tri_b = m_mesh.get_triangle( triangle_b );
            
            if (   tri_a[0] == tri_a[1] 
                || tri_a[1] == tri_a[2] 
                || tri_a[2] == tri_a[0] 
                || tri_b[0] == tri_b[1] 
                || tri_b[1] == tri_b[2] 
                || tri_b[2] == tri_b[0] )
            {
                continue;
            }
            
            size_t third_vertex_0 = m_mesh.get_third_vertex( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], tri_a );
            size_t third_vertex_1 = m_mesh.get_third_vertex( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], tri_b );
            
            if ( third_vertex_0 == third_vertex_1 )
            {
                continue;
            }
            
            bool flipped = false;
            
            double current_length = mag( xs[m_mesh.m_edges[i][1]] - xs[m_mesh.m_edges[i][0]] );        
            double potential_length = mag( xs[third_vertex_1] - xs[third_vertex_0] );     
            if ( potential_length < current_length - m_edge_flip_min_length_change )
            {
                flipped = flip_edge( i, triangle_a, triangle_b, third_vertex_0, third_vertex_1 );            
            }
            
            flip_occurred |= flipped;
        }
        
        flip_occurred_ever |= flip_occurred;
    }
    
    
    if ( flip_occurred_ever )
    {
        m_surf.trim_non_manifold( m_surf.m_dirty_triangles );
    }
    
    return flip_occurred_ever;
    
}

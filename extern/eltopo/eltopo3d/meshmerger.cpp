// ---------------------------------------------------------
//
//  meshmerger.cpp
//  Tyson Brochu 2011
//  
//  Search for mesh edges which are near to each other, zipper their neighbouring triangles together.
//
// ---------------------------------------------------------


#include <meshmerger.h>

#include <broadphase.h>
#include <collisionqueries.h>
#include <queue>
#include <runstats.h>
#include <surftrack.h>

// ---------------------------------------------------------
//  Extern globals
// ---------------------------------------------------------

extern RunStats g_stats;

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Move vertices around so v[0] and v[4] are closest together
///
// --------------------------------------------------------

void MeshMerger::twist_vertices( size_t *zipper_vertices )
{
    double min_dist = 1e+30, dist;
    Vec2st min_pair((size_t)~0, (size_t)~0);
    
    // find the closest pair among the 8 vertices
    for (int i=0; i<4; ++i) 
    {
        for (int j=4; j<8; ++j) 
        {
            dist = mag( m_surf.get_position(zipper_vertices[i]) - m_surf.get_position(zipper_vertices[j]) );
            if (dist < min_dist) 
            {
                min_dist = dist;
                min_pair[0] = i;
                min_pair[1] = j;
            }
        }
    }
    
    size_t new_vertices[8];
    for (int i=0; i<4; ++i) 
    {
        new_vertices[i]   = zipper_vertices[(min_pair[0] + i) % 4];
        new_vertices[i+4] = zipper_vertices[(min_pair[1] + i - 4) % 4 + 4];
    }
    
    memcpy( zipper_vertices, new_vertices, 8 * sizeof(size_t) );
    
}

// --------------------------------------------------------
///
/// Create a set of triangles to add to perform the zippering operation
///
// --------------------------------------------------------

bool MeshMerger::get_zipper_triangles( size_t edge_index_a, size_t edge_index_b, std::vector<Vec3st>& output_triangles )
{
    assert( output_triangles.size() == 8 );
    
    const Vec2st& edge_a = m_surf.m_mesh.m_edges[edge_index_a];
    const Vec2st& edge_b = m_surf.m_mesh.m_edges[edge_index_b];
    
    size_t zipper_vertices[8];
    
    zipper_vertices[0] = edge_a[0];
    zipper_vertices[2] = edge_a[1];
    zipper_vertices[4] = edge_b[0];
    zipper_vertices[6] = edge_b[1];
    
    const std::vector<size_t>& incident_triangles_a = m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a];
    
    assert( incident_triangles_a.size() == 2 );       // should be checked before calling this function
    
    const Vec3st& inc_tri_a0 = m_surf.m_mesh.get_triangle( incident_triangles_a[0] );
    const Vec3st& inc_tri_a1 = m_surf.m_mesh.get_triangle( incident_triangles_a[1] );
    
    size_t third_vertices[2];
    third_vertices[0] = m_surf.m_mesh.get_third_vertex( zipper_vertices[0], zipper_vertices[2], inc_tri_a0 );
    third_vertices[1] = m_surf.m_mesh.get_third_vertex( zipper_vertices[0], zipper_vertices[2], inc_tri_a1 );
    
    if ( m_surf.m_mesh.oriented(zipper_vertices[0], zipper_vertices[2], inc_tri_a0 ) ) 
    {
        zipper_vertices[1] = third_vertices[0];
        zipper_vertices[3] = third_vertices[1];
    } 
    else if ( m_surf.m_mesh.oriented(zipper_vertices[0], zipper_vertices[2], inc_tri_a1) ) 
    {
        zipper_vertices[3] = third_vertices[0];
        zipper_vertices[1] = third_vertices[1];
    } 
    else 
    {
        // Should not happen
        std::cout << "Orientation check failed" << std::endl;
        assert( false );
    }
    
    const std::vector<size_t>& incident_triangles_b = m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b];
    
    assert( incident_triangles_b.size() == 2 );       // should be checked before calling this function
    
    assert( edge_index_b < m_surf.m_mesh.m_edges.size() );
    
    const Vec2st& ce = m_surf.m_mesh.m_edges[edge_index_b];
    const std::vector<size_t>& et = m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b];
    
    const Vec3st& inc_tri_b0 = m_surf.m_mesh.get_triangle( incident_triangles_b[0] );
    const Vec3st& inc_tri_b1 = m_surf.m_mesh.get_triangle( incident_triangles_b[1] );
    
    third_vertices[0] = m_surf.m_mesh.get_third_vertex( ce[0], ce[1], m_surf.m_mesh.get_triangle( et[0] ) );
    
    third_vertices[0] = m_surf.m_mesh.get_third_vertex( zipper_vertices[4], zipper_vertices[6], inc_tri_b0 );
    third_vertices[1] = m_surf.m_mesh.get_third_vertex( zipper_vertices[4], zipper_vertices[6], inc_tri_b1 );   
    
    if ( m_surf.m_mesh.oriented(zipper_vertices[4], zipper_vertices[6], inc_tri_b0) ) 
    {
        zipper_vertices[5] = third_vertices[0];
        zipper_vertices[7] = third_vertices[1];
    } 
    else if ( m_surf.m_mesh.oriented(zipper_vertices[4], zipper_vertices[6], inc_tri_b1) ) 
    {
        zipper_vertices[7] = third_vertices[0];
        zipper_vertices[5] = third_vertices[1];
    } 
    else 
    {
        // Should not happen
        std::cout << "Orientation check failed" << std::endl;
        assert( false );
    }
    
    // Check for degenerate case
    for ( unsigned int i = 0; i < 8; ++i) 
    {
        for ( unsigned int j = i+1; j < 8; ++j) 
        {
            
            if ( zipper_vertices[i] == zipper_vertices[j] )         // vertices not distinct
            {
                return false;
            }
            
            // Check if an edge already exists between two vertices in opposite edge neighbourhoods
            // (i.e. look for an edge which would be created by zippering)
            
            if ( (i < 4) && (j > 3) )
            {
                
                for ( size_t ii = 0; ii < m_surf.m_mesh.m_vertex_to_edge_map[ zipper_vertices[i] ].size(); ++ii )
                {
                    for ( size_t jj = 0; jj < m_surf.m_mesh.m_vertex_to_edge_map[ zipper_vertices[j] ].size(); ++jj )
                    {
                        if ( m_surf.m_mesh.m_vertex_to_edge_map[ zipper_vertices[i] ][ii] == m_surf.m_mesh.m_vertex_to_edge_map[ zipper_vertices[j] ][jj] )
                        {
                            return false;
                        }
                    }
                }
            }
            
        }
    }
    
    // Twist so that vertices 0 and 4 are the pair closest together
    twist_vertices( zipper_vertices );
    
    // now we can use a closed formula to construct zippering triangles
    
    output_triangles[0] = Vec3st( zipper_vertices[0], zipper_vertices[4], zipper_vertices[1] );  // a e b
    output_triangles[1] = Vec3st( zipper_vertices[1], zipper_vertices[4], zipper_vertices[7] );  // b e h
    output_triangles[2] = Vec3st( zipper_vertices[1], zipper_vertices[7], zipper_vertices[2] );  // b h c
    output_triangles[3] = Vec3st( zipper_vertices[2], zipper_vertices[7], zipper_vertices[6] );  // c h g
    output_triangles[4] = Vec3st( zipper_vertices[2], zipper_vertices[6], zipper_vertices[3] );  // c g d
    output_triangles[5] = Vec3st( zipper_vertices[3], zipper_vertices[6], zipper_vertices[5] );  // d g f
    output_triangles[6] = Vec3st( zipper_vertices[3], zipper_vertices[5], zipper_vertices[0] );  // d f a
    output_triangles[7] = Vec3st( zipper_vertices[0], zipper_vertices[5], zipper_vertices[4] );  // a f e
    
    return true;
}


// --------------------------------------------------------
///
/// Check whether the introduction of the new zippering triangles causes a collision 
///
// --------------------------------------------------------

bool MeshMerger::zippering_introduces_collision( const std::vector<Vec3st>& new_triangles, 
                                                const std::vector<size_t>& deleted_triangles )
{
    for ( size_t i = 0; i < new_triangles.size(); ++i )
    {
        // Check all existing edges vs new triangles
        Vec3d low, high;
        minmax(m_surf.get_position(new_triangles[i][0]), m_surf.get_position(new_triangles[i][1]), m_surf.get_position(new_triangles[i][2]), low, high);
        
        std::vector<size_t> overlapping_triangles;
        m_surf.m_broad_phase->get_potential_triangle_collisions( low, high, true, true, overlapping_triangles );
        
        const Vec3st& current_triangle = new_triangles[i];
        
        // Check to make sure there doesn't already exist triangles with the same vertices
        for ( size_t t = 0; t < overlapping_triangles.size(); ++t )      
        {
            const Vec3st& other_triangle = m_surf.m_mesh.get_triangle(overlapping_triangles[t]);
            
            if (    ((current_triangle[0] == other_triangle[0]) || (current_triangle[0] == other_triangle[1]) || (current_triangle[0] == other_triangle[2]))
                && ((current_triangle[1] == other_triangle[0]) || (current_triangle[1] == other_triangle[1]) || (current_triangle[1] == other_triangle[2]))
                && ((current_triangle[2] == other_triangle[0]) || (current_triangle[2] == other_triangle[1]) || (current_triangle[2] == other_triangle[2])) ) 
            {
                return true;
            }
        }
        
        // Check all existing triangles vs new triangles
        for ( size_t t = 0; t < overlapping_triangles.size(); ++t )      
        {
            bool go_to_next_triangle = false;
            for ( size_t d = 0; d < deleted_triangles.size(); ++d )
            {
                if ( overlapping_triangles[t] == deleted_triangles[d] )
                {
                    go_to_next_triangle = true;
                    break;
                }
            }
            if ( go_to_next_triangle )   
            { 
                continue; 
            }
            
            if ( check_triangle_triangle_intersection( new_triangles[i], 
                                                      m_surf.m_mesh.get_triangle(overlapping_triangles[t]), 
                                                      m_surf.get_positions() ) )
            {
                return true;
            }     
        }
        
        // Check new triangles vs each other
        for ( size_t j = 0; j < new_triangles.size(); ++j )
        {
            if ( i == j )  { continue; }
            
            if ( check_triangle_triangle_intersection( new_triangles[i], 
                                                      new_triangles[j], 
                                                      m_surf.get_positions() ) )
            {
                return true;
            }
        }      
    }
    
    // For real collision safety, we need to check for vertices inside the new, joined volume.  
    // Checking edges vs triangles is technically not enough.
    
    return false;
}


// --------------------------------------------------------
///
/// Attempt to merge between two edges
///
// --------------------------------------------------------

bool MeshMerger::zipper_edges( size_t edge_index_a, size_t edge_index_b )
{
    // For now we'll only zipper edges which are incident on 2 triangles
    if ( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a].size() != 2 || m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b].size() != 2 )
    {
        g_stats.add_to_int( "merge_non_manifold_edges", 1 );
        return false;
    }
    
    //
    // Get the set of 8 new triangles which will join the two holes in the mesh
    //
    
    std::vector<Vec3st> new_triangles;
    new_triangles.resize(8);
    if ( false == get_zipper_triangles( edge_index_a, edge_index_b, new_triangles ) )
    {
        g_stats.add_to_int( "merge_no_set_of_triangles", 1 );
        return false;
    }
    
    // Keep a list of triangles to delete
    std::vector<size_t> deleted_triangles;
    deleted_triangles.push_back( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a][0] );
    deleted_triangles.push_back( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a][1] );
    deleted_triangles.push_back( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b][0] );
    deleted_triangles.push_back( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b][1] );   
    
    //
    // Check the new triangles for collision safety, ignoring the triangles which will be deleted
    //
    
    bool saved_verbose = m_surf.m_verbose;
    m_surf.m_verbose = false;
    
    if ( m_surf.m_collision_safety && zippering_introduces_collision( new_triangles, deleted_triangles ) )
    {
        m_surf.m_verbose = saved_verbose;
        g_stats.add_to_int( "merge_not_intersection_safe", 1 );
        return false;
    }
    
    m_surf.m_verbose = saved_verbose;
    
    //
    // Add the new triangles
    //
    
    size_t new_index = m_surf.add_triangle( new_triangles[0] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[1] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[2] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[3] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[4] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[5] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[6] );
    m_surf.m_dirty_triangles.push_back( new_index );
    new_index = m_surf.add_triangle( new_triangles[7] );
    m_surf.m_dirty_triangles.push_back( new_index );
    
    //
    // Remove the old triangles
    //
    
    m_surf.remove_triangle( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a][0] );
    m_surf.remove_triangle( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_a][0] );
    m_surf.remove_triangle( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b][0] );
    m_surf.remove_triangle( m_surf.m_mesh.m_edge_to_triangle_map[edge_index_b][0] );
    
    return true;
    
}


// ---------------------------------------------------------
///
/// Look for pairs of edges close to each other, attempting to merge when close edges are found.
///
// ---------------------------------------------------------

bool MeshMerger::merge_pass( )
{
    
    std::queue<Vec2st> edge_edge_candidates;
    
    //
    // Check edge-edge proximities for zippering candidates
    //
    
    bool merge_occured = false;
    
    // sorted by proximity so we merge closest pairs first
    std::vector<SortableEdgeEdgeProximity> proximities;
    
    for(size_t i = 0; i < m_surf.m_mesh.m_edges.size(); i++)
    {
        const Vec2st& e0 = m_surf.m_mesh.m_edges[i];
        
        if ( e0[0] == e0[1] ) { continue; }
        if ( m_surf.edge_is_solid(i) ) { continue; }
        
        if ( m_surf.m_mesh.m_is_boundary_vertex[ e0[0] ] || m_surf.m_mesh.m_is_boundary_vertex[ e0[1] ] )  { continue; }  // skip boundary vertices
        
        Vec3d emin, emax;
        m_surf.edge_static_bounds(i, emin, emax);
        emin -= m_surf.m_merge_proximity_epsilon * Vec3d(1,1,1);
        emax += m_surf.m_merge_proximity_epsilon * Vec3d(1,1,1);
        
        std::vector<size_t> edge_candidates;
        m_surf.m_broad_phase->get_potential_edge_collisions( emin, emax, false, true, edge_candidates );
        
        for(size_t j = 0; j < edge_candidates.size(); j++)
        {
            size_t proximal_edge_index = edge_candidates[j];
            const Vec2st& e1 = m_surf.m_mesh.m_edges[proximal_edge_index];
            
            if ( proximal_edge_index <= i )
            {
                continue;
            }
            
            if ( m_surf.m_mesh.m_is_boundary_vertex[ e1[0] ] || m_surf.m_mesh.m_is_boundary_vertex[ e1[1] ] )  { continue; }  // skip boundary vertices
            
            if(e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1])
            {
                double distance, s0, s2;
                Vec3d normal;
                
                check_edge_edge_proximity( m_surf.get_position(e0[0]), 
                                          m_surf.get_position(e0[1]), 
                                          m_surf.get_position(e1[0]), 
                                          m_surf.get_position(e1[1]), 
                                          distance, s0, s2, normal );
                
                if (distance < m_surf.m_merge_proximity_epsilon)
                {
                    
                    if ( m_surf.m_verbose ) 
                    { 
                        std::cout << "proximity: " << distance << " / " << m_surf.m_merge_proximity_epsilon << std::endl; //proximities[i].distance << std::endl; 
                    }
                    
                    if ( zipper_edges( i, proximal_edge_index ) )
                    {
                        
                        m_surf.trim_non_manifold( m_surf.m_dirty_triangles );
                        
                        if ( m_surf.m_verbose ) 
                        { 
                            std::cout << "zippered" << std::endl; 
                        }
                        
                        merge_occured = true;
                        
                        g_stats.add_to_int( "merge_success", 1 );
                    }
                    else
                    {
                        g_stats.add_to_int( "merge_failed", 1 );
                    }
                    
                }
            }
        }
    }
    
    
    if ( merge_occured )
    {
        m_surf.assert_no_degenerate_triangles();
    }
    
    return merge_occured;
    
    
}

// ---------------------------------------------------------
//
//  edgesplitter.cpp
//  Tyson Brochu 2011
//  
//  Functions supporting the "edge split" operation: subdividing an edge into two shorter edges.
//
// ---------------------------------------------------------

#include <edgesplitter.h>
#include <broadphase.h>
#include <collisionqueries.h>
#include <runstats.h>
#include <subdivisionscheme.h>
#include <surftrack.h>
#include <trianglequality.h>


// ---------------------------------------------------------
//  Extern globals
// ---------------------------------------------------------

extern RunStats g_stats;

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Constructor.  Active SurfTrack object must be supplied.
///
// ---------------------------------------------------------

EdgeSplitter::EdgeSplitter( SurfTrack& surf, bool use_curvature, double max_curvature_multiplier ) :
m_max_edge_length( UNINITIALIZED_DOUBLE ),
m_use_curvature( use_curvature ),
m_max_curvature_multiplier( max_curvature_multiplier ),
m_surf( surf )
{}


// --------------------------------------------------------
///
/// Check collisions between the edge [neighbour, new] and the given edge 
///
// --------------------------------------------------------

bool EdgeSplitter::split_edge_edge_collision( size_t neighbour_index, 
                                             const Vec3d& new_vertex_position, 
                                             const Vec3d& new_vertex_smooth_position, 
                                             const Vec2st& edge )
{
    
    size_t edge_vertex_0 = edge[0];
    size_t edge_vertex_1 = edge[1];
    size_t dummy_index = m_surf.get_num_vertices();
    
    if ( neighbour_index == edge_vertex_0 || neighbour_index == edge_vertex_1 )  { return false; }
    
    const std::vector<Vec3d>& x = m_surf.get_positions();
    
    double t_zero_distance; 
    check_edge_edge_proximity( new_vertex_position, 
                              x[ neighbour_index ], 
                              x[ edge_vertex_0 ], 
                              x[ edge_vertex_1 ],
                              t_zero_distance );
    
    if ( t_zero_distance < m_surf.m_improve_collision_epsilon )
    {
        return true;
    }
    
    if ( edge_vertex_1 < edge_vertex_0 ) { swap( edge_vertex_0, edge_vertex_1 ); }
    
    if ( segment_segment_collision(x[ neighbour_index ], x[ neighbour_index ], neighbour_index,
                                   new_vertex_position, new_vertex_smooth_position, dummy_index,
                                   x[ edge_vertex_0 ], x[ edge_vertex_0 ], edge_vertex_0,
                                   x[ edge_vertex_1 ], x[ edge_vertex_1 ], edge_vertex_1 ) )
        
    {      
        return true;
    }
    
    return false;
    
}


// ---------------------------------------------------------
///
/// Determine if the new vertex introduced by the edge split has a collision along its pseudo-trajectory.
///
// ---------------------------------------------------------

bool EdgeSplitter::split_triangle_vertex_collision( const Vec3st& triangle_indices, 
                                                   const Vec3d& new_vertex_position, 
                                                   const Vec3d& new_vertex_smooth_position, 
                                                   size_t overlapping_vert_index, 
                                                   const Vec3d& vert )
{
    
    if ( overlapping_vert_index == triangle_indices[0] || overlapping_vert_index == triangle_indices[1] || overlapping_vert_index == triangle_indices[2] )
    {
        return false;
    }
    
    Vec3st sorted_triangle = sort_triangle( triangle_indices );
    
    Vec3d tri_positions[3];
    Vec3d tri_smooth_positions[3];
    
    for ( unsigned int i = 0; i < 3; ++i )
    {
        if ( sorted_triangle[i] == m_surf.get_num_vertices() )
        {
            tri_positions[i] = new_vertex_position;
            tri_smooth_positions[i] = new_vertex_smooth_position;
        }
        else
        {
            tri_positions[i] = m_surf.get_position( sorted_triangle[i] );
            tri_smooth_positions[i] = m_surf.get_position( sorted_triangle[i] );
        }
    }
    
    
    // check distance at time t=0
    double t_zero_distance;
    check_point_triangle_proximity( vert, tri_positions[0], tri_positions[1], tri_positions[2], t_zero_distance );
    
    
    if ( t_zero_distance < m_surf.m_improve_collision_epsilon )
    {
        return true;
    }
    
    
    // now check continuous collision
    
    if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                  tri_positions[0], tri_smooth_positions[0], sorted_triangle[0],
                                  tri_positions[1], tri_smooth_positions[1], sorted_triangle[1],
                                  tri_positions[2], tri_smooth_positions[2], sorted_triangle[2] ) )
    {         
        return true;
    }
    
    return false;
    
    
}



// ---------------------------------------------------------
///
/// Determine if the pseudo-trajectory of the new vertex has a collision with the existing mesh.
///
// ---------------------------------------------------------

bool EdgeSplitter::split_edge_pseudo_motion_introduces_intersection( const Vec3d& new_vertex_position, 
                                                                    const Vec3d& new_vertex_smooth_position, 
                                                                    size_t edge,
                                                                    size_t tri0, 
                                                                    size_t tri1, 
                                                                    size_t vertex_a,
                                                                    size_t vertex_b,
                                                                    size_t vertex_c,
                                                                    size_t vertex_d )
{
    
    NonDestructiveTriMesh& m_mesh = m_surf.m_mesh;
    
    if ( !m_surf.m_collision_safety)
    {
        return false;
    }
    
    // 
    // new point vs all triangles
    // 
    
    {
        
        Vec3d aabb_low, aabb_high;
        minmax( new_vertex_position, new_vertex_smooth_position, aabb_low, aabb_high );
        
        aabb_low -= m_surf.m_aabb_padding * Vec3d(1,1,1);
        aabb_high += m_surf.m_aabb_padding * Vec3d(1,1,1);
        
        std::vector<size_t> overlapping_triangles;
        m_surf.m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, true, true, overlapping_triangles );
        
        for ( size_t i = 0; i < overlapping_triangles.size(); ++i )
        {
            
            if ( overlapping_triangles[i] == tri0 || overlapping_triangles[i] == tri1 )
            {
                continue;
            }
            
            size_t triangle_vertex_0 = m_mesh.get_triangle( overlapping_triangles[i] )[0];
            size_t triangle_vertex_1 = m_mesh.get_triangle( overlapping_triangles[i] )[1];
            size_t triangle_vertex_2 = m_mesh.get_triangle( overlapping_triangles[i] )[2];
            
            double t_zero_distance;
            
            check_point_triangle_proximity( new_vertex_position, 
                                           m_surf.get_position( triangle_vertex_0 ),
                                           m_surf.get_position( triangle_vertex_1 ),
                                           m_surf.get_position( triangle_vertex_2 ),
                                           t_zero_distance );
            
            size_t dummy_index = m_surf.get_num_vertices();
            
            if ( t_zero_distance < m_surf.m_improve_collision_epsilon )
            {
                return true;
            }
            
            Vec3st sorted_triangle = sort_triangle( Vec3st( triangle_vertex_0, triangle_vertex_1, triangle_vertex_2 ) );
            
            
            if ( point_triangle_collision(  new_vertex_position, new_vertex_smooth_position, dummy_index,
                                          m_surf.get_position( sorted_triangle[0] ), m_surf.get_position( sorted_triangle[0] ), sorted_triangle[0],
                                          m_surf.get_position( sorted_triangle[1] ), m_surf.get_position( sorted_triangle[1] ), sorted_triangle[1],
                                          m_surf.get_position( sorted_triangle[2] ), m_surf.get_position( sorted_triangle[2] ), sorted_triangle[2] ) )
                
            {
                return true;
            }
        }
        
    }
    
    //
    // new edges vs all edges
    //
    
    {
        
        Vec3d edge_aabb_low, edge_aabb_high;
        
        // do one big query into the broadphase for all 4 new edges
        minmax( new_vertex_position, new_vertex_smooth_position, 
               m_surf.get_position( vertex_a ), m_surf.get_position( vertex_b ), m_surf.get_position( vertex_c ), m_surf.get_position( vertex_d ),
               edge_aabb_low, edge_aabb_high );
        
        edge_aabb_low -= m_surf.m_aabb_padding * Vec3d(1,1,1);
        edge_aabb_high += m_surf.m_aabb_padding * Vec3d(1,1,1);
        
        std::vector<size_t> overlapping_edges;
        m_surf.m_broad_phase->get_potential_edge_collisions( edge_aabb_low, edge_aabb_high, true, true, overlapping_edges );
        
        const size_t vertex_neighbourhood[4] = { vertex_a, vertex_b, vertex_c, vertex_d };
        
        for ( size_t i = 0; i < overlapping_edges.size(); ++i )
        {
            
            if ( overlapping_edges[i] == edge ) { continue; }
            if ( m_mesh.m_edges[ overlapping_edges[i] ][0] == m_mesh.m_edges[ overlapping_edges[i] ][1] ) { continue; }
            
            for ( size_t v = 0; v < 4; ++v )
            {
                bool collision = split_edge_edge_collision( vertex_neighbourhood[v], 
                                                           new_vertex_position, 
                                                           new_vertex_smooth_position, 
                                                           m_mesh.m_edges[overlapping_edges[i]] );
                
                if ( collision ) { return true; }
            }
        }      
    }
    
    //
    // new triangles vs all points
    //
    
    {
        Vec3d triangle_aabb_low, triangle_aabb_high;
        
        // do one big query into the broadphase for all 4 new triangles
        minmax( new_vertex_position, new_vertex_smooth_position, 
               m_surf.get_position( vertex_a ), m_surf.get_position( vertex_b ), m_surf.get_position( vertex_c ), m_surf.get_position( vertex_d ),
               triangle_aabb_low, triangle_aabb_high );
        
        triangle_aabb_low -= m_surf.m_aabb_padding * Vec3d(1,1,1);
        triangle_aabb_high += m_surf.m_aabb_padding * Vec3d(1,1,1);
        
        std::vector<size_t> overlapping_vertices;
        m_surf.m_broad_phase->get_potential_vertex_collisions( triangle_aabb_low, triangle_aabb_high, true, true, overlapping_vertices );
        
        size_t dummy_e = m_surf.get_num_vertices();
        
        std::vector< Vec3st > triangle_indices;
        
        triangle_indices.push_back( Vec3st( vertex_a, dummy_e, vertex_c ) );    // triangle aec      
        triangle_indices.push_back( Vec3st( vertex_c, dummy_e, vertex_b ) );    // triangle ceb      
        triangle_indices.push_back( Vec3st( vertex_d, vertex_b, dummy_e ) );    // triangle dbe
        triangle_indices.push_back( Vec3st( vertex_d, dummy_e, vertex_a ) );    // triangle dea
        
        for ( size_t i = 0; i < overlapping_vertices.size(); ++i )
        {
            if ( m_mesh.m_vertex_to_triangle_map[overlapping_vertices[i]].empty() ) 
            { 
                continue; 
            }
            
            size_t overlapping_vert_index = overlapping_vertices[i];
            const Vec3d& vert = m_surf.get_position(overlapping_vert_index);
            
            for ( size_t j = 0; j < triangle_indices.size(); ++j )
            {
                bool collision = split_triangle_vertex_collision( triangle_indices[j], 
                                                                 new_vertex_position, 
                                                                 new_vertex_smooth_position, 
                                                                 overlapping_vert_index, 
                                                                 vert );
                
                if ( collision ) 
                { 
                    return true; 
                }
                
            }
        }
        
    }
    
    return false;
    
}

// --------------------------------------------------------
///
/// Split an edge, using subdivision_scheme to determine the new vertex location, if safe to do so.
///
// --------------------------------------------------------

bool EdgeSplitter::split_edge( size_t edge )
{   
    
    g_stats.add_to_int( "EdgeSplitter:edge_split_attempts", 1 );
    
    assert( edge_is_splittable(edge) );
    
    NonDestructiveTriMesh& mesh = m_surf.m_mesh;
    
    // --------------
    
    // Only split edges inicident on 2 triangles
    assert ( mesh.m_edge_to_triangle_map[edge].size() == 2 );
    
    // --------------
    
    size_t tri0 = mesh.m_edge_to_triangle_map[edge][0];
    size_t tri1 = mesh.m_edge_to_triangle_map[edge][1];
    double area0 = m_surf.get_triangle_area( tri0 );
    double area1 = m_surf.get_triangle_area( tri1 );
    
    // Splitting degenerate triangles causes problems
    if ( area0 < m_surf.m_min_triangle_area || area1 < m_surf.m_min_triangle_area )
    {
        g_stats.add_to_int( "EdgeSplitter:split_edge_incident_to_tiny_triangle", 1 );
        return false;
    }
    
    // --------------
    
    // convert triangles abc and dba into triangles aec, ceb, dbe and dea
    
    size_t vertex_a = mesh.m_edges[edge][0];
    size_t vertex_b = mesh.m_edges[edge][1];
    size_t vertex_c, vertex_d;
    
    if ( mesh.oriented( vertex_a, vertex_b, mesh.get_triangle(tri0) ) )
    {
        // tri0 = abc
		assert( mesh.oriented( vertex_b, vertex_a, mesh.get_triangle(tri1) ) );
        vertex_c = mesh.get_third_vertex( vertex_a, vertex_b, mesh.get_triangle(tri0) );      
        vertex_d = mesh.get_third_vertex( vertex_b, vertex_a, mesh.get_triangle(tri1) );
    }
    else
    {
        // tri1 = abc
        assert( mesh.oriented( vertex_a, vertex_b, mesh.get_triangle(tri1) ) );
        assert( mesh.oriented( vertex_b, vertex_a, mesh.get_triangle(tri0) ) );
        vertex_c = mesh.get_third_vertex( vertex_a, vertex_b, mesh.get_triangle(tri1) );
        vertex_d = mesh.get_third_vertex( vertex_b, vertex_a, mesh.get_triangle(tri0) );
    }
    
    // --------------
    
    // get edge midpoint and the point on the smooth surface
    
    Vec3d new_vertex_position = 0.5 * ( m_surf.get_position( vertex_a ) + m_surf.get_position( vertex_b ) );
    Vec3d new_vertex_smooth_position;
    
    // generate the new midpoint according to the subdivision scheme
    m_surf.m_subdivision_scheme->generate_new_midpoint( edge, m_surf, new_vertex_smooth_position );
    
    // --------------
    
    // check if the generated point introduces an intersection
    
    bool use_smooth_point = ! ( split_edge_pseudo_motion_introduces_intersection( new_vertex_position, 
                                                                                 new_vertex_smooth_position, 
                                                                                 edge, 
                                                                                 tri0, 
                                                                                 tri1, 
                                                                                 vertex_a, 
                                                                                 vertex_b, 
                                                                                 vertex_c, 
                                                                                 vertex_d ) );
    
    if ( !use_smooth_point ) { g_stats.add_to_int( "EdgeSplitter:split_smooth_vertex_collisions", 1 ); }
    
    // --------------
    
    // check normal inversion
    
    if ( use_smooth_point )
    {
        
        Vec3d tri0_normal = m_surf.get_triangle_normal( tri0 );
        Vec3d tri1_normal = m_surf.get_triangle_normal( tri1 );
        
        if ( dot( tri0_normal, tri1_normal ) >= 0.0 )
        {
            Vec3d new_normal = triangle_normal( m_surf.get_position(vertex_a), new_vertex_smooth_position, m_surf.get_position(vertex_c) );
            if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
            {
                use_smooth_point = false;
            }
            new_normal = triangle_normal( m_surf.get_position(vertex_c), new_vertex_smooth_position, m_surf.get_position(vertex_b) );
            if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
            {
                use_smooth_point = false;
            }         
            new_normal = triangle_normal( m_surf.get_position(vertex_d), m_surf.get_position(vertex_b), new_vertex_smooth_position );
            if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
            {
                use_smooth_point = false;
            }         
            new_normal = triangle_normal( m_surf.get_position(vertex_d), new_vertex_smooth_position, m_surf.get_position(vertex_a) );
            if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
            {
                use_smooth_point = false;
            }         
        }
    }
    
    // --------------
    
    // if the new point introduces an intersection, try using the edge midpoint
    
    if ( use_smooth_point == false )
    {
        
        if ( m_surf.m_verbose ) { std::cout << "not using smooth subdivision" << std::endl; }
        
        new_vertex_smooth_position = new_vertex_position;
        
        if ( split_edge_pseudo_motion_introduces_intersection( new_vertex_position, 
                                                              new_vertex_smooth_position, 
                                                              edge, 
                                                              tri0, 
                                                              tri1, 
                                                              vertex_a, 
                                                              vertex_b, 
                                                              vertex_c, 
                                                              vertex_d ) )
        {
            
            g_stats.add_to_int( "EdgeSplitter:split_midpoint_collisions", 1 );
            
            if ( m_surf.m_verbose )  { std::cout << "Even mid-point subdivision introduces collision.  Backing out." << std::endl; }
            return false;
        }
    }
 	else
    {
        if ( m_surf.m_verbose ) { std::cout << "using smooth subdivision" << std::endl; }
    }
    
    
    // --------------
    
    // Check angles on new triangles
    
    const Vec3d& va = m_surf.get_position( vertex_a );
    const Vec3d& vb = m_surf.get_position( vertex_b );
    const Vec3d& vc = m_surf.get_position( vertex_c );
    const Vec3d& vd = m_surf.get_position( vertex_d );
    const Vec3d& ve = new_vertex_smooth_position;
    
    double min_new_angle = min_triangle_angle( va, ve, vc );
    min_new_angle = min( min_new_angle, min_triangle_angle( vc, ve, vb ) );
    min_new_angle = min( min_new_angle, min_triangle_angle( vd, vb, ve ) );
    min_new_angle = min( min_new_angle, min_triangle_angle( vd, ve, va ) );
    
    if ( rad2deg(min_new_angle) < m_surf.m_min_triangle_angle )
    {
        g_stats.add_to_int( "EdgeSplitter:edge_split_small_angle", 1 );
        return false;
    }
    
    double max_current_angle = max_triangle_angle( va, vb, vc );
    max_current_angle = max( max_current_angle, max_triangle_angle( va, vb, vd ) );
    
    double max_new_angle = max_triangle_angle( va, ve, vc );
    max_new_angle = max( max_new_angle, max_triangle_angle( vc, ve, vb ) );
    max_new_angle = max( max_new_angle, max_triangle_angle( vd, vb, ve ) );
    max_new_angle = max( max_new_angle, max_triangle_angle( vd, ve, va ) );
    
    // if new angle is greater than the allowed angle, and doesn't 
    // improve the current max angle, prevent the split
    
    if ( rad2deg(max_new_angle) > m_surf.m_max_triangle_angle )
    {
        
        // if new triangle improves a large angle, allow it
        
        if ( rad2deg(max_new_angle) < rad2deg(max_current_angle) )
        {
            g_stats.add_to_int( "EdgeSplitter:edge_split_large_angle", 1 );      
            return false;
        }
    }
    
    // --------------
    
    // Do the actual splitting
    
    double new_vertex_mass = 0.5 * ( m_surf.m_masses[ vertex_a ] + m_surf.m_masses[ vertex_b ] );
    size_t vertex_e = m_surf.add_vertex( new_vertex_smooth_position, new_vertex_mass );
    
    // Add to change history
    m_surf.m_vertex_change_history.push_back( VertexUpdateEvent( VertexUpdateEvent::VERTEX_ADD, vertex_e, Vec2st( vertex_a, vertex_b) ) );
    
    if ( m_surf.m_verbose ) { std::cout << "new vertex: " << vertex_e << std::endl; }
    
    m_surf.remove_triangle( tri0 );
    m_surf.remove_triangle( tri1 );
    
    m_surf.add_triangle( Vec3st( vertex_a, vertex_e, vertex_c ) );
    m_surf.add_triangle( Vec3st( vertex_c, vertex_e, vertex_b ) );
    m_surf.add_triangle( Vec3st( vertex_d, vertex_b, vertex_e ) );
    m_surf.add_triangle( Vec3st( vertex_d, vertex_e, vertex_a ) );      
    
    return true;
    
}

// --------------------------------------------------------
///
/// Determine if edge should be allowed to be split
///
// --------------------------------------------------------

bool EdgeSplitter::edge_is_splittable( size_t edge_index )
{
    
    // skip deleted and solid edges
    if ( m_surf.m_mesh.edge_is_deleted(edge_index) ) { return false; }
    if ( m_surf.edge_is_solid(edge_index) ) { return false; }
    
    // skip non-manifold and boundary edges
    if ( m_surf.m_mesh.m_edge_to_triangle_map[edge_index].size() != 2 ) { return false; }
    if ( m_surf.m_mesh.m_is_boundary_edge[edge_index] ) { return false; }
    
    return true;
    
}

// --------------------------------------------------------
///
/// Split edges opposite large angles
///
// --------------------------------------------------------

bool EdgeSplitter::large_angle_split_pass()
{
    
    NonDestructiveTriMesh& mesh = m_surf.m_mesh;
    
    bool split_occurred = false;
    
    for ( size_t e = 0; e < mesh.m_edges.size(); ++e )
    {
        
        if ( !edge_is_splittable(e) ) { continue; }
        
        // get edge end points
        const Vec2st& edge = m_surf.m_mesh.m_edges[e];      
        const Vec3d& edge_point0 = m_surf.get_position( edge[0] );
        const Vec3d& edge_point1 = m_surf.get_position( edge[1] );
        
        // get triangles incident to the edge
        size_t t0 = mesh.m_edge_to_triangle_map[e][0];
        size_t t1 = mesh.m_edge_to_triangle_map[e][1];
        const Vec3st& tri0 = mesh.get_triangle(t0);
        const Vec3st& tri1 = mesh.get_triangle(t1);
        
        // get vertex opposite the edge for each triangle
        size_t opposite0 = mesh.get_third_vertex( e, tri0 );
        size_t opposite1 = mesh.get_third_vertex( e, tri1 );
        
        // compute the angle at each opposite vertex
        const Vec3d& opposite_point0 = m_surf.get_position(opposite0);
        const Vec3d& opposite_point1 = m_surf.get_position(opposite1);
        double angle0 = rad2deg( acos( dot( normalized(edge_point0-opposite_point0), normalized(edge_point1-opposite_point0) ) ) );
        double angle1 = rad2deg( acos( dot( normalized(edge_point0-opposite_point1), normalized(edge_point1-opposite_point1) ) ) );
        
        // if an angle is above the max threshold, split the edge
        
        if ( angle0 > m_surf.m_max_triangle_angle || angle1 > m_surf.m_max_triangle_angle )
        {
            
            bool result = split_edge( e );
            
            if ( result )
            {
                g_stats.add_to_int( "EdgeSplitter:large_angle_split_success", 1 );
            }
            else
            {
                g_stats.add_to_int( "EdgeSplitter:large_angle_split_failed", 1 );
            }
            
            split_occurred |= result;
        }
    }
    
    
    return split_occurred;
    
}

// --------------------------------------------------------
///
/// Split all long edges
///
// --------------------------------------------------------

bool EdgeSplitter::split_pass()
{
    
    if ( m_surf.m_verbose )
    {
        std::cout << "---------------------- Edge Splitter: splitting ----------------------" << std::endl;
    }
    
    assert( m_max_edge_length != UNINITIALIZED_DOUBLE );
    
    NonDestructiveTriMesh& mesh = m_surf.m_mesh;
    std::vector<SortableEdge> sortable_edges_to_try;
    
    for( size_t i = 0; i < mesh.m_edges.size(); i++ )
    {    
        if ( !edge_is_splittable(i) ) { continue; }
        
        size_t vertex_a = mesh.m_edges[i][0];
        size_t vertex_b = mesh.m_edges[i][1];
        
        assert( vertex_a < m_surf.get_num_vertices() );
        assert( vertex_b < m_surf.get_num_vertices() );
        
        double length;
        
        if ( m_use_curvature )
        {
            length = get_curvature_scaled_length( m_surf, vertex_a, vertex_b, 0.0, m_max_curvature_multiplier );
        }
        else
        {
            length = m_surf.get_edge_length(i);
        }
        
        if ( length > m_max_edge_length )
        {
            sortable_edges_to_try.push_back( SortableEdge( i, length ) );
        }
    }
    
    
    //
    // sort in ascending order, then iterate backwards to go from longest edge to shortest
    //
    
    // whether a split operation was successful in this pass
    
    bool split_occurred = false;
    
    std::sort( sortable_edges_to_try.begin(), sortable_edges_to_try.end() );
    
    std::vector<SortableEdge>::reverse_iterator iter = sortable_edges_to_try.rbegin();
    
    for ( ; iter != sortable_edges_to_try.rend(); ++iter )
    {
        size_t longest_edge = iter->m_edge_index;
        
        if ( !edge_is_splittable(longest_edge) ) { continue; }
        
        size_t vertex_a = mesh.m_edges[longest_edge][0];
        size_t vertex_b = mesh.m_edges[longest_edge][1];
        
        // recompute edge length -- a prior split may have somehow fixed this edge already
        double longest_edge_length;
        
        if ( m_use_curvature )
        {
            longest_edge_length = get_curvature_scaled_length( m_surf, vertex_a, vertex_b, 0.0, m_max_curvature_multiplier );
        }
        else
        {
            longest_edge_length = m_surf.get_edge_length(longest_edge);
        }
        
        if ( longest_edge_length > m_max_edge_length )
        {
            // perform the actual edge split
            bool result = split_edge( longest_edge );         
            split_occurred |= result;
        }
    }
    
    
    // Now split to reduce large angles
    
    bool large_angle_split_occurred = large_angle_split_pass();
    
    return split_occurred || large_angle_split_occurred;
    
}




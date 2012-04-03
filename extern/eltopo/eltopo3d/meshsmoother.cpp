// ---------------------------------------------------------
//
//  meshsmoother.cpp
//  Tyson Brochu 2011
//  
//  Functions related to the tangent-space mesh smoothing operation.
//
// ---------------------------------------------------------

#include <meshsmoother.h>

#include <impactzonesolver.h>
#include <lapack_wrapper.h>
#include <mat.h>
#include <nondestructivetrimesh.h>
#include <surftrack.h>

// ========================================================
//  NULL-space smoothing functions
// ========================================================

// ---------------------------------------------------------
///
/// Compute the maximum timestep that will not invert any triangle normals, using a quadratic solve as in [Jiao 2007].
///
// ---------------------------------------------------------

double MeshSmoother::compute_max_timestep_quadratic_solve( const std::vector<Vec3st>& tris, 
                                                          const std::vector<Vec3d>& positions, 
                                                          const std::vector<Vec3d>& displacements, 
                                                          bool verbose ) 
{
    double max_beta = 1.0;
    
    double min_area = BIG_DOUBLE;
    
    for ( size_t i = 0; i < tris.size(); ++i )
    {
        if ( tris[i][0] == tris[i][1] ) { continue; }
        
        const Vec3d& x1 = positions[tris[i][0]];
        const Vec3d& x2 = positions[tris[i][1]];
        const Vec3d& x3 = positions[tris[i][2]];
        
        const Vec3d& u1 = displacements[tris[i][0]];
        const Vec3d& u2 = displacements[tris[i][1]];
        const Vec3d& u3 = displacements[tris[i][2]];
        
        Vec3d new_x1 = x1 + u1;
        Vec3d new_x2 = x2 + u2;
        Vec3d new_x3 = x3 + u3;
        
        const Vec3d c0 = cross( (x2-x1), (x3-x1) );
        const Vec3d c1 = cross( (x2-x1), (u3-u1) ) - cross( (x3-x1), (u2-u1) );
        const Vec3d c2 = cross( (u2-u1), (u3-u1) );
        const double a = dot(c0, c2);
        const double b = dot(c0, c1);
        const double c = dot(c0, c0);
        
        double beta = 1.0;
        
        min_area = min( min_area, c );
        
        if ( c < 1e-14 )
        {
            if ( verbose ) { std::cout << "super small triangle " << i << " (" << tris[i] << ")" << std::endl; }
        }
        
        if ( fabs(a) == 0 )
        {
            
            if ( ( fabs(b) > 1e-14 ) && ( -c / b >= 0.0 ) )
            {
                beta = -c / b;
            }
            else
            {
                if ( verbose )
                {
                    if ( fabs(b) < 1e-14 )
                    {
                        std::cout << "triangle " << i << ": "; 
                        std::cout <<  "b == " << b << std::endl; 
                    }
                }
            }
        }
        else
        {
            double descriminant = b*b - 4.0*a*c;
            
            if ( descriminant < 0.0  )
            {
                // Hmm, what does this mean?
                if ( verbose )
                {
                    std::cout << "triangle " << i << ": descriminant == " << descriminant << std::endl;
                }
                
                beta = 1.0;
            }
            else
            {
                double q;
                if ( b > 0.0 )
                {
                    q = -0.5 * ( b + sqrt( descriminant ) );
                }
                else
                {
                    q = -0.5 * ( b - sqrt( descriminant ) );
                }
                
                double beta_1 = q / a;
                double beta_2 = c / q;
                
                if ( beta_1 < 0.0 )
                {
                    if ( beta_2 < 0.0 )
                    {
                        assert( dot( triangle_normal(x1, x2, x3), triangle_normal(new_x1, new_x2, new_x3) ) > 0.0 );
                    }
                    else
                    {
                        beta = beta_2;
                    }
                }
                else
                {
                    if ( beta_2 < 0.0 )
                    {
                        beta = beta_1;
                    }
                    else if ( beta_1 < beta_2 )
                    {
                        beta = beta_1;
                    }
                    else
                    {
                        beta = beta_2;
                    }
                }
                
            }
        }
        
        bool changed = false;
        if ( beta < max_beta )
        {
            max_beta = 0.99 * beta;
            changed = true;
            
            if ( verbose )
            {
                std::cout << "changing beta --- triangle: " << i << std::endl;
                std::cout << "new max beta: " << max_beta << std::endl;
                std::cout << "a = " << a << ", b = " << b << ", c = " << c << std::endl;
            }
            
            if ( max_beta < 1e-4 )
            {
                //assert(0);
            }
            
        }
        
        new_x1 = x1 + max_beta * u1;
        new_x2 = x2 + max_beta * u2;
        new_x3 = x3 + max_beta * u3;
        
        Vec3d old_normal = cross(x2-x1, x3-x1);
        Vec3d new_normal = cross(new_x2-new_x1, new_x3-new_x1);
        
        if ( dot( old_normal, new_normal ) < 0.0 )
        {
            std::cout << "triangle " << i << ": " << tris[i] << std::endl;
            std::cout << "old normal: " << old_normal << std::endl;
            std::cout << "new normal: " << new_normal << std::endl;
            std::cout << "dot product: " << dot( triangle_normal(x1, x2, x3), triangle_normal(new_x1, new_x2, new_x3) ) << std::endl;
            std::cout << (changed ? "changed" : "not changed") << std::endl;
            std::cout << "beta: " << beta << std::endl;
            std::cout << "max beta: " << max_beta << std::endl;
        }
    }
    
    return max_beta;
}


// --------------------------------------------------------
///
/// Find a new vertex location using NULL-space smoothing
///
// --------------------------------------------------------

void MeshSmoother::null_space_smooth_vertex( size_t v, 
                                            const std::vector<double>& triangle_areas, 
                                            const std::vector<Vec3d>& triangle_normals, 
                                            const std::vector<Vec3d>& triangle_centroids, 
                                            Vec3d& displacement ) const
{
    
    const NonDestructiveTriMesh& mesh = m_surf.m_mesh;
    
    if ( mesh.m_vertex_to_triangle_map[v].empty() )     
    { 
        displacement = Vec3d(0,0,0);
        return; 
    }
    
    const std::vector<size_t>& edges = mesh.m_vertex_to_edge_map[v];
    for ( size_t j = 0; j < edges.size(); ++j )
    {
        if ( mesh.m_edge_to_triangle_map[ edges[j] ].size() == 1 )
        {
            displacement = Vec3d(0,0,0);
            return;
        }
    }
    
    const std::vector<size_t>& incident_triangles = mesh.m_vertex_to_triangle_map[v];
    
    std::vector< Vec3d > N;
    std::vector< double > W;
    
    for ( size_t i = 0; i < incident_triangles.size(); ++i )
    {
        size_t triangle_index = incident_triangles[i];
        N.push_back( triangle_normals[triangle_index] );
        W.push_back( triangle_areas[triangle_index] );
    }
    
    Mat33d A(0,0,0,0,0,0,0,0,0);
    
    // Ax = b from N^TWni = N^TWd
    for ( size_t i = 0; i < N.size(); ++i )
    {
        A(0,0) += N[i][0] * W[i] * N[i][0];
        A(1,0) += N[i][1] * W[i] * N[i][0];
        A(2,0) += N[i][2] * W[i] * N[i][0];
        
        A(0,1) += N[i][0] * W[i] * N[i][1];
        A(1,1) += N[i][1] * W[i] * N[i][1];
        A(2,1) += N[i][2] * W[i] * N[i][1];
        
        A(0,2) += N[i][0] * W[i] * N[i][2];
        A(1,2) += N[i][1] * W[i] * N[i][2];
        A(2,2) += N[i][2] * W[i] * N[i][2];
    }
    
    // get eigen decomposition
    double eigenvalues[3];
    double work[9];
    int info = ~0, n = 3, lwork = 9;
    LAPACK::get_eigen_decomposition( &n, A.a, &n, eigenvalues, work, &lwork, &info );      
    
    if ( info != 0 )
    {
        std::cout << "Eigen decomposition failed" << std::endl;
        std::cout << "number of incident_triangles: " << incident_triangles.size() << std::endl;
        for ( size_t i = 0; i < incident_triangles.size(); ++i )
        {
            size_t triangle_index = incident_triangles[i];
            std::cout << "triangle: " << m_surf.m_mesh.get_triangle(triangle_index) << std::endl;
            std::cout << "normal: " << triangle_normals[triangle_index] << std::endl;
            std::cout << "area: " << triangle_areas[triangle_index] << std::endl;
        }
        
        assert(0);
    }
    
    // compute basis for null space
    std::vector<Vec3d> T;
    for ( unsigned int i = 0; i < 3; ++i )
    {
        if ( eigenvalues[i] < G_EIGENVALUE_RANK_RATIO * eigenvalues[2] )
        {
            T.push_back( Vec3d( A(0,i), A(1,i), A(2,i) ) );
        }
    }
    
    //   Mat33d null_space_projection( 1,0,0, 0,1,0, 0,0,1 );
    
    Mat33d null_space_projection(0,0,0,0,0,0,0,0,0);
    for ( unsigned int row = 0; row < 3; ++row )
    {
        for ( unsigned int col = 0; col < 3; ++col )
        {
            for ( size_t i = 0; i < T.size(); ++i )
            {
                null_space_projection(row, col) += T[i][row] * T[i][col];
            }
        }  
    }
    
    Vec3d t(0,0,0);      // displacement
    double sum_areas = 0;
    
    for ( size_t i = 0; i < incident_triangles.size(); ++i )
    {
        double area = triangle_areas[incident_triangles[i]];
        sum_areas += area;
        Vec3d c = triangle_centroids[incident_triangles[i]] - m_surf.get_position(v);
        t += area * c;
    }
    
    t = null_space_projection * t;
    t /= sum_areas;
    
    displacement = t;
}



// --------------------------------------------------------
///
/// NULL-space smoothing
///
// --------------------------------------------------------

bool MeshSmoother::null_space_smoothing_pass( double dt )
{
    if ( m_surf.m_verbose )
    {
        std::cout << "---------------------- El Topo: vertex redistribution ----------------------" << std::endl;
    }
    
    std::vector<double> triangle_areas;
    triangle_areas.reserve( m_surf.m_mesh.num_triangles());
    std::vector<Vec3d> triangle_normals;
    triangle_normals.reserve( m_surf.m_mesh.num_triangles());
    std::vector<Vec3d> triangle_centroids;
    triangle_centroids.reserve( m_surf.m_mesh.num_triangles());
    
    for ( size_t i = 0; i < m_surf.m_mesh.num_triangles(); ++i )
    {
        const Vec3st& tri = m_surf.m_mesh.get_triangle(i);
        if ( tri[0] == tri[1] )
        {
            triangle_areas.push_back( 0 );
            triangle_normals.push_back( Vec3d(0,0,0) );
            triangle_centroids.push_back( Vec3d(0,0,0) );
        }
        else
        {
            triangle_areas.push_back( m_surf.get_triangle_area( i ) );
            triangle_normals.push_back( m_surf.get_triangle_normal( i ) );
            triangle_centroids.push_back( (m_surf.get_position(tri[0]) + m_surf.get_position(tri[1]) + m_surf.get_position(tri[2])) / 3 );
        }
    }
    
    std::vector<Vec3d> displacements;
    displacements.resize( m_surf.get_num_vertices(), Vec3d(0) );
    
    double max_displacement = 1e-30;
    for ( size_t i = 0; i < m_surf.get_num_vertices(); ++i )
    {
        if ( !m_surf.vertex_is_solid(i) )
        {
            null_space_smooth_vertex( i, triangle_areas, triangle_normals, triangle_centroids, displacements[i] );
            max_displacement = max( max_displacement, mag( displacements[i] ) );
        }
    }
    
    // compute maximum dt
    double max_beta = 1.0; //compute_max_timestep_quadratic_solve( m_surf.m_mesh.get_triangles(), m_surf.m_positions, displacements, m_surf.m_verbose );
    
    if ( m_surf.m_verbose ) { std::cout << "max beta: " << max_beta << std::endl; }
    
    m_surf.m_velocities.resize( m_surf.get_num_vertices() );
    
    for ( size_t i = 0; i < m_surf.get_num_vertices(); ++i )
    {
        m_surf.set_newposition( i, m_surf.get_position(i) + (max_beta) * displacements[i] );
        m_surf.m_velocities[i] = (m_surf.get_newposition(i) - m_surf.get_position(i)) / dt;
    }
    
    // repositioned locations stored in m_newpositions, but needs to be collision safe
    if ( m_surf.m_collision_safety )
    {
        
        bool all_collisions_handled = m_surf.m_collision_pipeline->handle_collisions(dt);
        
        if ( !all_collisions_handled )
        {
            ImpactZoneSolver solver( m_surf );
            bool result = solver.inelastic_impact_zones(dt);
            
            if ( !result )
            {
                result = solver.rigid_impact_zones(dt);
            }
            
            if ( !result ) 
            {
                // couldn't fix collisions!
                std::cerr << "WARNING: Aborting mesh null-space smoothing due to CCD problem" << std::endl;
                return true;
            }
        }
        
        
        // TODO: Replace this with a cut-back and re-integrate
        // Actually, a call to DynamicSurface::integrate(dt) would be even better
        
        std::vector<Intersection> intersections;
        m_surf.get_intersections( false, true, intersections );
        
        if ( intersections.size() != 0 )
        {
            // couldn't fix collisions!
            std::cerr << "WARNING: Aborting mesh null-space smoothing due to CCD problem" << std::endl;
            return true;         
        }
        
    }
    
    // used to test convergence
    double max_position_change = 0.0;
    
    // Set positions
    for(size_t i = 0; i < m_surf.get_num_vertices(); i++)
    {
        max_position_change = max( max_position_change, mag( m_surf.get_newposition(i) - m_surf.get_position(i) ) );
    } 
    
    m_surf.set_positions_to_newpositions();
    
    
    if ( m_surf.m_verbose ) { std::cout << "max_position_change: " << max_position_change << std::endl; }
    
    // We will test convergence by checking whether the largest change in
    // position has magnitude less than: CONVERGENCE_TOL_SCALAR * average_edge_length  
    const static double CONVERGENCE_TOL_SCALAR = 1.0;   
    bool converged = false;
    if ( max_position_change < CONVERGENCE_TOL_SCALAR * m_surf.get_average_edge_length() )
    {
        converged = true;
    }
    
    return !converged;
}




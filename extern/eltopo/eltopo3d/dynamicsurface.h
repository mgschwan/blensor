// ---------------------------------------------------------
//
//  dynamicsurface.h
//  Tyson Brochu 2008
//  
//  A triangle mesh with associated vertex locations and  masses.  Query functions for getting geometry info.
//
//  The most important function is integrate(), which advances the mesh vertices from m_positions to m_newpositions, while 
//  performing collision detection and resolution.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_DYNAMICSURFACE_H
#define EL_TOPO_DYNAMICSURFACE_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <ccd_wrapper.h>
#include <nondestructivetrimesh.h>
#include <limits>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

// Broad-phase collision detector.  Avoids performing collision detection between far-away primitives.
class BroadPhase;

// Class for encapsulating all collision detection and resolution functionality.
class CollisionPipeline;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Edge-triangle intersection info.
///
// --------------------------------------------------------

struct Intersection
{
    
    /// Constructor
    ///
    Intersection(size_t edge_index, 
                 size_t triangle_index ) :
    m_edge_index( edge_index ),
    m_triangle_index( triangle_index )
    {}
    
    /// The index of the edge intersecting the triangle
    ///
    size_t m_edge_index;
    
    /// Index of the triangle intersecting the edge
    ///
    size_t m_triangle_index;
    
};


// --------------------------------------------------------
///
/// A surface mesh.  Essentially consists of a NonDestructiveTriMesh object coupled with a set of vertex locations in 3D space.
///
// --------------------------------------------------------

class DynamicSurface
{
    
public:
    
    /// Create a DynamicSurface object from the specified vertices, triangles, and vertex masses.
    ///
    DynamicSurface( const std::vector<Vec3d>& vs, 
                   const std::vector<Vec3st>& ts, 
                   const std::vector<double>& masses,
                   double in_proximity_epsilon = 1e-4,
                   double in_friction_coefficient = 0.0,
                   bool in_collision_safety = true,
                   bool in_verbose = false );
    
    /// Destructor
    /// 
    virtual ~DynamicSurface(); 
    
private:
    
    /// Disallowed, do not implement
    ///
    DynamicSurface( const DynamicSurface& );
    
    /// Disallowed, do not implement
    ///
    DynamicSurface& operator=( const DynamicSurface& );
    
public:
    
    /// Advance from current state to a collision-free state as close as possible to predicted state.
    /// 
    virtual void integrate( double dt, double& actual_dt );

    //
    // Utility
    //

    /// Break up the triangle mesh into connected components, determine surface IDs for all vertices.
    ///
    void partition_surfaces( std::vector<size_t>& surface_ids, std::vector< std::vector< size_t> >& surfaces ) const;
    
    /// Compute the area of the specified triangle
    ///
    inline double get_triangle_area(size_t tri) const;
    
    /// Compute the area of the specified triangle
    ///    
    inline double get_triangle_area(const Vec3st& tri) const;
    
    /// Compute the area of the specified triangle
    ///
    inline double get_triangle_area(size_t v0, size_t v1, size_t v2) const;
    
    /// Get the smallest triangle in the mesh by area.
    ///
    inline double get_min_triangle_area( size_t& out_triangle_index ) const;
    
    /// Compute the vector normal to the specified triangle's plane
    ///
    inline Vec3d get_triangle_normal(size_t tri) const;
    
    /// Compute the vector normal to the specified triangle's plane
    ///    
    inline Vec3d get_triangle_normal(const Vec3st& tri) const;
    
    /// Compute the vector normal to the specified triangle's plane
    ///    
    inline Vec3d get_triangle_normal(size_t v0, size_t v1, size_t v2) const;
    
    /// Compute the specified triangle's barycenter
    ///    
    inline Vec3d get_triangle_barycenter( size_t triangle_index ) const;
    
    /// Get an estimate for the surface normal at the specified vertex. Computed using an unweighted average of the normals of 
    /// incident triangles.
    ///
    inline Vec3d get_vertex_normal( size_t vertex ) const;
    
    /// Compute all vertex normals, using an unweighted average of incident triangle normals.
    ///
    void get_all_vertex_normals( std::vector<Vec3d>& normals ) const;
    
    /// Get an estimate for the surface normal at the specified vertex. Computed using a weighted average as described in [Max 1999].
    ///
    inline Vec3d get_vertex_normal_max( size_t vertex_index ) const;
    
    /// Compute the edge length of the specified edge
    ///
    inline double get_edge_length( size_t edge_index ) const;
    
    /// Get the average edge length over all edges
    ///
    inline double get_average_edge_length() const;
    
    /// Get the average edge length, disregarding edges with vertices marked as solid
    ///
    inline double get_average_non_solid_edge_length() const;
    
    /// Determine if the vertex is on a solid surface (has infinite mass).
    ///
    inline bool vertex_is_solid( size_t vertex_index ) const;
    
    /// Determine if the edge is on a solid surface (has infinite mass).
    ///
    inline bool edge_is_solid( size_t eedge_index ) const;
    
    /// Determine if the triangle is on a solid surface (has infinite mass).
    ///    
    inline bool triangle_is_solid( size_t triangle_index ) const;
    
    /// Compute the total surface area defined by the mesh
    ///
    inline double get_surface_area( ) const;
    
    /// Compute the total surface area using predicted vertex locations (m_newpositions)
    ///
    inline double get_predicted_surface_area() const;
    
    /// Compute the volume enclosed by the surface
    ///
    inline double get_volume() const;
    
    /// Compute the volume enclosed by the surface, using predicted vertex locations (m_newpositions)
    ///
    inline double get_predicted_volume() const;
    
    /// Compute the distance from the given point to the surface.  Also return the index of the closest triangle.
    ///
    double distance_to_surface( const Vec3d& p, size_t& out_closest_triangle ) const;
    
    /// Determine the rank of the primary space at the given vertex (see Jiao07).
    /// Rank {1, 2, 3} == {smooth, ridge, peak}
    ///
    unsigned int vertex_primary_space_rank( size_t v ) const;
    

    //
    // Broad phase collision detector
    //
    
    /// Delete and rebuild the broad phase object, using AABBs defined from m_positions.
    ///
    void rebuild_static_broad_phase( );
    
    /// Delete and rebuild the broad phase object, using AABBs defined from m_positions and m_newpositions.
    ///
    void rebuild_continuous_broad_phase( );
    
    /// Assume that the specified vertex has moved.  Update the broadphase entries of the vertex, its incident edges and incident 
    /// triangles.
    ///
    void update_static_broad_phase( size_t vertex_index );
    
    /// Assume that the specified vertex has moved.  Update the broadphase entries of the vertex, its incident edges and incident 
    /// triangles, using current and predicted positions.
    ///    
    void update_continuous_broad_phase( size_t vertex_index );  
    
    /// Get the padded AABB of the specified vertex using current positions.
    ///
    void vertex_static_bounds(size_t v, Vec3d &xmin, Vec3d &xmax) const;
    
    /// Get the padded AABB of the specified edge using current positions.
    ///
    void edge_static_bounds(size_t e, Vec3d &xmin, Vec3d &xmax) const;
    
    /// Get the padded AABB of the specified triangle using current positions.
    ///
    void triangle_static_bounds(size_t t, Vec3d &xmin, Vec3d &xmax) const; 
    
    /// Get the padded AABB of the specified vertex using current and predicted positions.
    ///
    void vertex_continuous_bounds(size_t v, Vec3d &xmin, Vec3d &xmax) const;
    
    /// Get the padded AABB of the specified edge using current and predicted positions.
    ///    
    void edge_continuous_bounds(size_t e, Vec3d &xmin, Vec3d &xmax) const;
    
    /// Get the padded AABB of the specified triangle using current and predicted positions.
    ///        
    void triangle_continuous_bounds(size_t t, Vec3d &xmin, Vec3d &xmax) const;
    
    /// Caution: slow!
    /// Check the consistency of the broad phase by comparing against the N^2 broadphase.
    ///
    void check_static_broad_phase_is_up_to_date() const;
    
    /// Caution: slow!
    /// Check the consistency of the broad phase by comparing against the N^2 broadphase.  Checks using current and predicted vertex 
    /// positions.
    void check_continuous_broad_phase_is_up_to_date() const;
    
    // 
    // Intersection detection 
    //
    
    /// Get the set of triangles intersected by the given segment. Also returns the barycentric coordinate along the segment of each
    /// intersection.
    ///
    void get_triangle_intersections(const Vec3d& segment_point_a, 
                                    const Vec3d& segment_point_b,
                                    std::vector<double>& hit_ss,
                                    std::vector<size_t>& hit_triangles ) const;
    
    /// Count the number of triangles intersected by the given segment.
    ///
    size_t get_number_of_triangle_intersections( const Vec3d& segment_point_a, 
                                                const Vec3d& segment_point_b ) const;
    
    /// Using exact intersection testing, count the number of triangle intersected by the given segment.
    ///
    size_t get_number_of_triangle_intersections_exact( const Vec3d& segment_point_a, 
                                                      const Vec3d& segment_point_b ) const;
    
    /// Test the given triangle against all other triangles in the mesh for intersection.
    ///
    bool check_triangle_vs_all_triangles_for_intersection( size_t tri_index );
    
    /// Test the given triangle against all other triangles in the mesh for intersection.
    ///
    bool check_triangle_vs_all_triangles_for_intersection( const Vec3st& tri );
    
    /// Get all self-intersections in the surface
    ///
    void get_intersections(bool degeneracy_counts_as_intersection, 
                           bool use_new_positions, 
                           std::vector<Intersection>& intersections );
    
    /// Look for self-intersections, but stop when the first one is found
    ///
    void get_first_intersection( bool degeneracy_counts_as_intersection, 
                                bool use_new_positions, 
                                Intersection& intersections );
    
    /// Fire an assert if the mesh contains a self-intersection. Uses m_positions as the vertex locations.
    ///
    void assert_mesh_is_intersection_free( bool degeneracy_counts_as_intersection );              
    
    /// Using m_newpositions as the vertex locations, fire an assert if the mesh contains a self-intersection.
    ///
    void assert_predicted_mesh_is_intersection_free( bool degeneracy_counts_as_intersection ); 

    /// Returns the number of vertices in the mesh, including any vertices marked as deleted
    ///
    inline size_t get_num_vertices() const;
    
    /// Returns the current positions of a vertex.
    ///
    inline const Vec3d& get_position( size_t index ) const;

    /// Returns the set of all current vertex positions.
    ///
    inline const std::vector<Vec3d>& get_positions( ) const;
    
    /// Set the current position of an individual vertex.
    ///
    inline void set_position( size_t index, const Vec3d& x );   
    
    /// Set the current positions of all vertices in the mesh.
    ///
    inline void set_all_positions( const std::vector<Vec3d>& xs );
    
    /// Set the current positions of all vertices in the mesh, from a C-array of doubles
    ///
    inline void set_all_positions( size_t n, const double* xs );
    
    /// Copy predicted vertex positions into the current positions
    ///
    inline void set_positions_to_newpositions();

    /// Returns the predicted position of a vertex.
    ///
    inline const Vec3d& get_newposition( size_t index ) const;
    
    /// Returns the set of all predicted vertex positions.
    ///
    inline const std::vector<Vec3d>& get_newpositions( ) const;
    
    /// Set the predicted position of an individual vertex.
    ///
    inline void set_newposition( size_t index, const Vec3d& x );   
    
    /// Set the predicted positions of all vertices in the mesh.
    ///
    inline void set_all_newpositions( const std::vector<Vec3d>& xs );
    
    /// Set the predicted positions of all vertices in the mesh from a C-array.
    ///
    inline void set_all_newpositions( size_t n, const double* xs );
    
    
    //
    // Data members
    //
    
    /// Elements closer than this have repulsion forces applied
    ///
    double m_proximity_epsilon;
    
    /// Dump lots of details to stdout
    ///
    bool m_verbose;
    
    /// Ensure that no mesh elements intersect, during mesh moving and mesh maintenance
    ///
    bool m_collision_safety;
    
    /// Vertex positions, predicted locations, velocities and masses
    ///
    std::vector<double> m_masses;
    
    /// The mesh graph
    ///
    NonDestructiveTriMesh m_mesh;
    
    /// collision acceleration structures
    ///
    BroadPhase* m_broad_phase;
    
    /// Encapsulates the collision detection functionality
    ///
    CollisionPipeline* m_collision_pipeline;
    
    /// Amount to pad AABBs by when doing broad-phase collision detection
    ///
    double m_aabb_padding;
    
protected:
    
    friend class CollisionPipeline;
    friend class ImpactZoneSolver;
    friend class MeshSmoother;
    
    /// Current and predicted vertex positions
    ///
    std::vector<Vec3d> pm_positions, pm_newpositions;
    
    /// Temporary velocities field
    ///
    std::vector<Vec3d> m_velocities;
    
};


// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Compute area of a triangle specified by three vertices
///
// --------------------------------------------------------

inline double triangle_area( const Vec3d& v0, const Vec3d &v1, const Vec3d &v2 )
{
    return 0.5 * mag( cross( v1 - v0, v2 - v0 ) );
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a triangle index
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(size_t tri) const
{
    const Vec3st &t = m_mesh.get_triangle( tri ); 
    return get_triangle_area(t[0], t[1], t[2]);
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a triple of vertex indices
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(const Vec3st& tri) const
{
    return get_triangle_area(tri[0], tri[1], tri[2]);
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a three vertex indices
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(size_t v0, size_t v1, size_t v2) const
{
    const Vec3d &p0 = get_position(v0);
    const Vec3d &p1 = get_position(v1);
    const Vec3d &p2 = get_position(v2);
    
    return 0.5 * mag(cross(p1-p0, p2-p0));
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by three vertices
///
// --------------------------------------------------------

inline Vec3d triangle_normal( const Vec3d& v0, const Vec3d &v1, const Vec3d &v2 )
{
    Vec3d u = v1 - v0;
    Vec3d v = v2 - v0;
    return normalized(cross(u, v));
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by a triangle index
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(size_t tri) const
{
    const Vec3st &t = m_mesh.get_triangle( tri ); 
    return get_triangle_normal(t[0], t[1], t[2]);
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by a triple of vertex indices
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(const Vec3st& tri) const
{
    return get_triangle_normal(tri[0], tri[1], tri[2]);
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by three vertex indices
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(size_t v0, size_t v1, size_t v2) const
{
    Vec3d u = get_position(v1) - get_position(v0);
    Vec3d v = get_position(v2) - get_position(v0);
    return normalized(cross(u, v));
}

// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_barycenter( size_t triangle_index ) const
{
    const Vec3st& tri = m_mesh.get_triangle( triangle_index );
    return 1.0 / 3.0 * ( get_position( tri[0] ) + get_position( tri[1] ) + get_position( tri[2] ) );
}

// --------------------------------------------------------
///
/// Return the triangle with the the smallest area, and that area
///
// --------------------------------------------------------

inline double DynamicSurface::get_min_triangle_area( size_t& triangle_index ) const
{
    double min_area = BIG_DOUBLE;
    for ( size_t i = 0; i < m_mesh.num_triangles(); ++i )
    {
        if ( m_mesh.get_triangle(i)[0] == m_mesh.get_triangle(i)[1] )
        {
            continue;
        }
        
        double area = get_triangle_area(i);
        if ( area < min_area )
        {
            min_area = area;
            triangle_index = i;
        }
    }
    
    return min_area;
}

// --------------------------------------------------------
///
/// Compute surface normal at the specified vertex (unweighted average of incident triangle normals).
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_vertex_normal( size_t vertex ) const
{
    Vec3d normal(0,0,0);
    for ( size_t i = 0; i < m_mesh.m_vertex_to_triangle_map[vertex].size(); ++i )
    {
        normal += get_triangle_normal( m_mesh.m_vertex_to_triangle_map[vertex][i] );
    }
    normal /= double(m_mesh.m_vertex_to_triangle_map[vertex].size());
    normal /= mag(normal);
    
    return normal;
}

// --------------------------------------------------------
///
/// Compute surface normal at the specified vertex (weighted according to [Max 1999]).
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_vertex_normal_max( size_t vertex_index ) const
{
    const std::vector<size_t>& inc_tris = m_mesh.m_vertex_to_triangle_map[vertex_index];
    
    Vec3d sum_cross_products(0,0,0);
    
    for ( size_t i = 0; i < inc_tris.size(); ++i )
    {
        const Vec3st& curr_tri = m_mesh.get_triangle( inc_tris[i] );
        
        if ( curr_tri[0] == curr_tri[1] ) { continue; }
        
        Vec2ui other_two;
        NonDestructiveTriMesh::index_in_triangle( curr_tri, vertex_index, other_two );
        
        size_t verti = curr_tri[other_two[0]];
        size_t vertnext = curr_tri[other_two[1]];
        
        Vec3d vi = get_position(verti) - get_position(vertex_index);
        Vec3d vnext = get_position(vertnext) - get_position(vertex_index);
        
        sum_cross_products += cross( vi, vnext ) / ( mag2(vi)*mag2(vnext) );
    }
    
    sum_cross_products /= mag( sum_cross_products );
    
    return sum_cross_products;
}


// --------------------------------------------------------
///
/// Compute length of the specified edge
///
// --------------------------------------------------------

inline double DynamicSurface::get_edge_length( size_t edge_index ) const
{
    return mag( get_position( m_mesh.m_edges[edge_index][1] ) - get_position( m_mesh.m_edges[edge_index][0] ) );
}

// --------------------------------------------------------
///
/// Compute average length over all mesh edges
///
// --------------------------------------------------------

inline double DynamicSurface::get_average_edge_length() const
{
    double sum_lengths = 0;
    for ( size_t i = 0; i < m_mesh.m_edges.size(); ++i )
    {
        const Vec2st& e = m_mesh.m_edges[i]; 
        if ( e[0] == e[1] )  { continue; }
        sum_lengths += mag( get_position(e[1]) - get_position(e[0]) ); 
    }

	double len = sum_lengths / (double) m_mesh.m_edges.size();

    return len;   
}

// --------------------------------------------------------
///
/// Compute average length over edges on non-solid meshes
///
// --------------------------------------------------------

inline double DynamicSurface::get_average_non_solid_edge_length() const
{
    double sum_lengths = 0;
    size_t counted_edges = 0;
    for ( size_t i = 0; i < m_mesh.m_edges.size(); ++i )
    {
        const Vec2st& e = m_mesh.m_edges[i]; 
        if ( e[0] == e[1] )  { continue; }
        if ( edge_is_solid(i) ) { continue; }
        sum_lengths += mag( get_position(e[1]) - get_position(e[0]) ); 
        ++counted_edges;
    }
    return sum_lengths / (double) counted_edges;   
}

// --------------------------------------------------------
///
/// Compute the surface area
///
// --------------------------------------------------------

inline double DynamicSurface::get_surface_area( ) const
{
    double area=0;
    const std::vector<Vec3st>& tris = m_mesh.get_triangles();
    for(size_t t=0; t < tris.size(); ++t )
    {
        if ( tris[t][0] ==  tris[t][1] ) { continue; }
        area += get_triangle_area(t);
    }
    return area;
}
// --------------------------------------------------------
///
/// Compute the surface area using predicted vertex locations
///
// --------------------------------------------------------

inline double DynamicSurface::get_predicted_surface_area( ) const
{
    double area=0;
    const std::vector<Vec3st>& tris = m_mesh.get_triangles();
    for(size_t t=0; t < tris.size(); ++t )
    {
        if ( tris[t][0] ==  tris[t][1] ) { continue; }
        const Vec3d &p0 = get_newposition(tris[t][0]);
        const Vec3d &p1 = get_newposition(tris[t][1]);
        const Vec3d &p2 = get_newposition(tris[t][2]);      
        area += 0.5 * mag(cross(p1-p0, p2-p0));
    }
    return area;
}

// --------------------------------------------------------
///
/// Compute the volume enclosed by this surface
///
// --------------------------------------------------------

inline double DynamicSurface::get_volume( ) const
{
    static const double inv_six = 1.0/6.0;
    double volume=0;
    const std::vector<Vec3st>& tris = m_mesh.get_triangles();
    for(size_t t=0; t < tris.size(); ++t )
    {
        if ( tris[t][0] == tris[t][1] ) { continue; }
        const Vec3st& tri = tris[t];
        volume += inv_six * triple(get_position(tri[0]), get_position(tri[1]), get_position(tri[2]));
    }
    return volume;
}

// --------------------------------------------------------
///
/// Compute the volume using predicted vertex locations
///
// --------------------------------------------------------

inline double DynamicSurface::get_predicted_volume( ) const
{
    static const double inv_six = 1.0/6.0;
    double volume=0;
    const std::vector<Vec3st>& tris = m_mesh.get_triangles();
    for(size_t t=0; t < tris.size(); ++t )
    {
        if ( tris[t][0] ==  tris[t][1] ) { continue; }
        const Vec3st& tri = tris[t];
        volume += inv_six * triple(get_newposition(tri[0]), get_newposition(tri[1]), get_newposition(tri[2]));
    }
    return volume;
}

// --------------------------------------------------------
///
/// Return true if the specified vertex is solid (should be treated as having infinite mass).
///
// --------------------------------------------------------

inline bool DynamicSurface::vertex_is_solid( size_t v ) const
{
    assert( v < m_masses.size() );
    return ( m_masses[v] == std::numeric_limits<double>::infinity() );
}

// --------------------------------------------------------
///
/// Return true if either end vertex of the specified edge is solid (should be treated as having infinite mass).
///
// --------------------------------------------------------

inline bool DynamicSurface::edge_is_solid( size_t e ) const
{
    const Vec2st& edge = m_mesh.m_edges[e];
    return ( vertex_is_solid(edge[0]) || vertex_is_solid(edge[1]) );
}

// --------------------------------------------------------
///
/// Return true if any corner vertex of the specified triangle is solid (should be treated as having infinite mass).
///
// --------------------------------------------------------

inline bool DynamicSurface::triangle_is_solid( size_t t ) const
{
    const Vec3st& tri = m_mesh.get_triangle(t);
    return ( vertex_is_solid(tri[0]) || vertex_is_solid(tri[1]) || vertex_is_solid(tri[2]) );
}


// ---------------------------------------------------------
///
/// Returns the number of vertices in the mesh, including any vertices marked as deleted
///
// ---------------------------------------------------------

inline size_t DynamicSurface::get_num_vertices() const
{
    return pm_positions.size();
}

// ---------------------------------------------------------
///
/// Returns the current positions of a vertex.
///
// ---------------------------------------------------------

inline const Vec3d& DynamicSurface::get_position( size_t index ) const
{
    assert( index < pm_positions.size() );
    return pm_positions[index];   
}

// ---------------------------------------------------------
///
/// Returns the set of all current vertex positions.
///
// ---------------------------------------------------------

inline const std::vector<Vec3d>& DynamicSurface::get_positions( ) const
{
    return pm_positions;
}

// ---------------------------------------------------------
///
/// Set the current position of an individual vertex.
///
// ---------------------------------------------------------

inline void DynamicSurface::set_position( size_t index, const Vec3d& x )
{
    assert( index < pm_positions.size() );
    pm_positions[index] = x;
    
    // update broad phase
    if ( m_collision_safety )
    {
        update_continuous_broad_phase( index );
    }
}

// ---------------------------------------------------------
///
/// Set the current positions of all vertices in the mesh.
///
// ---------------------------------------------------------

inline void DynamicSurface::set_all_positions( const std::vector<Vec3d>& xs )
{
    pm_positions = xs;
    pm_newpositions = xs;
    
    // update broad phase
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
    }
}

// ---------------------------------------------------------
///
/// Set the current positions of all vertices in the mesh, from a C-array of doubles
///
// ---------------------------------------------------------

inline void DynamicSurface::set_all_positions( size_t n, const double* xs )
{
    pm_positions.resize(n);
    for ( size_t i = 0; i < n; ++i )
    {
        pm_positions[i][0] = xs[3*i+0];
        pm_positions[i][1] = xs[3*i+1];
        pm_positions[i][2] = xs[3*i+2];
    }
    
    pm_newpositions = pm_positions;
    
    // update broad phase
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
    }
}

// ---------------------------------------------------------
///
/// Copy predicted vertex positions into the current positions
///
// ---------------------------------------------------------

inline void DynamicSurface::set_positions_to_newpositions()
{
    pm_positions = pm_newpositions;
    
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
    }
}

// ---------------------------------------------------------
///
/// Returns the predicted position of a vertex.
///
// ---------------------------------------------------------

inline const Vec3d& DynamicSurface::get_newposition( size_t index ) const
{
    assert( index < pm_newpositions.size() );
    return pm_newpositions[index];   
}

// ---------------------------------------------------------
///
/// Set the predicted position of an individual vertex.
///
// ---------------------------------------------------------

inline void DynamicSurface::set_newposition( size_t index, const Vec3d& x )
{
    assert( index < pm_newpositions.size() );
    
    pm_newpositions[index] = x;
    
    // update broad phase
    if ( m_collision_safety )
    {
        update_continuous_broad_phase( index );
    }
    
}

// ---------------------------------------------------------
///
/// Set the predicted positions of all vertices in the mesh.
///
// ---------------------------------------------------------

inline void DynamicSurface::set_all_newpositions( const std::vector<Vec3d>& xs )
{
    pm_newpositions = xs;
    
    // update broad phase
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
    }
}

// ---------------------------------------------------------
///
/// Set the predicted positions of all vertices in the mesh from a C-array.
///
// ---------------------------------------------------------

inline void DynamicSurface::set_all_newpositions( size_t n, const double* xs )
{
    pm_newpositions.resize(n);
    for ( size_t i = 0; i < n; ++i )
    {
        pm_newpositions[i][0] = xs[3*i+0];
        pm_newpositions[i][1] = xs[3*i+1];
        pm_newpositions[i][2] = xs[3*i+2];
    }
    
    // update broad phase
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
    }
}

// ---------------------------------------------------------
///
/// Returns the set of all predicted vertex positions.
///
// ---------------------------------------------------------

inline const std::vector<Vec3d>& DynamicSurface::get_newpositions( ) const
{
    return pm_newpositions;
}


// --------------------------------------------------------
///
/// Returns true if the specified edge is intersecting the specified triangle
///
// --------------------------------------------------------

inline bool check_edge_triangle_intersection_by_index( size_t edge_a, 
                                                      size_t edge_b, 
                                                      size_t triangle_a, 
                                                      size_t triangle_b, 
                                                      size_t triangle_c, 
                                                      const std::vector<Vec3d>& m_positions, 
                                                      bool verbose )
{
    if (    edge_a == triangle_a || edge_a == triangle_b || edge_a == triangle_c 
        || edge_b == triangle_a || edge_b == triangle_b || edge_b == triangle_c )
    {
        return false;
    }
    
    static const bool DEGEN_COUNTS_AS_INTERSECTION = true;
    
    return segment_triangle_intersection(m_positions[edge_a], edge_a, m_positions[edge_b], edge_b,
                                         m_positions[triangle_a], triangle_a, 
                                         m_positions[triangle_b], triangle_b, 
                                         m_positions[triangle_c], triangle_c,
                                         DEGEN_COUNTS_AS_INTERSECTION, verbose);
    
}


// --------------------------------------------------------
///
/// Returns true if the an edge from one of the triangles intersects the other triangle.
/// NOTE: Using this routine will produce duplicate checks.  Better to use check_edge_triangle_intersection where possible.
///
// --------------------------------------------------------

inline bool check_triangle_triangle_intersection( Vec3st triangle_a, 
                                                 Vec3st triangle_b, 
                                                 const std::vector<Vec3d>& positions )
{
    if ( triangle_a[0] == triangle_a[1] || triangle_b[0] == triangle_b[1] )    
    { 
        return false; 
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_a[0], triangle_a[1], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   positions, false ) )
    {
        return true;
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_a[1], triangle_a[2], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   positions, false ) )
    {
        return true;
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_a[2], triangle_a[0], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   positions, false ) )
    {
        return true;
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_b[0], triangle_b[1], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   positions, false ) )
    {
        return true;
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_b[1], triangle_b[2], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   positions, false ) )
    {
        return true;
    }
    
    if ( check_edge_triangle_intersection_by_index( triangle_b[2], triangle_b[0], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   positions, false ) )
    {
		return true;
    }
    
    return false;
}

#endif



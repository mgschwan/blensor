// ---------------------------------------------------------
//
//  nondestructivetrimesh.h
//  Tyson Brochu 2008
//  
//  The graph of a triangle surface mesh (no spatial information).  Elements can be added and 
//  removed dynamically.  Removing elements leaves empty space in the data structures, but they 
//  can be defragmented by updating the connectivity information (rebuilding the mesh).
//
// ---------------------------------------------------------

#ifndef EL_TOPO_NONDESTRUCTIVETRIMESH_H
#define EL_TOPO_NONDESTRUCTIVETRIMESH_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <cassert>
#include <options.h>
#include <vector>
#include <vec.h>


// ---------------------------------------------------------
//  Non-member function declarations
// ---------------------------------------------------------

/// Safely convert a size_t to an int
///
int to_int( size_t a );

/// Safely convert a ssize_t to an int
///
int to_int( ssize_t a );


// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Connectivity information for a triangle mesh.  Contains no information on the vertex locations in space.
///
// --------------------------------------------------------

class NonDestructiveTriMesh
{  
    
public:
    
    /// Constructor
    ///
    NonDestructiveTriMesh() :
    m_edges(0),
    m_is_boundary_edge(0), m_is_boundary_vertex(0),
    m_vertex_to_edge_map(0), m_vertex_to_triangle_map(0), m_edge_to_triangle_map(0), m_triangle_to_edge_map(0),
    m_tris(0)
    {}

    
    /// Return a const reference to the set of all triangles, including triangles marked as deleted.
    ///
    inline const std::vector<Vec3st>& get_triangles() const;
    
    /// Return a const reference to the specified triangle.
    ///
    inline const Vec3st& get_triangle( size_t index ) const;
    
    /// Get the number of triangles in the mesh.
    ///
    inline size_t num_triangles() const;
    
    /// Clear all mesh information
    ///
    void clear();
    
    /// Remove auxiliary connectivity information
    ///
    void clear_connectivity();
    
    /// Clear and rebuild connectivity information
    ///
    void update_connectivity( );
    
    /// Determine if the given vertex is on a boundary edge and store in data structure
    ///
    void update_is_boundary_vertex( size_t v );
    
    /// Find the index of an edge in the list of edges, if it exists. Return edges.size if the edge is not found.
    ///
    size_t get_edge_index(size_t vtx0, size_t vtx1) const;  
    
    /// Find the index of a triangle, if it exists. Return triangles.size if the triangle is not found.
    ///
    size_t get_triangle_index( size_t vtx0, size_t vtx1, size_t vtx2 ) const;  
    
    /// Get all triangles adjacent to the specified triangle
    ///
    void get_adjacent_triangles( size_t triangle_index, std::vector<size_t>& adjacent_triangles ) const;
    
    /// Get all vertices adjacent to the specified vertex
    ///
    void get_adjacent_vertices( size_t vertex_index, std::vector<size_t>& adjacent_vertices ) const;
    
    /// Add a triangle to the tris structure, update connectivity
    ///
    size_t nondestructive_add_triangle(const Vec3st& tri);
    
    /// Mark a triangle as deleted without actually changing the data structures
    ///
    void nondestructive_remove_triangle(size_t tri);
    
    /// Add a vertex, update connectivity.  Return index of new vertex.
    ///
    size_t nondestructive_add_vertex( );
    
    /// Remove a vertex, update connectivity
    ///
    void nondestructive_remove_vertex(size_t vtx);
    
    /// Set the stored set of triangles to the specified set.
    ///
    void replace_all_triangles( const std::vector<Vec3st>& new_tris );

    /// Update the number of vertices in the mesh.
    ///
    void set_num_vertices( size_t num_vertices );
    
    /// Given two vertices on a triangle, return the third vertex
    ///
    inline size_t get_third_vertex( size_t vertex0, size_t vertex1, const Vec3st& triangle ) const;

    /// Given two vertices on a triangle, return the third vertex
    ///
    inline size_t get_third_vertex( size_t edge_index, const Vec3st& triangle ) const;
    
    /// Given two vertices on a triangle, return the third vertex
    ///
    inline size_t get_third_vertex( size_t edge_index, size_t triangle_index ) const;
    
    /// Given two vertices on a triangle, return whether or not the triangle has the same orientation
    ///
    inline static bool oriented( size_t vertex0, size_t vertex1, const Vec3st& triangle );
    
    /// Ensure that all adjacent triangles have consistent orientation.
    ///
    void verify_orientation( );
    
    /// Return true if the given triangle is made up of the given vertices
    ///
    inline static bool triangle_has_these_verts( const Vec3st& tri, const Vec3st& verts );
    
    /// Return which vertex in tri matches v.  Also returns the other two vertices in tri.
    ///
    inline static size_t index_in_triangle( const Vec3st& tri, size_t v, Vec2ui& other_two );
    
    /// Return the edge incident on two triangles.  Returns ~0 if triangles are not adjacent.
    ///
    inline size_t get_common_edge( size_t triangle_a, size_t triangle_b );
    
    /// Determine if two triangles are adjacent (if they share an edge)
    ///
    inline bool triangles_are_adjacent( size_t triangle_a, size_t triangle_b );
    
    /// Remove triangles which have been deleted
    ///
    void clear_deleted_triangles( std::vector<Vec2st>* defragged_triangle_map = NULL );
    
    /// Determine if the given edge is on a surface composed of a single tet
    ///
    bool edge_is_on_single_tet( size_t edge_index ) const;
    
    /// Returns true if the triangle is marked for deletion
    ///
    inline bool triangle_is_deleted( size_t triangle_index ) const;
    
    /// Returns true if the edge is marked for deletion
    ///
    inline bool edge_is_deleted( size_t edge_index ) const;
    
    /// Returns true if the vertex is marked for deletion
    ///
    inline bool vertex_is_deleted( size_t vertex_index ) const;
    
    /// Check the consistency of auxiliary data structures
    ///
    void test_connectivity() const;
    
    // 
    // Data members
    //
    
    /// Edges as vertex pairs
    ///
    std::vector<Vec2st> m_edges;    
    
    /// Whether an edge is on a boundary
    ///
    std::vector<bool> m_is_boundary_edge;
    
    /// Whether a vertex is on a boundary
    ///
    std::vector<bool> m_is_boundary_vertex;
    
    /// Edges incident on vertices (given a vertex, which edges is it incident on)
    ///
    std::vector<std::vector<size_t> > m_vertex_to_edge_map; 
    
    /// Triangles incident on vertices (given a vertex, which triangles is it incident on)
    ///
    std::vector<std::vector<size_t> > m_vertex_to_triangle_map;    
    
    /// Triangles incident on edges (given an edge, which triangles is it incident on)
    ///
    std::vector<std::vector<size_t> > m_edge_to_triangle_map;    
    
    /// Edges around triangles (given a triangle, which 3 edges does it contain)
    ///
    std::vector<Vec3st> m_triangle_to_edge_map; 
    
    
private:
    
    /// List of triangles: the fundamental data
    ///
    std::vector<Vec3st> m_tris;
    
    /// Add an edge to the list of edges.  Return the index of the new edge.
    ///
    size_t nondestructive_add_edge(size_t vtx0, size_t vtx1);
    
    /// Mark an edge as deleted, update connectivity
    ///
    void nondestructive_remove_edge( size_t edge_index );
    
};


// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Safely convert a size_t to an int
///
// ---------------------------------------------------------

inline int to_int( size_t a )
{
    assert( a < INT_MAX );
    return static_cast<int>(a);
}

// ---------------------------------------------------------
///
/// Safely convert a ssize_t to an int
///
// ---------------------------------------------------------

inline int to_int( ssize_t a )
{
    assert( a < INT_MAX );
    return static_cast<int>(a);
}

// ---------------------------------------------------------
///
/// Return a reference to the set of all triangles, including triangles marked as deleted.
///
// ---------------------------------------------------------

inline const std::vector<Vec3st>& NonDestructiveTriMesh::get_triangles() const
{
    return m_tris;
}

// ---------------------------------------------------------
///
/// Return a reference to the specified triangle.
///
// ---------------------------------------------------------

inline const Vec3st& NonDestructiveTriMesh::get_triangle( size_t index ) const
{
    return m_tris[index];
}

// ---------------------------------------------------------
///
/// Get the number of triangles in the mesh.
///
// ---------------------------------------------------------

inline size_t NonDestructiveTriMesh::num_triangles() const
{
    return m_tris.size();
}


// --------------------------------------------------------
///
/// Return the vertices of the specified triangle, but in ascending order.
///
// --------------------------------------------------------

inline Vec3st sort_triangle( const Vec3st& t )
{
    if ( t[0] < t[1] )
    {
        if ( t[0] < t[2] )
        {
            if ( t[1] < t[2] )
            {
                return t;
            }
            else
            {
                return Vec3st( t[0], t[2], t[1] );
            }
        }
        else
        {
            return Vec3st( t[2], t[0], t[1] );
        }
    }
    else
    {
        if ( t[1] < t[2] )
        {
            if ( t[0] < t[2] )
            {
                return Vec3st( t[1], t[0], t[2] );
            }
            else
            {
                return Vec3st( t[1], t[2], t[0] );
            }
        }
        else
        {
            return Vec3st( t[2], t[1], t[0] );
        }
    }
}


// --------------------------------------------------------
///
/// Given a triangle and two vertices incident on it, return the third vertex in the triangle.
///
// --------------------------------------------------------

inline size_t NonDestructiveTriMesh::get_third_vertex( size_t vertex0, size_t vertex1, const Vec3st& triangle ) const
{
    if ( !( ( triangle[0] == vertex0 || triangle[1] == vertex0 || triangle[2] == vertex0 ) && ( triangle[0] == vertex1 || triangle[1] == vertex1 || triangle[2] == vertex1 ) ) )
    {
        std::cout << "tri: " << triangle << std::endl;
        std::cout << "v0: " << vertex0 << ", v1: " << vertex1 << std::endl;
        assert(false);
    }
    
    if ( triangle[0] == vertex0 )
    {
        if ( triangle[1] == vertex1 )
        {
            return triangle[2];
        }
        else
        {
            return triangle[1];
        }
    }
    else if ( triangle[1] == vertex0 )
    {
        if ( triangle[2] == vertex1 )
        {
            return triangle[0];
        }
        else
        {
            return triangle[2];
        }
    }
    else
    {
        if ( triangle[0] == vertex1 )
        {
            return triangle[1];
        }
        else
        {
            return triangle[0];
        }
    }
    
}

// ---------------------------------------------------------
///
/// Given an edge and a triangle, return the vertex in the triangle and not on the edge.
///
// ---------------------------------------------------------

inline size_t NonDestructiveTriMesh::get_third_vertex( size_t edge_index, const Vec3st& triangle ) const
{
    return get_third_vertex( m_edges[edge_index][0], m_edges[edge_index][1], triangle );
}

// ---------------------------------------------------------
///
/// Given an edge and a triangle, return the vertex in the triangle and not on the edge.
///
// ---------------------------------------------------------

inline size_t NonDestructiveTriMesh::get_third_vertex( size_t edge_index, size_t triangle_index ) const
{
    return get_third_vertex( m_edges[edge_index][0], m_edges[edge_index][1], m_tris[triangle_index] );
}


// ---------------------------------------------------------
///
/// Set the stored set of triangles to the specified set.
///
// ---------------------------------------------------------

inline void NonDestructiveTriMesh::replace_all_triangles( const std::vector<Vec3st>& new_tris )
{
    m_tris = new_tris;
    update_connectivity( );
}


// --------------------------------------------------------
///
/// Given a triangle and two vertices incident on it, determine if the triangle is oriented according to the order of the
/// given vertices.
///
// --------------------------------------------------------

inline bool NonDestructiveTriMesh::oriented( size_t vertex0, size_t vertex1, const Vec3st& triangle )
{
    assert ( triangle[0] == vertex0 || triangle[1] == vertex0 || triangle[2] == vertex0 );
    assert ( triangle[0] == vertex1 || triangle[1] == vertex1 || triangle[2] == vertex1 );
    
    if ( ( (triangle[0] == vertex0) && (triangle[1] == vertex1) ) || 
        ( (triangle[1] == vertex0) && (triangle[2] == vertex1) ) ||
        ( (triangle[2] == vertex0) && (triangle[0] == vertex1) ) )
    {
        return true;
    }
    
    return false;
}

// --------------------------------------------------------
///
/// Return true if the given triangle is made up of the given vertices
///
// --------------------------------------------------------

inline bool NonDestructiveTriMesh::triangle_has_these_verts( const Vec3st& tri, const Vec3st& verts )
{
    if ( ( tri[0] == verts[0] || tri[0] == verts[1] || tri[0] == verts[2] ) &&
        ( tri[1] == verts[0] || tri[1] == verts[1] || tri[1] == verts[2] ) &&
        ( tri[2] == verts[0] || tri[2] == verts[1] || tri[2] == verts[2] ) )
    {
        return true;
    }
    
    return false;
}

// --------------------------------------------------------
///
/// Return true if the given triangle is made up of the given vertices
///
// --------------------------------------------------------

inline size_t NonDestructiveTriMesh::index_in_triangle( const Vec3st& tri, size_t v, Vec2ui& other_two )
{
    if ( v == tri[0] )
    {
        other_two[0] = 1;
        other_two[1] = 2;
        return 0;
    }
    
    if ( v == tri[1] )
    {
        other_two[0] = 2;
        other_two[1] = 0;      
        return 1;
    }
    
    if ( v == tri[2] )
    {
        other_two[0] = 0;
        other_two[1] = 1;
        return 2;
    }
    
    assert(0);
    
    other_two[0] = static_cast<unsigned int>(~0);
    other_two[1] = static_cast<unsigned int>(~0);
    return static_cast<size_t>(~0);
}


// --------------------------------------------------------
///
/// Get the set of all triangles adjacent to a given triangle
///
// --------------------------------------------------------

inline void NonDestructiveTriMesh::get_adjacent_triangles( size_t triangle_index, std::vector<size_t>& adjacent_triangles ) const
{
    adjacent_triangles.clear();
    
    for ( unsigned int i = 0; i < 3; ++i )
    {
        size_t edge_index = m_triangle_to_edge_map[triangle_index][i];
        
        for ( size_t t = 0; t < m_edge_to_triangle_map[edge_index].size(); ++t )
        {
            if ( m_edge_to_triangle_map[edge_index][t] != triangle_index )
            {  
                adjacent_triangles.push_back( m_edge_to_triangle_map[edge_index][t] );
            }
        }
    }
    
}

// --------------------------------------------------------
///
/// Get the set of all vertices adjacent to a given vertices
///
// --------------------------------------------------------

inline void NonDestructiveTriMesh::get_adjacent_vertices( size_t vertex_index, std::vector<size_t>& adjacent_vertices ) const
{
    adjacent_vertices.clear();
    const std::vector<size_t>& incident_edges = m_vertex_to_edge_map[vertex_index];
    
    for ( size_t i = 0; i < incident_edges.size(); ++i )
    {
        if ( m_edges[ incident_edges[i] ][0] == vertex_index )
        {
            adjacent_vertices.push_back( m_edges[ incident_edges[i] ][1] );
        }
        else
        {
            assert( m_edges[ incident_edges[i] ][1] == vertex_index );
            adjacent_vertices.push_back( m_edges[ incident_edges[i] ][0] );
        }      
    }
    
}

// --------------------------------------------------------
///
/// Determine if the given edge is on a surface composed of a single tet
///
// --------------------------------------------------------

inline bool NonDestructiveTriMesh::edge_is_on_single_tet( size_t edge_index ) const
{
    const Vec2st& e = m_edges[edge_index];
    const std::vector<size_t>& incident_tris0 = m_vertex_to_triangle_map[ e[0] ];
    const std::vector<size_t>& incident_tris1 = m_vertex_to_triangle_map[ e[1] ];
    
    size_t triangle_nhood_size = incident_tris0.size();
    
    for ( size_t i = 0; i < incident_tris1.size(); ++i )
    {
        bool already_counted = false;
        for ( size_t j = 0; j < incident_tris0.size(); ++j )
        {
            if ( incident_tris1[i] == incident_tris0[j] )
            {
                already_counted = true;
                break;
            }
        }
        
        if ( !already_counted )
        {
            ++triangle_nhood_size;
        }
        
    }
    
    // will fire if one of the vertices is on a boundary
    assert( triangle_nhood_size >= 4 );
    
    return (triangle_nhood_size == 4);
    
}

// ---------------------------------------------------------
///
/// Returns true if the triangle is marked for deletion
///
// ---------------------------------------------------------

inline bool NonDestructiveTriMesh::triangle_is_deleted( size_t triangle_index ) const
{
    return ( m_tris[triangle_index][0] == m_tris[triangle_index][1] || 
            m_tris[triangle_index][1] == m_tris[triangle_index][2] ||
            m_tris[triangle_index][2] == m_tris[triangle_index][0] );
    
}

// ---------------------------------------------------------
///
/// Returns true if the edge is marked for deletion
///
// ---------------------------------------------------------

inline bool NonDestructiveTriMesh::edge_is_deleted( size_t edge_index ) const
{
    return ( m_edges[edge_index][0] == m_edges[edge_index][1] );
}

// ---------------------------------------------------------
///
/// Returns true if the vertex is marked for deletion
///
// ---------------------------------------------------------

inline bool NonDestructiveTriMesh::vertex_is_deleted( size_t vertex_index ) const
{
    return ( m_vertex_to_edge_map[vertex_index].size() == 0 );
}

// --------------------------------------------------------
///
/// Return the edge incident on two triangles.  Returns ~0 if triangles are not adjacent.
///
// --------------------------------------------------------

inline size_t NonDestructiveTriMesh::get_common_edge( size_t triangle_a, size_t triangle_b )
{
    const Vec3st& triangle_a_edges = m_triangle_to_edge_map[triangle_a];
    const Vec3st& triangle_b_edges = m_triangle_to_edge_map[triangle_b];
    
    for ( unsigned int i = 0; i < 3; ++i )
    {
        for ( unsigned int j = 0; j < 3; ++j )
        {
            if ( triangle_a_edges[i] == triangle_b_edges[j] )
            {
                return triangle_a_edges[i];
            }
        }      
    }
    
    return static_cast<unsigned int>(~0);
}


// --------------------------------------------------------
///
/// Determine if two triangles are adjacent (if they share an edge)
///
// --------------------------------------------------------

inline bool NonDestructiveTriMesh::triangles_are_adjacent( size_t triangle_a, size_t triangle_b )
{
    return ( get_common_edge( triangle_a, triangle_b ) != (size_t) ~0 );
}

#endif

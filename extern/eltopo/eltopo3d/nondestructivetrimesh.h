
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

#ifndef NONDESTRUCTIVETRIMESH_H
#define NONDESTRUCTIVETRIMESH_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <cassert>
#include <options.h>
#include <vector>
#include <vec.h>

// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Connectivity information for a triangle mesh.  Contains no information on the vertex locations in space.
///
// --------------------------------------------------------

struct NonDestructiveTriMesh
{  
   NonDestructiveTriMesh() :
      m_tris(0), m_edges(0),
      m_vtxedge(0), m_vtxtri(0), m_edgetri(0), m_triedge(0)
   {}
   
   void clear();
   
   void clear_connectivity();
   void update_connectivity( unsigned int nv );
   
   /// Find the index of an edge in the list of edges
   ///
   unsigned int get_edge(unsigned int vtx0, unsigned int vtx1) const;  
   
   /// Get all triangles adjacent to the specified triangle
   ///
   void get_adjacent_triangles( unsigned int triangle_index, std::vector<unsigned int>& adjacent_triangles ) const;
   
   unsigned int add_edge(unsigned int vtx0, unsigned int vtx1);
   
   void nondestructive_add_triangle(const Vec3ui& tri);
   void nondestructive_remove_triangle(unsigned int tri);
   
   unsigned int nondestructive_add_vertex( );
   void nondestructive_remove_vertex(unsigned int vtx);
   
   void nondestructive_add_edge( Vec2ui new_edge );
   void nondestructive_remove_edge( unsigned int edge_index );
   
   /// Given two vertices on a triangle, return the third vertex
   ///
   inline unsigned int get_third_vertex( unsigned int vertex0, unsigned int vertex1, const Vec3ui& triangle ) const;
   
   /// Given two vertices on a triangle, return whether or not the triangle has the same orientation
   ///
   inline static bool oriented( unsigned int vertex0, unsigned int vertex1, const Vec3ui& triangle );
   
   inline static bool triangle_has_these_verts( const Vec3ui& tri, const Vec3ui& verts );
   
   /// Return which vertex in tri matches v.  Also returns the other two vertices in tri.
   ///
   inline static unsigned int index_in_triangle( const Vec3ui& tri, unsigned int v, Vec2ui& other_two );
   
   /// Remove triangles which have been deleted
   ///
   void clear_deleted_triangles();
      
   // ---------------------------------------------------------
   // Data members
   
   /// List of triangles: the fundamental data
   ///
   std::vector<Vec3ui> m_tris;
   
   /// Edges as vertex pairs
   ///
   std::vector<Vec2ui> m_edges;    
   
   /// Edges incident on vertices (given a vertex, which edges is it incident on)
   ///
   std::vector<std::vector<unsigned int> > m_vtxedge; 
   
   /// Ttriangles incident on vertices (given a vertex, which triangles is it incident on)
   ///
   std::vector<std::vector<unsigned int> > m_vtxtri;    
   
   /// Triangles incident on edges (given an edge, which triangles is it incident on)
   ///
   std::vector<std::vector<unsigned int> > m_edgetri;    
   
   /// Edges around triangles (given a triangle, which 3 edges does it contain)
   ///
   std::vector<Vec3ui> m_triedge;    

};

// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Return the vertices of the specified triangle, but in ascending order.
///
// --------------------------------------------------------

inline Vec3ui sort_triangle( const Vec3ui& t )
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
            return Vec3ui( t[0], t[2], t[1] );
         }
      }
      else
      {
         return Vec3ui( t[2], t[0], t[1] );
      }
   }
   else
   {
      if ( t[1] < t[2] )
      {
         if ( t[0] < t[2] )
         {
            return Vec3ui( t[1], t[0], t[2] );
         }
         else
         {
            return Vec3ui( t[1], t[2], t[0] );
         }
      }
      else
      {
         return Vec3ui( t[2], t[1], t[0] );
      }
   }
}


// --------------------------------------------------------
///
/// Given a triangle and two vertices incident on it, return the third vertex in the triangle.
///
// --------------------------------------------------------

inline unsigned int NonDestructiveTriMesh::get_third_vertex( unsigned int vertex0, unsigned int vertex1, const Vec3ui& triangle ) const
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

// --------------------------------------------------------
///
/// Given a triangle and two vertices incident on it, determine if the triangle is oriented according to the order of the
/// given vertices.
///
// --------------------------------------------------------

inline bool NonDestructiveTriMesh::oriented( unsigned int vertex0, unsigned int vertex1, const Vec3ui& triangle )
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

inline bool NonDestructiveTriMesh::triangle_has_these_verts( const Vec3ui& tri, const Vec3ui& verts )
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

inline unsigned int NonDestructiveTriMesh::index_in_triangle( const Vec3ui& tri, unsigned int v, Vec2ui& other_two )
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
   
   other_two[0] = ~0;
   other_two[1] = ~0;
   return ~0;
}


// --------------------------------------------------------
///
/// Get the set of all triangles adjacent to a given triangle
///
// --------------------------------------------------------

inline void NonDestructiveTriMesh::get_adjacent_triangles( unsigned int triangle_index, std::vector<unsigned int>& adjacent_triangles ) const
{
   adjacent_triangles.clear();
   
   for ( unsigned int i = 0; i < 3; ++i )
   {
      unsigned int edge_index = m_triedge[triangle_index][i];

      for ( unsigned int t = 0; t < m_edgetri[edge_index].size(); ++t )
      {
         if ( m_edgetri[edge_index][t] != triangle_index )
         {  
            adjacent_triangles.push_back( m_edgetri[edge_index][t] );
         }
      }
   }
   
}


#endif


// ---------------------------------------------------------
//
//  nondestructivetrimesh.cpp
//  Tyson Brochu 2008
//  
//  Implementation of NonDestructiveTriMesh: the graph of a 
//  triangle surface mesh.  See header for more details.
//
// ---------------------------------------------------------

// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <nondestructivetrimesh.h>

#include <cstdarg>
#include <cstdlib>
#include <cmath>
#include <fstream>

#include <wallclocktime.h>


// ---------------------------------------------------------
// Local constants, typedefs, macros
// ---------------------------------------------------------

/// Avoid modulo operator in (i+1)%3
const static unsigned int i_plus_one_mod_three[3] = {1,2,0};

// ---------------------------------------------------------
// Extern globals
// ---------------------------------------------------------

// ---------------------------------------------------------
// Static function definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Determine whether two edges share the same vertices
///
// --------------------------------------------------------

static bool compare_edges(Vec2ui &e0, Vec2ui &e1)
{
   return (e0[0] == e1[0] && e0[1] == e1[1]) || (e0[0] == e1[1] && e0[1] == e1[0]);
}


// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Clear all mesh information
///
// --------------------------------------------------------

void NonDestructiveTriMesh::clear()
{
   m_tris.clear();
   clear_connectivity();
}


// --------------------------------------------------------
///
/// Mark a triangle as deleted without actually changing the data structures
///
// --------------------------------------------------------

void NonDestructiveTriMesh::nondestructive_remove_triangle(unsigned int tri)
{
   // Update the vertex->triangle map, m_vtxtri
   
   Vec3ui& t = m_tris[tri];
   for(unsigned int i = 0; i < 3; i++)
   {
      // Get the set of triangles incident on vertex t[i]
      std::vector<unsigned int>& vt = m_vtxtri[t[i]];
      
      for(unsigned int j = 0; j < vt.size(); j++)
      {
         // If a triangle incident on vertex t[i] is tri, delete it
         if(vt[j] == tri)
         {  
            vt.erase( vt.begin() + j );
            --j;
         }
      }
   }

   // Clear t, marking it as deleted
   t = Vec3ui(0,0,0);
   
   // Update the triangle->edge map, m_triedge
   
   Vec3ui& te = m_triedge[tri];
   
   for(unsigned int i = 0; i < 3; i++)
   {
      std::vector<unsigned int>& et = m_edgetri[te[i]];
      
      for( int j = 0; j < (int) et.size(); j++)
      {
         if(et[j] == tri)
         {
            et.erase( et.begin() + j );
            --j;
         }
      }
      
      if ( et.empty() )
      {
         // No triangles are incident on this edge.  Delete it.
         nondestructive_remove_edge( te[i] );
      }            
   }
   
   new (&te) Vec3ui(0,0,0);
   
}


// --------------------------------------------------------
///
/// Add a triangle to the tris structure, update connectivity
///
// --------------------------------------------------------

void NonDestructiveTriMesh::nondestructive_add_triangle( const Vec3ui& tri )
{
   int idx = m_tris.size();
   m_tris.push_back(tri);
   m_triedge.resize(idx+1);
   
   for(unsigned int i = 0; i < 3; i++)
   {
      unsigned int vtx0 = tri[ i ];
      unsigned int vtx1 = tri[ i_plus_one_mod_three[i] ];
            
      // Find the edge composed of these two vertices
      unsigned int e = get_edge(vtx0, vtx1);
      if(e == m_edges.size())
      {
         // if the edge doesn't exist, add it
         e = add_edge(vtx0, vtx1);
      }
      
      // Update connectivity
      m_edgetri[e].push_back(idx);       // edge->triangle
      m_triedge[idx][i] = e;             // triangle->edge
      m_vtxtri[tri[i]].push_back(idx);   // vertex->triangle
   }
   
}


// --------------------------------------------------------
///
/// Add a vertex, update connectivity.  Return index of new vertex.
///
// --------------------------------------------------------

unsigned int NonDestructiveTriMesh::nondestructive_add_vertex( )
{  
   assert( m_vtxedge.size() == m_vtxtri.size() );
   
   m_vtxedge.resize( m_vtxedge.size() + 1 );
   m_vtxtri.resize( m_vtxtri.size() + 1 );
      
   return m_vtxtri.size() - 1;
}


// --------------------------------------------------------
///
/// Remove a vertex, update connectivity
///
// --------------------------------------------------------

void NonDestructiveTriMesh::nondestructive_remove_vertex(unsigned int vtx)
{
    
    m_vtxtri[vtx].clear();    //triangles incident on vertices
    
    // check any m_edges incident on this vertex are marked as deleted
    for ( unsigned int i = 0; i < m_vtxedge[vtx].size(); ++i )
    {
       assert( m_edges[ m_vtxedge[vtx][i] ][0] == m_edges[ m_vtxedge[vtx][i] ][1] );
    }
    
    m_vtxedge[vtx].clear();   //edges incident on vertices
   
}


// --------------------------------------------------------
///
/// Mark an edge as deleted, update connectivity
///
// --------------------------------------------------------

void NonDestructiveTriMesh::nondestructive_remove_edge( unsigned int edge_index )
{
   // vertex 0
   {
      std::vector<unsigned int>& vertex_to_edge_map = m_vtxedge[ m_edges[edge_index][0] ];
      for ( unsigned int i=0; i < vertex_to_edge_map.size(); ++i)
      {
         if ( vertex_to_edge_map[i] == edge_index )
         {
            vertex_to_edge_map.erase( vertex_to_edge_map.begin() + i );
         }
      }
   }

   // vertex 1
   {
      std::vector<unsigned int>& vertex_to_edge_map = m_vtxedge[ m_edges[edge_index][1] ];
      for ( unsigned int i=0; i < vertex_to_edge_map.size(); ++i)
      {
         if ( vertex_to_edge_map[i] == edge_index )
         {
            vertex_to_edge_map.erase( vertex_to_edge_map.begin() + i );
         }
      }
   }

   m_edges[edge_index][0] = 0;
   m_edges[edge_index][1] = 0;  
}

// --------------------------------------------------------
///
/// Find edge specified by two vertices.  Return edges.size if the edge is not found.
///
// --------------------------------------------------------

unsigned int NonDestructiveTriMesh::get_edge(unsigned int vtx0, unsigned int vtx1) const
{
   assert( vtx0 < m_vtxedge.size() );
   assert( vtx1 < m_vtxedge.size() );
   
   const std::vector<unsigned int>& edges0 = m_vtxedge[vtx0];
   const std::vector<unsigned int>& edges1 = m_vtxedge[vtx1];
   
   for(unsigned int e0 = 0; e0 < edges0.size(); e0++)
   {
      unsigned int edge0 = edges0[e0];
      
      for(unsigned int e1 = 0; e1 < edges1.size(); e1++)
      {
         if( edge0 == edges1[e1] && m_edges[edge0][0] != m_edges[edge0][1] )
         {
            assert( ( m_edges[edge0][0] == vtx0 && m_edges[edge0][1] == vtx1 ) ||
                         ( m_edges[edge0][1] == vtx0 && m_edges[edge0][0] == vtx1 ) );
            
            return edge0;
         }
      }
   }
   
   return m_edges.size();
}

// --------------------------------------------------------
///
/// Add an edge to the list.  Return the index of the new edge.
///
// --------------------------------------------------------

unsigned int NonDestructiveTriMesh::add_edge(unsigned int vtx0, unsigned int vtx1)
{
   int edge_index = m_edges.size();
   m_edges.push_back(Vec2ui(vtx0, vtx1));
   
   m_edgetri.push_back( std::vector<unsigned int>() );
   
   m_vtxedge[vtx0].push_back(edge_index);
   m_vtxedge[vtx1].push_back(edge_index);
   
   return edge_index;
}


// --------------------------------------------------------
///
/// Remove triangles which have been deleted by nondestructive_remove_triangle
///
// --------------------------------------------------------

void NonDestructiveTriMesh::clear_deleted_triangles()
{  

//   if ( m_tris.size() < 250000 )
//   {
//      for( int i = 0; i < (int) m_tris.size(); i++ )
//      {
//         if( m_tris[i][0] == m_tris[i][1] )
//         {
//            m_tris.erase( m_tris.begin() + i );
//            --i;
//         }
//      }
//   }
//   else
   
   {
      std::vector<Vec3ui> new_tris;
      new_tris.reserve( m_tris.size() );
      std::vector<Vec3ui>::const_iterator iter = m_tris.begin();
      for( ; iter != m_tris.end(); ++iter )
      {
         if( (*iter)[0] != (*iter)[1] )
         {
            new_tris.push_back( *iter );
         }
      }
      m_tris = new_tris;
   }
}

// --------------------------------------------------------
///
/// Remove auxiliary connectivity information
///
// --------------------------------------------------------

void NonDestructiveTriMesh::clear_connectivity()
{
   m_edges.clear();
   m_vtxedge.clear();
   m_vtxtri.clear();
   m_edgetri.clear();
   m_triedge.clear();
}


// --------------------------------------------------------
///
/// Clear and rebuild connectivity information
///
// --------------------------------------------------------

void NonDestructiveTriMesh::update_connectivity( unsigned int nv )
{

   clear_connectivity();
   
   clear_deleted_triangles();
   
   m_vtxtri.resize(nv);
   m_vtxedge.resize(nv);
   m_triedge.resize(m_tris.size());
   
   for(unsigned int i = 0; i < m_tris.size(); i++)
   {
      Vec3ui& t = m_tris[i];
      
      if(t[0] != t[1])
      {
         
         for(unsigned int j = 0; j < 3; j++)
            m_vtxtri[t[j]].push_back(i);
         
         Vec3ui& te = m_triedge[i];
         
         for(int j = 0; j < 3; j++)
         {
            unsigned int vtx0 = t[j];
            unsigned int vtx1 = t[(j+1)%3];
            
            unsigned int e = get_edge(vtx0, vtx1);
            
            if(e == m_edges.size())
            {
               e = add_edge(vtx0, vtx1);
            }
            
            te[j] = e;
            m_edgetri[e].push_back(i);
         }
      }
   }

   
}




// ---------------------------------------------------------
//
//  meshrenderer.cpp
//  Tyson Brochu 2011
//  
//  OpenGL rendering for a triangle mesh.
//
// ---------------------------------------------------------

#include <meshrenderer.h>

#ifndef NO_GUI

#include <dynamicsurface.h>
#include <gluvi.h>

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// OpenGL render a mesh surface
///
// ---------------------------------------------------------

void MeshRenderer::render( const DynamicSurface& surface )
{
    //
    // edges
    //
    
    glDisable(GL_LIGHTING);
    glDepthFunc(GL_LEQUAL);
    
    if ( render_edges )
    {
        glLineWidth(2);
        glBegin(GL_LINES);
        
        for(size_t e = 0; e < surface.m_mesh.m_edges.size(); e++)
        {
            if ( surface.m_mesh.m_is_boundary_edge[e] )
            {
                glColor3d(1,0,0);
            }
            else
            {
                glColor3d(0,0,0);
            }
            
            const Vec2st& edge = surface.m_mesh.m_edges[e];
            const Vec3d& vtx0 = surface.get_position(edge[0]);
            const Vec3d& vtx1 = surface.get_position(edge[1]);
            glVertex3d(vtx0[0], vtx0[1], vtx0[2]);
            glVertex3d(vtx1[0], vtx1[1], vtx1[2]);
        }
        
        glEnd(); 
    }
    
    //
    // vertices
    //
    
    if ( render_vertex_rank )
    {
        glPointSize(5);
        glBegin(GL_POINTS);
        
        for ( size_t v = 0; v < surface.get_num_vertices(); ++v )
        {
            if ( surface.m_mesh.m_vertex_to_triangle_map[v].empty() )
            {
                continue;
            }
            
            if ( surface.vertex_is_solid(v) )
            {
                glColor3f( 1.0f, 0.0f, 0.0f );
            }
            else
            {
                glColor3f( 0.0f, 1.0f, 0.0f );
            }
            
            glVertex3dv( surface.get_position(v).v );      
            
        }
        glEnd();
    }   
    
    //
    // triangles
    //
    
    if ( render_fill_triangles )
    {
        if ( two_sided )
        {
            glLightModeli( GL_LIGHT_MODEL_TWO_SIDE, 1 );
        }
        else
        {
            glEnable(GL_CULL_FACE);
        }
        
        glEnable(GL_LIGHTING);
        glShadeModel(GL_SMOOTH);
        Gluvi::set_generic_lights();
        Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_FRONT);   // exterior surface colour
        Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_BACK);
        
        if ( !smooth_shading )
        {
            glDisable(GL_LIGHTING);
            glColor3d(1,1,1);
        }
        
        if ( render_edges )
        {
            glEnable(GL_POLYGON_OFFSET_FILL);
            glPolygonOffset(1.0f, 1.0f);      //  allow the wireframe to show through
        }
        
        glEnable(GL_DEPTH_TEST);
        glDepthMask(GL_TRUE);
        
        glBegin(GL_TRIANGLES);
        
        for(size_t i = 0; i < surface.m_mesh.num_triangles(); i++)
        {
            const Vec3st& tri = surface.m_mesh.get_triangle(i);
            
            const Vec3d& v0 = surface.get_position(tri[0]);
            const Vec3d& v1 = surface.get_position(tri[1]);
            const Vec3d& v2 = surface.get_position(tri[2]);
            
            glNormal3dv( surface.get_vertex_normal(tri[0]).v );
            glVertex3d(v0[0], v0[1], v0[2]);
            
            glNormal3dv( surface.get_vertex_normal(tri[1]).v );
            glVertex3d(v1[0], v1[1], v1[2]);
            
            glNormal3dv( surface.get_vertex_normal(tri[2]).v );
            glVertex3d(v2[0], v2[1], v2[2]);
            
        }
        
        glEnd();
        
        
        if ( render_edges )
        {
            glDisable(GL_POLYGON_OFFSET_FILL);
        }
        
        glDisable(GL_LIGHTING);
        
    }
    
}


// ---------------------------------------------------------
///
/// OpenGL render a mesh surface
///
// ---------------------------------------------------------

void MeshRenderer::render(const std::vector<Vec3d>& xs,
                          const std::vector<Vec3d>& normals,
                          const std::vector<Vec3st>& triangles,
                          const std::vector<Vec2st>& edges )

{
    
    //
    // edges
    //
    
    glDisable(GL_LIGHTING);
    glDepthFunc(GL_LEQUAL);
    
    if ( render_edges )
    {
        glLineWidth(2);
        glColor3f( 0.0f, 0.0f, 0.0f );
        glBegin(GL_LINES);
        for(size_t e = 0; e < edges.size(); e++)
        {
            const Vec2st& edge = edges[e];
            const Vec3d& vtx0 = xs[edge[0]];
            const Vec3d& vtx1 = xs[edge[1]];
            glVertex3dv( vtx0.v );
            glVertex3dv( vtx1.v );
        }
        glEnd(); 
    }
    
    //
    // vertices
    //
    
    if ( render_vertex_rank )
    {
        glPointSize(5);
        glBegin(GL_POINTS);
        for ( size_t v = 0; v < xs.size(); ++v )
        {
            glVertex3dv( xs[v].v );               
        }
        glEnd();
    }   
    
    //
    // triangles
    //
    
    if ( render_fill_triangles )
    {
        if ( two_sided )
        {
            glLightModeli( GL_LIGHT_MODEL_TWO_SIDE, 1 );
        }
        else
        {
            glEnable(GL_CULL_FACE);
        }
        
        glEnable(GL_LIGHTING);
        glShadeModel(GL_SMOOTH);
        Gluvi::set_generic_lights();
        Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_FRONT);   // exterior surface colour
        Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_BACK);
        
        if ( !smooth_shading )
        {
            glDisable(GL_LIGHTING);
            glColor3d(1,1,1);
        }
        
        if ( render_edges )
        {
            glEnable(GL_POLYGON_OFFSET_FILL);
            glPolygonOffset(1.0f, 1.0f);      //  allow the wireframe to show through
        }
        
        glEnable(GL_DEPTH_TEST);
        glDepthMask(GL_TRUE);
        
        glBegin(GL_TRIANGLES);
        for(size_t i = 0; i < triangles.size(); i++)
        {
            const Vec3st& tri = triangles[i];
            glNormal3dv( normals[tri[0]].v );
            glVertex3dv( xs[tri[0]].v );
            glNormal3dv( normals[tri[1]].v );
            glVertex3dv( xs[tri[1]].v );
            glNormal3dv( normals[tri[2]].v );
            glVertex3dv( xs[tri[2]].v );
        }      
        glEnd();
        
        if ( render_edges )
        {
            glDisable(GL_POLYGON_OFFSET_FILL);
        }
        
        glDisable(GL_LIGHTING);
    }
    
}


#endif // ndef NO_GUI


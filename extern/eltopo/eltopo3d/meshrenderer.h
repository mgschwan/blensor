// ---------------------------------------------------------
//
//  meshrenderer.h
//  Tyson Brochu 2011
//  
//  OpenGL rendering for a triangle mesh.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_MESHRENDERER_H
#define EL_TOPO_MESHRENDERER_H

// ---------------------------------------------------------
//  Nested includes
// ---------------------------------------------------------

#include <vec.h>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

class DynamicSurface;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Mesh rendering object.  Contains current rendering options and functions for doing OpenGL render of a mesh.
///
// ---------------------------------------------------------

class MeshRenderer
{
    
public:
    
    /// Constructor
    ///
    MeshRenderer() :
    render_edges( true ),
    render_fill_triangles( true ),
    render_vertex_rank( false ),
    smooth_shading( true ),
    two_sided( true )
    {}
    
    /// Whether to show mesh edges (wireframe)
    ///
    bool render_edges;
    
    /// Whether to render opaque triangles
    ///
    bool render_fill_triangles;
    
    /// Whether to render the primary-space rank for each vertex
    ///
    bool render_vertex_rank;
    
    /// Whether to use smooth or flat shading
    ///    
    bool smooth_shading;

    /// Render both sides of the triangles
    ///    
    bool two_sided;
    
    /// Display the surface in OpenGL using the current options settings
    ///
    void render( const DynamicSurface& surface );

    /// Display the specified geometry in OpenGL using the current options settings
    ///
    void render(const std::vector<Vec3d>& xs,
                const std::vector<Vec3d>& normals,
                const std::vector<Vec3st>& triangles,
                const std::vector<Vec2st>& edges );
    
    
};


#endif

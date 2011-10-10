// ---------------------------------------------------------
//
//  subdivisionscheme.h
//  Tyson Brochu 2008
//  
//  A collection of interpolation schemes for generating vertex locations.
//
// ---------------------------------------------------------

#ifndef SUBDIVISIONSCHEME_H
#define SUBDIVISIONSCHEME_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <vec.h>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

class DynamicSurface;

// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Subdivision scheme interface.  Declares the function prototype for finding an interpolated vertex location.
///
// --------------------------------------------------------

class SubdivisionScheme
{
public:
   virtual ~SubdivisionScheme() {}
   virtual void generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point ) = 0;
};

// --------------------------------------------------------
///
/// Midpoint scheme: simply places the new vertex at the midpoint of the edge
///
// --------------------------------------------------------

class MidpointScheme : public SubdivisionScheme
{
public:
   void generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point );   
};

// --------------------------------------------------------
///
/// Butterfly scheme: uses a defined weighting of nearby vertices to determine the new vertex location
///
// --------------------------------------------------------

class ButterflyScheme : public SubdivisionScheme
{
public:   
   void generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point );
};

// --------------------------------------------------------
///
/// Quadric error minimization scheme: places the new vertex at the location that minimizes the change in the quadric metric tensor along the edge.
///
// --------------------------------------------------------

class QuadraticErrorMinScheme : public SubdivisionScheme
{
public:
   void generate_new_midpoint( unsigned int edge_index, const DynamicSurface& surface, Vec3d& new_point );
};


#endif




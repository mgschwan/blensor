
// ---------------------------------------------------------
//
//  ccd_wrapper.h
//  Tyson Brochu 2009
//
//  General interface for collision and intersection queries.
//
// ---------------------------------------------------------


#ifndef CCD_WRAPPER_H
#define CCD_WRAPPER_H

#include <vec.h>

#define USE_CUBIC_SOLVER_CCD
//#define USE_TUNICATE_CCD

// --------------------------------------------------------------------------------------------------
// 2D
// --------------------------------------------------------------------------------------------------

// x0 is the point, x1-x2 is the segment. Take care to specify x1,x2 in sorted order of index!
bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, unsigned int index0,
                             const Vec2d& x1, const Vec2d& xnew1, unsigned int index1,
                             const Vec2d& x2, const Vec2d& xnew2, unsigned int index2);

bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, unsigned int index0,
                             const Vec2d& x1, const Vec2d& xnew1, unsigned int index1,
                             const Vec2d& x2, const Vec2d& xnew2, unsigned int index2,
                             double& edge_alpha, Vec2d& normal, double& time, double& rel_disp);

bool segment_segment_intersection(const Vec2d& x0, unsigned int index0, 
                                  const Vec2d& x1, unsigned int index1,
                                  const Vec2d& x2, unsigned int index2,
                                  const Vec2d& x3, unsigned int index3);

bool segment_segment_intersection(const Vec2d& x0, unsigned int index0, 
                                  const Vec2d& x1, unsigned int index1,
                                  const Vec2d& x2, unsigned int index2,
                                  const Vec2d& x3, unsigned int index3,
                                  double &s0, double& s2 );

void point_segment_distance( bool update, 
                             const Vec2d &x0, unsigned int index0, 
                             const Vec2d &x1, unsigned int index1, 
                             const Vec2d &x2, unsigned int index2, 
                             double &distance );

void point_segment_distance( bool update, 
                             const Vec2d &x0, unsigned int index0, 
                             const Vec2d &x1, unsigned int index1, 
                             const Vec2d &x2, unsigned int index2, 
                             double &distance, double &s, Vec2d &normal, double normal_multiplier );

// --------------------------------------------------------------------------------------------------
// 3D
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------
// Continuous collision detection
// --------------------------------------------------------------------------------------------------

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                              const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                              const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                              const Vec3d& x3, const Vec3d& xnew3, unsigned int index3);

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary1, bary2, bary3 to the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of point 0 minus triangle 1-2-3)
bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                              const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                              const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                              const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                              double& bary1, double& bary2, double& bary3,
                              Vec3d& normal,
                              double& t,
                              double& relative_normal_displacement,
                              bool verbose = false );

// x0-x1 and x2-x3 are the segments. Take care to specify x0,x1 and x2,x3 in sorted order of index!
bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                               const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                               const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                               const Vec3d& x3, const Vec3d& xnew3, unsigned int index3);

// x0-x1 and x2-x3 are the segments. Take care to specify x0,x1 and x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary0 and bary2 to parts of the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of edge 0-1 minus edge 2-3)
bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                               const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                               const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                               const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                               double& bary0, double& bary2,
                               Vec3d& normal,
                               double& t,
                               double& relative_normal_displacement,
                               bool verbose = false );


// --------------------------------------------------------------------------------------------------
// Static intersection detection
// --------------------------------------------------------------------------------------------------

// x0-x1 is the segment and and x2-x3-x4 is the triangle.
bool segment_triangle_intersection(const Vec3d& x0, unsigned int index0,
                                   const Vec3d& x1, unsigned int index1,
                                   const Vec3d& x2, unsigned int index2,
                                   const Vec3d& x3, unsigned int index3,
                                   const Vec3d& x4, unsigned int index4,
                                   bool degenerate_counts_as_intersection,
                                   bool verbose = false );

// x0 is the point and x1-x2-x3-x4 is the tetrahedron. Order is irrelevant.
bool point_tetrahedron_intersection(const Vec3d& x0, unsigned int index0,
                                    const Vec3d& x1, unsigned int index1,
                                    const Vec3d& x2, unsigned int index2,
                                    const Vec3d& x3, unsigned int index3,
                                    const Vec3d& x4, unsigned int index4);

// --------------------------------------------------------------------------------------------------
// Static distance
// --------------------------------------------------------------------------------------------------

void point_segment_distance( bool update, 
                             const Vec3d &x0, unsigned int index0,
                             const Vec3d &x1, unsigned int index1,
                             const Vec3d &x2, unsigned int index2,
                             double &distance);

void point_segment_distance( bool update, 
                             const Vec3d &x0, unsigned int index0,
                             const Vec3d &x1, unsigned int index1,
                             const Vec3d &x2, unsigned int index2,
                             double &distance, double &s, Vec3d &normal, double normal_multiplier );


void point_triangle_distance( const Vec3d& x0, unsigned int index0,
                             const Vec3d& x1, unsigned int index1,
                             const Vec3d& x2, unsigned int index2,
                             const Vec3d& x3, unsigned int index3,
                             double& distance );

void point_triangle_distance( const Vec3d& x0, unsigned int index0,
                              const Vec3d& x1, unsigned int index1,
                              const Vec3d& x2, unsigned int index2,
                              const Vec3d& x3, unsigned int index3,
                              double& distance, 
                              double& bary1, double& bary2, double& bary3, 
                              Vec3d& normal );

void segment_segment_distance( const Vec3d& x0, unsigned int index0,
                              const Vec3d& x1, unsigned int index1,
                              const Vec3d& x2, unsigned int index2,
                              const Vec3d& x3, unsigned int index3,
                              double& distance );

void segment_segment_distance( const Vec3d& x0, unsigned int index0,
                               const Vec3d& x1, unsigned int index1,
                               const Vec3d& x2, unsigned int index2,
                               const Vec3d& x3, unsigned int index3,
                               double& distance, 
                               double& bary0, double& bary2,
                               Vec3d& normal );

double tetrahedron_signed_volume(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3);

#endif


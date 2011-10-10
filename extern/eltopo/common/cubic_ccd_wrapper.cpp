
// ---------------------------------------------------------
//
//  cubic_ccd_wrapper.cpp
//  Tyson Brochu 2009
//
//  Cubic solver-based implementation of collision and intersection queries.
//
// ---------------------------------------------------------

#include <ccd_wrapper.h>

#ifdef USE_CUBIC_SOLVER_CCD

#include <collisionqueries.h>

static const double collision_epsilon = 1e-6;


// --------------------------------------------------------------------------------------------------
// 2D Continuous collision detection
// --------------------------------------------------------------------------------------------------

bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, unsigned int index0,
                             const Vec2d& x1, const Vec2d& xnew1, unsigned int index1,
                             const Vec2d& x2, const Vec2d& xnew2, unsigned int index2,
                             double& edge_alpha, Vec2d& normal, double& time, double& rel_disp)
{
   bool result = check_point_edge_collision( x0, x1, x2, xnew0, xnew1, xnew2, edge_alpha, normal, time, collision_epsilon );
   
   if ( result )
   {
      Vec2d dx0 = xnew0 - x0;
      Vec2d dx1 = xnew1 - x1;
      Vec2d dx2 = xnew2 - x2;
      rel_disp = dot( normal, dx0 - (edge_alpha)*dx1 - (1.0-edge_alpha)*dx2 );
   }
   
   return result;
   
}

bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, unsigned int index0,
                             const Vec2d& x1, const Vec2d& xnew1, unsigned int index1,
                             const Vec2d& x2, const Vec2d& xnew2, unsigned int index2 )
{
   return check_point_edge_collision( x0, x1, x2, xnew0, xnew1, xnew2, collision_epsilon );
}

// --------------------------------------------------------------------------------------------------
// 2D Static intersection detection
// --------------------------------------------------------------------------------------------------

bool segment_segment_intersection(const Vec2d& x0, unsigned int index0, 
                                  const Vec2d& x1, unsigned int index1,
                                  const Vec2d& x2, unsigned int index2,
                                  const Vec2d& x3, unsigned int index3)
{
   double s0, s2;
   return check_edge_edge_intersection( x0, x1, x2, x3, s0, s2, collision_epsilon );
}

bool segment_segment_intersection(const Vec2d& x0, unsigned int index0, 
                                  const Vec2d& x1, unsigned int index1,
                                  const Vec2d& x2, unsigned int index2,
                                  const Vec2d& x3, unsigned int index3,
                                  double &s0, double& s2 )
{
   return check_edge_edge_intersection( x0, x1, x2, x3, s0, s2, collision_epsilon );
}

// --------------------------------------------------------------------------------------------------
// 2D Static distance
// --------------------------------------------------------------------------------------------------

void point_segment_distance( bool update, 
                            const Vec2d &x0, unsigned int index0, 
                            const Vec2d &x1, unsigned int index1, 
                            const Vec2d &x2, unsigned int index2, 
                            double &distance )
{
   check_point_edge_proximity( update, x0, x1, x2, distance );
}

void point_segment_distance( bool update, 
                            const Vec2d &x0, unsigned int index0, 
                            const Vec2d &x1, unsigned int index1, 
                            const Vec2d &x2, unsigned int index2, 
                            double &distance, double &s, Vec2d &normal, double normal_multiplier )
{
   check_point_edge_proximity( update, x0, x1, x2, distance, s, normal, normal_multiplier );
}



// --------------------------------------------------------------------------------------------------
// 3D Continuous collision detection
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------


bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                              const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                              const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                              const Vec3d& x3, const Vec3d& xnew3, unsigned int index3 )
{   
   return check_point_triangle_collision( x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, collision_epsilon );
}

// --------------------------------------------------------------------------------------------------

bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                              const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                              const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                              const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                              double& bary1, double& bary2, double& bary3,
                              Vec3d& normal,
                              double& t,
                              double& relative_normal_displacement,
                              bool verbose )
{
   bool result = check_point_triangle_collision( x0, x1, x2, x3, 
                                                xnew0, xnew1, xnew2, xnew3,
                                                bary1, bary2, bary3,
                                                normal, t, collision_epsilon );
   
   Vec3d dx0 = xnew0 - x0;
   Vec3d dx1 = xnew1 - x1;
   Vec3d dx2 = xnew2 - x2;
   Vec3d dx3 = xnew3 - x3;   
   relative_normal_displacement = dot( normal, dx0 - bary1*dx1 - bary2*dx2 - bary3*dx3 );
   
   return result;   
}


// --------------------------------------------------------------------------------------------------


bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                               const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                               const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                               const Vec3d& x3, const Vec3d& xnew3, unsigned int index3)
{
   
   return check_edge_edge_collision( x0, x1, x2, x3,
                                    xnew0, xnew1, xnew2, xnew3,
                                    collision_epsilon );
   
}


// --------------------------------------------------------------------------------------------------



bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                               const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                               const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                               const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                               double& bary0, double& bary2,
                               Vec3d& normal,
                               double& t,
                               double& relative_normal_displacement,
                               bool verbose )
{
   bool result = check_edge_edge_collision( x0, x1, x2, x3,
                                           xnew0, xnew1, xnew2, xnew3,
                                           bary0, bary2,
                                           normal, t, 
                                           collision_epsilon );
   
   Vec3d dx0 = xnew0 - x0;
   Vec3d dx1 = xnew1 - x1;
   Vec3d dx2 = xnew2 - x2;
   Vec3d dx3 = xnew3 - x3;   
   
   if (relative_normal_displacement)
	   relative_normal_displacement = dot( normal, bary0*dx0 + (1.0-bary0)*dx1 - bary2*dx2 - (1.0-bary2)*dx3 );
   
   return result;   
}


// --------------------------------------------------------------------------------------------------
// 3D Static intersection detection
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------


// x0-x1 is the segment and and x2-x3-x4 is the triangle.
bool segment_triangle_intersection(const Vec3d& x0, unsigned int index0,
                                   const Vec3d& x1, unsigned int index1,
                                   const Vec3d& x2, unsigned int index2,
                                   const Vec3d& x3, unsigned int index3,
                                   const Vec3d& x4, unsigned int index4,
                                   bool degenerate_counts_as_intersection,
                                   bool verbose )
{
   return check_edge_triangle_intersection( x0, x1, x2, x3, x4, collision_epsilon, degenerate_counts_as_intersection, verbose );   
}


// --------------------------------------------------------------------------------------------------


// x0 is the point and x1-x2-x3-x4 is the tetrahedron. Order is irrelevant.
bool point_tetrahedron_intersection(const Vec3d& x0, unsigned int index0,
                                    const Vec3d& x1, unsigned int index1,
                                    const Vec3d& x2, unsigned int index2,
                                    const Vec3d& x3, unsigned int index3,
                                    const Vec3d& x4, unsigned int index4)
{
   return vertex_is_in_tetrahedron( x0, x1, x2, x3, x4, collision_epsilon );
}


// --------------------------------------------------------------------------------------------------
// 3D Static distance
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------


void point_segment_distance( bool update, 
                            const Vec3d &x0, unsigned int index0,
                            const Vec3d &x1, unsigned int index1,
                            const Vec3d &x2, unsigned int index2,
                            double &distance)
{
   check_point_edge_proximity( update, x0, x1, x2, distance);   
}

// --------------------------------------------------------------------------------------------------

void point_segment_distance( bool update, 
                            const Vec3d &x0, unsigned int index0,
                            const Vec3d &x1, unsigned int index1,
                            const Vec3d &x2, unsigned int index2,
                            double &distance, double &s, Vec3d &normal, double normal_multiplier )
{
   check_point_edge_proximity( update, x0, x1, x2, distance, s, normal, normal_multiplier );
}


// --------------------------------------------------------------------------------------------------


void point_triangle_distance( const Vec3d& x0, unsigned int index0,
                             const Vec3d& x1, unsigned int index1,
                             const Vec3d& x2, unsigned int index2,
                             const Vec3d& x3, unsigned int index3,
                             double& distance )
{
   check_point_triangle_proximity( x0, x1, x2, x3, distance );
}

// --------------------------------------------------------------------------------------------------


void point_triangle_distance( const Vec3d& x0, unsigned int index0,
                             const Vec3d& x1, unsigned int index1,
                             const Vec3d& x2, unsigned int index2,
                             const Vec3d& x3, unsigned int index3,
                             double& distance, 
                             double& bary1, double& bary2, double& bary3, 
                             Vec3d& normal )
{
   check_point_triangle_proximity( x0, x1, x2, x3, distance, bary1, bary2, bary3, normal );
}

// --------------------------------------------------------------------------------------------------

void segment_segment_distance( const Vec3d& x0, unsigned int index0,
                              const Vec3d& x1, unsigned int index1,
                              const Vec3d& x2, unsigned int index2,
                              const Vec3d& x3, unsigned int index3,
                              double& distance  )
{
   check_edge_edge_proximity( x0, x1, x2, x3, distance );
}

// --------------------------------------------------------------------------------------------------

void segment_segment_distance( const Vec3d& x0, unsigned int index0,
                              const Vec3d& x1, unsigned int index1,
                              const Vec3d& x2, unsigned int index2,
                              const Vec3d& x3, unsigned int index3,
                              double& distance, 
                              double& bary0, double& bary2,
                              Vec3d& normal )
{
   check_edge_edge_proximity( x0, x1, x2, x3, distance, bary0, bary2, normal );
}

// --------------------------------------------------------------------------------------------------

double tetrahedron_signed_volume(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3)
{
   return signed_volume( x0, x1, x2, x3 );
}

#endif




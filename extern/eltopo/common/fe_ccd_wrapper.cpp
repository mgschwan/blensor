
// ---------------------------------------------------------
//
//  fe_ccd_wrapper.cpp
//  Tyson Brochu 2009
//
//  Forward error analysis implementation of collision and intersection queries.
//
// ---------------------------------------------------------

#include <ccd_wrapper.h>

#ifdef USE_FORWARD_ERROR_CCD

#include <predicates.h>
#include <vec.h>

// --------------------------------------------------------------------------------------------------------------


bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                       const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                       const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                       const Vec3d& x3, const Vec3d& xnew3, unsigned int index3 )
{
   assert( index1 < index2 && index2 < index3 );
   return fe_point_triangle_collision( x0, xnew0, x1, xnew1, x2, xnew2, x3, xnew3 );
}


// --------------------------------------------------------------------------------------------------------------


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
   assert( index1 < index2 && index2 < index3 );
   return fe_point_triangle_collision( x0, xnew0, x1, xnew1, x2, xnew2, x3, xnew3, bary1, bary2, bary3, normal, t, relative_normal_displacement, verbose );
}


// --------------------------------------------------------------------------------------------------------------


bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                        const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                        const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                        const Vec3d& x3, const Vec3d& xnew3, unsigned int index3)
{
   assert( index0 < index1 && index2 < index3 );
   return fe_segment_segment_collision( x0, xnew0, x1, xnew1, x2, xnew2, x3, xnew3 );
}


// --------------------------------------------------------------------------------------------------------------



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
   assert( index0 < index1 && index2 < index3 );
   return fe_segment_segment_collision( x0, xnew0, x1, xnew1, x2, xnew2, x3, xnew3, bary0, bary2, normal, t, relative_normal_displacement, verbose );
}


#endif



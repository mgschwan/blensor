
// ---------------------------------------------------------
//
//  sos_ccd_wrapper.cpp
//  Tyson Brochu 2009
//
//  Tunicate-based implementation of collision and intersection queries.  Uses exact arithmetic with SoS.
//  (See Robert Bridson's "Tunicate" library.)
//
// ---------------------------------------------------------

#include <ccd_wrapper.h>

#ifdef USE_SOS_TUNICATE_CCD


#include <tunicate.h>
#include <vec.h>

const unsigned int nv = 1000000;

// return a unit-length vector orthogonal to u and v
static Vec3d get_normal(const Vec3d& u, const Vec3d& v)
{
   Vec3d c=cross(u,v);
   double m=mag(c);
   if(m) return c/m;
   // degenerate case: either u and v are parallel, or at least one is zero; pick an arbitrary orthogonal vector
   if(mag2(u)>=mag2(v)){
      if(std::fabs(u[0])>=std::fabs(u[1]) && std::fabs(u[0])>=std::fabs(u[2]))
         c=Vec3d(-u[1]-u[2], u[0], u[0]);
      else if(std::fabs(u[1])>=std::fabs(u[2]))
         c=Vec3d(u[1], -u[0]-u[2], u[1]);
      else
         c=Vec3d(u[2], u[2], -u[0]-u[1]);
   }else{
      if(std::fabs(v[0])>=std::fabs(v[1]) && std::fabs(v[0])>=std::fabs(v[2]))
         c=Vec3d(-v[1]-v[2], v[0], v[0]);
      else if(std::fabs(v[1])>=std::fabs(v[2]))
         c=Vec3d(v[1], -v[0]-v[2], v[1]);
      else
         c=Vec3d(v[2], v[2], -v[0]-v[1]);
   }
   m=mag(c);
   if(m) return c/m;
   // really degenerate case: u and v are both zero vectors; pick a random unit-length vector
   c[0]=random()%2 ? -0.577350269189626 : 0.577350269189626;
   c[1]=random()%2 ? -0.577350269189626 : 0.577350269189626;
   c[2]=random()%2 ? -0.577350269189626 : 0.577350269189626;
   return c;
}

// --------------------------------------------------------------------------------------------------------------


bool tunicate_point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                       const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                       const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                       const Vec3d& x3, const Vec3d& xnew3, unsigned int index3 )
{
   
   const int segment_tetrahedron_test = 2;

   double p0[4] = { x0[0], x0[1], x0[2], 0.0 };
   double pnew0[4] = { xnew0[0], xnew0[1], xnew0[2], 1.0 };
   double p1[4] = { x1[0], x1[1], x1[2], 0.0 };
   double pnew1[4] = { xnew1[0], xnew1[1], xnew1[2], 1.0 };
   double p2[4] = { x2[0], x2[1], x2[2], 0.0 };
   double pnew2[4] = { xnew2[0], xnew2[1], xnew2[2], 1.0 };
   double p3[4] = { x3[0], x3[1], x3[2], 0.0 };
   double pnew3[4] = { xnew3[0], xnew3[1], xnew3[2], 1.0 };
   
   double a0, a1, a2, a3, a4, a5;
   
   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1, p1,
                                    index2, p2,
                                    index3, p3,
                                    index3 + nv, pnew3,
                                    &a0, &a1, &a2, &a3, &a4, &a5 ) )
   {
      return true;
   }

   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1, p1,
                                    index2, p2,
                                    index2 + nv, pnew2,
                                    index3 + nv, pnew3,
                                    &a0, &a1, &a2, &a3, &a4, &a5 ) )
   {
      return true;
   }

   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1, p1,
                                    index1 + nv, pnew1,
                                    index2 + nv, pnew2,
                                    index3 + nv, pnew3,
                                    &a0, &a1, &a2, &a3, &a4, &a5 ) )
   {
      return true;
   }
   
   return false;
}


// --------------------------------------------------------------------------------------------------------------


bool tunicate_point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                       const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                       const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                       const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                                       double& bary1, double& bary2, double& bary3,
                                       Vec3d& normal,
                                       double& t,
                                       double& relative_normal_displacement,
                                       bool verbose )
{
 
   const int segment_tetrahedron_test = 2;
   
   double p0[4] = { x0[0], x0[1], x0[2], 0.0 };
   double pnew0[4] = { xnew0[0], xnew0[1], xnew0[2], 1.0 };
   double p1[4] = { x1[0], x1[1], x1[2], 0.0 };
   double pnew1[4] = { xnew1[0], xnew1[1], xnew1[2], 1.0 };
   double p2[4] = { x2[0], x2[1], x2[2], 0.0 };
   double pnew2[4] = { xnew2[0], xnew2[1], xnew2[2], 1.0 };
   double p3[4] = { x3[0], x3[1], x3[2], 0.0 };
   double pnew3[4] = { xnew3[0], xnew3[1], xnew3[2], 1.0 };
   
   bool collision=false;
   double bary[6];
   
   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1, p1,
                                    index2, p2,
                                    index3, p3,
                                    index3 + nv, pnew3,
                                    &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      collision=true;
      t=bary[1];
      normal=get_normal(x2-x1, x3-x1);
      relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew3-x3));
   }
   
   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                   index0, p0,
                                   index0 + nv, pnew0,
                                   index1, p1,
                                   index2, p2,
                                   index2 + nv, pnew2,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[1]<t)
      {
         collision=true;
         t=bary[1];
         normal=get_normal(x2-x1, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew2-x2));
      }
   }

   if ( sos_simplex_intersection4d( segment_tetrahedron_test,
                                   index0, p0,
                                   index0 + nv, pnew0,
                                   index1, p1,
                                   index1 + nv, pnew1,
                                   index2 + nv, pnew2,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[1]<t)
      {
         collision=true;
         t=bary[1];
         normal=get_normal(xnew2-xnew1, xnew3-xnew1);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew1-x1));
      }
   }
   
   return collision;
}


// --------------------------------------------------------------------------------------------------------------


bool tunicate_segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                        const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                        const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                        const Vec3d& x3, const Vec3d& xnew3, unsigned int index3)
{
   
   const int triangle_triangle_test = 3;
   
   double p0[4] = { x0[0], x0[1], x0[2], 0.0 };
   double pnew0[4] = { xnew0[0], xnew0[1], xnew0[2], 1.0 };
   double p1[4] = { x1[0], x1[1], x1[2], 0.0 };
   double pnew1[4] = { xnew1[0], xnew1[1], xnew1[2], 1.0 };
   double p2[4] = { x2[0], x2[1], x2[2], 0.0 };
   double pnew2[4] = { xnew2[0], xnew2[1], xnew2[2], 1.0 };
   double p3[4] = { x3[0], x3[1], x3[2], 0.0 };
   double pnew3[4] = { xnew3[0], xnew3[1], xnew3[2], 1.0 };
   
   double bary[6];
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                    index0, p0,
                                    index1, p1,
                                    index1, p1,
                                    index2, p2,
                                    index3, p3,
                                    index3 + nv, pnew3,
                                    &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1 + nv, pnew1,
                                    index2, p2,
                                    index3, p3,
                                    index3 + nv, pnew3,
                                    &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                    index0, p0,
                                    index1, p1,
                                    index1 + nv, pnew1,
                                    index2, p2,
                                    index2 + nv, pnew2,
                                    index3 + nv, pnew3,
                                    &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                    index0, p0,
                                    index0 + nv, pnew0,
                                    index1 + nv, pnew1,
                                    index2, p2,
                                    index2 + nv, pnew2,
                                    index3 + nv, pnew3,
                                    &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   return false;
}


// --------------------------------------------------------------------------------------------------------------



bool tunicate_segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                        const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                        const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                        const Vec3d& x3, const Vec3d& xnew3, unsigned int index3,
                                        double& bary0, double& bary2,
                                        Vec3d& normal,
                                        double& t,
                                        double& relative_normal_displacement,
                                        bool verbose )
{

   const int triangle_triangle_test = 3;
   
   double p0[4] = { x0[0], x0[1], x0[2], 0.0 };
   double pnew0[4] = { xnew0[0], xnew0[1], xnew0[2], 1.0 };
   double p1[4] = { x1[0], x1[1], x1[2], 0.0 };
   double pnew1[4] = { xnew1[0], xnew1[1], xnew1[2], 1.0 };
   double p2[4] = { x2[0], x2[1], x2[2], 0.0 };
   double pnew2[4] = { xnew2[0], xnew2[1], xnew2[2], 1.0 };
   double p3[4] = { x3[0], x3[1], x3[2], 0.0 };
   double pnew3[4] = { xnew3[0], xnew3[1], xnew3[2], 1.0 };
   
   bool collision=false;
   double bary[6];
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                   index0, p0,
                                   index1, p1,
                                   index1 + nv, pnew1,
                                   index2, p2,
                                   index3, p3,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      collision=true;
      bary0=0;
      bary2=0;
      t=bary[2];
      normal=get_normal(x1-x0, x3-x2);
      relative_normal_displacement=dot(normal, (xnew1-x1)-(xnew3-x3));
   }
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                   index0, p0,
                                   index0 + nv, pnew0,
                                   index1 + nv, pnew1,
                                   index2, p2,
                                   index3, p3,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[5]<t)
      {
         collision=true;
         bary0=0.5;//(bary[1]+1e-300)/(bary[1]+bary[2]+2e-300); // guard against zero/zero
         bary2=0;
         t=bary[5];
         normal=get_normal(xnew1-xnew0, x3-x2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew3-x3));
      }
   }
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                   index0, p0,
                                   index1, p1,
                                   index1 + nv, pnew1,
                                   index2, p2,
                                   index2 + nv, pnew2,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[2]<t){
         collision=true;
         bary0=0;
         bary2=0.5;//(bary[4]+1e-300)/(bary[4]+bary[5]+2e-300); // guard against zero/zero
         t=bary[2];
         normal=get_normal(x1-x0, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew1-x1)-(xnew2-x2));
      }
   }
   
   if ( sos_simplex_intersection4d( triangle_triangle_test,
                                   index0, p0,
                                   index0 + nv, pnew0,
                                   index1 + nv, pnew1,
                                   index2, p2,
                                   index2 + nv, pnew2,
                                   index3 + nv, pnew3,
                                   &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || 1-bary[0]<t){
         collision=true;
         bary0=0.5;//(bary[1]+1e-300)/(bary[1]+bary[2]+2e-300); // guard against zero/zero
         bary2=0.5;//(bary[4]+1e-300)/(bary[4]+bary[5]+2e-300); // guard against zero/zero
         t=1-bary[0];
         normal=get_normal(xnew1-xnew0, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew2-x2));
      }
   }

   return collision;
   
}



#endif



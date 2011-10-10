

// ---------------------------------------------------------
//
//  ccd_wrapper.cpp
//  Tyson Brochu 2009
//
//  Tunicate-based implementation of collision and intersection queries.  (See Robert Bridson's "Tunicate" library.)
//
// ---------------------------------------------------------

#include <ccd_wrapper.h>

#ifdef USE_TUNICATE_CCD

#include <collisionqueries.h>
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


bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                       const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                       const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                       const Vec3d& x3, const Vec3d& xnew3, unsigned int index3 )
{
   
   assert( index1 < index2 && index2 < index3 );
   
   const int segment_tetrahedron_test = 2;

   double p0[4] = { x0[0], x0[1], x0[2], 0.0 };
   double pnew0[4] = { xnew0[0], xnew0[1], xnew0[2], 1.0 };
   double p1[4] = { x1[0], x1[1], x1[2], 0.0 };
   double pnew1[4] = { xnew1[0], xnew1[1], xnew1[2], 1.0 };
   double p2[4] = { x2[0], x2[1], x2[2], 0.0 };
   double pnew2[4] = { xnew2[0], xnew2[1], xnew2[2], 1.0 };
   double p3[4] = { x3[0], x3[1], x3[2], 0.0 };
   double pnew3[4] = { xnew3[0], xnew3[1], xnew3[2], 1.0 };
   
   double bary[6];
   
   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, pnew1, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }
   
   return false;
}


// --------------------------------------------------------------------------------------------------------------
static void out4d( double* x )
{
   std::cout << x[0] << " " << x[1] << " " << x[2] << " " << x[3] << std::endl;
}

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
      
   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      collision=true;
      bary1=0;
      bary2=0;
      bary3=1;      
      t=bary[1];
      normal=get_normal(x2-x1, x3-x1);
      relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew3-x3));
      
      if ( verbose )
      {
         std::cout << "segment_tetrahedron_test positive with these inputs: " << std::endl;
         std::cout.precision(20);
         out4d(p0);
         out4d(pnew0);
         out4d(p1);
         out4d(p2);
         out4d(p3);
         out4d(pnew3);
      }        
      
   }
   
   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[1]<t)
      {
         collision=true;
         bary1=0;
         bary2=(bary[4]+1e-300)/(bary[4]+bary[5]+2e-300); // guard against zero/zero
         bary3=1-bary2;                  
         t=bary[1];
         normal=get_normal(x2-x1, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew2-x2));
         
         if ( verbose )
         {
            std::cout << "segment_tetrahedron_test positive with these inputs: " << std::endl;
            std::cout.precision(20);
            out4d(p0);
            out4d(pnew0);
            out4d(p1);
            out4d(p2);
            out4d(pnew2);
            out4d(pnew3);
         }        
         
      }
   }
   
   if ( simplex_intersection4d( segment_tetrahedron_test,
                                p0, pnew0, p1, pnew1, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[1]<t)
      {
         collision=true;
         bary1=(bary[3]+1e-300)/(bary[3]+bary[4]+bary[5]+3e-300); // guard against zero/zero
         bary2=(bary[4]+1e-300)/(bary[3]+bary[4]+bary[5]+3e-300); // guard against zero/zero
         bary3=1-bary1-bary2;         
         t=bary[1];
         normal=get_normal(xnew2-xnew1, xnew3-xnew1);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew1-x1));
         
         if ( verbose )
         {
            std::cout << "segment_tetrahedron_test positive with these inputs: " << std::endl;
            std::cout.precision(20);
            out4d(p0);
            out4d(pnew0);
            out4d(p1);
            out4d(pnew1);
            out4d(pnew2);
            out4d(pnew3);
         }        
         
      }
   }
   
   if ( collision )
   {
      Vec3d dx0 = xnew0 - x0;
      Vec3d dx1 = xnew1 - x1;
      Vec3d dx2 = xnew2 - x2;
      Vec3d dx3 = xnew3 - x3;         
      relative_normal_displacement = dot( normal, dx0 - bary1*dx1 - bary2*dx2 - bary3*dx3 );
   }
   
   return collision;
}


// --------------------------------------------------------------------------------------------------------------


bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, unsigned int index0,
                                        const Vec3d& x1, const Vec3d& xnew1, unsigned int index1,
                                        const Vec3d& x2, const Vec3d& xnew2, unsigned int index2,
                                        const Vec3d& x3, const Vec3d& xnew3, unsigned int index3)
{
   
   assert( index0 < index1 && index2 < index3 );
   
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
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, p1, p1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, pnew0, pnew1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, p1, pnew1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, pnew0, pnew1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      return true;
   }

   return false;
}





// --------------------------------------------------------------------------------------------------------------

static void output_4d( const double* v )
{
   int old_precision = std::cout.precision();
   std::cout.precision(20);
   std::cout << v[0] << " " << v[1] << " " << v[2] << " " << v[3] << std::endl;
   std::cout.precision(old_precision);
}


bool g_verbose = false;

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
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, p1, pnew1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      collision=true;
      bary0=0;
      bary2=0;
      t=bary[2];
      normal=get_normal(x1-x0, x3-x2);
      relative_normal_displacement=dot(normal, (xnew1-x1)-(xnew3-x3));
      
      if ( verbose )
      {
         std::cout << "triangle_triangle_test positive with these inputs: " << std::endl;
         output_4d(p0);
         output_4d(p1);
         output_4d(pnew1);
         output_4d(p2);
         output_4d(p3);
         output_4d(pnew3);
         
         std::cout << "barycentric coords: " << std::endl;
         for ( unsigned int i = 0; i < 6; ++i ) { std::cout << bary[i] << " " << std::endl; }
         
         g_verbose = true;
         simplex_intersection4d( triangle_triangle_test,
                                 p0, p1, pnew1, p2, p3, pnew3,
                                 &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] );
         g_verbose = false;
         
         assert(0);
      }        
            
   }
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, pnew0, pnew1, p2, p3, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[5]<t)
      {
         collision=true;
         bary0=(bary[1]+1e-300)/(bary[1]+bary[2]+2e-300); // guard against zero/zero
         bary2=0;
         t=bary[5];
         normal=get_normal(xnew1-xnew0, x3-x2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew3-x3));
         
         if ( verbose )
         {
            std::cout << "triangle_triangle_test positive with these inputs: " << std::endl;
            output_4d(p0);
            output_4d(pnew0);
            output_4d(pnew1);
            output_4d(p2);
            output_4d(p3);
            output_4d(pnew3);            
         }        
         
      }
   }
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, p1, pnew1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || bary[2]<t){
         collision=true;
         bary0=0;
         bary2=(bary[4]+1e-300)/(bary[4]+bary[5]+2e-300); // guard against zero/zero
         t=bary[2];
         normal=get_normal(x1-x0, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew1-x1)-(xnew2-x2));
         
         if ( verbose )
         {
            std::cout << "triangle_triangle_test positive with these inputs: " << std::endl;
            output_4d(p0);
            output_4d(p1);
            output_4d(pnew1);
            output_4d(p2);
            output_4d(pnew2);
            output_4d(pnew3);
         }        
         
      }
   }
   
   if ( simplex_intersection4d( triangle_triangle_test,
                                p0, pnew0, pnew1, p2, pnew2, pnew3,
                                &bary[0], &bary[1], &bary[2], &bary[3], &bary[4], &bary[5] ) )
   {
      if(!collision || 1-bary[0]<t){
         collision=true;
         bary0=(bary[1]+1e-300)/(bary[1]+bary[2]+2e-300); // guard against zero/zero
         bary2=(bary[4]+1e-300)/(bary[4]+bary[5]+2e-300); // guard against zero/zero
         t=1-bary[0];
         normal=get_normal(xnew1-xnew0, xnew3-xnew2);
         relative_normal_displacement=dot(normal, (xnew0-x0)-(xnew2-x2));
         
         if ( verbose )
         {
            std::cout << "triangle_triangle_test positive with these inputs: " << std::endl;
            output_4d(p0);
            output_4d(pnew0);
            output_4d(pnew1);
            output_4d(p2);
            output_4d(pnew2);
            output_4d(pnew3);
         }        
                  
      }
   }

   if ( collision )
   {
      Vec3d dx0 = xnew0 - x0;
      Vec3d dx1 = xnew1 - x1;
      Vec3d dx2 = xnew2 - x2;
      Vec3d dx3 = xnew3 - x3;   
      relative_normal_displacement = dot( normal, bary0*dx0 + (1.0-bary0)*dx1 - bary2*dx2 - (1.0-bary2)*dx3 );
   }
   
   return collision;
   
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
   double bary[5];
   return simplex_intersection3d( 2, x0.v, x1.v, x2.v, x3.v, x4.v, &bary[0], &bary[1], &bary[2], &bary[3], &bary[4] );
}


// --------------------------------------------------------------------------------------------------


// x0 is the point and x1-x2-x3-x4 is the tetrahedron. Order is irrelevant.
bool point_tetrahedron_intersection(const Vec3d& x0, unsigned int index0,
                                    const Vec3d& x1, unsigned int index1,
                                    const Vec3d& x2, unsigned int index2,
                                    const Vec3d& x3, unsigned int index3,
                                    const Vec3d& x4, unsigned int index4)
{
   double bary[5];
   return simplex_intersection3d( 1, x0.v, x1.v, x2.v, x3.v, x4.v, &bary[0], &bary[1], &bary[2], &bary[3], &bary[4] );   
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



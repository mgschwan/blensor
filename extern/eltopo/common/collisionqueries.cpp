#include "collisionqueries.h"

// check if segment x0-x1 and segment x2-x3 are intersecting and return barycentric coordinates of intersection if so
bool check_edge_edge_intersection( const Vec2d &x0, const Vec2d &x1, const Vec2d &x2, const Vec2d &x3, double &s01, double &s23, double tolerance )
{
   double x10=x1[0]-x0[0], y10=x1[1]-x0[1];
   double x31=x3[0]-x1[0], y31=x3[1]-x1[1];
   double x32=x3[0]-x2[0], y32=x3[1]-x2[1];
   double det=x32*y10-x10*y32;
   s01=(x31*y32-x32*y31)/det;
   if(s01 < -tolerance || s01 > 1+tolerance) return false;
   s23=(x31*y10-x10*y31)/det;
   if(s23< -tolerance || s23 > 1+tolerance) return false;
   // clamp
   if(s01<0) s01=0; else if(s01>1) s01=1;
   if(s23<0) s23=0; else if(s23>1) s23=1;
   return true;
}


// append all possible roots in [0,1] for the quadratic A*t^2+B*t+C to possible_t
static void find_possible_quadratic_roots_in_01( double A, double B, double C, std::vector<double> &possible_t, double tol )
{
   if(A!=0){
      double discriminant=B*B-4*A*C;
      if(discriminant>0){
         double numer;
         if(B>0) numer=0.5*(-B-sqrt(discriminant));
         else    numer=0.5*(-B+sqrt(discriminant));
         double t0=numer/A, t1=C/numer;
         if(t0<t1){
            if(t0>=-tol && t0<1)
               possible_t.push_back(max(0.,t0));
            if(t1>=-tol && t1<1)
               possible_t.push_back(max(0.,t1));
         }else{
            if(t1>=-tol && t1<1)
               possible_t.push_back(max(0.,t1));
            if(t0>=-tol && t0<1)
               possible_t.push_back(max(0.,t0));
         }
      }else{
         double t=-B/(2*A); // the extremum of the quadratic
         if(t>=-tol && t<1)
            possible_t.push_back(max(0.,t));
      }
   }else if(B!=0){
      double t=-C/B;
      if(t>=-tol && t<1)
         possible_t.push_back(max(0.,t));
   }
}


bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                 const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new, 
                                 double collision_epsilon )
{
   Vec2d x10=x1old-x0old, x20=x2old-x0old;
   Vec2d d10=(x1new-x0new)-x10, d20=(x2new-x0new)-x20;
   // figure out possible collision times to check
   std::vector<double> possible_t;
   double A=cross(d10,d20), B=cross(d10,x20)+cross(x10,d20), C=cross(x10,x20);
   find_possible_quadratic_roots_in_01(A, B, C, possible_t, collision_epsilon );
   possible_t.push_back(1); // always check the end
   // check proximities at possible collision times
   double proximity_tol=collision_epsilon*std::sqrt(mag2(x0old)+mag2(x0new)+mag2(x1old)+mag2(x1new)+mag2(x2new)+mag2(x2old));
   for(unsigned int i=0; i<possible_t.size(); ++i)
   {
      double collision_time=possible_t[i];
      double u=1-collision_time;
      double distance;
      check_point_edge_proximity( false, u*x0old+collision_time*x0new, u*x1old+collision_time*x1new, u*x2old+collision_time*x2new, distance );
      if(distance<=proximity_tol) return true;
   }
   return false;
}

// check if point x0 collides with segment x1-x2 during the motion from
// old to new positions, return barycentric coordinates, normal, and time if so.
bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                 const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new,
                                 double &s12, Vec2d &normal, double &collision_time, double tol )
{
   Vec2d x10=x1old-x0old, x20=x2old-x0old;
   Vec2d d10=(x1new-x0new)-x10, d20=(x2new-x0new)-x20;
   // figure out possible collision times to check
   std::vector<double> possible_t;
   double A=cross(d10,d20), B=cross(d10,x20)+cross(x10,d20), C=cross(x10,x20);
   find_possible_quadratic_roots_in_01(A, B, C, possible_t, tol );
   possible_t.push_back(1); // always check the end
   // check proximities at possible collision times
   double proximity_tol=tol*std::sqrt(mag2(x0old)+mag2(x0new)+mag2(x1old)+mag2(x1new)+mag2(x2new)+mag2(x2old));
   for(unsigned int i=0; i<possible_t.size(); ++i)
   {
      collision_time=possible_t[i];
      double u=1-collision_time;
      double distance;
      check_point_edge_proximity( false, 
                                  u*x0old+collision_time*x0new, 
                                  u*x1old+collision_time*x1new, 
                                  u*x2old+collision_time*x2new,
                                  distance, s12, normal, 1.0 );
      
      if(distance<=proximity_tol) 
      {
         return true;
      }
   }
   return false;
}



double signed_volume(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3)
{
   // Equivalent to triple(x1-x0, x2-x0, x3-x0), six times the signed volume of the tetrahedron.
   // But, for robustness, we want the result (up to sign) to be independent of the ordering.
   // And want it as accurate as possible...
   // But all that stuff is hard, so let's just use the common assumption that all coordinates are >0,
   // and do something reasonably accurate in fp.

   // This formula does almost four times too much multiplication, but if the coordinates are non-negative
   // it suffers in a minimal way from cancellation error.
   return ( x0[0]*(x1[1]*x3[2]+x3[1]*x2[2]+x2[1]*x1[2])
           +x1[0]*(x2[1]*x3[2]+x3[1]*x0[2]+x0[1]*x2[2])
           +x2[0]*(x3[1]*x1[2]+x1[1]*x0[2]+x0[1]*x3[2])
           +x3[0]*(x1[1]*x2[2]+x2[1]*x0[2]+x0[1]*x1[2]) )

        - ( x0[0]*(x2[1]*x3[2]+x3[1]*x1[2]+x1[1]*x2[2])
           +x1[0]*(x3[1]*x2[2]+x2[1]*x0[2]+x0[1]*x3[2])
           +x2[0]*(x1[1]*x3[2]+x3[1]*x0[2]+x0[1]*x1[2])
           +x3[0]*(x2[1]*x1[2]+x1[1]*x0[2]+x0[1]*x2[2]) );
}

// ---------------------------------------------------------
///
/// Compute all proximities between an edge and a triangle and report the minimum
///
// ---------------------------------------------------------

double lowest_triangle_edge_proximity( const Vec3d &t0, const Vec3d &t1, const Vec3d &t2, 
                                       const Vec3d &e0, const Vec3d &e1 )
{
   double min_dist = 1e30;

   double curr_dist;
   check_point_triangle_proximity( e0, t0, t1, t2, curr_dist );
   min_dist = min( min_dist, curr_dist );
   check_point_triangle_proximity( e1, t0, t1, t2, curr_dist );
   min_dist = min( min_dist, curr_dist );

   check_edge_edge_proximity( e0, e1, t0, t1, curr_dist );
   min_dist = min( min_dist, curr_dist );
   check_edge_edge_proximity( e0, e1, t1, t2, curr_dist );
   min_dist = min( min_dist, curr_dist );
   check_edge_edge_proximity( e0, e1, t2, t0, curr_dist );
   min_dist = min( min_dist, curr_dist );

   return min_dist;
}


// ---------------------------------------------------------
///
/// Return true if triangle (x1,x2,x3) intersects segment (x4,x5)
///
// ---------------------------------------------------------

static bool triangle_intersects_segment(const Vec3d &x1, const Vec3d &x2, const Vec3d &x3, 
                                        const Vec3d &x4, const Vec3d &x5,
                                        double tolerance, bool verbose, bool& degenerate )
{
   static const double machine_epsilon = 1e-7;
   
   degenerate = false;
   
   double d=signed_volume(x1, x2, x3, x5);
   double e=-signed_volume(x1, x2, x3, x4);
   
   if ( verbose )
   {
      std::cout << "d: " << d << std::endl;
      std::cout << "e: " << e << std::endl;
   }
   
   if ( ( fabs(d) < machine_epsilon ) || ( fabs(e) < machine_epsilon ) )
   {
      degenerate = true;
   }
   
   if((d>0) ^ (e>0))
   {
      // if the segment is completely on one side of the triangle but closer than tolerance, report intersection
//      if ( lowest_triangle_edge_proximity( x1, x2, x3, x4, x5 ) < tolerance )
//      {
//         if ( verbose ) { std::cout << "edge is totally on one side but closer than tolerance" << std::endl; }
//         return true;
//      }
      return false;
   }
   
   // note: using the triangle edges in the first two spots guarantees the same floating point result (up to sign)
   // if we transpose the triangle vertices -- e.g. testing an adjacent triangle -- so this triangle-line test is
   // watertight.
   double a=signed_volume(x2, x3, x4, x5);
   double b=signed_volume(x3, x1, x4, x5);
   double c=signed_volume(x1, x2, x4, x5);
   
   if ( verbose )
   {
      std::cout << "a: " << a << std::endl;
      std::cout << "b: " << b << std::endl;
      std::cout << "c: " << c << std::endl;
   }
   
   double sum_abc=a+b+c;
   
   if ( verbose ) std::cout << "sum_abc: " << sum_abc << std::endl;
   
   if( fabs(sum_abc) < machine_epsilon )
   {
      degenerate = true;
      return false;            // degenerate situation
   }
   
   double sum_de=d+e;
   
   if ( verbose ) std::cout << "sum_de: " << sum_de << std::endl;
   
   if( fabs(sum_de) < machine_epsilon )
   {
      degenerate = true;
      return false; // degenerate situation
   }

   
   if ( ( fabs(a) < machine_epsilon ) || ( fabs(b) < machine_epsilon ) || (fabs(c) < machine_epsilon) )
   {
      degenerate = true;
   }

   
   if((a>0) ^ (b>0))
   {
      // if the segment is completely on one side of the triangle but closer than tolerance, report intersection
//      if ( lowest_triangle_edge_proximity( x1, x2, x3, x4, x5 ) < tolerance )
//      {
//         if ( verbose ) 
//         { 
//            std::cout << "edge is totally on one side but closer than tolerance" << std::endl; 
//            std::cout << "lowest_triangle_edge_proximity: " << lowest_triangle_edge_proximity( x1, x2, x3, x4, x5 ) << std::endl;
//            std::cout << "degenerate: " << degenerate << std::endl;
//         }
//         return true;
//      }

      return false;
   }
   
   if((a>0) ^ (c>0))
   {
      // if the segment is completely on one side of the triangle but closer than tolerance, report intersection
//      if ( lowest_triangle_edge_proximity( x1, x2, x3, x4, x5 ) < tolerance )
//      {
//         return true;
//      }
      
      return false;
   }
   
   double over_abc=1/sum_abc;
   a*=over_abc;
   b*=over_abc;
   c*=over_abc;
         
   double over_de=1/sum_de;
   d*=over_de;
   e*=over_de;
   
   if ( verbose ) 
   {
      std::cout << "normalized coords: " << a << " " << b << " " << c << " " << d << " " << e << std::endl;
   }
   
   return true;
}

// ---------------------------------------------------------
///
/// Return true if triangle (xtri0,xtri1,xtri2) intersects segment (xedge0, xedge1), within the specified tolerance.
/// If degenerate_counts_as_intersection is true, this function will return true in a degenerate situation.
///
// ---------------------------------------------------------

bool check_edge_triangle_intersection(const Vec3d &xedge0, const Vec3d &xedge1,
                                      const Vec3d &xtri0, const Vec3d &xtri1, const Vec3d &xtri2,
                                      double tolerance, bool degenerate_counts_as_intersection, bool verbose )
{
   bool is_degenerate;
   if ( triangle_intersects_segment( xtri0, xtri1, xtri2, xedge0, xedge1, tolerance, verbose, is_degenerate ) )
   {
      if ( is_degenerate )
      {
         if ( degenerate_counts_as_intersection )
         {
            return true;
         }
      }
      else
      {
         return true;
      }
   }
   
   return false;
}


void check_point_edge_proximity(bool update, const Vec3d &x0, const Vec3d &x1, const Vec3d &x2,
                                double &distance)
{
   Vec3d dx(x2-x1);
   double m2=mag2(dx);
   // find parameter value of closest point on segment
   double s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
   // and find the distance
   if(update){
      distance=min(distance, dist(x0,s*x1+(1-s)*x2));
   }else{
      distance=dist(x0,s*x1+(1-s)*x2);
   }
}

// normal is from 1-2 towards 0, unless normal_multiplier<0
void check_point_edge_proximity(bool update, const Vec3d &x0, const Vec3d &x1, const Vec3d &x2,
                                double &distance, double &s, Vec3d &normal, double normal_multiplier)
{
   Vec3d dx(x2-x1);
   double m2=mag2(dx);
   if(update){
      // find parameter value of closest point on segment
      double this_s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
      // and find the distance
      Vec3d this_normal=x0-(this_s*x1+(1-this_s)*x2);
      double this_distance=mag(this_normal);
      if(this_distance<distance){
         s=this_s;
         distance=this_distance;
         normal=(normal_multiplier/(this_distance+1e-30))*this_normal;
      }
   }else{
      // find parameter value of closest point on segment
      s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
      // and find the distance
      normal=x0-(s*x1+(1-s)*x2);
      distance=mag(normal);
      normal*=normal_multiplier/(distance+1e-30);
   }
}

void check_point_edge_proximity( bool update, const Vec2d &x0, const Vec2d &x1, const Vec2d &x2,
                                 double &distance)
{
   Vec2d dx(x2-x1);
   double m2=mag2(dx);
   // find parameter value of closest point on segment
   double s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
   // and find the distance
   if(update){
      distance=min(distance, dist(x0,s*x1+(1-s)*x2));
   }else{
      distance=dist(x0, s*x1+(1-s)*x2);
   }
}

// normal is from 1-2 towards 0, unless normal_multiplier<0
void check_point_edge_proximity(bool update, const Vec2d &x0, const Vec2d &x1, const Vec2d &x2,
                                double &distance, double &s, Vec2d &normal, double normal_multiplier)
{
   Vec2d dx(x2-x1);
   double m2=mag2(dx);
   if(update){
      // find parameter value of closest point on segment
      double this_s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
      // and find the distance
      Vec2d this_normal=x0-(this_s*x1+(1-this_s)*x2);
      double this_distance=mag(this_normal);
      if(this_distance<distance){
         s=this_s;
         distance=this_distance;
         normal=(normal_multiplier/(this_distance+1e-30))*this_normal;
      }
   }else{
      // find parameter value of closest point on segment
      s=clamp(dot(x2-x0, dx)/m2, 0., 1.);
      // and find the distance
      normal=x0-(s*x1+(1-s)*x2);
      distance=mag(normal);
      if ( distance < 1e-10 )
      {
         normal = normalized(perp(x2 - x1));
         return;
      }
      
      normal*=normal_multiplier/(distance+1e-30);
   }
}

void check_edge_edge_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3, double &distance)
{
   // let's do it the QR way for added robustness
   Vec3d x01=x0-x1;
   double r00=mag(x01)+1e-30;
   x01/=r00;
   Vec3d x32=x3-x2;
   double r01=dot(x32,x01);
   x32-=r01*x01;
   double r11=mag(x32)+1e-30;
   x32/=r11;
   Vec3d x31=x3-x1;
   double s2=dot(x32,x31)/r11;
   double s0=(dot(x01,x31)-r01*s2)/r00;
   // check if we're in range
   if(s0<0){
      if(s2<0){
         // check both x1 against 2-3 and 3 against 0-1
         check_point_edge_proximity(false, x1, x2, x3, distance);
         check_point_edge_proximity(true, x3, x0, x1, distance);
      }else if(s2>1){
         // check both x1 against 2-3 and 2 against 0-1
         check_point_edge_proximity(false, x1, x2, x3, distance);
         check_point_edge_proximity(true, x2, x0, x1, distance);
      }else{
         s0=0;
         // check x1 against 2-3
         check_point_edge_proximity(false, x1, x2, x3, distance);
      }
   }else if(s0>1){
      if(s2<0){
         // check both x0 against 2-3 and 3 against 0-1
         check_point_edge_proximity(false, x0, x2, x3, distance);
         check_point_edge_proximity(true, x3, x0, x1, distance);
      }else if(s2>1){
         // check both x0 against 2-3 and 2 against 0-1
         check_point_edge_proximity(false, x0, x2, x3, distance);
         check_point_edge_proximity(true, x2, x0, x1, distance);
      }else{
         s0=1;
         // check x0 against 2-3
         check_point_edge_proximity(false, x0, x2, x3, distance);
      }
   }else{
      if(s2<0){
         s2=0;
         // check x3 against 0-1
         check_point_edge_proximity(false, x3, x0, x1, distance);
      }else if(s2>1){
         s2=1;
         // check x2 against 0-1
         check_point_edge_proximity(false, x2, x0, x1, distance);
      }else{ // we already got the closest points!
         distance=dist(s2*x2+(1-s2)*x3, s0*x0+(1-s0)*x1);
      }
   }
}

// find distance between 0-1 and 2-3, with barycentric coordinates for closest points, and
// a normal that points from 0-1 towards 2-3 (unreliable if distance==0 or very small)
void check_edge_edge_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                               double &distance, double &s0, double &s2, Vec3d &normal)
{
   // let's do it the QR way for added robustness
   Vec3d x01=x0-x1;
   double r00=mag(x01)+1e-30;
   x01/=r00;
   Vec3d x32=x3-x2;
   double r01=dot(x32,x01);
   x32-=r01*x01;
   double r11=mag(x32)+1e-30;
   x32/=r11;
   Vec3d x31=x3-x1;
   s2=dot(x32,x31)/r11;
   s0=(dot(x01,x31)-r01*s2)/r00;
   // check if we're in range
   if(s0<0){
      if(s2<0){
         // check both x1 against 2-3 and 3 against 0-1
         check_point_edge_proximity(false, x1, x2, x3, distance, s2, normal, -1.);
         check_point_edge_proximity(true, x3, x0, x1, distance, s0, normal, 1.);
      }else if(s2>1){
         // check both x1 against 2-3 and 2 against 0-1
         check_point_edge_proximity(false, x1, x2, x3, distance, s2, normal, -1.);
         check_point_edge_proximity(true, x2, x0, x1, distance, s0, normal, 1.);
      }else{
         s0=0;
         // check x1 against 2-3
         check_point_edge_proximity(false, x1, x2, x3, distance, s2, normal, -1.);
      }
   }else if(s0>1){
      if(s2<0){
         // check both x0 against 2-3 and 3 against 0-1
         check_point_edge_proximity(false, x0, x2, x3, distance, s2, normal, -1.);
         check_point_edge_proximity(true, x3, x0, x1, distance, s0, normal, 1.);
      }else if(s2>1){
         // check both x0 against 2-3 and 2 against 0-1
         check_point_edge_proximity(false, x0, x2, x3, distance, s2, normal, -1.);
         check_point_edge_proximity(true, x2, x0, x1, distance, s0, normal, 1.);
      }else{
         s0=1;
         // check x0 against 2-3
         check_point_edge_proximity(false, x0, x2, x3, distance, s2, normal, -1.);
      }
   }else{
      if(s2<0){
         s2=0;
         // check x3 against 0-1
         check_point_edge_proximity(false, x3, x0, x1, distance, s0, normal, 1.);
      }else if(s2>1){
         s2=1;
         // check x2 against 0-1
         check_point_edge_proximity(false, x2, x0, x1, distance, s0, normal, 1.);
      }else{ // we already got the closest points!
         normal=(s2*x2+(1-s2)*x3)-(s0*x0+(1-s0)*x1);
         distance=mag(normal);
         if(distance>0) normal/=distance;
         else{
            normal=cross(x1-x0, x3-x2);
            normal/=mag(normal)+1e-300;
         }
      }
   }
}

void check_point_triangle_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    double &distance)
{
   // do it the QR way for added robustness
   Vec3d x13=x1-x3;
   double r00=mag(x13)+1e-30;
   x13/=r00;
   Vec3d x23=x2-x3;
   double r01=dot(x23,x13);
   x23-=r01*x13;
   double r11=mag(x23)+1e-30;
   x23/=r11;
   Vec3d x03=x0-x3;
   double s2=dot(x23,x03)/r11;
   double s1=(dot(x13,x03)-r01*s2)/r00;
   double s3=1-s1-s2;
   // check if we are in range
   if(s1>=0 && s2>=0 && s3>=0){
      distance=dist(x0, s1*x1+s2*x2+s3*x3);
   }else{
      if(s1>0){ // rules out edge 2-3
         check_point_edge_proximity(false, x0, x1, x2, distance);
         check_point_edge_proximity(true, x0, x1, x3, distance);
      }else if(s2>0){ // rules out edge 1-3
         check_point_edge_proximity(false, x0, x1, x2, distance);
         check_point_edge_proximity(true, x0, x2, x3, distance);
      }else{ // s3>0: rules out edge 1-2
         check_point_edge_proximity(false, x0, x2, x3, distance);
         check_point_edge_proximity(true, x0, x1, x3, distance);
      }
   }
}

// find distance between 0 and 1-2-3, with barycentric coordinates for closest point, and
// a normal that points from 1-2-3 towards 0 (unreliable if distance==0 or very small)
void check_point_triangle_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    double &distance, double &s1, double &s2, double &s3, Vec3d &normal)
{
   // do it the QR way for added robustness
   Vec3d x13=x1-x3;
   double r00=mag(x13)+1e-30;
   x13/=r00;
   Vec3d x23=x2-x3;
   double r01=dot(x23,x13);
   x23-=r01*x13;
   double r11=mag(x23)+1e-30;
   x23/=r11;
   Vec3d x03=x0-x3;
   s2=dot(x23,x03)/r11;
   s1=(dot(x13,x03)-r01*s2)/r00;
   s3=1-s1-s2;
   // check if we are in range
   if(s1>=0 && s2>=0 && s3>=0){
      normal=x0-(s1*x1+s2*x2+s3*x3);
      distance=mag(normal);
      if(distance>0) normal/=distance;
      else{
         normal=cross(x2-x1, x3-x1);
         normal/=mag(normal)+1e-300;
      }
   }else{
      double s, d;
      if(s1>0){ // rules out edge 2-3
         check_point_edge_proximity(false, x0, x1, x2, distance, s, normal, 1.);
         s1=s; s2=1-s; s3=0; d=distance;
         check_point_edge_proximity(true, x0, x1, x3, distance, s, normal, 1.);
         if(distance<d){
            s1=s; s2=0; s3=1-s;
         }
      }else if(s2>0){ // rules out edge 1-3
         check_point_edge_proximity(false, x0, x1, x2, distance, s, normal, 1.);
         s1=s; s2=1-s; s3=0; d=distance;
         check_point_edge_proximity(true, x0, x2, x3, distance, s, normal, 1.);
         if(distance<d){
            s1=0; s2=s; s3=1-s; d=distance;
         }
      }else{ // s3>0: rules out edge 1-2
         check_point_edge_proximity(false, x0, x2, x3, distance, s, normal, 1.);
         s1=0; s2=s; s3=1-s; d=distance;
         check_point_edge_proximity(true, x0, x1, x3, distance, s, normal, 1.);
         if(distance<d){
            s1=s; s2=0; s3=1-s;
         }
      }
   }
}

void find_coplanarity_times(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                            const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                            std::vector<double> &possible_times)
{
   const double tol=1e-8;
   possible_times.clear();
   // cubic coefficients, A*t^3+B*t^2+C*t+D (for t in [0,1])
   Vec3d x03=x0-x3, x13=x1-x3, x23=x2-x3;
   Vec3d v03=(xnew0-xnew3)-x03, v13=(xnew1-xnew3)-x13, v23=(xnew2-xnew3)-x23;
   double A=triple(v03,v13,v23),
          B=triple(x03,v13,v23)+triple(v03,x13,v23)+triple(v03,v13,x23),
          C=triple(x03,x13,v23)+triple(x03,v13,x23)+triple(v03,x13,x23),
          D=triple(x03,x13,x23);
   const double convergence_tol=tol*(std::fabs(A)+std::fabs(B)+std::fabs(C)+std::fabs(D));

   // find intervals to check, or just solve it if it reduces to a quadratic =============================
   std::vector<double> interval_times;
   double discriminant=B*B-3*A*C; // of derivative of cubic, 3*A*t^2+2*B*t+C, divided by 4 for convenience
   if(discriminant<=0){ // monotone cubic: only one root in [0,1] possible
      // so we just 
      interval_times.push_back(0);
      interval_times.push_back(1);
   }else{ // positive discriminant, B!=0
      if(A==0){ // the cubic is just a quadratic, B*t^2+C*t+D ========================================
         discriminant=C*C-4*B*D; // of the quadratic
         if(discriminant<=0){
            double t=-C/(2*B);
            if(t>=-tol && t<=1+tol){
               t=clamp(t, 0., 1.);
               if(std::fabs(signed_volume((1-t)*x0+t*xnew0, (1-t)*x1+t*xnew1, (1-t)*x2+t*xnew2, (1-t)*x3+t*xnew3))<convergence_tol)
                  possible_times.push_back(t);
            }
         }else{ // two separate real roots
            double t0, t1;
            if(C>0) t0=(-C-std::sqrt(discriminant))/(2*B);
            else    t0=(-C+std::sqrt(discriminant))/(2*B);
            t1=D/(B*t0);
            if(t1<t0) swap(t0,t1);
            if(t0>=-tol && t0<=1+tol) possible_times.push_back(clamp(t0, 0., 1.));
            if(t1>=-tol && t1<=1+tol) add_unique(possible_times, clamp(t1, 0., 1.));
         }
         return;
      }else{ // cubic is not monotone: divide up [0,1] accordingly =====================================
         double t0, t1;
         if(B>0) t0=(-B-std::sqrt(discriminant))/(3*A);
         else    t0=(-B+std::sqrt(discriminant))/(3*A);
         t1=C/(3*A*t0);
         if(t1<t0) swap(t0,t1);
         interval_times.push_back(0);
         if(t0>0 && t0<1)
            interval_times.push_back(t0);
         if(t1>0 && t1<1)
            interval_times.push_back(t1);
         interval_times.push_back(1);
      }
   }

   // look for roots in indicated intervals ==============================================================
   // evaluate coplanarity more accurately at each endpoint of the intervals
   std::vector<double> interval_values(interval_times.size());
   for(unsigned int i=0; i<interval_times.size(); ++i){
      double t=interval_times[i];
      interval_values[i]=signed_volume((1-t)*x0+t*xnew0, (1-t)*x1+t*xnew1, (1-t)*x2+t*xnew2, (1-t)*x3+t*xnew3);
   }
   // first look for interval endpoints that are close enough to zero, without a sign change
   for(unsigned int i=0; i<interval_times.size(); ++i){
      if(interval_values[i]==0){
         possible_times.push_back(interval_times[i]);
      }else if(std::fabs(interval_values[i])<convergence_tol){
         if((i==0 || (interval_values[i-1]>=0 && interval_values[i]>=0) || (interval_values[i-1]<=0 && interval_values[i]<=0))    
          &&(i==interval_times.size()-1 || (interval_values[i+1]>=0 && interval_values[i]>=0) || (interval_values[i+1]<=0 && interval_values[i]<=0))){
            possible_times.push_back(interval_times[i]);
         }
      }
   }
   // and then search in intervals with a sign change
   for(unsigned int i=1; i<interval_times.size(); ++i){
      double tlo=interval_times[i-1], thi=interval_times[i], tmid;
      double vlo=interval_values[i-1], vhi=interval_values[i], vmid;
      if((vlo<0 && vhi>0) || (vlo>0 && vhi<0)){
         // start off with secant approximation (in case the cubic is actually linear)
         double alpha=vhi/(vhi-vlo);
         tmid=alpha*tlo+(1-alpha)*thi;
         for(int iteration=0; iteration<75; ++iteration){
            vmid=signed_volume((1-tmid)*x0+tmid*xnew0, (1-tmid)*x1+tmid*xnew1,
                               (1-tmid)*x2+tmid*xnew2, (1-tmid)*x3+tmid*xnew3);
            if(std::fabs(vmid)<1e-2*convergence_tol) break;
            if((vlo<0 && vmid>0) || (vlo>0 && vmid<0)){ // if sign change between lo and mid
               thi=tmid;
               vhi=vmid;
            }else{ // otherwise sign change between hi and mid
               tlo=tmid;
               vlo=vmid;
            }
            if(iteration%2) alpha=0.5; // sometimes go with bisection to guarantee we make progress
            else alpha=vhi/(vhi-vlo); // other times go with secant to hopefully get there fast
            tmid=alpha*tlo+(1-alpha)*thi;
         }
         possible_times.push_back(tmid);
      }
   }
   sort(possible_times.begin(), possible_times.end());
}

bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                               const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                               double collision_epsilon)
{
   std::vector<double> possible_times;
   find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
   for(unsigned int a=0; a<possible_times.size(); ++a){
      double t=possible_times[a];
      Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
      double distance;
      check_edge_edge_proximity(xt0, xt1, xt2, xt3, distance);
      if(distance<collision_epsilon)
         return true;
   }
   return false;
}

bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                               const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                               double &s0, double &s2, Vec3d &normal, double &t, double collision_epsilon)
{
   std::vector<double> possible_times;
   find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
   for(unsigned int a=0; a<possible_times.size(); ++a){
      t=possible_times[a];
      Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
      double distance;
      check_edge_edge_proximity(xt0, xt1, xt2, xt3, distance, s0, s2, normal);
      if(distance<collision_epsilon){
         // now figure out a decent normal
         if(distance<1e-2*collision_epsilon){ // if we don't trust the normal...
            // first try the cross-product of edges at collision time
            normal=cross(xt1-xt0, xt3-xt2);
            double m=mag(normal);
            if(m>sqr(collision_epsilon)){
               normal/=m;
            }else{
               // if that didn't work, try cross-product of edges at the start
               normal=cross(x1-x0, x3-x2);
               m=mag(normal);
               if(m>sqr(collision_epsilon)){
                  normal/=m;
               }else{
                  // if that didn't work, try vector between points at the start
                  normal=(s2*x2+(1-s2)*x3)-(s0*x0+(1-s0)*x1);
                  m=mag(normal);
                  if(m>collision_epsilon){
                     normal/=m;
                  }else{
                     // if that didn't work, boy are we in trouble; just get any non-parallel vector
                     Vec3d dx=xt1-xt0;
                     if(dx[0]!=0 || dx[1]!=0){
                        normal=Vec3d(dx[1], -dx[0], 0);
                        normal/=mag(normal);
                     }else{
                        dx=xt3-xt2;
                        if(dx[0]!=0 || dx[1]!=0){
                           normal=Vec3d(dx[1], -dx[0], 0);
                           normal/=mag(normal);
                        }else{
                           normal=Vec3d(0, 1, 0); // the last resort
                        }
                     }
                  }
               }
            }
         }
         return true;
      }
   }
   return false;
}

bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                    double collision_epsilon)
{
   std::vector<double> possible_times;
   find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
   for(unsigned int a=0; a<possible_times.size(); ++a){
      double t=possible_times[a];
      Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
      double distance;
      check_point_triangle_proximity(xt0, xt1, xt2, xt3, distance);
      if(distance<collision_epsilon)
         return true;
   }
   return false;
}

bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                    double &s1, double &s2, double &s3, Vec3d &normal, double &t, double collision_epsilon)
{
   std::vector<double> possible_times;
   find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
   for(unsigned int a=0; a<possible_times.size(); ++a){
      t=possible_times[a];
      Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
      double distance;
      check_point_triangle_proximity(xt0, xt1, xt2, xt3, distance, s1, s2, s3, normal);
      if(distance<collision_epsilon){
         // now figure out a decent normal
         if(distance<1e-2*collision_epsilon){ // if we don't trust the normal...
            // first try the triangle normal at collision time
            normal=cross(xt2-xt1, xt3-xt1);
            double m=mag(normal);
            if(m>sqr(collision_epsilon)){
               normal/=m;
            }else{
               // if that didn't work, try triangle normal at start
               normal=cross(x2-x1, x3-x1);
               m=mag(normal);
               if(m>sqr(collision_epsilon)){
                  normal/=m;
               }else{
                  // if that didn't work, try vector between points at the start
                  normal=(s1*x1+s2*x2+s3*x3)-x0;
                  m=mag(normal);
                  if(m>collision_epsilon){
                     normal/=m;
                  }else{
                     // if that didn't work, boy are we in trouble; just get any non-parallel vector
                     Vec3d dx=xt2-xt1;
                     if(dx[0]!=0 || dx[1]!=0){
                        normal=Vec3d(dx[1], -dx[0], 0);
                        normal/=mag(normal);
                     }else{
                        dx=xt3-xt1;
                        if(dx[0]!=0 || dx[1]!=0){
                           normal=Vec3d(dx[1], -dx[0], 0);
                           normal/=mag(normal);
                        }else{
                           normal=Vec3d(0, 1, 0); // the last resort
                        }
                     }
                  }
               }
            }
         }
         return true;
      }
   }
   return false;
}

// ---------------------------------------------------------
///
/// Detect if point p lies within the tetrahedron defined by x1 x2 x3 x4.
/// Assumes tet is given with x123 forming an oriented triangle.
/// Returns true if vertex proximity to any of the tet's faces is less than epsilon.
///
// ---------------------------------------------------------

bool vertex_is_in_tetrahedron( const Vec3d &p, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3, const Vec3d &x4, double epsilon )
{
   double distance;  
   
   // triangle 1 - x1 x2 x3
   double a = signed_volume(p, x1, x2, x3);
   
   if (fabs(a) < epsilon)     // degenerate
   {        
      check_point_triangle_proximity(p, x1, x2, x3, distance);
      if ( distance < epsilon )
      {
         return true;
      }
   }
   
   // triangle 2 - x2 x4 x3
   double b = signed_volume(p, x2, x4, x3);
   
   if (fabs(b) < epsilon)         // degenerate
   {
      check_point_triangle_proximity(p, x2, x4, x3, distance);
      if ( distance < epsilon )
      {
         return true;
      }
   }
   
   if ((a > epsilon) ^ (b > epsilon))
   {
      return false;
   }
   
   // triangle 3 - x1 x4 x2
   double c = signed_volume(p, x1, x4, x2);
   if (fabs(c) < epsilon) 
   {
      check_point_triangle_proximity(p, x1, x4, x2, distance);
      if ( distance < epsilon )
      {
         return true;
      }
   }
   
   if ((a > epsilon) ^ (c > epsilon))
   {
      return false;
   }
   
   // triangle 4 - x1 x3 x4
   double d = signed_volume(p, x1, x3, x4);
   if (fabs(d) < epsilon) 
   { 
      check_point_triangle_proximity(p, x1, x3, x4, distance);
      if ( distance < epsilon )
      {
         return true;
      }
   }
   
   if ((a > epsilon) ^ (d > epsilon))
   {
      return false;
   }
   
   // if there was a degenerate case, but the point was not in any triangle, the point must be outside the tet
   if ( (fabs(a) < epsilon) || (fabs(b) < epsilon) || (fabs(c) < epsilon) || (fabs(d) < epsilon) ) 
   {
      return false;
   }
   
   return true;    // point is on the same side of all triangles
}


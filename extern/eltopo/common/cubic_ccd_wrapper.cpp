// ---------------------------------------------------------
//
//  cubic_ccd_wrapper.cpp
//  Tyson Brochu 2009
//
//  Cubic solver-based implementation of collision and intersection queries.
//
// ---------------------------------------------------------


#include <ccd_defs.h>
#include <ccd_wrapper.h>

bool simplex_verbose = false;


#ifdef USE_CUBIC_SOLVER_CCD

#include <collisionqueries.h>
#include <tunicate.h>

namespace
{
    
    const double cubic_solver_tol = 1e-8;
    const double degen_normal_epsilon = 1e-6;
    const double g_collision_epsilon = 1e-6;
    
    bool check_edge_edge_intersection(const Vec2d &x0, const Vec2d &x1, const Vec2d &x2, const Vec2d &x3, double &s01, double &s23, double tolerance );
    
    bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                    const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new,
                                    double collision_epsilon );
    
    bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                    const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new,
                                    double &s12, Vec2d &normal, double &collision_time, double collision_epsilon );
    
    bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                   const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                   double collision_epsilon);
    bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                   const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                   double &s0, double &s2, Vec3d &normal, double &t, double collision_epsilon);
    
    
    bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                        const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                        double collision_epsilon);
    bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                        const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                        double &s1, double &s2, double &s3, Vec3d &normal, double &t,
                                        double collision_epsilon);
    
    void find_coplanarity_times(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                std::vector<double> &possible_times);
    
    
    // ---------------------------------------------------------
    
    
    
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
    void find_possible_quadratic_roots_in_01( double A, double B, double C, std::vector<double> &possible_t, double tol )
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
        for(size_t i=0; i<possible_t.size(); ++i)
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
        for(size_t i=0; i<possible_t.size(); ++i)
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
    
    // ---------------------------------------------------------
    
    
    bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                   const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                   double collision_epsilon)
    {
        std::vector<double> possible_times;
        find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
        for(size_t a=0; a<possible_times.size(); ++a){
            double t=possible_times[a];
            Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
            double distance;
            check_edge_edge_proximity(xt0, xt1, xt2, xt3, distance);
            if(distance<collision_epsilon)
                return true;
        }
        return false;
    }
    
    
    // ---------------------------------------------------------
    
    void degenerate_get_edge_edge_collision_normal(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                                   double s0, double s2, Vec3d& normal )
    {  
        
        // if that didn't work, try cross-product of edges at the start
        normal=cross(x1-x0, x3-x2);
        double m=mag(normal);
        if(m>sqr(degen_normal_epsilon)){
            normal/=m;
        }else{
            // if that didn't work, try vector between points at the start
            normal=(s2*x2+(1-s2)*x3)-(s0*x0+(1-s0)*x1);
            m=mag(normal);
            if(m>degen_normal_epsilon){
                normal/=m;
            }else{
                // if that didn't work, boy are we in trouble; just get any non-parallel vector
                Vec3d dx=x1-x0;
                if(dx[0]!=0 || dx[1]!=0){
                    normal=Vec3d(dx[1], -dx[0], 0);
                    normal/=mag(normal);
                }else{
                    dx=x3-x2;
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
    
    
    // ---------------------------------------------------------
    
    bool check_edge_edge_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                   const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                   double &s0, double &s2, Vec3d &normal, double &t, double collision_epsilon)
    {
        std::vector<double> possible_times;
        find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
        for(size_t a=0; a<possible_times.size(); ++a){
            t=possible_times[a];
            Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
            double distance;
            check_edge_edge_proximity(xt0, xt1, xt2, xt3, distance, s0, s2, normal);
            if(distance<collision_epsilon){
                // now figure out a decent normal
                if(distance<1e-2*degen_normal_epsilon){ // if we don't trust the normal...
                    // first try the cross-product of edges at collision time
                    normal=cross(xt1-xt0, xt3-xt2);
                    double m=mag(normal);
                    if(m>sqr(degen_normal_epsilon)){
                        normal/=m;
                    }else
                    {
                        degenerate_get_edge_edge_collision_normal( x0, x1, x2, x3, s0, s2, normal );
                    }
                }
                return true;
            }
        }
        return false;
    }
    
    // ---------------------------------------------------------
    
    bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                        const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                        double collision_epsilon)
    {
        std::vector<double> possible_times;
        find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
        for(size_t a=0; a<possible_times.size(); ++a){
            double t=possible_times[a];
            Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
            double distance;
            check_point_triangle_proximity(xt0, xt1, xt2, xt3, distance);
            if(distance<collision_epsilon)
                return true;
        }
        return false;
    }
    
    // ---------------------------------------------------------
    
    
    void degenerate_get_point_triangle_collision_normal(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                                        
                                                        double &s1, double &s2, double &s3,
                                                        Vec3d& normal )
    {
        
        // try triangle normal at start
        normal=cross(x2-x1, x3-x1);
        double m=mag(normal);
        if(m>sqr(degen_normal_epsilon))
        {
            normal/=m;
        }
        else
        {
            // if that didn't work, try vector between points at the start
            
            normal=(s1*x1+s2*x2+s3*x3)-x0;
            m=mag(normal);
            if(m>degen_normal_epsilon)
            {
                normal/=m;
            }
            else
            {
                // if that didn't work, boy are we in trouble; just get any non-parallel vector
                Vec3d dx=x2-x1;
                if(dx[0]!=0 || dx[1]!=0)
                {
                    normal=Vec3d(dx[1], -dx[0], 0);
                    normal/=mag(normal);
                }
                else
                {
                    dx=x3-x1;
                    if(dx[0]!=0 || dx[1]!=0)
                    {
                        normal=Vec3d(dx[1], -dx[0], 0);
                        normal/=mag(normal);
                    }
                    else
                    {
                        normal=Vec3d(0, 1, 0); // the last resort
                    }
                }
            }
        }
    }
    
    
    // ---------------------------------------------------------
    
    bool check_point_triangle_collision(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                        const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                        double &s1, double &s2, double &s3, Vec3d &normal, double &t, double collision_epsilon)
    {
        std::vector<double> possible_times;
        find_coplanarity_times(x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, possible_times);
        
        for(size_t a=0; a<possible_times.size(); ++a){
            t=possible_times[a];
            Vec3d xt0=(1-t)*x0+t*xnew0, xt1=(1-t)*x1+t*xnew1, xt2=(1-t)*x2+t*xnew2, xt3=(1-t)*x3+t*xnew3;
            double distance;
            check_point_triangle_proximity(xt0, xt1, xt2, xt3, distance, s1, s2, s3, normal);
            if(distance<collision_epsilon){
                // now figure out a decent normal
                if(distance<1e-2*degen_normal_epsilon)
                { // if we don't trust the normal...
                    // first try the triangle normal at collision time
                    normal=cross(xt2-xt1, xt3-xt1);
                    double m=mag(normal);
                    if(m>sqr(degen_normal_epsilon)){
                        normal/=m;
                    }
                    else
                    {
                        degenerate_get_point_triangle_collision_normal( x0, x1, x2, x3, s1, s2, s3, normal );               
                    }
                }
                return true;
            }
        }
        return false;
    }
    
    
    void find_coplanarity_times(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                                std::vector<double> &possible_times)
    {
        
        if ( simplex_verbose )
        {
            std::cout << "finding coplanarity times... " << std::endl;
        }
        
        possible_times.clear();
        
        // cubic coefficients, A*t^3+B*t^2+C*t+D (for t in [0,1])
        Vec3d x03=x0-x3, x13=x1-x3, x23=x2-x3;
        Vec3d v03=(xnew0-xnew3)-x03, v13=(xnew1-xnew3)-x13, v23=(xnew2-xnew3)-x23;
        double A=triple(v03,v13,v23),
        B=triple(x03,v13,v23)+triple(v03,x13,v23)+triple(v03,v13,x23),
        C=triple(x03,x13,v23)+triple(x03,v13,x23)+triple(v03,x13,x23),
        D=triple(x03,x13,x23);
        const double convergence_tol=cubic_solver_tol*(std::fabs(A)+std::fabs(B)+std::fabs(C)+std::fabs(D));
        
        // find intervals to check, or just solve it if it reduces to a quadratic =============================
        std::vector<double> interval_times;
        double discriminant=B*B-3*A*C; // of derivative of cubic, 3*A*t^2+2*B*t+C, divided by 4 for convenience
        if(discriminant<=0){ // monotone cubic: only one root in [0,1] possible
            
            if ( simplex_verbose ) { std::cout << "monotone cubic" << std::endl; }
            
            // so we just 
            interval_times.push_back(0);
            interval_times.push_back(1);
        }else{ // positive discriminant, B!=0
            if(A==0){ // the cubic is just a quadratic, B*t^2+C*t+D ========================================
                discriminant=C*C-4*B*D; // of the quadratic
                if(discriminant<=0){
                    double t=-C/(2*B);
                    if(t>=-cubic_solver_tol && t<=1+cubic_solver_tol){
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
                    if(t0>=-cubic_solver_tol && t0<=1+cubic_solver_tol) possible_times.push_back(clamp(t0, 0., 1.));
                    if(t1>=-cubic_solver_tol && t1<=1+cubic_solver_tol) add_unique(possible_times, clamp(t1, 0., 1.));
                }
                
                if ( simplex_verbose )
                {
                    std::cout << "A == 0" << std::endl;
                    for ( size_t i = 0; i < possible_times.size(); ++i )
                    {
                        std::cout << "possible_time: " << possible_times[i] << std::endl;
                    }
                    std::cout << std::endl;
                }
                
                return;
            }else{ // cubic is not monotone: divide up [0,1] accordingly =====================================
                double t0, t1;
                if(B>0) t0=(-B-std::sqrt(discriminant))/(3*A);
                else    t0=(-B+std::sqrt(discriminant))/(3*A);
                t1=C/(3*A*t0);
                if(t1<t0) swap(t0,t1);
                
                if ( simplex_verbose ) { std::cout << "interval times: " << t0 << ", " << t1 << std::endl; }
                
                interval_times.push_back(0);
                if(t0>0 && t0<1)
                    interval_times.push_back(t0);
                if(t1>0 && t1<1)
                    interval_times.push_back(t1);
                interval_times.push_back(1);
            }
        }
        
        if ( simplex_verbose )
        {
            unsigned int n_samples = 20;
            double dt = 1.0 / (double)n_samples;
            double min_val = 1e30;
            for ( unsigned int i = 0; i < n_samples; ++i )
            {
                double sample_t = dt * i;
                double sample_val = signed_volume((1-sample_t)*x0+sample_t*xnew0, 
                                                  (1-sample_t)*x1+sample_t*xnew1, 
                                                  (1-sample_t)*x2+sample_t*xnew2, 
                                                  (1-sample_t)*x3+sample_t*xnew3);
                
                std::cout << "sample_val: " << sample_val << std::endl;
                
                min_val = min( min_val, fabs(sample_val) );
            }
            std::cout << "min_val: " << min_val << std::endl;
        }   
        
        
        // look for roots in indicated intervals ==============================================================
        // evaluate coplanarity more accurately at each endpoint of the intervals
        std::vector<double> interval_values(interval_times.size());
        for(size_t i=0; i<interval_times.size(); ++i){
            double t=interval_times[i];
            interval_values[i]=signed_volume((1-t)*x0+t*xnew0, (1-t)*x1+t*xnew1, (1-t)*x2+t*xnew2, (1-t)*x3+t*xnew3);   
            if ( simplex_verbose ) 
            {  
                std::cout << "interval time: " << t << ", value: " << interval_values[i] << std::endl; 
            }
        }
        
        if ( simplex_verbose ) 
        {  
            std::cout << "convergence_tol: " << convergence_tol << std::endl;
        }
        
        // first look for interval endpoints that are close enough to zero, without a sign change
        for(size_t i=0; i<interval_times.size(); ++i){
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
        for(size_t i=1; i<interval_times.size(); ++i){
            double tlo=interval_times[i-1], thi=interval_times[i], tmid;
            double vlo=interval_values[i-1], vhi=interval_values[i], vmid;
            if((vlo<0 && vhi>0) || (vlo>0 && vhi<0)){
                // start off with secant approximation (in case the cubic is actually linear)
                double alpha=vhi/(vhi-vlo);
                tmid=alpha*tlo+(1-alpha)*thi;
                int iteration=0;
                
                if ( simplex_verbose ) { std::cout << "cubic solver tol: " << 1e-2*convergence_tol << std::endl; }
                
                for(; iteration<50; ++iteration){
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
                if ( iteration >= 50 && simplex_verbose )
                {
                    std::cout << "cubic solve failed" << std::endl;
                }
                possible_times.push_back(tmid);
            }
        }
        sort(possible_times.begin(), possible_times.end());
        
        if ( simplex_verbose )
        {
            std::cout << "=================" << std::endl;
            
            for ( size_t i = 0; i < possible_times.size(); ++i )
            {
                std::cout << "possible_time: " << possible_times[i] << std::endl;
            }
            std::cout << std::endl;
        }
        
        
    }
    
    
    
} // namespace


// --------------------------------------------------------------------------------------------------
// 2D Continuous collision detection
// --------------------------------------------------------------------------------------------------

bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, size_t ,
                             const Vec2d& x1, const Vec2d& xnew1, size_t ,
                             const Vec2d& x2, const Vec2d& xnew2, size_t ,
                             double& edge_alpha, Vec2d& normal, double& time, double& rel_disp)
{
    bool result = check_point_edge_collision( x0, x1, x2, xnew0, xnew1, xnew2, edge_alpha, normal, time, g_collision_epsilon );
    
    if ( result )
    {
        Vec2d dx0 = xnew0 - x0;
        Vec2d dx1 = xnew1 - x1;
        Vec2d dx2 = xnew2 - x2;
        rel_disp = dot( normal, dx0 - (edge_alpha)*dx1 - (1.0-edge_alpha)*dx2 );
    }
    
    
    return result;
    
}

// --------------------------------------------------------------------------------------------------

bool point_segment_collision(const Vec2d& x0, const Vec2d& xnew0, size_t ,
                             const Vec2d& x1, const Vec2d& xnew1, size_t ,
                             const Vec2d& x2, const Vec2d& xnew2, size_t  )
{
    
    bool result = check_point_edge_collision( x0, x1, x2, xnew0, xnew1, xnew2, g_collision_epsilon );
    
    return result;
    
}

// --------------------------------------------------------------------------------------------------
// 2D Static intersection detection
// --------------------------------------------------------------------------------------------------

bool segment_segment_intersection(const Vec2d& x0, size_t , 
                                  const Vec2d& x1, size_t ,
                                  const Vec2d& x2, size_t ,
                                  const Vec2d& x3, size_t )
{
    double s0, s2;
    return check_edge_edge_intersection( x0, x1, x2, x3, s0, s2, g_collision_epsilon );
}

bool segment_segment_intersection(const Vec2d& x0, size_t , 
                                  const Vec2d& x1, size_t ,
                                  const Vec2d& x2, size_t ,
                                  const Vec2d& x3, size_t ,
                                  double &s0, double& s2 )
{
    return check_edge_edge_intersection( x0, x1, x2, x3, s0, s2, g_collision_epsilon );
}


// --------------------------------------------------------------------------------------------------
// 3D Continuous collision detection
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------


bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, size_t ,
                              const Vec3d& x1, const Vec3d& xnew1, size_t ,
                              const Vec3d& x2, const Vec3d& xnew2, size_t ,
                              const Vec3d& x3, const Vec3d& xnew3, size_t  )
{   
    bool cubic_result = check_point_triangle_collision( x0, x1, x2, x3, xnew0, xnew1, xnew2, xnew3, g_collision_epsilon );
    return cubic_result;
}

// --------------------------------------------------------------------------------------------------

bool point_triangle_collision(const Vec3d& x0, const Vec3d& xnew0, size_t ,
                              const Vec3d& x1, const Vec3d& xnew1, size_t ,
                              const Vec3d& x2, const Vec3d& xnew2, size_t ,
                              const Vec3d& x3, const Vec3d& xnew3, size_t ,
                              double& bary1, double& bary2, double& bary3,
                              Vec3d& normal,
                              double& relative_normal_displacement )
{
    
    double t;
    bool cubic_result = check_point_triangle_collision( x0, x1, x2, x3, 
                                                       xnew0, xnew1, xnew2, xnew3,
                                                       bary1, bary2, bary3,
                                                       normal, t, g_collision_epsilon );
    
    Vec3d dx0 = xnew0 - x0;
    Vec3d dx1 = xnew1 - x1;
    Vec3d dx2 = xnew2 - x2;
    Vec3d dx3 = xnew3 - x3;   
    relative_normal_displacement = dot( normal, dx0 - bary1*dx1 - bary2*dx2 - bary3*dx3 );
    
    return cubic_result;
}


// --------------------------------------------------------------------------------------------------


bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, size_t ,
                               const Vec3d& x1, const Vec3d& xnew1, size_t ,
                               const Vec3d& x2, const Vec3d& xnew2, size_t ,
                               const Vec3d& x3, const Vec3d& xnew3, size_t )
{
    
    bool cubic_result = check_edge_edge_collision( x0, x1, x2, x3,
                                                  xnew0, xnew1, xnew2, xnew3,
                                                  g_collision_epsilon );
    
    return cubic_result;
    
}


// --------------------------------------------------------------------------------------------------



bool segment_segment_collision(const Vec3d& x0, const Vec3d& xnew0, size_t ,
                               const Vec3d& x1, const Vec3d& xnew1, size_t ,
                               const Vec3d& x2, const Vec3d& xnew2, size_t ,
                               const Vec3d& x3, const Vec3d& xnew3, size_t ,
                               double& bary0, double& bary2,
                               Vec3d& normal,
                               double& relative_normal_displacement )
{
    
    double t;
    bool cubic_result = check_edge_edge_collision( x0, x1, x2, x3,
                                                  xnew0, xnew1, xnew2, xnew3,
                                                  bary0, bary2,
                                                  normal, t, 
                                                  g_collision_epsilon );
    
    Vec3d dx0 = xnew0 - x0;
    Vec3d dx1 = xnew1 - x1;
    Vec3d dx2 = xnew2 - x2;
    Vec3d dx3 = xnew3 - x3;   
    
    relative_normal_displacement = dot( normal, bary0*dx0 + (1.0-bary0)*dx1 - bary2*dx2 - (1.0-bary2)*dx3 );
    
    return cubic_result;
    
}


// --------------------------------------------------------------------------------------------------
// 3D Static intersection detection
// --------------------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------------------

// x0-x1 is the segment and and x2-x3-x4 is the triangle.
bool segment_triangle_intersection(const Vec3d& x0, size_t ,
                                   const Vec3d& x1, size_t ,
                                   const Vec3d& x2, size_t ,
                                   const Vec3d& x3, size_t ,
                                   const Vec3d& x4, size_t ,
                                   bool ,
                                   bool  )
{
    double bary[5];
    return simplex_intersection3d( 2, x0.v, x1.v, x2.v, x3.v, x4.v, &bary[0], &bary[1], &bary[2], &bary[3], &bary[4] );
}


// --------------------------------------------------------------------------------------------------

bool segment_triangle_intersection(const Vec3d& x0, size_t ,
                                   const Vec3d& x1, size_t ,
                                   const Vec3d& x2, size_t ,
                                   const Vec3d& x3, size_t ,
                                   const Vec3d& x4, size_t ,
                                   double& bary0, double& bary1, double& bary2, double& bary3, double& bary4,
                                   bool ,
                                   bool  )
{
    return simplex_intersection3d( 2, x0.v, x1.v, x2.v, x3.v, x4.v, &bary0, &bary1, &bary2, &bary3, &bary4 );
}


// --------------------------------------------------------------------------------------------------

// x0 is the point and x1-x2-x3-x4 is the tetrahedron. Order is irrelevant.
bool point_tetrahedron_intersection(const Vec3d& x0, size_t ,
                                    const Vec3d& x1, size_t ,
                                    const Vec3d& x2, size_t ,
                                    const Vec3d& x3, size_t ,
                                    const Vec3d& x4, size_t )
{
    double bary[5];
    return simplex_intersection3d( 1, x0.v, x1.v, x2.v, x3.v, x4.v, &bary[0], &bary[1], &bary[2], &bary[3], &bary[4] );
}

#endif




#if 0
#include "levelset.h"
#include "util.h"
#include "array2_utils.h"
#include "array3_utils.h"

float interpolate_phi(const Vec2f& point, const Array2f& grid, const Vec2f& origin, const float dx) {
   float inv_dx = 1/dx;
   Vec2f temp = (point-origin)*inv_dx;
   return interpolate_value(temp, grid);
}

float interpolate_phi(const Vec3f& point, const Array3f& grid, const Vec3f& origin, const float dx) {
   float inv_dx = 1/dx;
   Vec3f temp = (point-origin)*inv_dx;
   return interpolate_value(temp, grid);
}

float interpolate_normal(Vec2f& normal, const Vec2f& point, const Array2f& grid, const Vec2f& origin, const float dx) {
   float inv_dx = 1/dx;
   Vec2f temp = (point-origin)*inv_dx;
   float value = interpolate_gradient(normal, temp, grid);
   if(mag(normal) != 0)
      normalize(normal);
   return value;
}

float interpolate_normal(Vec3f& normal, const Vec3f& point, const Array3f& grid, const Vec3f& origin, const float dx) {
   float inv_dx = 1/dx;
   Vec3f temp = (point-origin)*inv_dx;
   float value = interpolate_gradient(normal, temp, grid);
   if(mag(normal) != 0)
      normalize(normal);
   return value;
}

void project_to_isosurface(Vec2f& point, const float target_value, const Array2f& grid, const Vec2f& origin, const float dx) {
   float tol = 0.01f*dx; //some fraction of a grid cell;
   int max_iter = 5;
   
   int iter = 0;
   Vec2f normal;
   float phi = interpolate_normal(normal, point, grid, origin, dx);
   while(fabs(phi - target_value) > tol && iter++ < max_iter) {
      point -= (phi - target_value) * normal;
      phi = interpolate_normal(normal, point, grid, origin, dx);
   }
}

void project_to_isosurface(Vec3f& point, const float target_value, const Array3f& grid, const Vec3f& origin, const float dx) {
   float tol = 0.01f*dx; //some fraction of a grid cell;
   int max_iter = 5;
   
   int iter = 0;
   Vec3f normal;
   float phi = interpolate_normal(normal, point, grid, origin, dx);
   while(fabs(phi - target_value) > tol && iter++ < max_iter) {
      point -= (phi - target_value) * normal;
      phi = interpolate_normal(normal, point, grid, origin, dx);
   }
}


//On a signed distance field, compute the fraction inside the (negative) isosurface
//along the 1D line segment joining phi_left and phi_right sample points.
float fraction_inside(float phi_left, float phi_right)
{
   //Note: should not generate divide by zero, because if
   //signs are different, and both values are != 0,
   //abs(left - right) is necessarily >= left, or right, alone, ie. not 0
   
   return 
      (phi_left >= 0 && phi_right >= 0)? //all empty
         0.0f : 
         (  (phi_left < 0 && phi_right < 0)? //all full
            1.0f:
            (
               (phi_left >= 0)?
               (1 - phi_left / (phi_left - phi_right)): //right inside 
               (phi_left / (phi_left - phi_right)) //left inside
            )
         );
}

//On a signed distance field, compute the fraction inside the (negative) isosurface
//along the 1D line segment joining phi_left and phi_right sample points.
//Except now there are two level sets, and we want the fraction that is the union
//of their interiors
float fraction_inside_either(float phi_left0, float phi_right0, float phi_left1, float phi_right1)
{
   if(phi_left0 <= 0) {
      if(phi_right0 <= 0) {
         //entirely inside solid0 [-/-][?]
         return 1;
      }
      else { //phi_right0 > 0
         if(phi_left1 <= 0) {
            if(phi_right1 <= 0) {
               //entirely inside solid1 -> [-/+][-/-]
               return 1;
            }
            else {//both left sides are inside, neither right side [-/+][-/+]
               return max( fraction_inside(phi_left0, phi_right0), 
                           fraction_inside(phi_left1, phi_right1) );
            }
         }
         else { //phi_left1 > 0 
            if(phi_right1 <= 0) { //opposite sides are interior [-/+][+/-]
               float frac0 = fraction_inside(phi_left0, phi_right0);
               float frac1 = fraction_inside(phi_left1, phi_right1);
               float total =  frac0+frac1;
               if(total <= 1)
                  return total;
               else
                  return 1;

            }
            else {//phi_right1 > 0
               //phi1 plays no role, both outside [-/+][+/+]
               return fraction_inside(phi_left0, phi_right0);
            }
         }
      }
   }
   else {
      if(phi_right0 <= 0) {
         if(phi_left1 <= 0) {
            if(phi_right1 <= 0) {
               //entirely inside solid1[+/-][-/-]
               return 1;
            }
            else {
               //coming in from opposing sides [+/-][-/+]
               float frac0 = fraction_inside(phi_left0, phi_right0);
               float frac1 = fraction_inside(phi_left1, phi_right1);
               float total =  frac0+frac1;
               if(total <= 1)
                  return total;
               else
                  return 1;
            }
         }
         else { //phi_left1 > 0 
            if(phi_right1 <= 0) {
               //coming from the same side, take the larger one [+/-][+/-]
               return max( fraction_inside(phi_left0, phi_right0), 
                           fraction_inside(phi_left1, phi_right1) );
            }
            else { //phi_right > 0
               //Only have to worry about phi_0 [+/-][+/+]
               return fraction_inside(phi_left0, phi_right0);
            }
             
         }
      }
      else {
         //Only have to worry about phi_1 [+/+][?]
         return fraction_inside(phi_left1, phi_right1);
      }
   }
}

void compute_volume_fractions(const Array2f& levelset, const Vec2f& ls_origin, float ls_dx, Array2f& volumes, const Vec2f& v_origin, float v_dx, int subdivisions) {
   
   float sub_dx = v_dx / (float)(subdivisions+1);
   
   for(int j = 0; j < volumes.nj; ++j) for(int i = 0; i < volumes.ni; ++i) {
      //centre of the volume cells
      Vec2f bottom_left = v_origin + Vec2f(i*v_dx, j*v_dx);
      int inside_samples = 0;
      for(int subj = 0; subj < subdivisions+1; ++subj) for(int subi = 0; subi < subdivisions+1; ++subi) {
         Vec2f point = bottom_left + Vec2f( (subi+0.5f)*sub_dx, (subj+0.5f)*sub_dx);
         float data = interpolate_phi(point, levelset, ls_origin, ls_dx);
         inside_samples += (data < 0)?1:0;
      }
      volumes(i,j) = (float)inside_samples / (float)sqr(subdivisions+1);
   }
}

void compute_volume_fractions(const Array3f& levelset, const Vec3f& ls_origin, float ls_dx, Array3f& volumes, const Vec3f& v_origin, float v_dx, int subdivisions) {
   
   float sub_dx = v_dx / (float)(subdivisions+1);
   
   for(int k = 0; k < volumes.nk; ++k) for(int j = 0; j < volumes.nj; ++j) for(int i = 0; i < volumes.ni; ++i) {
      //centre of the volume cells
      Vec3f bottom_left = v_origin + Vec3f((i-0.5f)*v_dx, (j-0.5f)*v_dx, (k-0.5f)*v_dx);
      int inside_samples = 0;
      
      //Speedup! Test the centre point, and if it's more than a grid cell away from the interface, we can assume 
      //the cell is either totally full or totally empty
      float estimate = interpolate_phi(bottom_left + 0.5f*v_dx*Vec3f(1,1,1), levelset, ls_origin, ls_dx);
      if(estimate > v_dx) {
         volumes(i,j,k) = 0;
         continue;
      }
      else if(estimate < -v_dx) {
         volumes(i,j,k) = 1;
         continue;
      }

      for(int subk = 0; subk < subdivisions+1; ++subk) for(int subj = 0; subj < subdivisions+1; ++subj) for(int subi = 0; subi < subdivisions+1; ++subi) {
         Vec3f point = bottom_left + Vec3f( (subi+0.5f)*sub_dx, (subj+0.5f)*sub_dx, (subk+0.5f)*sub_dx);
         float data = interpolate_phi(point, levelset, ls_origin, ls_dx);
         inside_samples += (data < 0)?1:0;
      }
      volumes(i,j,k) = (float)inside_samples / (float)cube(subdivisions+1);
   }
}

#endif

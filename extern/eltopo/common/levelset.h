#include "array2.h"
#include "array3.h"
#include "vec.h"

//Functions for dealing with grid-based level sets, data stored at nodes
float interpolate_phi(const Vec2f& point, const Array2f& grid, const Vec2f& origin, const float dx);
float interpolate_phi(const Vec3f& point, const Array3f& grid, const Vec3f& origin, const float dx);
float interpolate_normal(Vec2f& normal, const Vec2f& point, const Array2f& grid, const Vec2f& origin, const float dx);
float interpolate_normal(Vec3f& normal, const Vec3f& point, const Array3f& grid, const Vec3f& origin, const float dx);
void project_to_isosurface(Vec2f& point, const float target_value, const Array2f& grid, const Vec2f& origin, const float dx);
void project_to_isosurface(Vec3f& point, const float target_value, const Array3f& grid, const Vec3f& origin, const float dx);
void compute_volume_fractions(const Array2f& levelset, const Vec2f& ls_origin, float ls_dx, Array2f& volumes, const Vec2f& v_origin, float v_dx, int subdivisions);
void compute_volume_fractions(const Array3f& levelset, const Vec3f& ls_origin, float ls_dx, Array3f& volumes, const Vec3f& v_origin, float v_dx, int subdivisions);

//a couple handy functions for 1D distance fractions
float fraction_inside(float phi_left, float phi_right);
float fraction_inside_either(float phi_left0, float phi_right0, float phi_left1, float phi_right1);


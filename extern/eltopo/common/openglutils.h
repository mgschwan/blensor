#ifndef OPENGL_UTILS_H
#define OPENGL_UTILS_H

#include <vector>
#include "vec.h"
#include "array2.h"

void draw_circle2d(const Vec2f& centre, float rad, int segs);
void draw_grid2d(const Vec2f& origin, float dx, int nx, int ny);
void draw_box2d(const Vec2f& origin, float width, float height);
void draw_segmentset2d(const std::vector<Vec2f>& vertices, const std::vector<Vec2ui>& edges);
void draw_segmentset2d(const std::vector<Vec2f>& vertices, const std::vector<Vec2i>& edges);
void draw_points2d(const std::vector<Vec2f>& points);
void draw_polygon2d(const std::vector<Vec2f>& vertices);
void draw_polygon2d(const std::vector<Vec2f>& vertices, const std::vector<int>& order);
void draw_segment2d(const Vec2f& start, const Vec2f& end);
void draw_arrow2d(const Vec2f& start, const Vec2f& end, float arrow_head_len);
void draw_grid_data2d(Array2f& data, Vec2f origin, float dx, bool color = false);
void draw_trimesh2d(const std::vector<Vec2f>& vertices, const std::vector<Vec3ui>& tris);    
   
void draw_trimesh3d(const std::vector<Vec3f>& vertices, const std::vector<Vec3ui>& tris);
void draw_trimesh3d(const std::vector<Vec3f>& vertices, const std::vector<Vec3ui>& tris, const std::vector<Vec3f>& normals);
void draw_box3d(const Vec3f& dimensions);

#endif
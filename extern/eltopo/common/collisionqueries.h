#ifndef COLLISIONQUERIES_H
#define COLLISIONQUERIES_H

#include "vec.h"

// 2D ====================================================================================================

bool check_edge_edge_intersection(const Vec2d &x0, const Vec2d &x1, const Vec2d &x2, const Vec2d &x3, double &s01, double &s23, double tolerance );

bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                 const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new,
                                 double collision_epsilon );

bool check_point_edge_collision( const Vec2d &x0old, const Vec2d &x1old, const Vec2d &x2old,
                                 const Vec2d &x0new, const Vec2d &x1new, const Vec2d &x2new,
                                 double &s12, Vec2d &normal, double &collision_time, double collision_epsilon );

void check_point_edge_proximity(bool update, const Vec2d &x0, const Vec2d &x1, const Vec2d &x2,
                                double &distance);

void check_point_edge_proximity(bool update, const Vec2d &x0, const Vec2d &x1, const Vec2d &x2,
                                double &distance, double &s, Vec2d &normal, double normal_multiplier);

// 3D ====================================================================================================

double lowest_triangle_edge_proximity( const Vec3d &t0, const Vec3d &t1, const Vec3d &t2, 
                                       const Vec3d &e0, const Vec3d &e1 );

bool check_edge_triangle_intersection(const Vec3d &xedge0, const Vec3d &xedge1,
                                      const Vec3d &xtri0, const Vec3d &xtri1, const Vec3d &xtri2,
                                      double tolerance, bool degenerate_counts_as_intersection, bool verbose );

void check_point_edge_proximity(bool update, const Vec3d &x0, const Vec3d &x1, const Vec3d &x2,
                                double &distance);
void check_point_edge_proximity(bool update, const Vec3d &x0, const Vec3d &x1, const Vec3d &x2,
                                double &distance, double &s, Vec3d &normal, double normal_multiplier);

void check_edge_edge_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                               double &distance);
void check_edge_edge_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                               double &distance, double &s0, double &s2, Vec3d &normal);

void check_point_triangle_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    double &distance);
void check_point_triangle_proximity(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                                    double &distance, double &s1, double &s2, double &s3, Vec3d &normal);

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

double signed_volume(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3);

void find_coplanarity_times(const Vec3d &x0, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3,
                            const Vec3d &xnew0, const Vec3d &xnew1, const Vec3d &xnew2, const Vec3d &xnew3,
                            std::vector<double> &possible_times);

bool vertex_is_in_tetrahedron( const Vec3d &p, const Vec3d &x1, const Vec3d &x2, const Vec3d &x3, const Vec3d &x4, double epsilon );

#endif

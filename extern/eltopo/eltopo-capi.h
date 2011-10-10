#ifdef _cplusplus
extern "C" {

#endif
	
// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary1, bary2, bary3 to the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of point 0 minus triangle 1-2-3)	
int eltopo_point_tri_moving_v3_d(double x0[3], double xnew0[3], unsigned int index0,
									  double x1[3] , double xnew1[3], unsigned int index1,
									  double x2[3] , double xnew2[3], unsigned int index2,
									  double x3[3] , double xnew3[3], unsigned int index3,
									  double normal[3], double bary[3], double *t, 
									  double *relative_normal_displacement);

// x0-x1 and x2-x3 are the segments. Take care to specify x0,x1 and x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary0 and bary2 to parts of the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of edge 0-1 minus edge 2-3)
int eltopo_line_line_moving_isect_v3_d(double x0[3], double xnew0[3], unsigned int index0,
									  double x1[3] , double xnew1[3], unsigned int index1,
									  double x2[3] , double xnew2[3], unsigned int index2,
									  double x3[3] , double xnew3[3], unsigned int index3,
									  double normal[3], double bary[2], double *t,
									  double *relative_normal_displacement);

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary1, bary2, bary3 to the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of point 0 minus triangle 1-2-3)
int eltopo_point_tri_moving_v3v3_f(float v1[2][3], int i1, float v2[2][3], int i2,
                                   float v3[2][3],  int i3, float v4[2][3], int i4,
                                   float normal[3], float bary[3], float *t, float *relative_normal_displacement);

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary1, bary2, bary3 to the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of point 0 minus triangle 1-2-3)
int eltopo_point_tri_moving_v3v3_d(double v1[2][3], int i1, double v2[2][3], int i2,
                                   double v3[2][3],  int i3, double v4[2][3], int i4,
                                   double normal[3], double bary[3], double *t, double *relative_normal_displacement);



// x0-x1 and x2-x3 are the segments. Take care to specify x0,x1 and x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary0 and bary2 to parts of the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of edge 0-1 minus edge 2-3)
int eltopo_line_line_moving_isect_v3v3_d(double v1[2][3], int i1, double v2[2][3], int i2,
									  double v3[2][3],  int i3, double v4[2][3], int i4,
									  double normal[3], double bary[2], double *t, double *relnor);

// x0-x1 and x2-x3 are the segments. Take care to specify x0,x1 and x2,x3 in sorted order of index!
// If there is a collision, returns true and sets bary0 and bary2 to parts of the barycentric coordinates of
// the collision point, sets normal to the collision point, t to the collision time, and the relative
// normal displacement (in terms of edge 0-1 minus edge 2-3)
int eltopo_line_line_moving_isect_v3v3_f(float v1[2][3], int i1, float v2[2][3], int i2,
									  float v3[2][3],  int i3, float v4[2][3], int i4,
									  float normal[3], float bary[3], float *t, float *relnor);


void eltopo_start_memarena(void);
void eltopo_end_memarena(void);

#ifdef _cplusplus
}
#endif

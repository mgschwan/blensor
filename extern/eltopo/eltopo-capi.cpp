#include "common/vec.h"
#include "ccd_wrapper.h"
#include "cfloat"
#include "../../source/blender/blenlib/BLI_memarena.h"
// --------------------------------------------------------------------------------------------------
// Continuous collision detection
// --------------------------------------------------------------------------------------------------

MemArena *arena = NULL;

/*overload default new operator*/
void *operator new(size_t size) {
	if (arena)
		return BLI_memarena_alloc(arena, size);
	else
		return malloc(size);
}

void operator delete(void *ptr) {
	if (!arena)
		free(ptr);
}

extern "C" void eltopo_start_memarena(void)
{
	arena = BLI_memarena_new(1<<18, "eltopo arena");	
}

extern "C" void eltopo_end_memarena(void)
{
	if (arena) {
		BLI_memarena_free(arena);
		arena = NULL;
	}
}

static int non_penetration_filter_tri_v3(Vec3d v0, Vec3d vnew0, 
	Vec3d v1, Vec3d vnew1, Vec3d v2, Vec3d vnew2, Vec3d v3, Vec3d vnew3)
{
	Vec3d n0, n1, nv, vec;
	double dotA, dotB, dotC, dotD, dotE, dotF;
	
	/*non-penetration filter
	  see "Fast Continuous Collision Detection using Deforming Non-Penetration Filters"
	  by Min Zhejiang,Dinesh Manocha†, and Ruofeng Tong.
	*/
	n0 = cross(v1 - v2, v3 - v2);

	vec = v0 - v1;
	dotA = dot(vec, n0);
	vec = vnew0 - vnew1;
	dotF = dot(vec, n0);

	n1 = cross(vnew1 - vnew2, vnew3 - vnew2);

	vec = vnew0 - vnew1;
	dotB = dot(vec, n1);
	vec = v0 - v1;
	dotE = dot(vec, n1);
	
	nv = 0.5*(n0 + n1 + cross((vnew2 - v2) - (vnew1 - v1), (vnew3 - v3) - (vnew1 - v1)));

	vec = vnew0 - vnew1; 
	dotD = dot(vec, nv);
	vec = v0 - v1;
	dotC = dot(vec, nv);

	return ((dotA >= 0.0) == (dotB >= 0.0) && ((2.0*dotF + dotC)/3.0 >= 0.0) 
		 == (dotA >= 0.0) && (2.0*dotD + dotE)/3.0 >= 0.0 == (dotA >= 0.0));
}

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
extern "C" int eltopo_point_tri_moving_v3_d(double x0[3], double xnew0[3], unsigned int index0,
									  double x1[3] , double xnew1[3], unsigned int index1,
									  double x2[3] , double xnew2[3], unsigned int index2,
									  double x3[3] , double xnew3[3], unsigned int index3,
									  double no[3], double bary[3], double *t, double *relnor)
{
	Vec3d n0, n1, nv, vec, v0(x0), vnew0(xnew0), v1(x1), vnew1(xnew1), v2(x2), vnew2(xnew2), v3(x3), vnew3(xnew3);
	Vec3d vno;
	double bx, by, bz, dotA, dotB, dotC, dotD, dotE, dotF;
	int ret;
	
	if (non_penetration_filter_tri_v3(v0, vnew0, v1, vnew1, v2, vnew2, v3, vnew3)) {
		return 0;
	}
	
	ret = (int)point_triangle_collision(v0, vnew0, index0, v1, vnew1, index1, 
										 v2, vnew2, index2, v3, vnew3, index3,
										 bx, by, bz, vno, *t, *relnor, false);
	
	if (bary) {
		bary[0] = bx; bary[1] = by; bary[2] = bz;
	}
	
	if (no) {
		no[0] = vno[0]; no[1] = vno[1]; no[2] = vno[2];
	}
	
	return ret;
}

// x0 is the point, x1-x2-x3 is the triangle. Take care to specify x1,x2,x3 in sorted order of index!
extern "C" int eltopo_line_line_moving_isect_v3_d(double x0[3], double xnew0[3], unsigned int index0,
									  double x1[3], double xnew1[3], unsigned int index1,
									  double x2[3], double xnew2[3], unsigned int index2,
									  double x3[3], double xnew3[3], unsigned int index3, 
									  double no[3], double bary[2], double *t, double *relnor)
{
	Vec3d v0(x0), vnew0(xnew0), v1(x1), vnew1(xnew1), v2(x2), vnew2(xnew2), v3(x3), vnew3(xnew3);
	Vec3d vno;
	int ret;
	
	if (non_penetration_filter_tri_v3(v0, vnew0, v1, vnew1, v2, vnew2, v3, vnew3)) {
		return 0;
	}

	ret = (int)segment_segment_collision(v0, vnew0, index0, v1, vnew1, index1, v2, 
										  vnew2, index2, v3, vnew3, index3, bary[0],
										  bary[1], vno, *t, *relnor, 0);
	
	if (bary[0]<-DBL_EPSILON*10 || bary[0]>1.0+DBL_EPSILON*10)
		ret = 0;
	if (bary[1]<-DBL_EPSILON*10 || bary[1]>1.0+DBL_EPSILON*10)
		ret = 0;
	
	if (no) {
		no[0] = vno[0]; no[1] = vno[1]; no[2] = vno[2];
	}
	
	return ret;
}


extern "C" int eltopo_point_tri_moving_v3v3_d(double v1[2][3], int i1, double v2[2][3], int i2,
											  double v3[2][3],  int i3, double v4[2][3], int i4,
											  double normal[3], double bary[3], double *t, double *relnor)
{
	return eltopo_point_tri_moving_v3_d(v1[0], v1[1], i1, v2[0], v2[1], i2, v3[0], 
										v3[1], i3, v4[0], v4[1], i4, normal, bary, t, relnor);
}

extern "C" int eltopo_point_tri_moving_v3v3_f(float v1[2][3], int i1, float v2[2][3], int i2,
											  float v3[2][3],  int i3, float v4[2][3], int i4,
											  float normal[3], float bary[3], float *t, float *relnor)

{
	double d1[2][3], d2[2][3], d3[2][3], d4[2][3];
	double dno[3], dbary[3], dt, drelnor;
	int i, ret;
	
	for (i=0; i<3; i++) {
		d1[0][i] = v1[0][i]; d1[1][i] = v1[1][i];
		d2[0][i] = v2[0][i]; d2[1][i] = v2[1][i];
		d3[0][i] = v3[0][i]; d3[1][i] = v3[1][i];
		d4[0][i] = v4[0][i]; d4[1][i] = v4[1][i];
	}
	
	ret = eltopo_point_tri_moving_v3v3_d(d1, i1, d2, i2, d3, i3, d4, i4, 
										  dno, dbary, &dt, &drelnor);
	
	if (bary) {
		bary[0] = dbary[0]; bary[1] = dbary[1]; bary[2] = dbary[2];
	}
	if (normal) {
		normal[0] = dno[0]; normal[1] = dno[1]; normal[2] = dno[2];
	}
	if (t)
		*t = dt;
	if (relnor)
		*relnor = drelnor;
	
	return ret;	
}


extern "C" int eltopo_line_line_moving_isect_v3v3_d(double v1[2][3], int i1, double v2[2][3], int i2,
											  double v3[2][3],  int i3, double v4[2][3], int i4,
											  double normal[3], double bary[2], double *t, double *relnor)
{
	return eltopo_line_line_moving_isect_v3_d(v1[0], v1[1], i1, v2[0], v2[1], i2, v3[0], 
										v3[1], i3, v4[0], v4[1], i4, normal, bary, t, relnor);
}

extern "C" int eltopo_line_line_moving_isect_v3v3_f(float v1[2][3], int i1, float v2[2][3], int i2,
											  float v3[2][3],  int i3, float v4[2][3], int i4,
											  float normal[3], float bary[3], float *t, float *relnor)

{
	double d1[2][3], d2[2][3], d3[2][3], d4[2][3];
	double dno[3], dbary[2], dt, drelnor;
	int i, ret;
	
	for (i=0; i<3; i++) {
		d1[0][i] = v1[0][i]; d1[1][i] = v1[1][i];
		d2[0][i] = v2[0][i]; d2[1][i] = v2[1][i];
		d3[0][i] = v3[0][i]; d3[1][i] = v3[1][i];
		d4[0][i] = v4[0][i]; d4[1][i] = v4[1][i];
	}
	
	ret = eltopo_line_line_moving_isect_v3v3_d(d1, i1, d2, i2, d3, i3, d4, i4, 
										  dno, dbary, &dt, &drelnor);
	
	if (bary) {
		bary[0] = dbary[0]; bary[1] = dbary[1];
	}
	if (normal) {
		normal[0] = dno[0]; normal[1] = dno[1]; normal[2] = dno[2];
	}
	if (t)
		*t = dt;
	
	if (relnor)
		*relnor = drelnor;
	
	return ret;	
}

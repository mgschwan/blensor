#include "marching_triangles.h"

void MarchingTriangles::
contour_grid(void)
{
   edge.resize(0);
   x.resize(0);
   edge_cross.clear();
   for(int j=0; j+1<phi.nj; ++j) for(int i=0; i+1<phi.ni; ++i)
      contour_square(i,j);
}

void MarchingTriangles::
contour_square(int i, int j)
{
   contour_triangle(Vec2i(i,j), Vec2i(i+1,j), Vec2i(i+1,j+1), phi(i,j), phi(i+1,j), phi(i+1,j+1));
   contour_triangle(Vec2i(i,j), Vec2i(i+1,j+1), Vec2i(i,j+1), phi(i,j), phi(i+1,j+1), phi(i,j+1));
}

// assumes triangle is oriented counterclockwise
void MarchingTriangles::
contour_triangle(const Vec2i& x0, const Vec2i& x1, const Vec2i& x2, float p0, float p1, float p2)
{
   // guard against topological degeneracies
   if(p0==0) p0=1e-30f;
   if(p1==0) p1=1e-30f;
   if(p2==0) p2=1e-30f;

   if(p0<0){
      if(p1<0){
         if(p2<0) return; // no contour here
         else /* p2>0 */ edge.push_back(Vec2i(find_edge_cross(x1,x2,p1,p2), find_edge_cross(x0,x2,p0,p2)));
      }else{ // p1>0
         if(p2<0)        edge.push_back(Vec2i(find_edge_cross(x0,x1,p0,p1), find_edge_cross(x1,x2,p1,p2)));
         else /* p2>0 */ edge.push_back(Vec2i(find_edge_cross(x0,x1,p0,p1), find_edge_cross(x0,x2,p0,p2)));
      }
   }else{ // p0>0
      if(p1<0){
         if(p2<0)        edge.push_back(Vec2i(find_edge_cross(x0,x2,p0,p2), find_edge_cross(x0,x1,p0,p1)));
         else /* p2>0 */ edge.push_back(Vec2i(find_edge_cross(x1,x2,p1,p2), find_edge_cross(x0,x1,p0,p1)));
      }else{ // p1>0
         if(p2<0)        edge.push_back(Vec2i(find_edge_cross(x0,x2,p0,p2), find_edge_cross(x1,x2,p1,p2)));
         else /* p2>0 */ return; // no contour here
      }
   }
}

// return the vertex of the edge crossing (create it if necessary) between given grid points and function values
int MarchingTriangles::
find_edge_cross(const Vec2i& x0, const Vec2i& x1, float p0, float p1)
{
   unsigned int vertex_index;
   if(edge_cross.get_entry(Vec4i(x0.v[0], x0.v[1], x1.v[0], x1.v[1]), vertex_index)){
      return vertex_index;
   }else if(edge_cross.get_entry(Vec4i(x1.v[0], x1.v[1], x0.v[0], x0.v[1]), vertex_index)){
      return vertex_index;
   }else{
      float a=p1/(p1-p0), b=1-a;
      vertex_index=(int)x.size();
      x.push_back(Vec2f(origin[0]+dx*(a*x0[0]+b*x1[0]),
                        origin[1]+dx*(a*x0[1]+b*x1[1])));
      edge_cross.add(Vec4i(x0.v[0], x0.v[1], x1.v[0], x1.v[1]), vertex_index);
      return vertex_index;
   }
}


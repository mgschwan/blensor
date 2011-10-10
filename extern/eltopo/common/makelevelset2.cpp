#include "makelevelset2.h"

// find distance x0 is from segment x1-x2
static double point_segment_distance(const Vec2d &x0, const Vec2d &x1, const Vec2d &x2)
{
   Vec2d dx(x2-x1);
   double m2=mag2(dx);
   // find parameter value of closest point on segment
   double s12=(double)( dot(x2-x0, dx)/m2 );
   if(s12<0){
      s12=0;
   }else if(s12>1){
      s12=1;
   }
   // and find the distance
   return mag(s12*x1+(1-s12)*x2 - x0);
}

static void check_neighbour(const std::vector<Vec2ui> &edge, const std::vector<Vec2d> &x,
                            Array2d &phi, Array2i &closest_edge,
                            const Vec2d &gx, int i0, int j0, int i1, int j1)
{
   if(closest_edge(i0,j0)==closest_edge(i1,j1))
      return;
   if(closest_edge(i1,j1)>=0){
      unsigned int p, q; assign(edge[closest_edge(i1,j1)], p, q);
      double d=point_segment_distance(gx, x[p], x[q]);
      if(d<phi(i0,j0)){
         phi(i0,j0)=d;
         closest_edge(i0,j0)=closest_edge(i1,j1);
      }
   }
}

void make_level_set2(const std::vector<Vec2ui> &edge, const std::vector<Vec2d> &x,
                     const Vec2d &origin, double dx, int nx, int ny,
                     Array2d &phi)
{
   phi.resize(nx, ny);
   phi.assign((nx+ny)*dx); // upper bound on distance
   Array2i closest_edge(nx, ny, -1);
   Array2i intersection_count(nx, ny, 0); // intersection_count(i,j) is # of edge intersections in (i-1,i]x{j}
   // we begin by initializing distances near the mesh, and figuring out intersection counts
   Vec2d ijmin, ijmax;
   for(unsigned int e=0; e<edge.size(); ++e){
      unsigned int p, q; assign(edge[e], p, q);
      minmax((x[p]-origin)/dx, (x[q]-origin)/dx, ijmin, ijmax);
      // do distances
      int i0=clamp(int(ijmin[0])-1, 0, nx-1), i1=clamp(int(ijmax[0])+2, 0, nx-1);
      int j0=clamp(int(ijmin[1])-1, 0, ny-1), j1=clamp(int(ijmax[1])+2, 0, ny-1);
      for(int j=j0; j<=j1; ++j) for(int i=i0; i<=i1; ++i){
         Vec2d gx(i*dx+origin[0], j*dx+origin[1]);
         double d=point_segment_distance(gx, x[p], x[q]);
         if(d<phi(i,j)){
            phi(i,j)=d;
            closest_edge(i,j)=e;
         }
      }
      // and do intersection counts
      if(x[p][1]!=x[q][1]){ // if it's not a horizontal edge
         double fi0, fj0, fi1, fj1;
         if(x[p][1]<x[q][1]){
            fi0=((double)x[p][0]-origin[0])/dx;
            fj0=((double)x[p][1]-origin[1])/dx;
            fi1=((double)x[q][0]-origin[0])/dx;
            fj1=((double)x[q][1]-origin[1])/dx;
         }else{
            fi0=((double)x[q][0]-origin[0])/dx;
            fj0=((double)x[q][1]-origin[1])/dx;
            fi1=((double)x[p][0]-origin[0])/dx;
            fj1=((double)x[p][1]-origin[1])/dx;
         }
         j0=clamp(int(std::floor(fj0)), 0, ny-1)+1;
         j1=clamp(int(std::floor(fj1)), 0, ny-1);
         for(int j=j0; j<=j1; ++j){
            double alpha=(j-fj0)/(fj1-fj0);
            double fi=(1-alpha)*fi0 + alpha*fi1; // where the edge intersects the j'th grid line
            int i_interval=int(std::ceil(fi)); // intersection is in (i_interval-1,i_interval]
            if(i_interval<0) i_interval=0; // we enlarge the first interval to include everything to the left
            if(i_interval<nx){
               ++intersection_count(i_interval,j);
            } // we ignore intersections that are beyond the right edge of the grid
         }
      }
   }
   // and now we fill in the rest of the distances with fast sweeping
   for(unsigned int pass=0; pass<2; ++pass){
      for(int j=1; j<ny; ++j) for(int i=1; i<nx; ++i){
         Vec2d gx(i*dx+origin[0], j*dx+origin[1]);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i-1, j-1);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i-1, j);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i, j-1);
      }
      for(int j=ny-2; j>=0; --j) for(int i=nx-2; i>=0; --i){
         Vec2d gx(i*dx+origin[0], j*dx+origin[1]);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i+1, j+1);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i+1, j);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i, j+1);
      }
      for(int j=ny-2; j>=0; --j) for(int i=1; i<nx; ++i){
         Vec2d gx(i*dx+origin[0], j*dx+origin[1]);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i-1, j+1);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i-1, j);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i, j+1);
      }
      for(int j=1; j<ny; ++j) for(int i=nx-2; i>=0; --i){
         Vec2d gx(i*dx+origin[0], j*dx+origin[1]);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i+1, j-1);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i+1, j);
         check_neighbour(edge, x, phi, closest_edge, gx, i, j, i, j-1);
      }
   }
   // then figure out signs (inside/outside) from intersection counts
   for(int j=0; j<ny; ++j){
      int total_count=0;
      for(int i=0; i<nx; ++i){
         total_count+=intersection_count(i,j);
         if(total_count%2==1){ // if parity of intersections so far is odd,
            phi(i,j)=-phi(i,j); // we are inside the mesh
         }
      }
   }
}


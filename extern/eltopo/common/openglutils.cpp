#include "openglutils.h"

#ifdef __APPLE__
#include <GLUT/glut.h> // why does Apple have to put glut.h here...
#else
#include <GL/glut.h> // ...when everyone else puts it here?
#endif

#include "vec.h"
#include <cfloat>

void draw_circle2d(const Vec2f& centre, float rad, int segs)
{
   glBegin(GL_POLYGON);
   for(int i=0;i<segs;i++){
      float cosine=rad*cos(i*2*M_PI/(float)(segs));
      float sine=rad* sin(i*2*M_PI/(float)(segs));
      glVertex2fv((Vec2f(cosine,sine) + centre).v);
   }
   glEnd();
}

void draw_grid2d(const Vec2f& origin, float dx, int nx, int ny) {
   float width = nx*dx;
   float height = ny*dx;
   
   glBegin(GL_LINES);
   for(int i = 0; i <= nx; i++) {
      Vec2f a(i*dx, 0);
      Vec2f b(i*dx, height);
      glVertex2fv((origin+a).v); 
      glVertex2fv((origin+b).v);
   }
   for(int j = 0; j <= ny; ++j) {
      Vec2f a(0,j*dx);
      Vec2f b(width,j*dx);
      glVertex2fv((origin + a).v); 
      glVertex2fv((origin + b).v);
   }
   glEnd();
}

void draw_box2d(const Vec2f& origin, float width, float height) {
   glBegin(GL_POLYGON);
   glVertex2fv(origin.v);
   glVertex2fv((origin + Vec2f(0, height)).v);
   glVertex2fv((origin + Vec2f(width, height)).v);
   glVertex2fv((origin + Vec2f(width, 0)).v);
   glEnd();
}

void draw_segmentset2d(const std::vector<Vec2f>& vertices, const std::vector<Vec2ui>& edges) {
   glBegin(GL_LINES);
   for(unsigned int i = 0; i < edges.size(); ++i) {
      glVertex2fv(vertices[edges[i][0]].v);      
      glVertex2fv(vertices[edges[i][1]].v);
   }
   glEnd();
}

void draw_segmentset2d(const std::vector<Vec2f>& vertices, const std::vector<Vec2i>& edges) {
   glBegin(GL_LINES);
   for(unsigned int i = 0; i < edges.size(); ++i) {
      glVertex2fv(vertices[edges[i][0]].v);      
      glVertex2fv(vertices[edges[i][1]].v);
   }
   glEnd();
}

void draw_points2d(const std::vector<Vec2f>& points) {
   glBegin(GL_POINTS);
   for(unsigned int i = 0; i < points.size(); ++i) {
      glVertex2fv(points[i].v);      
   }
   glEnd();
}

void draw_polygon2d(const std::vector<Vec2f>& vertices) {
   glBegin(GL_POLYGON);
   for(unsigned int i = 0; i < vertices.size(); ++i)
      glVertex2fv(vertices[i].v);      
   glEnd();
}

void draw_polygon2d(const std::vector<Vec2f>& vertices, const std::vector<int>& order) {
   glBegin(GL_POLYGON);
   for(unsigned int i = 0; i < order.size(); ++i)
      glVertex2fv(vertices[order[i]].v);      
   glEnd();

}
void draw_segment2d(const Vec2f& start, const Vec2f& end) {
   glBegin(GL_LINES);
   glVertex2fv(start.v);      
   glVertex2fv(end.v);      
   glEnd();
}

void draw_arrow2d(const Vec2f& start, const Vec2f& end, float arrow_head_len)
{
   Vec2f direction = end - start;

   Vec2f dir_norm = direction;
   
   //TODO Possibly automatically scale arrowhead length based on vector magnitude
   if(mag(dir_norm) < 1e-14)
      return;

   normalize(dir_norm);
   Vec2f perp(dir_norm[1],-dir_norm[0]);

   Vec2f tip_left = end + arrow_head_len/(float)sqrt(2.0)*(-dir_norm + perp);
   Vec2f tip_right = end + arrow_head_len/(float)sqrt(2.0)*(-dir_norm - perp);
   
   glBegin(GL_LINES);
   glVertex2fv(start.v);
   glVertex2fv(end.v);
   glVertex2fv(end.v);
   glVertex2fv(tip_left.v);
   glVertex2fv(end.v);
   glVertex2fv(tip_right.v);
   glEnd();
    
}

void draw_trimesh2d(const std::vector<Vec2f>& vertices, const std::vector<Vec3ui>& tris) {
   glBegin(GL_TRIANGLES);
   for(unsigned int i = 0; i < tris.size(); ++i) {
      glVertex2fv(vertices[tris[i][0]].v);
      glVertex2fv(vertices[tris[i][1]].v);
      glVertex2fv(vertices[tris[i][2]].v);
    }
   glEnd();
}
       
       
void hueToRGB(float hue, float sat, float val, float &r, float &g, float &b) {   
   //compute hue (adapted from an older Wikipedia article)
   int Hi = (int)(floor(hue / 60.0f)) % 6;
   float f = hue / 60 - Hi;
   float p = val * (1 - sat);
   float q = val * (1- f * sat);
   float t = val * (1 - (1 - f) * sat);
   
   switch(Hi) {
      case 0:
         r=val;
         g=t;
         b=p;
         break;
      case 1:
         r=q;
         g=val;
         b=p;
         break;
      case 2:
         r=p;
         g=val;
         b=t;
         break;
      case 3:
         r=p;
         g=q;
         b=val;
         break;
      case 4:
         r=t;
         g=p;
         b=val;
        break;
      case 5:
         r=val;
         g=p;
         b=q;
         break;
   }
}

void draw_grid_data2d(Array2f& data, Vec2f origin, float dx, bool color) {
   float max_val = FLT_MIN;
   float min_val = FLT_MAX;
   for(int j = 0; j < data.nj; ++j) for(int i = 0; i < data.ni; ++i) {
      max_val = max(data(i,j),max_val);
      min_val = min(data(i,j),min_val);
   }
   
   for(int j = 0; j < data.nj; ++j) {
      for(int i = 0; i < data.ni; ++i) {
         glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
         Vec2f bl = origin + Vec2f(i*dx,j*dx);
         float r,g,b;
         if(color) {
            hueToRGB(240*(data(i,j) - min_val)/(max_val-min_val), 1, 1, r,g,b);
         }
         else {
            float gray = (data(i,j) - min_val)/(max_val-min_val);
            r = g = b = gray;
         }
         //TODO Black body colormap, if I can find it.
         glColor3f(r,g,b);
         draw_box2d(bl, dx, dx);
      }
   }

}

void draw_trimesh3d(const std::vector<Vec3f>& vertices, const std::vector<Vec3ui>& tris) {
   glBegin(GL_TRIANGLES);
   for(unsigned int i = 0; i < tris.size(); ++i) {
      glVertex3fv(vertices[tris[i][0]].v);
      glVertex3fv(vertices[tris[i][1]].v);
      glVertex3fv(vertices[tris[i][2]].v);
   }
   glEnd();
}

void draw_trimesh3d(const std::vector<Vec3f>& vertices, const std::vector<Vec3ui>& tris, const std::vector<Vec3f> & normals) {
   glBegin(GL_TRIANGLES);
   for(unsigned int i = 0; i < tris.size(); ++i) {
      glNormal3fv(normals[tris[i][0]].v);
      glVertex3fv(vertices[tris[i][0]].v);
      glNormal3fv(normals[tris[i][1]].v);
      glVertex3fv(vertices[tris[i][1]].v);
      glNormal3fv(normals[tris[i][2]].v);
      glVertex3fv(vertices[tris[i][2]].v);
   }
   glEnd();
}

void draw_box3d(const Vec3f& dimensions) {
   
   //Draw an axis-aligned box with specified dimensions, 
   //where the midpoint of the box is at the origin

   float width = dimensions[0];
   float height = dimensions[1];
   float depth = dimensions[2];

   glBegin(GL_POLYGON);
   glNormal3f(-1,0,0);
   glVertex3f(-0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(-0.5*width, 0.5*height, 0.5*depth);
   glVertex3f(-0.5*width, 0.5*height, -0.5*depth);
   glVertex3f(-0.5*width, -0.5*height, -0.5*depth);
   glEnd();

   glBegin(GL_POLYGON);
   glNormal3f(1,0,0);
   glVertex3f(0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(0.5*width, 0.5*height, 0.5*depth);
   glVertex3f(0.5*width, 0.5*height, -0.5*depth);
   glVertex3f(0.5*width, -0.5*height, -0.5*depth);
   glEnd();

   glBegin(GL_POLYGON);
   glNormal3f(0,0,-1);
   glVertex3f(-0.5*width, -0.5*height, -0.5*depth);
   glVertex3f(0.5*width, -0.5*height, -0.5*depth);
   glVertex3f(0.5*width, 0.5*height, -0.5*depth);
   glVertex3f(-0.5*width, 0.5*height, -0.5*depth);
   glEnd();

   glBegin(GL_POLYGON);
   glNormal3f(0,0,1);
   glVertex3f(-0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(0.5*width, 0.5*height, 0.5*depth);
   glVertex3f(-0.5*width, 0.5*height, 0.5*depth);
   glEnd();

   glBegin(GL_POLYGON);
   glNormal3f(0,-1,0);
   glVertex3f(-0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(0.5*width, -0.5*height, 0.5*depth);
   glVertex3f(0.5*width, -0.5*height, -0.5*depth);
   glVertex3f(-0.5*width, -0.5*height, -0.5*depth);
   glEnd();

   glBegin(GL_POLYGON);
   glNormal3f(0,1,0);
   glVertex3f(-0.5*width, 0.5*height, 0.5*depth);
   glVertex3f(0.5*width, 0.5*height, 0.5*depth);
   glVertex3f(0.5*width, 0.5*height, -0.5*depth);
   glVertex3f(-0.5*width, 0.5*height, -0.5*depth);
   glEnd();
}

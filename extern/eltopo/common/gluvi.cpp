
#include <cmath>
#include <cstdarg>
#include <cstdlib>
#include <fstream>
#include <gluvi.h>
#include <limits>
#include <vec.h>

#ifdef __APPLE__
#include <OpenGL/OpenGL.h>
#else
#include <GL/gl.h>
#include <GL/glu.h>
#include <GL/glut.h>
#include <GL/glext.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

using namespace std;

namespace Gluvi{
    
    bool taking_screenshot = false;
    GLuint screenshot_fbo;
    
    
    Target3D::
    Target3D(float target_[3], float dist_, float heading_, float pitch_, float fovy_, float near_clip_factor_, float far_clip_factor_)
    : dist(dist_), heading(heading_), pitch(pitch_),
    default_dist(dist_), default_heading(heading_), default_pitch(pitch_),
    fovy(fovy_), 
    near_clip_factor(near_clip_factor_), far_clip_factor(far_clip_factor_),
    action_mode(INACTIVE),
    oldmousex(0), oldmousey(0)
    {
        if(target_){
            target[0]=target_[0];
            target[1]=target_[1];
            target[2]=target_[2];
        }else{
            target[0]=0;
            target[1]=0;
            target[2]=0;
        }
        default_target[0]=target[0];
        default_target[1]=target[1];
        default_target[2]=target[2];
    }
    
    void Target3D::
    click(int button, int state, int x, int y)
    {
        if(state==GLUT_UP)
            action_mode=INACTIVE;
        else if(button==GLUT_LEFT_BUTTON)
            action_mode=ROTATE;
        else if(button==GLUT_MIDDLE_BUTTON)
            action_mode=TRUCK;
        else if(button==GLUT_RIGHT_BUTTON)
            action_mode=DOLLY;
        oldmousex=x;
        oldmousey=y;
    }
    
    void Target3D::
    drag(int x, int y)
    {
        switch(action_mode){
            case INACTIVE:
                return; // nothing to do
            case ROTATE:
                heading+=0.007f*(oldmousex-x);
                if(heading<-M_PI) heading+=2.0f*(float)M_PI;
                else if(heading>M_PI) heading-=2.0f*(float)M_PI;
                pitch+=0.007f*(oldmousey-y);
                if(pitch<-0.5*M_PI) pitch=-0.5f*(float)M_PI;
                else if(pitch>0.5*M_PI) pitch=0.5f*(float)M_PI;
                break;
            case TRUCK:
                target[0]+=(0.002f*dist)*cos(heading)*(oldmousex-x);
                target[1]-=(0.002f*dist)*(oldmousey-y);
                target[2]-=(0.002f*dist)*sin(heading)*(oldmousex-x);
                break;
            case DOLLY:
                dist*=pow(1.01f, oldmousey-y + x-oldmousex);
                break;
        }
        oldmousex=x;
        oldmousey=y;
        glutPostRedisplay();
    }
    
    void Target3D::
    return_to_default(void)
    {
        target[0]=default_target[0];
        target[1]=default_target[1];
        target[2]=default_target[2];
        dist=default_dist;
        heading=default_heading;
        pitch=default_pitch;
    }
    
    void Target3D::
    transform_mouse(int x, int y, float ray_origin[3], float ray_direction[3])
    {
        float ch=cos(heading), sh=sin(heading);
        float cp=cos(pitch), sp=sin(pitch);
        
        ray_origin[0]=target[0]+dist*sh*cp;
        ray_origin[1]=target[1]-dist*sp;
        ray_origin[2]=target[2]+dist*ch*cp;
        
        float scale=0.5f*tan(fovy)/winheight;
        float camx=(x-0.5f*winwidth)*scale, camy=(0.5f*winheight-y)*scale, camz=-1.0f; // in camera coordinates, this is ray_direction (but not normalized)
        // now need to rotate into world space from camera space
        float px=camx, py=camy*cp-camz*sp, pz=camy*sp+camz*cp;
        ray_direction[0]=px*ch+pz*sh;
        ray_direction[1]=py;
        ray_direction[2]=-px*sh+pz*ch;
        
        //@@@ is this right to get us to the near clipping plane?
        ray_origin[0]+=near_clip_factor*dist*ray_direction[0];
        ray_origin[1]+=near_clip_factor*dist*ray_direction[1];
        ray_origin[2]+=near_clip_factor*dist*ray_direction[2];
        
        // normalize direction vector
        float mag=sqrt(ray_direction[0]*ray_direction[0]
                       + ray_direction[1]*ray_direction[1]
                       + ray_direction[2]*ray_direction[2]);
        ray_direction[0]/=mag;
        ray_direction[1]/=mag;
        ray_direction[2]/=mag;
    }
    
    void Target3D::
    get_viewing_direction(float direction[3])
    {
        float ch=cos(heading), sh=sin(heading);
        float cp=cos(pitch), sp=sin(pitch);
        direction[0]=-sh*cp;
        direction[1]=sp;
        direction[2]=-ch*cp;
    }
    
    void Target3D::get_up_vector(float up[3])
    {
        // Rotate the y-coordinate vector about the x-axis by pitch, then the y-axis by heading
        // up = R_y(h) * R_x(p) * <0,1,0>
        
        float ch=cos(heading), sh=sin(heading);
        float cp=cos(pitch), sp=sin(pitch);
        up[0] = sh*sp;
        up[1] = cp;
        up[2] = ch*sp;   
    }
    
    void Target3D::
    gl_transform(void)
    {
        glViewport(0, 0, (GLsizei)winwidth, (GLsizei)winheight);
        
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        //gluPerspective(fovy, winwidth/(float)winheight, near_clip_factor*dist, far_clip_factor*dist);
        
        gluPerspective(fovy, winwidth/(float)winheight, near_clip_factor, far_clip_factor);
        
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        //   GLfloat pos[3];
        //   pos[0]=target[0]-dist*sin(heading)*cos(pitch);
        //   pos[1]=target[1]-dist*sin(pitch);
        //   pos[2]=target[2]-dist*cos(heading)*cos(pitch);
        glTranslatef(0, 0, -dist); // translate target dist away in the z direction
        glRotatef(-180.0f/(float)M_PI*pitch, 1.0f, 0.0f, 0.0f); // rotate pitch in the yz plane
        glRotatef(-180.0f/(float)M_PI*heading, 0.0f, 1.0f, 0.0f); // rotate heading in the xz plane
        glTranslatef(-target[0], -target[1], -target[2]); // translate target to origin
    }
    
    void Target3D::
    export_rib(ostream &output)
    {
        output<<"Clipping "<<near_clip_factor*dist<<" "<<far_clip_factor*dist<<endl; // could be more generous here!
        output<<"Projection \"perspective\" \"fov\" "<<fovy<<endl;
        output<<"ReverseOrientation"<<endl;  // RenderMan has a different handedness from OpenGL's default
        output<<"Scale 1 1 -1"<<endl;        // so we need to correct for that here
        output<<"Translate 0 0 "<<-dist<<endl;
        output<<"Rotate "<<-180/M_PI*pitch<<" 1 0 0"<<endl;
        output<<"Rotate "<<-180/M_PI*heading<<" 0 1 0"<<endl;
        output<<"Translate "<<-target[0]<<" "<<-target[1]<<" "<<-target[2]<<endl;
    }
    
    //=================================================================================
    
    TargetOrtho3D::
    TargetOrtho3D(float target_[3], float dist_, float heading_, float pitch_, float height_factor_, float near_clip_factor_, float far_clip_factor_)
    : dist(dist_), heading(heading_), pitch(pitch_),
    default_dist(dist_), default_heading(heading_), default_pitch(pitch_),
    height_factor(height_factor_),
    near_clip_factor(near_clip_factor_), far_clip_factor(far_clip_factor_), action_mode(INACTIVE),   
    oldmousex(0), oldmousey(0)
    {
        if(target_){
            target[0]=target_[0];
            target[1]=target_[1];
            target[2]=target_[2];
        }else{
            target[0]=0;
            target[1]=0;
            target[2]=0;
        }
        default_target[0]=target[0];
        default_target[1]=target[1];
        default_target[2]=target[2];
        default_dist=dist;
        default_heading=heading;
        default_pitch=pitch;
    }
    
    void TargetOrtho3D::
    click(int button, int state, int x, int y)
    {
        if(state==GLUT_UP)
            action_mode=INACTIVE;
        else if(button==GLUT_LEFT_BUTTON)
            action_mode=ROTATE;
        else if(button==GLUT_MIDDLE_BUTTON)
            action_mode=TRUCK;
        else if(button==GLUT_RIGHT_BUTTON)
            action_mode=DOLLY;
        oldmousex=x;
        oldmousey=y;
    }
    
    void TargetOrtho3D::
    drag(int x, int y)
    {
        switch(action_mode){
            case INACTIVE:
                return; // nothing to do
            case ROTATE:
                heading+=0.007f*(oldmousex-x);
                if(heading<-M_PI) heading+=2.0f*(float)M_PI;
                else if(heading>M_PI) heading-=2.0f*(float)M_PI;
                pitch+=0.007f*(oldmousey-y);
                if(pitch<-0.5f*(float)M_PI) pitch=-0.5f*(float)M_PI;
                else if(pitch>0.5f*(float)M_PI) pitch=0.5f*(float)M_PI;
                break;
            case TRUCK:
                target[0]+=(0.002f*dist)*cos(heading)*(oldmousex-x);
                target[1]-=(0.002f*dist)*(oldmousey-y);
                target[2]-=(0.002f*dist)*sin(heading)*(oldmousex-x);
                break;
            case DOLLY:
                dist*=pow(1.01f, oldmousey-y + x-oldmousex);
                break;
        }
        oldmousex=x;
        oldmousey=y;
        glutPostRedisplay();
    }
    
    void TargetOrtho3D::
    return_to_default(void)
    {
        target[0]=default_target[0];
        target[1]=default_target[1];
        target[2]=default_target[2];
        dist=default_dist;
        heading=default_heading;
        pitch=default_pitch;
    }
    
    void TargetOrtho3D::
    transform_mouse(int, int, float* /*ray_origin[3]*/, float* /*ray_direction[3]*/ )
    {
        // @@@ unimplemented
    }
    
    void TargetOrtho3D::
    get_viewing_direction(float direction[3])
    {
        float ch=cos(heading), sh=sin(heading);
        float cp=cos(pitch), sp=sin(pitch);
        direction[0]=-sh*cp;
        direction[1]=sp;
        direction[2]=-ch*cp;
    }
    
    void TargetOrtho3D::
    gl_transform(void)
    {
        glViewport(0, 0, (GLsizei)winwidth, (GLsizei)winheight);
        
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        float halfheight=0.5f*height_factor*dist, halfwidth=halfheight*winwidth/(float)winheight;
        glOrtho(-halfwidth, halfwidth, -halfheight, halfheight, near_clip_factor*dist, far_clip_factor*dist);
        
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        glTranslatef(0, 0, -dist); // translate target dist away in the z direction
        glRotatef(-180.0f/(float)M_PI*pitch, 1.0f, 0.0f, 0.0f); // rotate pitch in the yz plane
        glRotatef(-180.0f/(float)M_PI*heading, 0.0f, 1.0f, 0.0f); // rotate heading in the xz plane
        glTranslatef(-target[0], -target[1], -target[2]); // translate target to origin
    }
    
    void TargetOrtho3D::
    export_rib(ostream &output)
    {
        output<<"Clipping "<<near_clip_factor*dist<<" "<<far_clip_factor*dist<<endl; // could be more generous here!
        output<<"Projection \"orthographic\""<<endl;
        //@@@ incomplete: need a scaling according to height_factor*dist somewhere in here
        output<<"ReverseOrientation"<<endl;  // RenderMan has a different handedness from OpenGL's default
        output<<"Scale 1 1 -1"<<endl;        // so we need to correct for that here
        output<<"Translate 0 0 "<<-dist<<endl;
        output<<"Rotate "<<-180/M_PI*pitch<<" 1 0 0"<<endl;
        output<<"Rotate "<<-180/M_PI*heading<<" 0 1 0"<<endl;
        output<<"Translate "<<-target[0]<<" "<<-target[1]<<" "<<-target[2]<<endl;
    }
    
    //=================================================================================
    
    PanZoom2D::
    PanZoom2D(float bottom_, float left_, float height_)
    : bottom(bottom_), left(left_), height(height_), 
    default_bottom(bottom_), default_left(left_), default_height(height_), action_mode(INACTIVE),
    oldmousex(0), oldmousey(0), moved_since_mouse_down(false),
    clickx(~0), clicky(~0)
    {}
    
    void PanZoom2D::
    click(int button, int state, int x, int y)
    {
        if(state==GLUT_UP){
            float r=height/winheight;
            switch(action_mode){
                case PAN:
                    if(!moved_since_mouse_down){
                        // make mouse click the centre of the window
                        left+=r*(x-0.5f*winwidth);
                        bottom+=r*(0.5f*winheight-y);
                        glutPostRedisplay();
                    }
                    break;
                case ZOOM_IN:
                    if(moved_since_mouse_down){
                        // zoom in to selection
                        float desired_width=fabs((x-clickx)*height/winheight);
                        float desired_height=fabs((y-clicky)*height/winheight);
                        if(desired_height==0) desired_height=height/winheight;
                        if(desired_width*winheight > desired_height*winwidth)
                            desired_height=winheight*desired_width/winwidth;
                        else
                            desired_width=winwidth*desired_height/winheight;
                        left+=0.5f*(x+clickx)*height/winheight-0.5f*desired_width;
                        bottom+=(winheight-0.5f*(y+clicky))*height/winheight-0.5f*desired_height;
                        height=desired_height;
                        
                    }else{
                        // zoom in by some constant factor on the mouse click
                        float factor=0.70710678118654752440084f;
                        left+=(1-factor)*height*(x/(float)winheight);
                        bottom+=(1-factor)*height*(1-y/(float)winheight);
                        height*=factor;
                    }
                    glutPostRedisplay();
                    break;
                case ZOOM_OUT:
                    // zoom out by some constant factor
                {
                    float factor=1.41421356237309504880168f;
                    left-=0.5f*(factor-1)*height;
                    bottom-=0.5f*(factor-1)*winwidth*height/winheight;
                    height*=factor;
                }
                    glutPostRedisplay();
                    break;
                default:
                    ;// nothing to do
            }
            action_mode=INACTIVE;
            
        }else if(button==GLUT_LEFT_BUTTON)
        {
            action_mode=PAN;
        }
        else if(button==GLUT_MIDDLE_BUTTON){
            clickx=x;
            clicky=y;
            action_mode=ZOOM_IN;
        }else if(button==GLUT_RIGHT_BUTTON)
            action_mode=ZOOM_OUT;
        moved_since_mouse_down=false;
        oldmousex=x;
        oldmousey=y;
    }
    
    void PanZoom2D::
    drag(int x, int y)
    {
        if(x!=oldmousex || y!=oldmousey){
            moved_since_mouse_down=true;
            if(action_mode==PAN){
                float r=height/winheight;
                left-=r*(x-oldmousex);
                bottom+=r*(y-oldmousey);
                glutPostRedisplay();
            }else if(action_mode==ZOOM_IN)
                glutPostRedisplay();
            
            glutPostRedisplay();
            oldmousex=x;
            oldmousey=y;
        }
    }
    
    void PanZoom2D::
    return_to_default(void)
    {
        bottom=default_bottom;
        left=default_left;
        height=default_height;
    }
    
    void PanZoom2D::
    transform_mouse(int x, int y, float coords[2])
    {
        float r=height/winheight;
        coords[0]=x*r+left;
        coords[1]=(winheight-y)*r+bottom;
    }
    
    void PanZoom2D::
    gl_transform(void)
    {
        glViewport(0, 0, (GLsizei)winwidth, (GLsizei)winheight);
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glOrtho(left, left+(height*winwidth)/winheight, bottom, bottom+height, 0, 1);
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
    }
    
    void PanZoom2D::
    export_rib(ostream &output)
    {
        // no projection matrix
        output<<"Clipping 1 2000"<<endl; // somewhat arbitrary - hopefully this is plenty of space
        output<<"ReverseOrientation"<<endl;  // RenderMan has a different handedness from OpenGL's default
        output<<"Scale 1 1 -1"<<endl;        // so we need to correct for that here
        // scale so that smaller dimension gets scaled to size 2
        float scalefactor;
        if(winwidth>winheight) scalefactor=2.0f/height;
        else scalefactor=2.0f/(winwidth*height/winheight);
        output<<"Scale "<<scalefactor<<" "<<scalefactor<<" 1"<<endl;
        // translate so centre of view gets mapped to (0,0,1000)
        output<<"Translate "<<-(left+0.5*winwidth*height/winheight)<<" "<<-(bottom+0.5*height)<< " 1000"<<endl;
    }
    
    void PanZoom2D::
    display_screen(void)
    {
        if(action_mode==ZOOM_IN && moved_since_mouse_down){
            glColor3f(1,1,1);
            glBegin(GL_LINE_STRIP);
            glVertex2i(clickx, winheight-clicky);
            glVertex2i(oldmousex, winheight-clicky);
            glVertex2i(oldmousex, winheight-oldmousey);
            glVertex2i(clickx, winheight-oldmousey);
            glVertex2i(clickx, winheight-clicky);
            glEnd();
        }
    }
    
    //=================================================================================
    
    StaticText::
    StaticText(const char *text_)
    : text(text_)
    {}
    
    void StaticText::
    display(int x, int y)
    {
        dispx=x;
        dispy=y;
        width=glutBitmapLength(GLUT_BITMAP_HELVETICA_12, (const unsigned char*)text)+1;
        height=15;
        glColor3f(0.3f, 0.3f, 0.3f);
        glRasterPos2i(x, y-height+2);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
        glColor3f(1, 1, 1);
        glRasterPos2i(x+1, y-height+3);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
    }
    
    //=================================================================================
    
    DynamicText::DynamicText( const std::string& text_ )
    : 
    text(text_)
    {
        color[0] = 0.0f;
        color[1] = 0.0f;
        color[2] = 0.0f;
    }
    
    void DynamicText::set_color( float r, float g, float b )
    {
        color[0] = r;
        color[1] = g;
        color[2] = b;
    }
    
    void DynamicText::display( int x, int y )
    {
        dispx=x;
        dispy=y;
        width=glutBitmapLength(GLUT_BITMAP_HELVETICA_12, (const unsigned char*)text.c_str())+1;
        height=15;
        
        //   glColor3f(0.3f, 0.3f, 0.3f);
        //   glRasterPos2i(x, y-height+2);
        //   for(int i=0; text[i]!=0; ++i)
        //      glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
        
        glColor3f( color[0], color[1], color[2] );
        
        glRasterPos2i(x+1, y-height+3);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);   
    }
    
    
    //=================================================================================
    
    Button::
    Button(const char *text_, int minwidth_)
    : status(UNINVOLVED), text(text_), minwidth(minwidth_)
    {}
    
    void Button::
    display(int x, int y)
    {
        dispx=x;
        dispy=y;
        int textwidth=glutBitmapLength(GLUT_BITMAP_HELVETICA_12, (const unsigned char*)text);
        if(textwidth<minwidth) width=minwidth+24;
        else width=textwidth+24;
        height=17;
        if(status==UNINVOLVED){
            glColor3f(0.7f, 0.7f, 0.7f);
            glBegin(GL_QUADS);
            glVertex2i(x+1, y-1);
            glVertex2i(x+width, y-1);
            glVertex2i(x+width, y-height+1);
            glVertex2i(x+1, y-height+1);
            glEnd();
            glColor3f(0.3f, 0.3f, 0.3f);
            glLineWidth(1);
            glBegin(GL_LINE_STRIP);
            glVertex2i(x, y-2);
            glVertex2i(x, y-height);
            glVertex2i(x+width-1, y-height);
            glEnd();
            glColor3f(0.3f, 0.3f, 0.3f);
        }else{
            if(status==SELECTED) glColor3f(0.8f, 0.8f, 0.8f);
            else                 glColor3f(1, 1, 1);
            glBegin(GL_QUADS);
            glVertex2i(x, y-1);
            glVertex2i(x+width, y-1);
            glVertex2i(x+width, y-height);
            glVertex2i(x, y-height);
            glEnd();
            glColor3f(0, 0, 0);
        }
        glRasterPos2i(x+(width-textwidth)/2, y-height+5);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
    }
    
    bool Button::
    click(int state, int x, int y)
    {
        if(state==GLUT_DOWN && x>dispx && x<=dispx+width && y<dispy-2 && y>=dispy-height){
            status=HIGHLIGHTED;
            glutPostRedisplay();
            return true;
        }else if(state==GLUT_UP && status!=UNINVOLVED){
            status=UNINVOLVED;
            glutPostRedisplay();
            if(x>=dispx && x<dispx+width && y<dispy-2 && y>=dispy-height)
                action();
            return true;
        }else
            return false;
    }
    
    void Button::
    drag(int x, int y)
    {
        // needs to control highlighting (SELECTED vs. HIGHLIGHTED)
        if(status==SELECTED && x>=dispx && x<dispx+width && y<dispy-2 && y>=dispy-height){
            status=HIGHLIGHTED;
            glutPostRedisplay();
        }else if(status==HIGHLIGHTED && !(x>=dispx && x<dispx+width && y<dispy-2 && y>=dispy-height)){
            status=SELECTED;
            glutPostRedisplay();
        }
    }
    
    //=================================================================================
    
    Slider::
    Slider(const char *text_, int length_, int position_, int justify_)
    : status(UNINVOLVED), text(text_), length(length_), justify(justify_), position(position_),
    scrollxmin(~0), scrollxmax(~0), scrollymin(~0), scrollymax(~0), clickx(~0) 
    {}
    
    void Slider::
    display(int x, int y)
    {
        dispx=x;
        dispy=y;
        width=glutBitmapLength(GLUT_BITMAP_HELVETICA_12, (const unsigned char*)text);
        if(width<justify) width=justify;
        width+=11+6+length+1;
        height=15;
        glColor3f(0.3f, 0.3f, 0.3f);
        glRasterPos2i(x, y-height+2);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
        glColor3f(1, 1, 1);
        glRasterPos2i(x+1, y-height+3);
        for(int i=0; text[i]!=0; ++i)
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, text[i]);
        scrollxmin=x+width-length-12;
        scrollxmax=x+width;
        scrollymin=y-height+1;
        scrollymax=y-2;
        glColor3f(0.3f, 0.3f, 0.3f);
        glLineWidth(1);
        glBegin(GL_LINE_STRIP);
        glVertex2i(scrollxmin, scrollymax-1);
        glVertex2i(scrollxmin, scrollymin);
        glVertex2i(scrollxmax-1, scrollymin);
        glVertex2i(scrollxmax-1, scrollymax-1);
        glEnd();
        glColor3f(0.7f, 0.7f, 0.7f);
        glBegin(GL_LINE_STRIP);
        glVertex2i(scrollxmin+1, scrollymax);
        glVertex2i(scrollxmin+1, scrollymin+1);
        glVertex2i(scrollxmax, scrollymin+1);
        glVertex2i(scrollxmax, scrollymax);
        glEnd();
        if(status==UNINVOLVED){
            glColor3f(0.3f, 0.3f, 0.3f);
            glBegin(GL_LINE_STRIP);
            glVertex2i(scrollxmin+position+2, scrollymax-2);
            glVertex2i(scrollxmin+position+2, scrollymin+2);
            glVertex2i(scrollxmin+position+10, scrollymin+2);
            glEnd();
            glColor3f(0.7f, 0.7f, 0.7f);
            glBegin(GL_QUADS);
            glVertex2i(scrollxmin+position+3, scrollymin+3);
            glVertex2i(scrollxmin+position+11, scrollymin+3);
            glVertex2i(scrollxmin+position+11, scrollymax);
            glVertex2i(scrollxmin+position+3, scrollymax);
            glEnd();
        }else{ // SELECTED
            glColor3f(1, 1, 1);
            glBegin(GL_QUADS);
            glVertex2i(scrollxmin+position+2, scrollymin+2);
            glVertex2i(scrollxmin+position+11, scrollymin+2);
            glVertex2i(scrollxmin+position+11, scrollymax);
            glVertex2i(scrollxmin+position+2, scrollymax);
            glEnd();
        }
    }
    
    bool Slider::
    click(int state, int x, int y)
    {
        if(state==GLUT_DOWN && x>scrollxmin+position+2 && x<=scrollxmin+position+11 && y<scrollymax-1 && y>=scrollymin+2){
            status=SELECTED;
            clickx=x;
            glutPostRedisplay();
            return true;
        }else if(status!=UNINVOLVED && state==GLUT_UP){
            status=UNINVOLVED;
            glutPostRedisplay();
            return true;
        }else
            return false;
    }
    
    void Slider::
    drag(int x, int /*y*/ )
    {
        if(status==SELECTED){
            glutPostRedisplay();
            int newposition=position+(x-clickx);
            clickx=x;
            if(newposition<0){
                clickx+=(0-newposition);
                newposition=0;
            }else if(newposition>length){
                clickx+=(length-newposition);
                newposition=length;
            }
            if(newposition!=position){
                position=newposition;
                action();
                glutPostRedisplay();
            }
        }
    }
    
    //=================================================================================
    
    WidgetList::
    WidgetList(int indent_, bool hidden_)
    : indent(indent_), hidden(hidden_), list(), downclicked_member(-1)
    {
    }
    
    void WidgetList::
    display(int x, int y)
    {
        dispx=x;
        dispy=y;
        if(hidden){
            width=height=0;
        }else{
            height=0;
            for(unsigned int i=0; i<list.size(); ++i){
                list[i]->display(x+indent, y-height);
                height+=list[i]->height;
                width=(width<indent+list[i]->width) ? indent+list[i]->width : width;
            }
        }
    }
    
    bool WidgetList::
    click(int state, int x, int y)
    {
        //if(hidden || x<dispx || x>=dispx+width || y>=dispy || y<dispy-height) return false; // early exit
        if(state==GLUT_DOWN){ // search for correct widget
            for(unsigned int i=0; i<list.size(); ++i){
                if(list[i]->click(state, x, y)){
                    downclicked_member=i;
                    return true;
                }
            }
        }else if(state==GLUT_UP && downclicked_member>=0){
            list[downclicked_member]->click(state, x, y);
            downclicked_member=-1;
        }
        return false;
    }
    
    void WidgetList::
    drag(int x, int y)
    {
        if(downclicked_member>=0)
            list[downclicked_member]->drag(x, y);
    }
    
    
    //=================================================================================
    
    typedef enum {NOBODY, CAMERA, WIDGETS, USER} MouseOwnerType;
    
    MouseOwnerType mouse_owner = NOBODY;
    
    //
    // Local ("static") functions
    //
    
    namespace {
        
        //=================================================================================
        
        void gluviReshape(int w, int h)
        {
            winwidth=w;
            winheight=h;
            glutPostRedisplay(); // triggers the camera to adjust itself to the new dimensions
        }
        
        //=================================================================================
        
        void gluviDisplay()
        {
            
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
            
            // draw the scene
            if(camera) camera->gl_transform();
            if(userDisplayFunc) userDisplayFunc();
            
            // now draw widgets on top
            glPushAttrib(GL_CURRENT_BIT|GL_ENABLE_BIT|GL_LINE_BIT);
            glDisable(GL_DEPTH_TEST);
            glDisable(GL_LIGHTING);
            glLineWidth(1);
            // and probably more needs setting before widgets
            
            glMatrixMode(GL_MODELVIEW);
            glLoadIdentity();
            glMatrixMode(GL_PROJECTION);
            glLoadIdentity();
            gluOrtho2D(0, winwidth, 0, winheight);
            
            root.display(0, winheight);
            
            // and allow the camera to draw something on screen (e.g. for zooming extent)
            if(camera) camera->display_screen();
            
            glPopAttrib();
            
            glutSwapBuffers();
        }
        
        void gluviMouse(int button, int state, int x, int y)
        {
            if(state==GLUT_DOWN){
                int mods=glutGetModifiers();
                if(camera && mods==GLUT_ACTIVE_SHIFT){
                    camera->click(button, state, x, y);
                    mouse_owner=CAMERA;
                    //}else if(button==GLUT_LEFT_BUTTON && root.click(state, x, winheight-y)){
                    //   mouse_owner=WIDGETS;
                }else if(userMouseFunc){
                    userMouseFunc(button, state, x, y);
                    mouse_owner=USER;
                }
            }else{ // mouse up - send event to whoever got the mouse down
                switch(mouse_owner){
                    case CAMERA:
                        camera->click(button, state, x, y);
                        break;
                    case WIDGETS:
                        //root.click(state, x, winheight-y);
                        break;
                    case USER:
                        if(userMouseFunc) userMouseFunc(button, state, x, y);
                        break;
                    default:
                        ;// nothing to do
                }
                mouse_owner=NOBODY;
            }
        }
        
        //=================================================================================
        
        void gluviDrag(int x, int y)
        {
            switch(mouse_owner){
                case CAMERA:
                    camera->drag(x, y);
                    break;
                case WIDGETS:
                    //root.drag(x, winheight-y);
                    break;
                case USER:
                    if(userDragFunc) userDragFunc(x, y);
                    break;
                default:
                    ;// nothing to do
            }
        }
        
        
    }  // namespace
    
    
    //=================================================================================
    
    void ppm_screenshot(const char *filename_format, ...)
    {
        va_list ap;
        va_start(ap, filename_format);
#ifdef _MSC_VER
#define FILENAMELENGTH 256
        char filename[FILENAMELENGTH];
        _vsnprintf(filename, FILENAMELENGTH, filename_format, ap);
        ofstream out(filename, ofstream::binary);
#else
        char *filename;
        vasprintf(&filename, filename_format, ap);
        ofstream out(filename, ofstream::binary);
        free(filename);
#endif
        if(!out) return;
        GLubyte *image_buffer=new GLubyte[3*winwidth*winheight];
        glReadBuffer(GL_FRONT);
        glReadPixels(0, 0, winwidth, winheight, GL_RGB, GL_UNSIGNED_BYTE, image_buffer);
        out<<"P6\n"<<winwidth<<' '<<winheight<<" 255\n";
        for(int i=1; i<=winheight; ++i)
            out.write((const char*)image_buffer+3*winwidth*(winheight-i), 3*winwidth);
        delete[] image_buffer;
    }
    
    namespace { 
        
        void write_big_endian_ushort(std::ostream &output, unsigned short v)
        {
            output.put( static_cast<char>((v>>8)%256) );
            output.put( static_cast<char>(v%256) );
        }
        
        void write_big_endian_uint(std::ostream &output, unsigned int v)
        {
            output.put(static_cast<char>((v>>24)%256));
            output.put(static_cast<char>((v>>16)%256));
            output.put(static_cast<char>((v>>8)%256));
            output.put(static_cast<char>(v%256));
        }
        
    }  // unnamed namespace
    
    void sgi_screenshot(const char *filename_format, ...)
    {
        va_list ap;
        va_start(ap, filename_format);
#ifdef _MSC_VER
#define FILENAMELENGTH 256
        char filename[FILENAMELENGTH];
        _vsnprintf(filename, FILENAMELENGTH, filename_format, ap);
        ofstream output(filename, ofstream::binary);
#else
        char *filename;
        vasprintf(&filename, filename_format, ap);
        ofstream output(filename, ofstream::binary);
#endif
        if(!output) return;
        
        const int mipmap_level = 1;
        const int size_scale = 1 << (mipmap_level);
        
        winwidth = size_scale * winwidth;
        winheight = size_scale * winheight;
        
        glGenFramebuffers(1, &screenshot_fbo);
        glBindFramebuffer(GL_FRAMEBUFFER, screenshot_fbo);
        
        GLuint textureId;
        glGenTextures(1, &textureId);
        glBindTexture(GL_TEXTURE_2D, textureId);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE); // automatic mipmap
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, mipmap_level);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, winwidth, winheight, 0, GL_RGBA, GL_UNSIGNED_BYTE, 0);
        
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_2D, textureId, 0);
        
        //
        // Depth/stencil buffer
        //
        
        GLuint depthRenderbuffer;
        glGenRenderbuffers(1, &depthRenderbuffer);
        glBindRenderbuffer(GL_RENDERBUFFER, depthRenderbuffer);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, winwidth, winheight);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, depthRenderbuffer);
        GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        
        if (status != GL_FRAMEBUFFER_COMPLETE) 
        {
            std::cout << "Problem with OpenGL framebuffer after specifying depth/stencil render buffer: " << hex << status << std::endl;
            assert(0);
        }
        
        glPixelStorei(GL_PACK_ALIGNMENT, 1);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);   
        glBlendFunc (GL_SRC_ALPHA_SATURATE, GL_ONE);
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
        
        // draw the scene
        
        taking_screenshot = true;
        
        if(camera) camera->gl_transform();
        if(userDisplayFunc) userDisplayFunc();
        
        taking_screenshot = false;
        
        glEnable(GL_TEXTURE_2D);
        glGenerateMipmapEXT(GL_TEXTURE_2D);
        
        GLint file_width, file_height;
        glGetTexLevelParameteriv( GL_TEXTURE_2D, mipmap_level, GL_TEXTURE_WIDTH, &file_width );
        glGetTexLevelParameteriv( GL_TEXTURE_2D, mipmap_level, GL_TEXTURE_HEIGHT, &file_height );
        
        GLubyte *buffer = new GLubyte[ 4 * file_width * file_height ]; 
        
        glGetTexImage( GL_TEXTURE_2D, mipmap_level, GL_RGBA, GL_UNSIGNED_BYTE, buffer );
        
        
        GLubyte* r_buffer = new GLubyte[file_width*file_height];            
        GLubyte* g_buffer = new GLubyte[file_width*file_height];            
        GLubyte* b_buffer = new GLubyte[file_width*file_height];            
        
        for(int y = 0; y < file_height; y++)
            for(int x = 0; x < file_width; x++)
            {
                int startAddressOfPixel = ((y*file_width) + x)*4;
                
                r_buffer[ ((y*file_width) + x) ] = buffer[startAddressOfPixel+0];
                g_buffer[ ((y*file_width) + x) ] = buffer[startAddressOfPixel+1];
                b_buffer[ ((y*file_width) + x) ] = buffer[startAddressOfPixel+2];
            }
        
        
        // first write the SGI header
        
        write_big_endian_ushort(output, 474); // magic number to identify this as an SGI image file
        output.put(0); // uncompressed
        output.put(1); // use 8-bit colour depth
        write_big_endian_ushort(output, 3); // number of dimensions
        assert( file_width < std::numeric_limits<unsigned short>::max() );
        assert( file_height < std::numeric_limits<unsigned short>::max() );   
        write_big_endian_ushort(output, static_cast<unsigned short>(file_width) ); // x size
        write_big_endian_ushort(output, static_cast<unsigned short>(file_height) ); // y size
        write_big_endian_ushort(output, 3); // three colour channels (z size)
        write_big_endian_uint(output, 0); // minimum pixel value
        write_big_endian_uint(output, 255); // maximum pixel value
        write_big_endian_uint(output, 0); // dummy spacing
        // image name
        int i;
        for(i=0; i<80 && filename[i]; ++i)
            output.put(filename[i]);
        for(; i<80; ++i)
            output.put(0);
        write_big_endian_uint(output, 0); // colormap is normal
        for(i=0; i<404; ++i) output.put(0); // filler to complete header
        
        // now write the SGI image data
        
        output.write((const char*)r_buffer, file_width*file_height);
        output.write((const char*)g_buffer, file_width*file_height);
        output.write((const char*)b_buffer, file_width*file_height);
        
        delete[] r_buffer;
        delete[] g_buffer;
        delete[] b_buffer;
        delete[] buffer;
        
        glBindFramebuffer( GL_FRAMEBUFFER, 0 );
        glBindTexture(GL_TEXTURE_2D, 0);
        
        winwidth /= size_scale;
        winheight /= size_scale;
        if(camera) camera->gl_transform();
        
        glDeleteTextures( 1, &textureId );
        glDeleteRenderbuffers( 1, &depthRenderbuffer );
        glDeleteFramebuffers(1, &screenshot_fbo);
        
#ifndef _MSC_VER
        free(filename);
#endif
    }
    
    void set_generic_lights(void)
    {
        glEnable(GL_LIGHTING);
        {
            GLfloat ambient[4] = {.3f, .3f, .3f, 1.0f};
            glLightModelfv (GL_LIGHT_MODEL_AMBIENT,ambient);
        }
        {
            GLfloat color[4] = {.4f, .4f, .4f, 1.0f};
            glLightfv (GL_LIGHT0, GL_DIFFUSE, color);
            glLightfv (GL_LIGHT0, GL_SPECULAR, color);
            glEnable (GL_LIGHT0);
        }
        {
            GLfloat color[4] = {.4f, .4f, .4f, 1.0f};
            glLightfv (GL_LIGHT1, GL_DIFFUSE, color);
            glLightfv (GL_LIGHT1, GL_SPECULAR, color);
            glEnable (GL_LIGHT1);
        }
        {
            GLfloat color[4] = {.2f, .2f, .2f, 1.0f};
            glLightfv (GL_LIGHT2, GL_DIFFUSE, color);
            glLightfv (GL_LIGHT2, GL_SPECULAR, color);
            glEnable (GL_LIGHT2);
        }
    }
    
    void set_generic_material(float r, float g, float b, GLenum face)
    {
        GLfloat ambient[4], diffuse[4], specular[4];
        ambient[0]=0.1f*r+0.03f; ambient[1]=0.1f*g+0.03f; ambient[2]=0.1f*b+0.03f; ambient[3]=1.0f;
        diffuse[0]=0.7f*r;      diffuse[1]=0.7f*g;      diffuse[2]=0.7f*b;      diffuse[3]=1.0f;
        specular[0]=0.1f*r+0.1f; specular[1]=0.1f*g+0.1f; specular[2]=0.1f*b+0.1f; specular[3]=1.0f;
        glMaterialfv(face, GL_AMBIENT, ambient);
        glMaterialfv(face, GL_DIFFUSE, diffuse);
        glMaterialfv(face, GL_SPECULAR, specular);
        glMaterialf(face, GL_SHININESS, 32);
    }
    
    void set_matte_material(float r, float g, float b, GLenum face)
    {
        GLfloat ambient[4], diffuse[4], specular[4];
        ambient[0]=0.1f*r+0.03f; ambient[1]=0.1f*g+0.03f; ambient[2]=0.1f*b+0.03f; ambient[3]=1.0f;
        diffuse[0]=0.9f*r;      diffuse[1]=0.9f*g;      diffuse[2]=0.9f*b;      diffuse[3]=1.0f;
        specular[0]=0;         specular[1]=0;         specular[2]=0;         specular[3]=1;
        glMaterialfv(face, GL_AMBIENT, ambient);
        glMaterialfv(face, GL_DIFFUSE, diffuse);
        glMaterialfv(face, GL_SPECULAR, specular);
    }
    
    /** 
     * Draw a vector in 3D.  If arrow_head_length not specified, set it to 10% of vector length.
     * Mar 29, 2006
     */
    void draw_3d_arrow(const float base[3], const float point[3], float arrow_head_length)
    {
        //glPushAttrib(GL_CURRENT_BIT|GL_ENABLE_BIT|GL_LINE_BIT);
        //glDisable(GL_LIGHTING);
        glLineWidth(1);
        glColor3f(0.5f,0.5f,0.5f);
        
        Vec3f w(point[0]-base[0], point[1]-base[1], point[2]-base[2]);
        float len = mag(w);
        w = w / len;    // normalize to build coordinate system
        
        // create a coordinate system from the vector:
        // get a vector perp to w and y-axis
        Vec3f u = cross(w, Vec3f(0,1,0));
        
        // If vector is parallel to the y-axis, use the x-axis
        if (mag(u) == 0)
            u = cross(w, Vec3f(1,0,0));
        
        // get a vector perp to w and u
        Vec3f v = cross(w, u/mag(u));
        v = v/mag(v);
        
        if (!arrow_head_length)
            arrow_head_length = 0.1f * len;
        
        // arrow head points
        //@@@@@@@ POSSIBILITY: CREATE FOUR ARROW HEAD SEGMENTS INSTEAD OF TWO
        Vec3f arrow1, arrow2;
        arrow1[0] = point[0] + arrow_head_length * (v[0] - w[0]);
        arrow1[1] = point[1] + arrow_head_length * (v[1] - w[1]);
        arrow1[2] = point[2] + arrow_head_length * (v[2] - w[2]);
        arrow2[0] = point[0] + arrow_head_length * (-v[0] - w[0]);
        arrow2[1] = point[1] + arrow_head_length * (-v[1] - w[1]);
        arrow2[2] = point[2] + arrow_head_length * (-v[2] - w[2]);
        
        glBegin(GL_LINES);
        glVertex3f(base[0],   base[1],   base[2]);
        glVertex3f(point[0],  point[1],  point[2]);
        glVertex3f(point[0],  point[1],  point[2]);
        glVertex3f(arrow1[0], arrow1[1], arrow1[2]);
        glVertex3f(point[0],  point[1],  point[2]);
        glVertex3f(arrow2[0], arrow2[1], arrow2[2]);
        glEnd();
        
        //glPopAttrib();
    }
    
    // draw_2d_arrow assumptions: 
    // line width, point size, and color are set by the user prior to calling the routine
    /*
     void draw_2d_arrow(const Vec2f base, const Vec2f point, float arrow_head_length)
     {
     //glPushAttrib(GL_CURRENT_BIT|GL_ENABLE_BIT|GL_LINE_BIT);
     //glDisable(GL_LIGHTING);
     
     Vec2f w = point-base;
     float len = mag(w);
     
     if (len==0) {
     glBegin(GL_POINTS);
     glVertex2f(base[0], base[1]);
     glEnd();
     return;
     }
     
     w = w / len;    // normalize to build coordinate system
     
     // u = w + 90 
     // using rotation matrix  0  1
     //	                     -1  0
     Vec2f u = Vec2f(1*w[1], -1*w[0]);
     u = u/mag(u);
     
     // v = w - 90 (in fact v=-u)
     Vec2f v = Vec2f(-1*w[1], 1*w[0]);
     v = v/mag(v);
     
     if (!arrow_head_length) {
     arrow_head_length = 0.1f * len;
     }
     
     // arrow head points
     Vec2f arrow1, arrow2;
     arrow1 = point + arrow_head_length * (v-w);
     arrow2 = point + arrow_head_length * (u-w);
     
     glBegin(GL_LINES);
     glVertex2f(base[0], base[1]);
     glVertex2f(point[0], point[1]);
     glVertex2f(point[0], point[1]);
     glVertex2f(arrow1[0], arrow1[1]);
     glVertex2f(point[0], point[1]);
     glVertex2f(arrow2[0], arrow2[1]);
     glEnd();
     
     //glPopAttrib();
     }
     */
    
    void draw_coordinate_grid(float size, int spacing)
    {
        glPushAttrib(GL_CURRENT_BIT|GL_ENABLE_BIT|GL_LINE_BIT);
        glDisable(GL_LIGHTING);
        glLineWidth(1);
        
        glBegin(GL_LINES);
        glColor3f(0.5f,0.5f,0.5f);
        for(int i=-spacing; i<=spacing; ++i){
            glVertex3f(-size,0,i*size/spacing);
            glVertex3f((i!=0)*size,0,i*size/spacing);
            glVertex3f(i*size/spacing,0,-size);
            glVertex3f(i*size/spacing,0,(i!=0)*size);
        }
        glColor3f(1,0,0);
        glVertex3f(0,0,0);
        glVertex3f(size,0,0);
        glColor3f(0,1,0);
        glVertex3f(0,0,0);
        glVertex3f(0,size,0);
        glColor3f(0,0,1);
        glVertex3f(0,0,0);
        glVertex3f(0,0,size);
        glEnd();
        
        glPopAttrib();
    }
    
    void draw_text( const float* /*point[3]*/, const char* /*text*/, int /*fontsize*/ )
    {
        // please implement me!
    }
    
    int windowID = 0;
    
    //=================================================================================
    
    void init(const char *windowtitle, int *argc, char **argv)
    {
        glutInit(argc, argv);
        glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGBA|GLUT_ALPHA|GLUT_DEPTH|GLUT_STENCIL);
        glutInitWindowSize(winwidth, winheight);
        windowID = glutCreateWindow(windowtitle);
        glutReshapeFunc(gluviReshape);
        glutDisplayFunc(gluviDisplay);
        glutMouseFunc(gluviMouse);
        glutMotionFunc(gluviDrag);
        glEnable(GL_DEPTH_TEST);
        glClearDepth(1);
        glPixelStorei(GL_PACK_ALIGNMENT, 1);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        
        glBlendFunc (GL_SRC_ALPHA_SATURATE, GL_ONE);
        glClearColor (1.0f, 1.0f, 1.0f, 1.0f);
    }
    
    //=================================================================================
    
    void (*userDisplayFunc)(void)=0; 
    void (*userMouseFunc)(int button, int state, int x, int y)=0;
    void (*userDragFunc)(int x, int y)=0;
    Camera *camera=0;
    WidgetList root(0);
    int winwidth=720, winheight=480;
    
    //=================================================================================
    
    void run(void)
    {
        glutMainLoop();
    }
    
}     // namespace Gluvi


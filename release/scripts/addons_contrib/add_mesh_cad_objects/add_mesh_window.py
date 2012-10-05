'''bl_info = {
    "name": "Window",
    "author": "SayPRODUCTIONS",
    "version": (1, 0),
    "blender": (2, 5, 9),
    "api": 33333,
    "location": "View3D > Add > Mesh > Say3D",
    "description": "Window olusturma",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
	'''
import bpy
from bpy.props import *
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
import operator
from math import pi, sin, cos, sqrt, atan

def MAhs():
    if 'Wood' not in bpy.data.materials:
        mtl=bpy.data.materials.new('Wood')
        mtl.diffuse_color     = (0.3,0.18,0.12)
        mtl.diffuse_shader    = 'LAMBERT' 
        mtl.diffuse_intensity = 1.0 
    else:
        mtl=bpy.data.materials['Glass']
    return mtl
def MPVC():
    if 'PVC' not in bpy.data.materials:
        mtl=bpy.data.materials.new('PVC')
        mtl.diffuse_color     = (0.5,0.4,0.3)
        mtl.diffuse_shader    = 'LAMBERT' 
        mtl.diffuse_intensity = 1.0 
    else:
        mtl=bpy.data.materials['PVC']
    return mtl

def MGlass():

    if 'Glass' not in bpy.data.materials:
        mtl = bpy.data.materials.new('Glass')
        mtl.diffuse_color     = (0.5,0.8,1.0)
        mtl.diffuse_shader    = 'LAMBERT' 
        mtl.diffuse_intensity = 1.0 
        mtl.use_transparency = True
        mtl.type = 'SURFACE'
        mtl.alpha = 0.3
        mtl.raytrace_mirror.use = True
        mtl.raytrace_mirror.reflect_factor = 0.65
    else:
        mtl=bpy.data.materials['Glass']
    return mtl
def MMer():
    if 'Marble' not in bpy.data.materials:
        mtl=bpy.data.materials.new('Marble')
        mtl.diffuse_color     = (0.2,0.1,0.1)
        mtl.diffuse_shader    = 'LAMBERT' 
        mtl.diffuse_intensity = 1.0 
    else:
        mtl=bpy.data.materials['Marble']
    return mtl

    matnew1.diffuse_shader = 'OREN_NAYAR' 
    matnew1.roughness = 0.909

    #spec1
    matnew1.specular_color = spec1
    matnew1.specular_shader = 'COOKTORR'
    matnew1.specular_intensity = 0.5
    matnew1.alpha = alpha
    matnew1.ambient = 1
    matnew1.emit=emit

    return mtl
def Prs(s):
    if  s.prs=='1':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  60;s.gnx1=  110;s.gnx2=  60
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='2':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  60;s.gnx1=   60;s.gnx2=  60
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='3':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=190;s.mr=True
        s.gnx0=  55;s.gnx1=   50;s.gnx2=  55
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='4':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=150;s.mr=True
        s.gnx0=  55;s.gnx1=   50;s.gnx2=  55
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='5':
        s.gen=3;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=150;s.mr=True
        s.gnx0=  50;s.gnx1=   40;s.gnx2=  50
        s.k00 =True;s.k01 =False;s.k02 =True
    if  s.prs=='6':
        s.gen=1;s.yuk=1;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=40;s.mr=True
        s.gnx0=40
        s.k00 =False
    if  s.prs=='7':
        s.gen=1;s.yuk=2;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=195;s.gny1=40
        s.gnx0=70
        s.k00 =True;s.k10 =False
        s.mr=False
    if  s.prs=='8':
        s.gen=1;s.yuk=2;s.kl1=5;s.kl2=5;s.fk=2
        s.gny0=180;s.gny1=35
        s.gnx0=70
        s.k00 =True;s.k10 =False
        s.mr=False
def kub(f,y,k,x,l,r,u,d):
    k=(k*2)+(x*y)
    if d==1:f.append([  k,   1+k, y+1+k,   y+k])#Alt
    if u==1:f.append([3+k,   2+k, y+2+k, y+3+k])#Ust
    if l==1:f.append([1+k,     k,   2+k,   3+k])#Sol
    if r==1:f.append([y+k, y+1+k, y+3+k, y+2+k])#Sag
    f.append([   k,   y+k, y+2+k,   2+k])#On
    f.append([ 3+k, y+3+k, y+1+k,   1+k])#Arka
def add_object(self, context):
    fc=[];vr=[];kx=[]
    mx=self.gen;my=self.yuk;k1=self.kl1/100;y=my*4+4;k2=self.kl2/100;k3=self.fk/200

    u=self.kl1/100;X=[0,round(u,2)]
    if mx> 0:u+=self.gnx0 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 1:u+=self.gnx1 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 2:u+=self.gnx2 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 3:u+=self.gnx3 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 4:u+=self.gnx4 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 5:u+=self.gnx5 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 6:u+=self.gnx6 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    if mx> 7:u+=self.gnx7 /100;X.append(round(u,2));u+=k2;X.append(round(u,2))
    X[-1]=X[-2]+k1

    u=self.kl1/100;Z=[0,round(u,2)]
    if my> 0:u+=self.gny0 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 1:u+=self.gny1 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 2:u+=self.gny2 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 3:u+=self.gny3 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    if my> 4:u+=self.gny4 /100;Z.append(round(u,2));u+=k2;Z.append(round(u,2))
    Z[-1]=Z[-2]+k1

    u=X[-1]/2

    kp=[];kp.append(self.k00);kp.append(self.k10);kp.append(self.k20);kp.append(self.k30);kp.append(self.k40);kx.append(kp)
    kp=[];kp.append(self.k01);kp.append(self.k11);kp.append(self.k21);kp.append(self.k31);kp.append(self.k41);kx.append(kp)
    kp=[];kp.append(self.k02);kp.append(self.k12);kp.append(self.k22);kp.append(self.k32);kp.append(self.k42);kx.append(kp)
    kp=[];kp.append(self.k03);kp.append(self.k13);kp.append(self.k23);kp.append(self.k33);kp.append(self.k43);kx.append(kp)
    kp=[];kp.append(self.k04);kp.append(self.k14);kp.append(self.k24);kp.append(self.k34);kp.append(self.k44);kx.append(kp)
    kp=[];kp.append(self.k05);kp.append(self.k15);kp.append(self.k25);kp.append(self.k35);kp.append(self.k45);kx.append(kp)
    kp=[];kp.append(self.k06);kp.append(self.k16);kp.append(self.k26);kp.append(self.k36);kp.append(self.k46);kx.append(kp)
    kp=[];kp.append(self.k07);kp.append(self.k17);kp.append(self.k27);kp.append(self.k37);kp.append(self.k47);kx.append(kp)
    Glass=[];mer=[]

    for x in X:
        for z in Z:
            vr.append([x-u, -k1/2,z]);vr.append([x-u,k1/2,z])
    for x in range(0,mx*2+1):
        for z in range(0,my*2+1):
            if x%2==0:t=0;d=0
            else:     t=1;d=1
            if z%2==0:l=0;r=0
            else:     l=1;r=1
            if z  ==  0:d=1
            if z ==my*2:t=1
            if x  ==  0:l=1
            if x ==mx*2:r=1
            if x%2==0 or z%2==0:kub(fc,y,z,x,l,r,t,d)
    #Divide
    for x in range(0,mx*2):
        for z in range(0,my*2):
            if x%2==1 and z%2==1:
                d=Z[ z ];  t=Z[z+1]
                l=X[ x ]-u;r=X[x+1]-u
                ac=0
                if kx[int(x/2)][int(z/2)]==True:
                    ac=k1-0.01
                    vr.append([l,    k1/2+ac,d   ]);vr.append([l,   -k1/2+ac,d   ])
                    vr.append([l+k1, k1/2+ac,d+k1]);vr.append([l+k1,-k1/2+ac,d+k1])
                    vr.append([r,    k1/2+ac,d   ]);vr.append([r,   -k1/2+ac,d   ])
                    vr.append([r-k1, k1/2+ac,d+k1]);vr.append([r-k1,-k1/2+ac,d+k1])
                    vr.append([r,    k1/2+ac,t   ]);vr.append([r,   -k1/2+ac,t   ])
                    vr.append([r-k1, k1/2+ac,t-k1]);vr.append([r-k1,-k1/2+ac,t-k1])
                    vr.append([l,    k1/2+ac,t   ]);vr.append([l,   -k1/2+ac,t   ])
                    vr.append([l+k1, k1/2+ac,t-k1]);vr.append([l+k1,-k1/2+ac,t-k1])
                    l+=k1;r-=k1;d+=k1;t-=k1;n=len(vr)
                    fc.append([n- 1,n- 2,n- 6,n- 5]);fc.append([n- 5,n- 6,n-10,n- 9])
                    fc.append([n- 9,n-10,n-14,n-13]);fc.append([n- 2,n- 1,n-13,n-14])
                    fc.append([n- 2,n- 4,n- 8,n- 6]);fc.append([n- 6,n- 8,n-12,n-10])
                    fc.append([n-10,n-12,n-16,n-14]);fc.append([n- 4,n- 2,n-14,n-16])
                    fc.append([n- 3,n- 1,n- 5,n- 7]);fc.append([n- 7,n- 5,n- 9,n-11])
                    fc.append([n-11,n- 9,n-13,n-15]);fc.append([n- 1,n- 3,n-15,n-13])
                    fc.append([n- 4,n- 3,n- 7,n- 8]);fc.append([n- 8,n- 7,n-11,n-12])
                    fc.append([n-12,n-11,n-15,n-16]);fc.append([n- 3,n- 4,n-16,n-15])
                #Fitil
                vr.append([l,      k3+ac,d     ]);vr.append([l,     -k3+ac,d     ])
                vr.append([l+k3*2, k3+ac,d+k3*2]);vr.append([l+k3*2,-k3+ac,d+k3*2])
                vr.append([r,      k3+ac,d     ]);vr.append([r,     -k3+ac,d     ])
                vr.append([r-k3*2, k3+ac,d+k3*2]);vr.append([r-k3*2,-k3+ac,d+k3*2])
                vr.append([r,      k3+ac,t     ]);vr.append([r,     -k3+ac,t     ])
                vr.append([r-k3*2, k3+ac,t-k3*2]);vr.append([r-k3*2,-k3+ac,t-k3*2])
                vr.append([l,      k3+ac,t     ]);vr.append([l,     -k3+ac,t     ])
                vr.append([l+k3*2, k3+ac,t-k3*2]);vr.append([l+k3*2,-k3+ac,t-k3*2])
                n=len(vr)
                fc.append([n- 1,n- 2,n- 6,n- 5]);fc.append([n- 5,n- 6,n-10,n- 9])
                fc.append([n- 9,n-10,n-14,n-13]);fc.append([n- 2,n- 1,n-13,n-14])
                fc.append([n- 2,n- 4,n- 8,n- 6]);fc.append([n- 6,n- 8,n-12,n-10])
                fc.append([n-10,n-12,n-16,n-14]);fc.append([n- 4,n- 2,n-14,n-16])
                fc.append([n- 3,n- 1,n- 5,n- 7]);fc.append([n- 7,n- 5,n- 9,n-11])
                fc.append([n-11,n- 9,n-13,n-15]);fc.append([n- 1,n- 3,n-15,n-13])
                #Glass
                vr.append([l+k3*2, 0.003+ac,d+k3*2]);vr.append([l+k3*2,-0.003+ac,d+k3*2])
                vr.append([r-k3*2, 0.003+ac,d+k3*2]);vr.append([r-k3*2,-0.003+ac,d+k3*2])
                vr.append([r-k3*2, 0.003+ac,t-k3*2]);vr.append([r-k3*2,-0.003+ac,t-k3*2])
                vr.append([l+k3*2, 0.003+ac,t-k3*2]);vr.append([l+k3*2,-0.003+ac,t-k3*2])
                n=len(vr)
                fc.append([n-1,n-3,n-4,n-2]);fc.append([n-3,n-5,n-6,n-4])
                fc.append([n-5,n-7,n-8,n-6]);fc.append([n-7,n-1,n-2,n-8])
                fc.append([n-3,n-1,n-7,n-5]);fc.append([n-2,n-4,n-6,n-8])
                n=len(fc)
                Glass.append(n-1);Glass.append(n-2);Glass.append(n-3)
                Glass.append(n-4);Glass.append(n-5);Glass.append(n-6)
    #Marble
    if self.mr==True:
        mrh=-self.mr1/100
        mrg= self.mr2/100
        mdv= (self.mr3/200)+mrg
        msv=-(mdv+(self.mr4/100))
        vr.append([-u,mdv,  0]);vr.append([u,mdv,  0])
        vr.append([-u,msv,  0]);vr.append([u,msv,  0])
        vr.append([-u,mdv,mrh]);vr.append([u,mdv,mrh])
        vr.append([-u,msv,mrh]);vr.append([u,msv,mrh])
        n=len(vr)
        fc.append([n-1,n-2,n-4,n-3])
        fc.append([n-3,n-4,n-8,n-7])
        fc.append([n-6,n-5,n-7,n-8])
        fc.append([n-2,n-1,n-5,n-6])
        fc.append([n-4,n-2,n-6,n-8])
        fc.append([n-5,n-1,n-3,n-7])
        n=len(fc)
        mer.append(n-1);mer.append(n-2);mer.append(n-3)
        mer.append(n-4);mer.append(n-5);mer.append(n-6)
#OBJE -----------------------------------------------------------
    mesh = bpy.data.meshes.new(name='Window')
    mesh.from_pydata(vr,[],fc)
    mesh.materials.append(MPVC());mesh.materials.append(MGlass());mesh.materials.append(MMer())
    for i in Glass:
        mesh.polygons[i].material_index=1
    for i in mer:
        mesh.polygons[i].material_index=2
    mesh.update(calc_edges=True)
    object_data_add(context, mesh, operator=None)
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
#----------------------------------------------------------------
class OBJECT_OT_add_object(bpy.types.Operator):
    bl_idname = "mesh.add_say3d_pencere"
    bl_label = "Window"
    bl_description = "Window Olustur"
    bl_options = {'REGISTER', 'UNDO'}
    prs = EnumProperty(items = (('1',"WINDOW 250X200",""),
                                ('2',"WINDOW 200X200",""),
                                ('3',"WINDOW 180X200",""),
                                ('4',"WINDOW 180X160",""),
                                ('5',"WINDOW 160X160",""),
                                ('6',"WINDOW 50X50",""),
                                ('7',"DOOR 80X250",""),
                                ('8',"DOOR 80X230","")),
                                name="",description="")
    son=prs
    gen=IntProperty(name='Horizontal',    min=1,max= 8, default= 3, description='Horizontal Divide')
    yuk=IntProperty(name='Vertical',    min=1,max= 5, default= 1, description='Vertical Divide')
    kl1=IntProperty(name='Frame',  min=2,max=50, default= 5, description='Frame Thickness')
    kl2=IntProperty(name='Gap',   min=2,max=50, default= 5, description='Gap Thickness')
    fk =IntProperty(name='Piping',    min=1,max=20, default= 2, description='Piping Thickness')

    mr=BoolProperty(name='Sill', default=True,description='Sill')
    mr1=IntProperty(min=1, max=20, default= 4,  description='Height')
    mr2=IntProperty(min=0, max=20, default= 4,  description='Width')
    mr3=IntProperty(min=1, max=50, default=20,  description='Sill Thickness')
    mr4=IntProperty(min=0, max=50, default= 0,  description='Jamb Thickness')

    gnx0=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx1=IntProperty(min=1,max=300,default=110,description='Width')
    gnx2=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx3=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx4=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx5=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx6=IntProperty(min=1,max=300,default= 60,description='Width')
    gnx7=IntProperty(min=1,max=300,default= 60,description='Width')

    gny0=IntProperty(min=1,max=300,default=190,description='Height')
    gny1=IntProperty(min=1,max=300,default= 45,description='Height')
    gny2=IntProperty(min=1,max=300,default= 45,description='Height')
    gny3=IntProperty(min=1,max=300,default= 45,description='Height')
    gny4=IntProperty(min=1,max=300,default= 45,description='Height')

    k00=BoolProperty(default=True); k01=BoolProperty(default=False)
    k02=BoolProperty(default=True); k03=BoolProperty(default=False)
    k04=BoolProperty(default=False);k05=BoolProperty(default=False)
    k06=BoolProperty(default=False);k07=BoolProperty(default=False)

    k10=BoolProperty(default=False);k11=BoolProperty(default=False)
    k12=BoolProperty(default=False);k13=BoolProperty(default=False)
    k14=BoolProperty(default=False);k15=BoolProperty(default=False)
    k16=BoolProperty(default=False);k17=BoolProperty(default=False)

    k20=BoolProperty(default=False);k21=BoolProperty(default=False)
    k22=BoolProperty(default=False);k23=BoolProperty(default=False)
    k24=BoolProperty(default=False);k25=BoolProperty(default=False)
    k26=BoolProperty(default=False);k27=BoolProperty(default=False)

    k30=BoolProperty(default=False);k31=BoolProperty(default=False)
    k32=BoolProperty(default=False);k33=BoolProperty(default=False)
    k34=BoolProperty(default=False);k35=BoolProperty(default=False)
    k36=BoolProperty(default=False);k37=BoolProperty(default=False)

    k40=BoolProperty(default=False);k41=BoolProperty(default=False)
    k42=BoolProperty(default=False);k43=BoolProperty(default=False)
    k44=BoolProperty(default=False);k45=BoolProperty(default=False)
    k46=BoolProperty(default=False);k47=BoolProperty(default=False)
    #--------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        layout.prop(self,'prs')
        box=layout.box()
        box.prop(self,'gen');box.prop(self,'yuk')
        box.prop(self,'kl1');box.prop(self,'kl2')
        box.prop(self, 'fk')

        box.prop(self,'mr')
        row=box.row();row.prop(self,'mr1', text="Sill Height");row.prop(self,'mr2', text="Sill Width")
        row=box.row();row.prop(self,'mr3', text="Sill Thick");row.prop(self,'mr4', text="Jamb Thick")
        row=layout.row()
        row.label(text="Column Settings")
        row=layout.row()
        for i in range(0,self.gen):
            row.prop(self,'gnx'+str(i))
            row=layout.row()
        for j in range(0,self.yuk):
            row.prop(self,'gny'+str(self.yuk-j-1),text="Height")
            row=layout.row()
            row.label(text="Window Sash")
            row=layout.row()
            for i in range(0,self.gen):
                row.prop(self,'k'+str(self.yuk-j-1)+str(i))
            row=layout.row()
    def execute(self, context):
        if self.son!=self.prs:
            Prs(self)
            self.son=self.prs
        add_object(self,context)
        return {'FINISHED'}
# Registration
def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_object.bl_idname,
        text="WINDOW",
        icon="MOD_LATTICE")
def register():
    bpy.utils.register_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_mesh_add.append(add_object_button)
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_mesh_add.remove(add_object_button)
if __name__ == '__main__':
    register()
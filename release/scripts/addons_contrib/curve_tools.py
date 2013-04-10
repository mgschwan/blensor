# #####BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# #####END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Curve Tools",
    "author": "Zak",
    "version": (0, 1, 5),
    "blender": (2, 59, 0),
    "location": "Properties > Object data",
    "description": "Creates driven Lofts or Birails between curves",
    "warning": "may be buggy or incomplete",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Curve/Curve_Tools",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=27720",
    "category": "Add Curve"}

### UPDATES
#1.5

#-Fixed birail function
#-Added Curve Snap to W key specials menu.
#-Removed some functions that arent needed and wrapped into the operators.
#-nurbs with weights for loft and birail
#-Panel Moved to view 3d tools
#-inserted TODO comments
#-tried to implement live tension and bias for Hermite interpolation by driving the mesh but
#i dont know why, the code is executed all the time even if you dont change the variables.
#-snap to curves affects all the curves on the scene
#-i was able to preserve handle types when split or subdivide


#1.4
#-incorporate curve snap
#assign a copy transform to helper
#-nurbs implemented (in progress)

import bpy
from mathutils import *
from bpy.props import *

print("----------")


### PROPERTIES
class sprops(bpy.types.PropertyGroup):
    pass


bpy.utils.register_class(sprops)

#bpy.selection will store objects names in the order they were selected
bpy.selection=[]


#dodriver a simple checker to chosse whether  you want a driven mesh or not.
bpy.types.Scene.dodriver = BoolProperty(name = "dodriver",                                      default=False)

#interpolation types
myitems = (('0','Linear', ''),('1','Cubic',''),('2','Catmull',''), ('3','Hermite',''))
bpy.types.Scene.intype = EnumProperty(name="intype", items = myitems, default='3')

#number of steps and spans to be created
bpy.types.Scene.steps = IntProperty(name="steps", default=12, min=2)
bpy.types.Scene.spans = IntProperty(name="spans", default=12, min=2)

#parameters for Hermite interpolation
bpy.types.Scene.tension = FloatProperty(name = "tension", min=0.0, default=0.0)
bpy.types.Scene.bias = FloatProperty(name = "bias", min=0.0, default = 0.5)

#proportional birail
bpy.types.Scene.proportional = BoolProperty(name="proportional", default=False)

#this stores the result of calculating the curve length
bpy.types.Scene.clen = FloatProperty(name="clen", default=0.0, precision=5)

#minimun distance for merge curve tool
bpy.types.Scene.limit = FloatProperty(name="limit", default=0.1, precision=3)


### SELECT BY ORDER BLOCK

#i dont know what to do with this. Im not using it yet.
def selected_points(curve):

    selp = []
    for spl in curve.splines:
        if spl.type=="BEZIER":
            points = spl.bezier_points
            for p in points:
                if p.select_control_point:
                    selp.append(p)

        elif spl.type=="NURBS":
            points = spl.points
            for p in points:
                if p.select:
                    selp.append(p)
    return selp

#writes bpy.selection when a new object is selected or deselected
#it compares bpy.selection with bpy.context.selected_objects

def select():

    #print(bpy.context.mode)
    if bpy.context.mode=="OBJECT":
        obj = bpy.context.object
        sel = len(bpy.context.selected_objects)

        if sel==0:
            bpy.selection=[]
        else:
            if sel==1:
                bpy.selection=[]
                bpy.selection.append(obj)
            elif sel>len(bpy.selection):
                for sobj in bpy.context.selected_objects:
                    if (sobj in bpy.selection)==False:
                        bpy.selection.append(sobj)

            elif sel<len(bpy.selection):
                for it in bpy.selection:
                    if (it in bpy.context.selected_objects)==False:
                        bpy.selection.remove(it)

    #on edit mode doesnt work well


#executes selection by order at 3d view
class Selection(bpy.types.Header):
    bl_label = "Selection"
    bl_space_type = "VIEW_3D"

    def __init__(self):
        #print("hey")
        select()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label("Sel: "+str(len(bpy.selection)))

### GENERAL CURVE FUNCTIONS

#distance between 2 points
def dist(p1, p2):
    return (p2-p1).magnitude

#sets cursors position for debugging porpuses
def cursor(pos):
    bpy.context.scene.cursor_location = pos

#cuadratic bezier value
def quad(p, t):
    return p[0]*(1.0-t)**2.0 + 2.0*t*p[1]*(1.0-t) + p[2]*t**2.0

#cubic bezier value
def cubic(p, t):
    return p[0]*(1.0-t)**3.0 + 3.0*p[1]*t*(1.0-t)**2.0 + 3.0*p[2]*(t**2.0)*(1.0-t) + p[3]*t**3.0

#gets a bezier segment's control points on global coordinates
def getbezpoints(spl, mt, seg=0):
    points = spl.bezier_points
    p0 = mt * points[seg].co
    p1 = mt * points[seg].handle_right
    p2 = mt * points[seg+1].handle_left
    p3 = mt * points[seg+1].co
    return p0, p1, p2, p3

#gets nurbs polygon control points on global coordinates
def getnurbspoints(spl, mw):
    pts = []
    ws = []
    for p in spl.points:
        v = Vector(p.co[0:3])*mw
        pts.append(v)
        ws.append(p.weight)
    return pts , ws

#calcs a nurbs knot vector
def knots(n, order, type=0):#0 uniform 1 endpoints 2 bezier

    kv = []

    t = n+order
    if type==0:
        for i in range(0, t):
            kv.append(1.0*i)

    elif type==1:
        k=0.0
        for i in range(1, t+1):
            kv.append(k)
            if i>=order and i<=n:
                k+=1.0
    elif type==2:
        if order==4:
            k=0.34
            for a in range(0,t):
                if a>=order and a<=n: k+=0.5
                kv.append(floor(k))
                k+=1.0/3.0

        elif order==3:
            k=0.6
            for a in range(0, t):
                if a >=order and a<=n: k+=0.5
                kv.append(floor(k))

    ##normalize the knot vector
    for i in range(0, len(kv)):
        kv[i]=kv[i]/kv[-1]

    return kv

#nurbs curve evaluation
def C(t, order, points, weights, knots):
    #c = Point([0,0,0])
    c = Vector()
    rational = 0
    i = 0
    while i < len(points):
        b = B(i, order, t, knots)
        p = points[i] * (b * weights[i])
        c = c + p
        rational = rational + b*weights[i]
        i = i + 1

    return c * (1.0/rational)

#nurbs basis function
def B(i,k,t,knots):
    ret = 0
    if k>0:
        n1 = (t-knots[i])*B(i,k-1,t,knots)
        d1 = knots[i+k] - knots[i]
        n2 = (knots[i+k+1] - t) * B(i+1,k-1,t,knots)
        d2 = knots[i+k+1] - knots[i+1]
        if d1 > 0.0001 or d1 < -0.0001:
            a = n1 / d1
        else:
            a = 0
        if d2 > 0.0001 or d2 < -0.0001:
            b = n2 / d2
        else:
            b = 0
        ret = a + b
        #print "B i = %d, k = %d, ret = %g, a = %g, b = %g\n"%(i,k,ret,a,b)
    else:
        if knots[i] <= t and t <= knots[i+1]:
            ret = 1
        else:
            ret = 0
    return ret

#calculates a global parameter t along all control points
#t=0 begining of the curve
#t=1 ending of the curve

def calct(obj, t):

    spl=None
    mw = obj.matrix_world
    if obj.data.splines.active==None:
        if len(obj.data.splines)>0:
            spl=obj.data.splines[0]
    else:
        spl = obj.data.splines.active

    if spl==None:
        return False

    if spl.type=="BEZIER":
        points = spl.bezier_points
        nsegs = len(points)-1

        d = 1.0/nsegs
        seg = int(t/d)
        t1 = t/d - int(t/d)

        if t==1:
            seg-=1
            t1 = 1.0

        p = getbezpoints(spl,mw, seg)

        coord = cubic(p, t1)

        return coord

    elif spl.type=="NURBS":
        data = getnurbspoints(spl, mw)
        pts = data[0]
        ws = data[1]
        order = spl.order_u
        n = len(pts)
        ctype = spl.use_endpoint_u
        kv = knots(n, order, ctype)

        coord = C(t, order-1, pts, ws, kv)

        return coord

#length of the curve
def arclength(objs):
    length = 0.0

    for obj in objs:
        if obj.type=="CURVE":
            prec = 1000 #precision
            inc = 1/prec #increments

            ### TODO: set a custom precision value depending the number of curve points
            #that way it can gain on accuracy in less operations.

            #subdivide the curve in 1000 lines and sum its magnitudes
            for i in range(0, prec):
                ti = i*inc
                tf = (i+1)*inc
                a = calct(obj, ti)
                b = calct(obj, tf)
                r = (b-a).magnitude
                length+=r

    return length


class ArcLengthOperator(bpy.types.Operator):

    bl_idname = "curve.arc_length_operator"
    bl_label = "Measures the length of a curve"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        objs = context.selected_objects
        context.scene.clen = arclength(objs)
        return {'FINISHED'}

### LOFT INTERPOLATIONS

#objs = selected objects
#i = object index
#t = parameter along u direction
#tr = parameter along v direction

#linear
def intl(objs, i, t, tr):
    p1 = calct(objs[i],t)
    p2 = calct(objs[i+1], t)

    r = p1 + (p2 - p1)*tr

    return r

#tipo = interpolation type
#tension and bias are for hermite interpolation
#they can be changed to obtain different lofts.

#cubic
def intc(objs, i, t, tr, tipo=3, tension=0.0, bias=0.0):

    ncurves =len(objs)

    #if 2 curves go to linear interpolation regardless the one you choose
    if ncurves<3:
        return intl(objs, i, t, tr)
    else:

        #calculates the points to be interpolated on each curve
        if i==0:
            p0 = calct(objs[i], t)
            p1 = p0
            p2 = calct(objs[i+1], t)
            p3 = calct(objs[i+2], t)
        else:
            if ncurves-2 == i:
                p0 = calct(objs[i-1], t)
                p1 = calct(objs[i], t)
                p2 = calct(objs[i+1], t)
                p3 = p2
            else:
                p0 = calct(objs[i-1], t)
                p1 = calct(objs[i], t)
                p2 = calct(objs[i+1], t)
                p3 = calct(objs[i+2], t)


    #calculates the interpolation between those points
    #i used methods from this page: http://paulbourke.net/miscellaneous/interpolation/

    if tipo==0:
        #linear
        return intl(objs, i, t, tr)
    elif tipo == 1:
        #natural cubic
        t2 = tr*tr
        a0 = p3-p2-p0+p1
        a1 = p0-p1-a0
        a2 = p2-p0
        a3 = p1
        return a0*tr*t2 + a1*t2+a2*tr+a3
    elif tipo == 2:
        #catmull it seems to be working. ill leave it for now.
        t2 = tr*tr
        a0 = -0.5*p0 +1.5*p1 -1.5*p2 +0.5*p3
        a1 = p0 - 2.5*p1 + 2*p2 -0.5*p3
        a2 = -0.5*p0 + 0.5 *p2
        a3 = p1
        return a0*tr*tr + a1*t2+a2*tr+a3

    elif tipo == 3:
        #hermite
        tr2 = tr*tr
        tr3 = tr2*tr
        m0 = (p1-p0)*(1+bias)*(1-tension)/2
        m0+= (p2-p1)*(1-bias)*(1-tension)/2
        m1 = (p2-p1)*(1+bias)*(1-tension)/2
        m1+= (p3-p2)*(1-bias)*(1-tension)/2
        a0 = 2*tr3 - 3*tr2 + 1
        a1 = tr3 - 2 * tr2+ tr
        a2 = tr3 - tr2
        a3 = -2*tr3 + 3*tr2

        return a0*p1+a1*m0+a2*m1+a3*p2


#handles loft driver expression
#example: loftdriver('Loft', 'BezierCurve;BezierCurve.001;BezierCurve.002', 3)

#name: its the name of the mesh to be driven
#objs: the  names of the curves that drives the mesh
#3 interpolation type

def loftdriver(name, objs, intype):
    #print("ejecutando "+name)
    intype = int(intype)

    tension = 0.0
    bias = 0.5
    #if the loft object still exists proceed normal
    try:
        resobj = bpy.data.objects[name]
        spans = resobj["spans"]
        steps = resobj["steps"]
        if intype==3: #hermite
            tension = resobj['tension']
            bias = resobj['bias']

    #if not delete the driver
    except:
        curve = bpy.context.object
        for it in curve.keys():
            if it == "driver":
                curve.driver_remove('["driver"]')
        return False

    objs = objs.split(";")
    #objs = objs[0:-1]


    #retrieves the curves from the objs string
    for i, l in enumerate(objs):
        objs[i] = bpy.data.objects[l]



    #calcs the new vertices coordinates if we change the curves.
    vxs = loft(objs, steps, spans, intype, tension, bias)

    #apply the new cordinates to the loft object
    me = resobj.data

    for i in range(0, len(me.vertices)):
        me.vertices[i].co = vxs[i]
    me.update()
    return spans

#NOTES:
#loftdriver function will fail or produce weird results if:
#the user changes resobj["spans"] or resobj["steps"]
#if we delete any vertex from the loft object

### TODO:check if thats the case to remove the drivers

#creates the drivers expressions for each curve
def createloftdriver(objs, res, intype):

    line = ""
    for obj in objs:
        line+=obj.name+";"
    line=line[0:-1]
    name = res.name

    interp = str(intype)

    for obj in objs:
        obj["driver"] = 1.0

        obj.driver_add('["driver"]')
        obj.animation_data.drivers[0].driver.expression = "loftdriver('"+ name +"', '" + line + "', "+interp+")"


    ### creating this driver will execute loft all the time without reason,
    #and if i cant drive the mesh i cannot implement live tension and bias

#   res['driver'] = 1.0
#   if res.animation_data==None:
#       res.animation_data_create()
#   res.driver_add('["driver"]')
#   res.animation_data.drivers[0].driver.expression = "loftdriver('"+ name +"', '" + line + "', "+interp+")"

#calculates the vertices position of the loft object
def loft(objs, steps, spans, interpolation=1, tension=0.0, bias=0.5):
    verts=[]

    for i in range(0, len(objs)):

        for j in range(0,steps+1):
            t = 1.0*j/steps
            verts.append(calct(objs[i], t))

        temp2=[]
        if i<len(objs)-1:
            for l in range(1, spans):
                tr = 1.0*l/spans
                for k in range(0, steps+1):
                    t=1.0*k/steps
                    if interpolation:
                        pos = intc(objs, i, t, tr, interpolation, tension, bias)
                    else:
                        pos = intl(objs,i, t, tr)

                    temp2.append(pos)
            verts.extend(temp2)
    return verts


#loft operator

class LoftOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.loft_operator"
    bl_label = "Loft between bezier curves"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        #retrieves the curves in the order they were selected
        objs = bpy.selection

        spans = context.scene.spans
        steps = context.scene.steps

        intype = int(context.scene.intype)

        verts = loft(objs, steps, spans, intype)

        nfaces = steps*spans*(len(objs)-1)
        faces=[]
        for i in range(0, nfaces):
            d = int(i/steps)
            f = [i+d,i+d+1, i+d+steps+2, i+d+steps+1]
            #inverts normals
            #f = [i+d,i+d+steps+1, i+d+steps+2, i+d+1]
            faces.append(f)


        me = bpy.data.meshes.new("Loft")
        me.from_pydata(verts,[], faces)
        me.update()
        newobj = bpy.data.objects.new("Loft", me)
        #newobj.data = me
        scn = context.scene
        scn.objects.link(newobj)
        scn.objects.active = newobj
        newobj.select = True
        bpy.ops.object.shade_smooth()

        #the object stores its own steps and spans
        #this way the driver will know how to deform the mesh
        newobj["steps"] = steps
        newobj["spans"] = spans

        if intype==3:
            newobj['tension'] = context.scene.tension
            newobj['bias'] = context.scene.bias


        if context.scene.dodriver:
            createloftdriver(objs, newobj, intype)

        return {'FINISHED'}

class UpdateFix(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.update_fix"
    bl_label = "Update fix"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        #print("------------")
#       for it in bpy.app.driver_namespace:
#           print(it)
        bpy.app.driver_namespace['loftdriver'] = loftdriver
        bpy.app.driver_namespace['birail1driver'] = birail1driver
        for obj in context.scene.objects:
            if obj.type=="CURVE" and obj.animation_data!=None and len(obj.animation_data.drivers)>0:
                for drv in obj.animation_data.drivers:
                    if drv.data_path=='["driver"]':
                        cad = drv.driver.expression
                        drv.driver.expression = ""
                        drv.driver.expression = cad

        return {'FINISHED'}


#derives a curve at a given parameter
def deriv(curve, t, unit=False):

    a = t + 0.001
    if t==1: a=t-0.001

    pos = calct(curve, t)
    der = (pos-calct(curve, a))/(t-a)
    if unit:
        der = der/der.magnitude
    return der

### BIRAIL1 BLOCK


#see explanation video about the construction
#http://vimeo.com/25455967

#calculates birail vertices

### TODO: when the 3 curves are coplanar it should fail, cause the cross product. check that
def birail1(objs, steps, spans, proportional):

    profile=objs[0]
    ### TODO: identify which path is left or right
    path1 = objs[1]
    path2 = objs[2]

    trans = []

    r0 = [calct(path1,0), calct(path2, 0)]
    r0mag = (r0[1]-r0[0]).magnitude

    for i in range(0, steps):
        u = i/(steps-1)
        appr0 = r0[0]+(r0[1]-r0[0])*u
        trans.append(calct(profile, u)-appr0)

    der10 = deriv(path1, 0)
    der20 = deriv(path2, 0)

    verts = []

    mult = 1.0

    for i in range(0, spans):
        v = i/(spans-1)
        r = [calct(path1, v),calct(path2, v)]
        rmag = (r[1]-r[0]).magnitude

        der1 = deriv(path1, v)
        der2 = deriv(path2, v)

        angle1 = der10.angle(der1)
        angle2 = der20.angle(der2)

        #if angle1!=0.0 and angle2!=0: we can avoid some operations by doing this check but im lazy
        cr1 = der1.cross(der10)
        rot1 = Matrix().Rotation(-angle1, 3, cr1)

        cr2 = der2.cross(der20)
        rot2 = Matrix().Rotation(-angle2, 3, cr2)

        if proportional:
            mult = rmag/r0mag

        for j in range(0, steps):
            u = j/(steps-1)

            app = r[0]+(r[1]-r[0])*u

            newtr1 = trans[j].copy()
            newtr1.rotate(rot1)

            newtr2 = trans[j].copy()
            newtr2.rotate(rot2)

            r1 = (newtr1-trans[j])*(1-u)
            r2 = (newtr2-trans[j])*(u)

            res = r1+r2+app+mult*trans[j]

            verts.append(res)

    return verts


#same as loft driver
### TODO check if it is registered
def birail1driver(name, objs):

    objs = objs.split(";")
    #objs = objs[0:-1]

    for i, l in enumerate(objs):
        objs[i] = bpy.data.objects[l]

    try:
        resobj = bpy.data.objects[name]
        spans = resobj["spans"]
        steps = resobj["steps"]
        prop = resobj["prop"]

    except:
        curve = bpy.context.object
        curve.driver_remove('["driver"]')
        return False

    vxs = birail1(objs, steps, spans, prop)

    me = resobj.data

    for i in range(0, len(me.vertices)):
        me.vertices[i].co = vxs[i]
    me.update()
    return spans

def createbirail1driver(objs, res):

    line = ""
    for obj in objs:
        line+=obj.name+";"
    line=line[0:-1]
    for obj in objs:
        obj["driver"] = 1.0
        obj.driver_add('["driver"]')
        obj.animation_data.drivers[0].driver.expression = "birail1driver('"+ res.name +"', '" + line + "')"

### TODO: check polls and if initial variables are ok to perform the birail
class Birail1Operator(bpy.types.Operator):

    bl_idname = "mesh.birail1_operator"
    bl_label = "Birail between 3 bezier curves"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):

        objs = bpy.selection

        if len(objs)!=3:
            self.report({'ERROR'},"Please select 3 curves")
            return {'FINISHED'}

        scn = context.scene
        spans = scn.spans
        steps = scn.steps
        prop = scn.proportional

        verts = birail1(objs, steps, spans, prop)

        if verts!=[]:
            faces=[]

            nfaces = (steps-1)*(spans-1)

            for i in range(0, nfaces):
                d = int(i/(steps-1))
                f = [i+d+1, i+d, i+d+steps, i+d+steps+1 ]
                faces.append(f)

            me = bpy.data.meshes.new("Birail")
            me.from_pydata(verts,[], faces)
            me.update()
            newobj = bpy.data.objects.new("Birail", me)
            newobj.data = me

            scn.objects.link(newobj)
            scn.objects.active = newobj
            newobj.select = True
            bpy.ops.object.shade_smooth()
            newobj['steps']=steps
            newobj['spans']=spans
            newobj['prop']=prop

            if scn.dodriver:
                createbirail1driver(objs, newobj)

        return {'FINISHED'}

#register the drivers
bpy.app.driver_namespace['loftdriver'] = loftdriver
bpy.app.driver_namespace['birail1driver'] = birail1driver

### MERGE SPLINES BLOCK

#reads spline points
#spl spline to read
#rev reads the spline forward or backwards
def readspline(spl, rev=0):
    res = []

    if spl.type=="BEZIER":
        points = spl.bezier_points
        for p in points:
            if rev:
                h2 = p.handle_left
                h1 = p.handle_right
                h2type = p.handle_left_type
                h1type = p.handle_right_type
            else:
                h1 = p.handle_left
                h2 = p.handle_right
                h1type = p.handle_left_type
                h2type = p.handle_right_type

            co = p.co
            res.append([h1, co, h2, h1type, h2type])
    if rev:
        res.reverse()

    return res

#returns a new merged spline
#cu curve object
#pts1 points from the first spline
#pts2 points from the second spline

def merge(cu, pts1, pts2):
    newspl = cu.data.splines.new(type="BEZIER")
    for i, p in enumerate(pts1):

        if i>0: newspl.bezier_points.add()
        newspl.bezier_points[i].handle_left = p[0]
        newspl.bezier_points[i].co = p[1]
        newspl.bezier_points[i].handle_right = p[2]
        newspl.bezier_points[i].handle_left_type = p[3]
        newspl.bezier_points[i].handle_right_type = p[4]

    newspl.bezier_points[-1].handle_right_type="FREE"
    newspl.bezier_points[-1].handle_left_type="FREE"

    newspl.bezier_points[-1].handle_right = pts2[0][2]


    for j in range(1, len(pts2)):

        newspl.bezier_points.add()
        newspl.bezier_points[-1].handle_left = pts2[j][0]
        newspl.bezier_points[-1].co = pts2[j][1]
        newspl.bezier_points[-1].handle_right = pts2[j][2]
        newspl.bezier_points[-1].handle_left_type = pts2[j][3]
        newspl.bezier_points[-1].handle_right_type = pts2[j][4]

    return newspl

#looks if the splines first and last points are close to another spline
### TODO: Check if the objects selected are valid
### if possible implement nurbs

class MergeSplinesOperator(bpy.types.Operator):

    bl_idname = "curve.merge_splines"
    bl_label = "Merges spline points inside a limit"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        curves = []
        limit = context.scene.limit
        print("merguing")
        for obj in context.selected_objects:
            if obj.type=="CURVE":
                curves.append(obj)

        for cu in curves:
            splines = []
            for spl in cu.data.splines:
                splines.append(spl)
            print(splines)
            #compares all the splines inside a curve object
            for spl1 in splines:
                for spl2 in splines:
                    print(spl1, spl2)
                    if spl1!=spl2 and spl1.type==spl2.type=="BEZIER" and spl1.use_cyclic_u==spl2.use_cyclic_u==False:
                        print("not cyclic")
                        if len(spl1.bezier_points)>1  and len(spl2.bezier_points)>1:

                            #edges of the 2 splines
                            p1i = spl1.bezier_points[0].co
                            p1f = spl1.bezier_points[-1].co
                            p2i = spl2.bezier_points[0].co
                            p2f = spl2.bezier_points[-1].co

                            if dist(p1i, p2i)<limit:
                                print("join p1i p2i")

                                p1 = readspline(spl2, 1)
                                p2 = readspline(spl1)
                                res=merge(cu, p1, p2)
                                cu.data.splines.remove(spl1)
                                cu.data.splines.remove(spl2)
                                splines.append(res)
                                break
                            elif dist(p1i, p2f)<limit:
                                print("join p1i p2f")
                                p1 = readspline(spl2)
                                p2 = readspline(spl1)
                                res = merge(cu, p1, p2)
                                cu.data.splines.remove(spl1)
                                cu.data.splines.remove(spl2)
                                splines.append(res)
                                break
                            elif dist(p1f, p2i)<limit:
                                print("join p1f p2i")
                                p1 = readspline(spl1)
                                p2 = readspline(spl2)
                                res = merge(cu, p1, p2)
                                cu.data.splines.remove(spl1)
                                cu.data.splines.remove(spl2)
                                splines.append(res)
                                break
                            elif dist(p1f, p2f)<limit:
                                print("unir p1f p2f")
                                p1 = readspline(spl1)
                                p2 = readspline(spl2, 1)
                                res = merge(cu, p1, p2)
                                cu.data.splines.remove(spl1)
                                cu.data.splines.remove(spl2)
                                splines.append(res)
                                break

        #splines.remove(spl1)
        return {'FINISHED'}

### NURBS WEIGHTS

class NurbsWeightsPanel(bpy.types.Panel):
    bl_label = "Nurbs Weights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "data"

    @classmethod
    def poll(cls, context):
        if context.active_object != None and context.active_object.type =="CURVE" and context.active_object.data.splines.active!=None and context.active_object.data.splines.active.type=="NURBS":
            return True
        else:
            return False


    def draw(self, context):
        layout = self.layout

        obj = context.object

        for p in obj.data.splines.active.points:
            if p.select:
                row = layout.row()
                row.prop(p,  "weight")

### CUT / SUBDIVIDE CURVE
#obj curve object
#t parameter to perform the cut or split
#method True = subdivide, Flase= Split

def cutcurve(obj, t, method=True):

    #flocal to global transforms or viceversa


    #retrieves the active spline or the first spline if there no one active

    spline=None
    if obj.data.splines.active==None:
        for sp in obj.data.splines:
            if sp.type=="BEZIER":
                spline= sp
                break
    else:
        if obj.data.splines.active.type!="BEZIER":
            return False
        else:
            spline=obj.data.splines.active

    if spline==None: return False

    points = spline.bezier_points
    nsegs = len(points)-1

    #transform global t into local t1
    d = 1.0/nsegs
    seg = int(t/d)
    t1 = t/d-int(t/d)
    if t>=1.0:
        t=1.0
        seg-=1
        t1 = 1.0

    #if t1 is not inside a segment dont perform any action
    if t1>0.0 and t1<1.0:
        mw = obj.matrix_world
        mwi = obj.matrix_world.copy().inverted()

        pts = getbezpoints(spline, mw, seg)

        #position on the curve to perform the action
        pos = calct(obj, t)

        #De Casteljau's algorithm to get the handles
        #http://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm
        h1 = pts[0]+(pts[1]-pts[0])*t1
        h4 = pts[2]+(pts[3]-pts[2])*t1
        r = pts[1]+(pts[2]-pts[1])*t1
        h2 = h1+(r-h1)*t1
        h3 = r+(h4-r)*t1


        if method:
            #SUBDIVIDE
            splp = []
            type = "ALIGNED"
            for i, p in enumerate(points):
                ph1 = p.handle_left*mw
                pco = p.co*mw
                ph2 = p.handle_right*mw
                ph1type = p.handle_left_type
                ph2type = p.handle_right_type
                splp.append([ph1, pco, ph2, ph1type, ph2type])
                p.handle_left_type = type
                p.handle_right_type = type

                if i==seg:
                    splp[-1][2]=h1
                    splp.append([h2, pos, h3, type, type])

                if i==seg+1:
                    splp[-1][0]=h4
                    splp[-1][3]=type
                    splp[-1][4]=type
                #if i dont set all the handles to "FREE"
                #it returns weirds result
                ### TODO: find out how to preserve handle's types

            points.add()
            for i, p in enumerate(points):
                p.handle_left_type = "FREE"
                p.handle_right_type ="FREE"
                p.handle_left = splp[i][0]*mwi
                p.co = splp[i][1]*mwi
                p.handle_right=splp[i][2]*mwi
                p.handle_left_type = splp[i][3]
                p.handle_right_type =splp[i][4]
        else:
            #SPLIT CURVE
            spl1 = []
            spl2 = []
            k=0 #changes to 1 when the first spline is processed
            type = "ALIGNED"
            for i, p in enumerate(points):
                ph1 = p.handle_left*mw
                pco = p.co*mw
                ph2 = p.handle_right*mw
                ph1type = p.handle_left_type
                ph2type = p.handle_right_type
                if k==0:
                    spl1.append([ph1, pco, ph2, ph1type, ph2type])
                else:
                    spl2.append([ph1, pco, ph2, ph1type, ph2type])

                if i==seg:
                    spl1[-1][2]=h1
                    spl1.append([h2, pos, h3, type, type])
                    spl2.append([h2, pos, h3, type, type])
                    k=1

                if i==seg+1:
                    spl2[-1][0]=h4
                    spl2[-1][3]=type
                    spl2[-1][4]=type

            sp1 = obj.data.splines.new(type="BEZIER")
            for i, p in enumerate(spl1):
                if i>0: sp1.bezier_points.add()
                sp1.bezier_points[i].handle_left_type = "FREE"
                sp1.bezier_points[i].handle_right_type ="FREE"
                sp1.bezier_points[i].handle_left = spl1[i][0]*mwi
                sp1.bezier_points[i].co = spl1[i][1]*mwi
                sp1.bezier_points[i].handle_right=spl1[i][2]*mwi
                #i tried to preserve the handles here but
                #didnt work well

                sp1.bezier_points[i].handle_left_type = spl1[i][3]
                sp1.bezier_points[i].handle_right_type =spl1[i][4]

            sp2 = obj.data.splines.new(type="BEZIER")
            for i, p in enumerate(spl2):
                if i>0: sp2.bezier_points.add()
                sp2.bezier_points[i].handle_left_type = "FREE"
                sp2.bezier_points[i].handle_right_type = "FREE"
                sp2.bezier_points[i].handle_left = spl2[i][0]*mwi
                sp2.bezier_points[i].co = spl2[i][1]*mwi
                sp2.bezier_points[i].handle_right=spl2[i][2]*mwi
                sp2.bezier_points[i].handle_left_type = spl2[i][3]
                sp2.bezier_points[i].handle_right_type =spl2[i][4]

            obj.data.splines.remove(spline)

class CutCurveOperator(bpy.types.Operator):
    """Subdivide / Split a bezier curve"""
    bl_idname = "curve.cut_operator"
    bl_label = "Cut curve operator"

    #cut or split
    method = bpy.props.BoolProperty(default=False)
    t = 0.0

    @classmethod
    def poll(self, context):
        if context.active_object!=None:
            return context.active_object.type=="CURVE"
        else:
            return False


    def modal(self, context, event):

        if event.type == 'MOUSEMOVE':
            #full screen width
            #not tested for multiple monitors
            fullw = context.window_manager.windows[0].screen.areas[0].regions[0].width

            self.t = event.mouse_x/fullw

            #limit t to [0,...,1]
            if self.t<0:
                self.t=0.0
            elif self.t>1.0:
                self.t=1.0

            obj = context.object
            pos = calct(obj, self.t)

            #if calct() detects a non bezier spline returns false
            if pos==False:
                return {'CANCELLED'}
            cursor(pos)

        elif event.type == 'LEFTMOUSE':
            #print(self.method, self.t)
            cutcurve(context.object, self.t, self.method)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            #print("Cancelled")

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        if context.object:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}

### CURVE SNAP BLOCK

class AllowCurveSnap(bpy.types.Operator):
    bl_idname = "curve.allow_curve_snap"
    bl_label = "Allow Curve Snap"

    add = bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object!=None

    def execute(self, context):
        add = self.add

        scn = context.scene

        if add==False:
            for helper in context.scene.objects:
                for key  in helper.keys():
                    print(key)
                    if key=="is_snap_helper" and helper[key]==1:
                        scn.objects.unlink(helper)
        else:
            #objs = context.selected_objects
            objs = context.scene.objects
            for obj in objs:
                if obj.type=="CURVE":

                    res = obj.data.resolution_u

                    obj.data.resolution_u = 100

                    me = obj.to_mesh(scene=scn, apply_modifiers=True,settings = "PREVIEW" )
                    obj.data.resolution_u = res
                    newobj = bpy.data.objects.new(obj.name+"_snap", me)
                    scn.objects.link(newobj)
                    newobj.layers = obj.layers
                    newobj.matrix_world = obj.matrix_world
                    newobj["is_snap_helper"]=True
                    newobj.hide_render=True
                    newobj.hide_select = True
                    cons = newobj.constraints.new(type="COPY_TRANSFORMS")
                    cons.target =obj

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator("curve.allow_curve_snap").add=True
    self.layout.operator("curve.allow_curve_snap", text = "Delete Snap Helpers").add=False

### PANEL
class CurvePanel(bpy.types.Panel):
    bl_label = "Curve Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_options = {'REGISTER', 'UNDO'}
    #bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}
    steps = IntProperty(min=2, default = 12)

    @classmethod
    def poll(cls, context):
        return (context.active_object != None) and (context.active_object.type=="CURVE")
    def draw(self, context):
        layout = self.layout

        obj = context.object
        scn = context.scene

        align = True
        row = layout.row(align=align)

        row.prop(context.scene, "intype", text = "")
        row.prop(context.scene, "dodriver", text = "Driven")
        if scn.intype=='3': #Hermite interp
            row = layout.row(align=align)
            row.prop(scn, "tension")
            row.prop(scn, "bias")

        row = layout.row(align=align)
        row.prop(context.scene, "steps")
        row.prop(context.scene, "spans")
        row = layout.row(align=align)
        row.operator("mesh.loft_operator", text = "Loft")
        row.operator("mesh.update_fix", text = "Update Fix")
        row = layout.row(align=align)
        row.operator("mesh.birail1_operator", text = "Birail 1")
        row.prop(context.scene, "proportional", text = "Proportional")
        row = layout.row(align=align)
        row.operator("curve.arc_length_operator", text = "Calc Length")
        row.prop(context.scene, "clen", text = "")
        row = layout.row(align=align)
        row.operator("curve.merge_splines", text = "Merge")
        row.prop(context.scene,"limit",  text = "Limit")
        row = layout.row(align=align)
        row.operator("curve.cut_operator", text="Subdivide").method=True
        row.operator("curve.cut_operator", text="Split").method=False

#       col1 = row.column()
#       col1.prop(context.scene, "intype", text = "")
#       col1.prop(context.scene, "dodriver", text = "Driven")
#       row = layout.row(align=align)
#       col2 = row.column(align=align)
#       col2.prop(context.scene, "steps")
#       col2.prop(context.scene, "spans")
#       row = layout.row(align=align)
#       row.operator("mesh.loft_operator", text = "Loft")
#       row.operator("mesh.update_fix", text = "Update Fix")
#       row = layout.row(align=align)
#       row.operator("mesh.birail1_operator", text = "Birail 1")
#       row.prop(context.scene, "proportional", text = "Proportional")
#       row = layout.row(align=align)
#       row.operator("curve.arc_length_operator", text = "Calc Length")
#       row.prop(context.scene, "clen", text = "")
#       row = layout.row(align=align)
#       row.operator("curve.merge_splines", text = "Merge")
#       row.prop(context.scene,"limit",  text = "Limit")
#       row = layout.row(align=align)
#       row.operator("curve.cut_operator", text="Subdivide").method=True
#       row.operator("curve.cut_operator", text="Split").method=False

classes = [AllowCurveSnap, Selection, LoftOperator, Birail1Operator,
            ArcLengthOperator, UpdateFix, MergeSplinesOperator, CutCurveOperator, NurbsWeightsPanel, CurvePanel]

bpy.app.driver_namespace['loftdriver'] = loftdriver
bpy.app.driver_namespace['birail1driver'] = birail1driver

def register():

    domenu=1
    for op in dir(bpy.types):
        if op=="CURVE_OT_allow_curve_snap":
            domenu=0
            break
    if domenu:
        bpy.types.VIEW3D_MT_object_specials.append(menu_func)

    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)


if __name__ == "__main__":
    register()

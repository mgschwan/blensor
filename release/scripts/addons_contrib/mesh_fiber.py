
#Fiber Generator V3 - June 5th, 2012
#Created by Alan Dennis (RipSting)
#dennisa@onid.orst.edu
#Updated for 2.6 by Gert De Roost (paleajed)
#_________________________________________________
#Special thanks to Alfredo de Greef (Eeshlo) for
#providing the DyNoise module and the multmat
#and renormal subroutines!!!
#Thanks goes out to Peter De Bock for
#fixing the vertex color problems!!!
#_________________________________________________



#--------------I N F O R M A T I O N--------------
#
#Go to user preferences->addons and navigate to Mesh category
#Enable Fiber addon.  Subpanel will appear in Tools panel.
#
#You must have at least one mesh object selected.
#You may select multiple mesh objects for the script
#to run on.

bl_info = {
    "name": "Fiber",
    "author": "Alan Dennis - Gert De Roost",
    "version": (3, 1, 0),
    "blender": (2, 6, 4),
    "location": "View3D > Mesh Tools",
    "description": "Generates mesh grass or hair",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=32802",
    "category": "Mesh"}

if "bpy" in locals():
	import imp

import bpy
import bmesh
import os

from math import pow
import string
from mathutils import *
from mathutils.noise import random, hetero_terrain as HTerrain, seed_set as InitNoise



seed = 1
CurVersion = "3"
txtFollowtext = "Follow Normals / Z-Axis"


#Get the current .fib filename
bpy.context.user_preferences.filepaths.use_relative_paths = 0
a = bpy.data.filepath
b = os.path.dirname(a)
a = a.split(os.sep)[len(a.split(os.sep)) -1]
fname = b + os.sep + str(a.split(".")[0]) + ".fib"
fname = fname.replace("//", "")



bpy.types.Scene.txtFile = bpy.props.StringProperty(
		name="Set file",
#		attr="custompath",# this a variable that will set or get from the scene
		description="",
		maxlen= 1024,
		subtype='FILE_PATH',
		default= fname)
	
bpy.types.Scene.txtFaces = bpy.props.StringProperty(
		name="",
		description="",
		maxlen= 1024,
		default= "")


bpy.types.Scene.chkPointed = bpy.props.BoolProperty(
		name = "Pointed", 
		description = "Pointed?",
		default = False)
	
bpy.types.Scene.chkVCol = bpy.props.BoolProperty(
		name = "Use VCol", 
		description = "Use VCol?",
		default = False)
	
bpy.types.Scene.chkWind = bpy.props.BoolProperty(
		name = "Use Wind", 
		description = "Use Wind?",
		default = False)
	
bpy.types.Scene.chkGuides = bpy.props.BoolProperty(
		name = "Use Guides", 
		description = "Use Guides?",
		default = False)



bpy.types.Scene.sldDensity = bpy.props.FloatProperty(
		name = "Density", 
		description = "Enter density",
		default = 5,
		min = 0,
		max = 50)

bpy.types.Scene.sldSegments = bpy.props.IntProperty(
		name = "Segments", 
		description = "Enter segments",
		default = 3,
		min = 1,
		max = 20)

bpy.types.Scene.sldLength = bpy.props.FloatProperty(
		name = "Length of Segment", 
		description = "Enter segment length",
		default = 5,
		min = 0,
		max = 50)

bpy.types.Scene.sldSegRand = bpy.props.FloatProperty(
		name = "Randomize Length %", 
		description = "Enter Randomize Length %",
		default = 0,
		min = 0,
		max = 1.0)

bpy.types.Scene.sldWidth = bpy.props.FloatProperty(
		name = "Width", 
		description = "Enter Width",
		default = 3,
		min = 0,
		max = 20)

bpy.types.Scene.sldGravity = bpy.props.FloatProperty(
		name = "Gravity", 
		description = "Enter Gravity",
		default = 2,
		min = 0,
		max = 20)

bpy.types.Scene.sldInit = bpy.props.FloatProperty(
		name = "Initial Gravity", 
		description = "Enter Initial Gravity",
		default = 0,
		min = 0,
		max = 50)

bpy.types.Scene.sldRand = bpy.props.FloatProperty(
		name = "Randomize Direction", 
		description = "Enter Randomize Direction",
		default = 5,
		min = 0,
		max = 50)

bpy.types.Scene.sldRloc = bpy.props.FloatProperty(
		name = "Frizziness", 
		description = "Enter Frizziness",
		default = 0,
		min = 0,
		max = 50)

bpy.types.Scene.sldFollow = bpy.props.FloatProperty(
		name = "Normals / Clumpiness", 
		description = "Enter Normals / Clumpiness",
		default = 1,
		min = 0,
		max = 1)

bpy.types.Scene.sldFalloff = bpy.props.FloatProperty(
		name = "Clumpiness Falloff", 
		description = "Enter Clumpiness Falloff",
		default = 2,
		min = 0,
		max = 10)

bpy.types.Scene.sldControl = bpy.props.IntProperty(
		name = "Fiber Guides", 
		description = "Enter Fiber Guides",
		default = 10,
		min = 3,
		max = 100)

bpy.types.Scene.sldCtrlSeg = bpy.props.IntProperty(
		name = "Fiber Guide Segments", 
		description = "Enter Fiber Guide Segments",
		default = 4,
		min = 3,
		max = 4)


class FiberPanel(bpy.types.Panel):
	bl_label = "Fiber"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):

		scn = bpy.context.scene
		layout = self.layout
		
		layout.label("Fiber Generator-	Version " + str(CurVersion), icon = 'PLUGIN')
	
		row = layout.row()
		row.operator("fiber.savepreset", text="Save Preset")
		row.operator("fiber.loadpreset", text="Load Preset")
#		row.operator("fiber.exit", text="Exit")
		layout.prop(scn, "txtFile")
		
		layout.prop(scn, "sldDensity")
		layout.prop(scn, "sldSegments")
		layout.prop(scn, "sldLength")
		layout.prop(scn, "sldSegRand")
		layout.prop(scn, "sldWidth")
		layout.prop(scn, "sldGravity")
		layout.prop(scn, "sldInit")
		layout.prop(scn, "sldRand")
		layout.prop(scn, "sldRloc")
		layout.prop(scn, "sldFollow")
		layout.prop(scn, "sldFalloff")
		layout.prop(scn, "sldControl")
	
		row = layout.split(0.8)
		row.prop(scn, "sldCtrlSeg")
		row.operator("fiber.make", text="Make")
		
		row = layout.row()
		row.prop(scn, "chkPointed")
		row.prop(scn, "chkVCol")
		row.prop(scn, "chkWind")
		row.prop(scn, "chkGuides")
	
		row = layout.row()
		row.operator("fiber.estimate", text="Estimate Faces")
		row.prop(scn, "txtFaces")
		row.operator("fiber.create", text="Create")

		updatepars()



class SavePreset(bpy.types.Operator):
	bl_idname = "fiber.savepreset"
	bl_label = ""
	bl_description = "Saves .fib preset"

	def invoke(self, context, event):
		
		scn = bpy.context.scene
		SavePreset(scn.txtFile)

		return {'FINISHED'}

class LoadPreset(bpy.types.Operator):
	bl_idname = "fiber.loadpreset"
	bl_label = ""
	bl_description = "Loads .fib preset"

	def invoke(self, context, event):
		
		scn = bpy.context.scene
		LoadPreset(scn.txtFile)

		return {'FINISHED'}

class Exit(bpy.types.Operator):
	bl_idname = "fiber.exit"
	bl_label = ""
	bl_description = "Exits Fiber"

	def invoke(self, context, event):
		
		pass

		return {'FINISHED'}

class Make(bpy.types.Operator):
	bl_idname = "fiber.make"
	bl_label = ""
	bl_description = "Make fiber guide segments"

	def invoke(self, context, event):
		
		scn = bpy.context.scene
		ControlPoints(scn.sldControl, scn.sldCtrlSeg)

		return {'FINISHED'}

class EstimateFaces(bpy.types.Operator):
	bl_idname = "fiber.estimate"
	bl_label = ""
	bl_description = "Estimate # faces"

	def invoke(self, context, event):
		
		global tempbm, firstrun
		
		scn = bpy.context.scene
		faces = 0
		objects = bpy.context.selected_objects
		mat = adapt(objects[0])
		tempbm = bmesh.new()
		for num in range(len(objects)):
			original = objects[num].data
			bm = bmesh.new()
			bm.from_mesh(original)
			newbm = bmesh.new()
			for fa in bm.faces:
				faces += (int(fncArea(fa,mat) * scn.sldDensity))
		scn.txtFaces = str(faces *2)
		print (str(faces *2) + " faces predicted")

		return {'FINISHED'}

class Create(bpy.types.Operator):
	bl_idname = "fiber.create"
	bl_label = ""
	bl_description = "Create faces"

	def invoke(self, context, event):
		
		RunFiber()

		return {'FINISHED'}



def register():
	bpy.utils.register_module(__name__)


def unregister():
	bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
	register()





#	elif evt == 72: #Use Wind
#		if chkWind.val == 1:
#			try:
#				Wind = Object.Get("Wind")
#				test = Wind.LocY
#			except:
#				Wind = Object.New(Object.Types.EMPTY)
#				Wind.name = "Wind"
#
#				Wind.LocX = 0.0
#				Wind.LocY = 0.0
#				Wind.LocZ = 0.0
#				Wind.RotX = 0.0
#				Wind.RotY = 0.0
#				Wind.RotZ = 0.0


def SavePreset(FName):

	FName = FName.replace("//", "")
	try:
		f = open(FName,'w')
	except:
		message = "unable to save file."
		return
	
	writeln(f,CurVersion)
	
	scn = bpy.context.scene
	writeln(f, scn.sldDensity)
	writeln(f, scn.sldGravity)
	writeln(f, scn.sldSegments)
	writeln(f, scn.sldLength)
	writeln(f, scn.sldWidth)
	writeln(f, scn.sldInit)
	writeln(f, scn.sldRand)
	writeln(f, scn.sldRloc)
	writeln(f, scn.sldFollow)
	writeln(f, scn.sldControl)
	writeln(f, scn.sldCtrlSeg)
	writeln(f, scn.sldSegRand)
	writeln(f, scn.sldFalloff)
		
	if scn.chkPointed:
		writeln(f, "1")
	else:
		writeln(f, "0")
	if scn.chkVCol:
		writeln(f, "1")
	else:
		writeln(f, "0")
	if scn.chkWind:
		writeln(f, "1")
	else:
		writeln(f, "0")
	if scn.chkGuides:
		writeln(f, "1")
	else:
		writeln(f, "0")
	writeln(f,int(random()*1000))
	writeln(f,1) #First Run
	objects = bpy.context.selected_objects
	for z in range(len(objects)):
		writeln(f,objects[z].name)
	f.close()

def LoadPreset(FName):

	global FVersion, seed, firstrun, objects

	FName = FName.replace("//", "")
	try:
		f = open(FName,'r')
	except:
		message = "unable to open preset."
		return
	
	FVersion = readfloat(f)
	
	scn = bpy.context.scene
	scn.sldDensity	= readfloat(f)	
	scn.sldGravity	= readfloat(f)
	scn.sldSegments = readint(f)
	scn.sldLength	= readfloat(f)
	scn.sldWidth	= readfloat(f)
	scn.sldInit		= readfloat(f)
	scn.sldRand		= readfloat(f)
	scn.sldRloc		= readfloat(f)
	scn.sldFollow	= readfloat(f)
	scn.sldControl	= readfloat(f)
	scn.sldCtrlSeg	= readfloat(f)
	scn.sldSegRand	= readfloat(f)
	scn.sldFalloff	= readfloat(f)
		
	scn.chkPointed	= readint(f)
	scn.chkVCol		= readint(f)
	scn.chkWind		= readint(f)
	scn.chkGuides	= readint(f)
	seed		= readint(f)
	firstrun	= readint(f)
	
	objects = []
	#Load object list
	while 0==0:
		item = readstr(f)
		if len(item) > 0:
			objects.append(bpy.data.objects.get(item))
		else:
			break

	f.close()
	InitNoise(seed)
	updatepars()


def updatepars():
	
	global d, grav2, s, l2, w, n, FVersion
	global r, rl, follow, ctrl, CtrlSeg, SegRnd, Ff
	global pointed, UseVCol, UseWind, UseGuides, seed
	global objects
	global firstrun, grav2z, l2z, wz, nz, rz, rlz
	
	scn = bpy.context.scene
	
	d = scn.sldDensity
	grav2z = scn.sldGravity
	grav2 = grav2z / 100.0
	s = scn.sldSegments
	l2z = scn.sldLength
	l2 = l2z / 100.0
	wz = scn.sldWidth
	w = wz / 100.0
	nz = scn.sldInit
	n = nz / 100.0
	rz = scn.sldRand
	r = rz / 10.0
	rlz = scn.sldRloc
	rl = rlz / 100.0
	follow = scn.sldFollow
	ctrl = scn.sldControl
	CtrlSeg = scn.sldCtrlSeg
	SegRnd = scn.sldSegRand
	Ff = scn.sldFalloff
	
	pointed = scn.chkPointed
	UseVCol = scn.chkVCol
	UseWind = scn.chkWind
	UseGuides = scn.chkGuides

	

def readint(f):
	return int(f.readline())

def readfloat(f):
	return float(f.readline())

def readstr(f):
	s = (f.readline())
	return s.strip()

def writeln(f,x):
  f.write(str(x))
  f.write("\n")

 
	
def fncArea(f, mat):
	#_______________________________________________________
	#Finds the area of a face with global coordinates
	#Updated v1.4 to include matrix calculations (DUH!!!)
	#Parameters: f=bmesh face, mat = bmesh matrix
	#_______________________________________________________
	if len(f.verts) > 2:
		
		v1 = multmat(mat, f.verts[0])
		v2 = multmat(mat, f.verts[1])
		v3 = multmat(mat, f.verts[2])

		adist = pow(pow(v1.co[0] - v2.co[0],2)+ pow(v1.co[1] - v2.co[1],2)+ pow(v1.co[2] - v2.co[2],2),.5)
		bdist = pow(pow(v2.co[0] - v3.co[0],2)+ pow(v2.co[1] - v3.co[1],2)+ pow(v2.co[2] - v3.co[2],2),.5)
		cdist = pow(pow(v3.co[0] - v1.co[0],2)+ pow(v3.co[1] - v1.co[1],2)+ pow(v3.co[2] - v1.co[2],2),.5)	
	
		semi = (adist+bdist+cdist)/2
		area = pow(semi*(semi-adist)*(semi-bdist)*(semi-cdist),.5)

		if len(f.verts) == 4:
			v4 = multmat(mat,f.verts[3])
			adist = pow(pow(v1.co[0] - v3.co[0],2)+ pow(v1.co[1] - v3.co[1],2)+ pow(v1.co[2] - v3.co[2],2),.5)
			bdist = pow(pow(v3.co[0] - v4.co[0],2)+ pow(v3.co[1] - v4.co[1],2)+ pow(v3.co[2] - v4.co[2],2),.5)	
			cdist = pow(pow(v4.co[0] - v1.co[0],2)+ pow(v4.co[1] - v1.co[1],2)+ pow(v4.co[2] - v1.co[2],2),.5)	
	
			semi = (adist+bdist+cdist)/2
			area += pow(semi*(semi-adist)*(semi-bdist)*(semi-cdist),.5)
		return area
	else:
		return 0
def fncdistance(pt1,pt2):
	#_______________________________________________________
	#Returns the distance between two points
	#Parameters: pt1,pt2- 3 point tuples [x,y,z]
	#_______________________________________________________
	return pow(pow(pt1[0]-pt2[0],2)+pow(pt1[1]-pt2[1],2)+pow(pt1[2]-pt2[2],2),.5)

def fncFindWeight(pt1,pt2,pt3):
	#_______________________________________________________
	#Returns the weight between two points and an origin
	#Parameters: pt1,pt2- 3 point tuples [x,y,z]
	#pt3 is the origin
	#_______________________________________________________
	dist = [fncdistance(pt3,pt1),fncdistance(pt3,pt2)]
	return 1- (dist[1] / (dist[0] + dist[1]))

def fncFindWeightedVert(pt1,pt2,weight):
	#_______________________________________________________
	#Returns the weighted coordinates of a vert between two points
	#Parameters: pt1,pt2- 3 point tuples [x,y,z]
	#weight from 0 to 1
	#_______________________________________________________
	movedist = [pt1[0],pt1[2]]
	if pt1[0] - pt2[0] == 0:
		pt1[0] += .01
	slope = (pt1[1] - pt2[1]) / (pt1[0] - pt2[0])
	mult = [pt2[0] - pt1[0], pt2[2] - pt1[2]]
	return ([weight * mult[0] + movedist[0],float(slope * weight + (pt1[1]/mult[0])) * mult[0],weight * mult[1] + movedist[1]])

# need to fix
def multmat(mMatrix,vert):
	#_______________________________________________________
	#Finds the global coordinates of a vertex and takes into
	#consideration parenting and mesh deformation.
	#Parameters: mMatrix = bmesh matrix, vert = bmesh vertex
	#_______________________________________________________
	#Takes a vert and the parent's object matrix 
	x= vert.co[0];	y= vert.co[1]; z= vert.co[2] 
	x1 = (x * mMatrix[0][0]) + (y * mMatrix[1][0]) + (z * mMatrix[2][0]) + mMatrix[3][0] 
	y1 = (x * mMatrix[0][1]) + (y * mMatrix[1][1]) + (z * mMatrix[2][1]) + mMatrix[3][1] 
	z1 = (x * mMatrix[0][2]) + (y * mMatrix[1][2]) + (z * mMatrix[2][2]) + mMatrix[3][2] 

	newV = tempbm.verts.new((x1,y1,z1))
		
	return newV

def vecsub(a,b): 
	#_______________________________________________________
	#Finds a vector from two 3D points
	#Parameters: a,b = bmesh matrix coordinate
	#_______________________________________________________
	return [a[0]-b[0], a[1]-b[1], a[2]-b[2]] 

def renormal(p1,p2,p3):
	#_______________________________________________________
	#Takes three co-planar 3D points and returns the face normal
	#Parameters: p1,p2,p3 = bmesh verts
	#_______________________________________________________  
	norm = [0,0,0] 
	v1 = vecsub(p1.co, p2.co) 
	v2 = vecsub(p1.co, p3.co) 
	norm[0] = v1[1]*v2[2] - v1[2]*v2[1] 
	norm[1] = v1[2]*v2[0] - v1[0]*v2[2] 
	norm[2] = v1[0]*v2[1] - v1[1]*v2[0]

	#keep normals at a distance of 1 unit
	if not(norm[0] == 0 and norm[1] == 0 and norm[2] == 0):
		normaldist = 1/(pow(pow(norm[0],2)+pow(norm[1],2)+pow(norm[2],2),.5))
		for z in range(3):
			norm[z] *= normaldist
	
	return norm

def Bezier3(p1,p2,p3,mu):
	#_________________________________________
	#Three control point Bezier interpolation
	#Parameters: p1 to p3- 3 point tuple [x,y,z]
	#mu ranges from 0 to 1 (start to end of curve) 
	#_________________________________________
	p = [0,0,0]

	mu2 = mu * mu
	mum1 = 1 - mu
	mum12 = mum1 * mum1
	for z in range(3):	
		p[z] = p1[z] * mum12 + 2 * p2[z] * mum1 * mu + p3[z] * mu2

	return(p);

def Bezier4(p1,p2,p3,p4,mu):
	#_________________________________________
	#Four control point Bezier interpolation
	#Parameters: p1 to p4- 3 point tuple [x,y,z]
	#mu ranges from 0 to 1 (start to end of curve) 
	#_________________________________________
	p = [0,0,0]
	mum1 = 1 - mu
	mum13 = mum1 * mum1 * mum1
	mu3 = mu * mu * mu

	for z in range(3):
		p[z] = mum13*p1[z] + 3*mu*mum1*mum1*p2[z] + 3*mu*mu*mum1*p3[z] + mu3*p4[z]
	return(p)

def Bezier(p,mu):
	#_________________________________________
	#General Bezier curve
	#Parameters: p array of points ( etc [[x1,y1,z1],[x2,y2,z2],...] )
	#mu ranges from 0 to 1 (start to end of curve)
	#IMPORTANT, the last point is not computed
	#_________________________________________
	b = [0,0,0]
	n = len(p)
	muk = 1
	munk = pow(1-mu,n)

	
	for k in range(n):	
		nn = n
		kn = k
		nkn = n - k
		blend = muk * munk
		muk *= mu
		munk /= (1-mu)
		while nn >= 1:
			blend *= nn
			nn -=1
			if kn > 1:
				blend /= float(kn)
				kn-=1
			if nkn > 1:
				blend /= float(nkn)
				nkn-=1
		for z in range(3):	  
			b[z] += p[k][z] * blend
	return(b)

def ControlPoints(ctrlnum, CtrlSeg):
	#_______________________________________________________
	#Creates 4 point bezier curves to act as guides for fibers
	#Parameters: ctrlnum- the number of control curves to create
	#_______________________________________________________  
	global mat, grav, tempbm
	grav = 0
	objects = bpy.context.selected_objects
	for num in range(len(objects)):
		i = 0
		original = objects[num].data

		if ctrlnum > len(original.polygons):
			ctnm = len(original.polygons)
		else:
			ctnm = ctrlnum
			
		mat = adapt(objects[num])

		vertex = [0,0,0]
	
		bm = bmesh.new()
		bm.from_mesh(original)
		
		newbm = bmesh.new()
		tempbm = bmesh.new()
		
		for fs in range(0, len(original.polygons), int(len(original.polygons) / ctnm)):
			f = bm.faces[fs]
			
			normal = renormal(multmat(mat, f.verts[0]),multmat(mat, f.verts[1]),multmat(mat, f.verts[2]))
					
			for z in range(3):
				vertex[z] = normal[z]
		
			#centerpoint coordinates
			vertex = [0,0,0]
			for va in f.verts:
				v = multmat(mat, va)
				for z in range(3):
					#z is the coordinate plane (x,y,or z)
					vertex[z] += v.co[z]
			for z in range(3):
				vertex[z] /= len(f.verts)
			
			for z in range(CtrlSeg):
				i += 1
				v =newbm.verts.new((vertex[0] + (z * normal[0]), vertex[1] + (z * normal[1]), vertex[2] + (z * normal[2])))

			for z in range(CtrlSeg-1):
				newbm.edges.new((newbm.verts[i-1-z], newbm.verts[i-2-z]))
	
		GuideMesh = bpy.data.meshes.new(original.name+"_Fiber.C")
		newbm.to_mesh(GuideMesh)
		obj = bpy.data.objects.new(name=original.name+"_Fiber.C", object_data=GuideMesh)
		scene = bpy.context.scene
		scene.objects.link(obj)

def adapt(selobj):
	
	# Rotating / panning / zooming 3D view is handled here.
	# Transform lists of coords to draw.
	if selobj.rotation_mode == "AXIS_ANGLE":
		return
		# How to find the axis WXYZ values ?
		ang =  selobj.rotation_axis_angle
		mat_rotX = Matrix.Rotation(ang, 4, ang)
		mat_rotY = Matrix.Rotation(ang, 4, ang)
		mat_rotZ = Matrix.Rotation(ang, 4, ang)
	elif selobj.rotation_mode == "QUATERNION":
		w, x, y, z = selobj.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		matrix = quat.to_matrix()
		matrix.resize_4x4()
	else:
		ax, ay, az = selobj.rotation_euler
		mat_rotX = Matrix.Rotation(-ax, 4, 'X')
		mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
		mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
	if selobj.rotation_mode == "XYZ":
		matrix = mat_rotX * mat_rotY * mat_rotZ
	elif selobj.rotation_mode == "XZY":
		matrix = mat_rotX * mat_rotZ * mat_rotY
	elif selobj.rotation_mode == "YXZ":
		matrix = mat_rotY * mat_rotX * mat_rotZ
	elif selobj.rotation_mode == "YZX":
		matrix = mat_rotY * mat_rotZ * mat_rotX
	elif selobj.rotation_mode == "ZXY":
		matrix = mat_rotZ * mat_rotX * mat_rotY
	elif selobj.rotation_mode == "ZYX":
		matrix = mat_rotZ * mat_rotY * mat_rotX

	sx, sy, sz = selobj.scale
	mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
	mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
	mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
	matrix = mat_scX * mat_scY * mat_scZ * matrix

	return matrix






def RunFiber():
	#_______________________________________________________
	#The main routine that is called from outside this script
	#Parameters: none- loads settings from .fib file.
	#_______________________________________________________  
	global firstrun, mat, FpF, UseWind, UseGuides, tempbm

	firstrun = 1
	InitNoise(seed)
	print ("\n")
	print ("RipSting's Fiber Generator v3 for 2.6 by Gert De Roost, running on", str(len(bpy.context.selected_objects)), "object(s)")

	
	#____________________________________________________________
	#Extract properties from the empty "Wind" if enabled
	#____________________________________________________________
	if UseWind == 1:
		try:
			Wind = bpy.data.objects.get("Wind")
			Height = Wind.scale[2] / 50.0
			SizeX = Wind.scale[0]
			SizeY = Wind.scale[1]
			DirX = Wind.location[0] / 100.0
			DirY = Wind.location[1] / 100.0
			Falloff = Wind.location[2] /100.0
			Roughness = .5
		except:
			print ("Cannot find an empty named \"wind\": Not using wind engine.")
			UseWind = 0

	#____________________________________________________________
	#Other variable declarations
	#____________________________________________________________

	vertexcount = 0
	objnum = 0

	polycenter = [0,0,0]
	corner1 = [0,0,0]
	corner2 = [0,0,0]
	normal = [0,0,0]
	direc = [0,0,0]
	basevertex = [0,0,0]
	vertex = [0,0,0]
	vertexold = [0,0,0]
	vertexno = [0,0,0]
	randomdir = [0,0,0]
	gravitydir = [0,0,0]
	WindDir = [0,0,0,0] #First two are initial, second two are incremental
	vCorner = [0,0] #Vertex color corners
	vColor1 = [0,0,0]
	vColor2 = [0,0,0]
	aColor = [0,0,0]
	vPercent = [0,0,0]
	addVariables = [0,0,0]
	VcolClump = 1
	
	tempbm = bmesh.new()

	frame = bpy.context.scene.frame_current
	redoFpF = 0
	try:
		test = FpF
	except:
		redoFpF = 1
	#____________________________________________________________
	#Setup Density if not already initialized
	#____________________________________________________________
	if firstrun == 1 or redoFpF == 1:
		print ("Storing fiber information for animation")
		dens = d
		seg = s
		FpF = []
		newbm = bmesh.new()
		objects = bpy.context.selected_objects
		for num in range(len(objects)):
			mat = adapt(objects[num])
			original = objects[num].data
			bm = bmesh.new()
			bm.from_mesh(original)
			for f in bm.faces:
				if len(f.verts) < 3: break
				FpF.append(int(fncArea(f, mat) * d))
			bm.free()
		newbm.free()
	#____________________________________________________________
	
	fnum = -1
	for num in range(len(objects)):
		i=0 #set vertex count to zero
		original = objects[num].data
		origbm = bmesh.new()
		origbm.from_mesh(original)
		
		mat = adapt(objects[num])
		
		meshname = original.name
		if firstrun == 0:
			me = bpy.data.meshes.get(meshname+"_Fiber."+str(objnum))
			newbm.from_mesh(me)
		else:
			me = bpy.data.meshes.new(meshname+"_Fiber."+str(objnum))
		

		#____________________________________________________________
		#Test for fiber guides
		#____________________________________________________________
		if UseGuides == 1:
			try:
				Guides = bpy.data.meshes.get(meshname +"_Fiber.C")
				Gbm =  bmesh.new()
				Gbm.from_mesh(Guides)
				GuideOBJ = bpy.data.objects.get(meshname+"_Fiber.C")
				GMat = adapt(GuideOBJ)
				if (len(Guides.vertices)/CtrlSeg) != int(len(Guides.vertices)/CtrlSeg):
					print ("Uneven number of control points non-divisible by" , CtrlSeg ,"\nPlease re-create fiber guides.")
					print (len(Guides.vertices))
					UseGuides = 0
			except:
				UseGuides = 0
				
		#____________________________________________________________
		for f in origbm.faces:
			
			#Skip over faces with only 2 verts (Edges) v1.3
			if len(f.verts) < 3: break
			
			fnum += 1
		
			p=0
			if UseGuides == 0:
				#____________________________________________________________
				#find normal direction
				#____________________________________________________________	

				normal = renormal(multmat(mat, f.verts[0]),multmat(mat, f.verts[1]),multmat(mat, f.verts[2]))

				#follownormals- 1 = follow, 0 = don't follow
				normal[0] *= follow
				normal[1] *= follow
				normal[2] = (1 - follow) + (normal[2] * follow)
				#____________________________________________________________

			#centerpoint coordinates
			polycenter = [0,0,0]
			for va in f.verts:
				v = multmat(mat, va)
				for z in range(3):
					#z is the coordinate plane (x,y,or z)
					polycenter[z] += v.co[z]
			for z in range(3):
				polycenter[z] /= len(f.verts)
			
			col_lay = origbm.loops.layers.color.active
			if UseVCol == 1 and col_lay != None:
					# colorvalues of centerpoint
					for z in range(len(f.loops)):
						aColor[0] += (f.loops[z][col_lay].r) * 255
						aColor[1] += (f.loops[z][col_lay].g) * 255
						aColor[2] += (f.loops[z][col_lay].b) * 255
					for z in range(3):
						aColor[z] /= len(f.loops)

			for x in range (FpF[fnum]): #loop for density in each poly
				#no need to calculate things if density for face is 0
				if UseVCol == 1 and col_lay != None:
					if (f.loops[0][col_lay].b) * 255 + (f.loops[1][col_lay].b) * 255 + (f.loops[1][col_lay].b) * 255 == 0:
						break

				vertexcount += s*2 + 2
						
				#_____________________________________________________________
				#Find a point on the current face for the fiber to grow out of
				#My logic behind this:
				#pick a random point between the center of the poly and any corner
				#pick a random point between the center and the next corner adjacent to the original
				#pick a random distance between those other two random points
				#This ensures that the blade will actually be on the face
				#____________________________________________________________
				cornernum = int(random() * len(f.verts)) #Pick a random corner
				vCorner[0] = cornernum
				cornernum += 1
				if cornernum > len(f.verts)-1:
					cornernum = 0
				vCorner[1] = cornernum
				#____________________________________________________________
				#Find random location for new fiber on the current face
				#Much simplified randomization speeds process (v1.3)
				#____________________________________________________________
				percent = pow(random(),.5) #optimized V1.3: replaced 14 different random() statements!!!
				vPercent[0] = percent
				vPercent[1] = percent
				
				for z in range(3):
					corner1[z] = (multmat(mat, f.verts[vCorner[0]]).co[z] - polycenter[z]) * percent + polycenter[z]			
				for z in range(3):
					corner2[z] = (multmat(mat, f.verts[vCorner[1]]).co[z] - polycenter[z]) * percent + polycenter[z]
					
				percent = random()
				vPercent[2] = percent
				for z in range(3):
					basevertex[z] = (corner2[z] - corner1[z]) * percent + corner1[z]
				vertex = basevertex
				
				#____________________________________________________________
				#Vertex color Stuff (v1.2)
				#____________________________________________________________
				if UseVCol == 1 and col_lay != None:
					vColor1[0] = (f.loops[vCorner[0]][col_lay].r) * 255
					vColor1[1] = (f.loops[vCorner[0]][col_lay].g) * 255
					vColor1[2] = (f.loops[vCorner[0]][col_lay].b) * 255
					vColor2[0] = (f.loops[vCorner[1]][col_lay].r) * 255
					vColor2[1] = (f.loops[vCorner[1]][col_lay].g) * 255
					vColor2[2] = (f.loops[vCorner[1]][col_lay].b) * 255

					for z in range(2):
						addVariables[z] = ((aColor[z] * (1-vPercent[0])) + (vColor1[z] * vPercent[0]))/2
						addVariables[z] = (addVariables[z] * (1-vPercent[2]) + (((aColor[z] * (1-vPercent[1])) + (vColor2[z] * vPercent[1]))/2) * vPercent[2])/2
					addVariables[2] = (vColor1[2] + vColor2[2])/2
				else:
					#Use these values if no vertex colors are present
					addVariables = [63.75,63.75,255] 
					
				#Green ties into the length of the fibers
				#If Using fiber guides, Green ties into clumpiness
				l = l2 * ((addVariables[1]) / 2)
				VcolClump = 1 #addVariables[1] / 85.0
				#Red ties into the gravity effect on the fibers
				grav = grav2 * ((addVariables[0]) / 5)
				#Blue ties into density...	x is the faces generated so far for the face... v1.3
				FaceDensity = int(FpF[fnum] * addVariables[2]) -1
				#print FaceDensity, x
				if x >= FaceDensity:
					break
			
				#____________________________________________________________
				#Wind
				#____________________________________________________________
				if UseWind == 1:
					WindStrength = ((HTerrain([vertex[0]/SizeX+(frame*DirX), vertex[1]/SizeY+(frame*DirY), frame*Falloff], 1, 1, Height, Roughness) -(Height/2)) * Height)*pow(l,1.5)
				
					#Find Y/X Slope that the wind is blowing at
					if abs(Wind.location[0]) > abs(Wind.location[1]):
						WindDir[0] = (Wind.location[1] / Wind.location[0]) * WindStrength
						WindDir[1] = WindStrength
						if Wind.location[1] < 0:		   
							WindDir[1] = -WindDir[1]
					else:
						WindDir[0] = WindStrength
						if Wind.location[1] == 0:
							Wind.location[1] = .001

						WindDir[1] = (Wind.location[0] / Wind.location[1]) * WindStrength
							
						if Wind.location[0] < 0:
							WindDir[0] = -WindDir[0]
					if Wind.location[1] < 0:
						WindDir[0] = -WindDir[0]
					WindDir[2] = 0
					WindDir[3] = 0

				if UseGuides == 0:
					#____________________________________________________________
					#Normal stuff
					#____________________________________________________________
					for z in range(3):
						vertexno[z] = normal[z] + (r * (random()-.5))	
				#____________________________________________________________
				#Find random direction that the blade is rotated
				#(So that it looks good from all angles, and isn't uniform)
				#____________________________________________________________
				rw= [random() -.5, random() -.5]

				#Find Y/X Slope that the blade is facing
				if abs(rw[0]) > abs(rw[1]):
					direc[0] = (rw[1] / rw[0]) * w
					direc[1] = w
					if rw[1] < 0:
						direc[1] = - direc[1]
				else:
					direc[0] = w
					direc[1] = (rw[0] / rw[1]) * w
					if rw[0] < 0:
						direc[0] = -direc[0]
				#direc[2] = rw
				#____________________________________________________________
				#Start the creation process!
				#____________________________________________________________
				i = i + 2 #increment vertex count
				gravitydir = [0,0,n] #right now I only have gravity working on the Z axis
					
				#____________________________________________________________
				#If the fiber mesh already exists, simply move the verts instead
				#of creating new ones.	Preserves material data.
				#____________________________________________________________
				if firstrun == 0:
					#Move base verts
					for z in range(3):
						#vertex[z] = me.vertices[i-2].co[z]
						me.vertices[i-1].co[z] = vertex[z] + direc[z]
						me.vertices[i-2].co[z] = vertex[z]
				else:	
					#Create base verts
					me.vertices.add(2)
					me.vertices[-1].co = (vertex[0], vertex[1], vertex[2])
					me.vertices[-2].co = (vertex[0] + direc[0], vertex[1] + direc[1], vertex[2] + direc[2])
				
				if UseGuides == 0:
					#____________________________________________________________
					#Normal creation routine with gravity, randomdir, etc.
					#____________________________________________________________
					for y in range (s):
						
						for z in range(3):
							randomdir[z] = (random()-.5) * rl
							vertexold[z] = vertex[z]
					
						WindDir[2] += WindDir[0]
						WindDir[3] += WindDir[1]
						
						gravitydir[2] += grav
						vertex[0] += (vertexno[0]) * l - gravitydir[0] + WindDir[2] + randomdir[0]
						vertex[1] += (vertexno[1]) * l - gravitydir[1] + WindDir[3] + randomdir[1]
						vertex[2] += (vertexno[2]) * l - gravitydir[2] + randomdir[2]
			
						#____________________________________________________________
						#Fix segment length issues with gravity
						#____________________________________________________________	
						distance = pow(pow(vertexold[0] - vertex[0],2)+pow(vertexold[1] - vertex[1],2)+pow(vertexold[2] - vertex[2],2),.5)
						divide = (distance/(l +.001))
						#for z in range(3):
						vertex[0] =	 (vertex[0]-vertexold[0]) / divide + vertexold[0]
						vertex[1] =	 (vertex[1]-vertexold[1]) / divide + vertexold[1]
						vertex[2] =	 (vertex[2]-vertexold[2]) / divide + vertexold[2]
						#____________________________________________________________					

						already = 0
						if pointed == 1 and y == s-1:
							i += 1 #increment vertex count
							if firstrun == 0:
								#Move base verts
								me.vertices[i-1].co[0] = vertex[0]+direc[0]/2
								me.vertices[i-1].co[1] = vertex[1]+direc[1]/2
								me.vertices[i-1].co[2] = vertex[2]+direc[2]/2
							else:	
								#Create base verts
								me.vertices.add(1)
								me.vertices[-1].co = (vertex[0]+direc[0]/2,vertex[1]+direc[1]/2,vertex[2]+direc[2]/2)
						else:
							i += 2 #increment vertex count
							if firstrun == 0:
								#Move base verts
								me.vertices[i-2].co[0] = vertex[0]
								me.vertices[i-2].co[1] = vertex[1]
								me.vertices[i-2].co[2] = vertex[2]
								me.vertices[i-1].co[0] = vertex[0]+direc[0]
								me.vertices[i-1].co[1] = vertex[1]+direc[1]
								me.vertices[i-1].co[2] = vertex[2]+direc[2]
							else:	
								#Create base verts
								me.vertices.add(2)
								me.vertices[-1].co = (vertex[0],vertex[1],vertex[2]+randomdir[2])
								me.vertices[-2].co = (vertex[0]+direc[0],vertex[1]+direc[1],vertex[2]+direc[2])
								already = 1	
								me.tessfaces.add(1)
								face = me.tessfaces[-1]
								face.vertices_raw = (i-4, i-2, i-1, i-3)

								
						if firstrun == 1:
							if not(already):
								me.tessfaces.add(1)
								face = me.tessfaces[-1]
								face.vertices = (i-2, i-1, i-3)

							uv_lay = me.tessface_uv_textures.active
							if uv_lay == None:
								uv_lay = me.tessface_uv_textures.new()

							if uv_lay != None:
								uv_lay.data[face.index].uv1 = (0,float(y)/s)
								if pointed == 1 and y == s-1:
									uv_lay.data[face.index].uv2 = (.5,1)
									uv_lay.data[face.index].uv3 = (1,float(y)/s)
								else:
									uv_lay.data[face.index].uv2 = (0,float(y)/s + (1.0/s))
									uv_lay.data[face.index].uv3 = (1,float(y)/s + (1.0/s))
									uv_lay.data[face.index].uv4 = (1,float(y)/s)
								
				else:
					#____________________________________________________________
					#Use Guides instead of gravity, segment length, etc.	(check) 
					#____________________________________________________________
					Guide = []
					Guide1 = []
					Guide2 = []

					
					GuideOBJ = bpy.data.objects.get(original.name+"_Fiber.C")
					GMat = GuideOBJ.matrix_world
					gv = Gbm.verts

					#____________________________________________________________
					#Find Closest two fiber guides and store them in c[]	(check)
					#____________________________________________________________
					c = [0,CtrlSeg]
					if fncdistance(multmat(GMat, gv[c[1]]).co, basevertex) < fncdistance(multmat(GMat,gv[c[0]]).co, basevertex):
						#Swap
						temp = c[1]
						c[1] = c[0]
						c[0] = temp
					for y in range(CtrlSeg*2,len(gv),CtrlSeg):
						if fncdistance(multmat(GMat,gv[y]).co,basevertex) < fncdistance(multmat(GMat,gv[c[0]]).co,basevertex):
							c[1] = c[0] 
							c[0] = y
						elif fncdistance(multmat(GMat,gv[y]).co,basevertex) < fncdistance(multmat(GMat,gv[c[1]]).co,basevertex):
							c[1] = y

					#____________________________________________________________
					#Get the coordinates of the guides' control points		(check)
					#____________________________________________________________
					Guide0 = []
					for y in range(CtrlSeg):
						Guide1.append ([multmat(GMat,gv[c[0]+y]).co[0],multmat(GMat,gv[c[0]+y]).co[1],multmat(GMat,gv[c[0]+y]).co[2]])
						Guide2.append ([multmat(GMat,gv[c[1]+y]).co[0],multmat(GMat,gv[c[1]+y]).co[1],multmat(GMat,gv[c[1]+y]).co[2]])
					for y in range(len(Guide1)):
						Guide0.append([0,0,0])
						for z in range(3):
							Guide0[y][z] = Guide1[y][z]
					for y in range(1,CtrlSeg):
						for z in range(3):
							Guide1[y][z] -= Guide1[0][z]
							Guide2[y][z] -= Guide2[0][z]

					#____________________________________________________________
					#Determine weight of the two fiber guides ()			(check) 
					#____________________________________________________________
					weight = fncFindWeight(gv[c[0]].co,gv[c[1]].co,vertex)
					#____________________________________________________________
					#Find single, weighted, control fiber					(check)
					#____________________________________________________________
					Guide.append ([0,0,0])
					for y in range(1,CtrlSeg):
						Guide.append (fncFindWeightedVert(Guide1[y],Guide2[y],weight))
					Flen = SegRnd * random()
					#print Guide
					#____________________________________________________________
					#Create the Fiber	
					#____________________________________________________________
					for y in range(1,s):
						#____________________________________________________________
						#Impliment Wind
						#____________________________________________________________
						WindDir[2] += WindDir[0]
						WindDir[3] += WindDir[1]
						for z in range(3):
							randomdir[z] = (random()-.5) * rl
						#____________________________________________________________
						#Use Bezier interpolation
						#____________________________________________________________
						if CtrlSeg == 3:
							v = Bezier3(Guide[0],Guide[1],Guide[2],float(y)/s * (1-Flen))
						elif CtrlSeg == 4:
							v = Bezier4(Guide[0],Guide[1],Guide[2],Guide[3],float(y)/s * (1-Flen))
						else:
							v = Bezier(Guide,float(y)/s * (1-Flen))
						vertex = [v[0]+basevertex[0],v[1]+basevertex[1],v[2]+basevertex[2]]
						
						#____________________________________________________________
						#Clumping
						#____________________________________________________________
						if follow != 0:
							for z in range(1,len(Guide1)):
								Guide1[z] += Guide0
							
							weight = pow(1-((float(y)/s) * (follow * VcolClump)),Ff) #Ff = Clumpiness Falloff
							if CtrlSeg == 3:
								v = Bezier3(Guide0[0],Guide0[1],Guide0[2],float(y)/s * (1-Flen)) #Flen = random fiber length
							elif CtrlSeg == 4:
								v = Bezier4(Guide0[0],Guide0[1],Guide0[2],Guide0[3],float(y)/s * (1-Flen))
							else:
								v = Bezier(Guide0,float(y)/s * (1-Flen))
	
							vertex = fncFindWeightedVert(v, vertex, weight)

						#____________________________________________________________
						#Create Verts & Faces
						#____________________________________________________________
						vertex = [vertex[0]+randomdir[0]+WindDir[2],vertex[1]+randomdir[1]+WindDir[3], vertex[2] + randomdir[2]]
						
						already = 0
						if y == s-1 and pointed == 1:
							i += 1
							if firstrun == 1:
								me.vertices.add(1)
								me.vertices[-1].co = (vertex[0] + direc[0]/2, vertex[1] + direc[1]/2, vertex[2] + direc[2]/2)	
							else:
								me.vertices[i-1].co[0] = vertex[0]+direc[0]/2
								me.vertices[i-1].co[1] = vertex[1]+direc[1]/2
								me.vertices[i-1].co[2] = vertex[2]+direc[2]/2
						else:
							i +=2
							if firstrun == 1:
								me.vertices.add(2)
								me.vertices[-1].co = (vertex[0], vertex[1], vertex[2])
								me.vertices[-2].co = (vertex[0]+direc[0], vertex[1]+direc[1], vertex[2]+direc[2])
								already = 1
								me.tessfaces.add(1)
								face = me.tessfaces[-1]
								face.vertices_raw = (i-4, i-2, i-1, i-3)
							else:
								#Move base verts
								me.vertices[i-2].co[0] = vertex[0]
								me.vertices[i-2].co[1] = vertex[1]
								me.vertices[i-2].co[2] = vertex[2]
								me.vertices[i-1].co[0] = vertex[0]+direc[0]
								me.vertices[i-1].co[1] = vertex[1]+direc[1]
								me.vertices[i-1].co[2] = vertex[2]+direc[2]
							
						if firstrun == 1:
							if not(already):
								me.tessfaces.add(1)
								face = me.tessfaces[-1]
								face.vertices = (i-2, i-1, i-3)
							
							uv_lay = me.tessface_uv_textures.active
							if uv_lay == None:
								uv_lay = me.tessface_uv_textures.new()

							if uv_lay != None:
								uv_lay.data[face.index].uv1 = (0,float(y)/s)
								if pointed == 1 and y == s-1:
									uv_lay.data[face.index].uv2 = (.5,1)
									uv_lay.data[face.index].uv3 = (1,float(y)/s)
								else:
									uv_lay.data[face.index].uv2 = (0,float(y)/s + (1.0/s))
									uv_lay.data[face.index].uv3 = (1,float(y)/s + (1.0/s))
									uv_lay.data[face.index].uv4 = (1,float(y)/s)
		
		me.validate()
		me.update(calc_edges=True, calc_tessface=True)			
		obj = bpy.data.objects.new(name=meshname+"_Fiber."+str(objnum), object_data=me)
		obj.location = objects[num].location
		scene = bpy.context.scene
		scene.objects.link(obj)
		vertexcount = 0 
		
		

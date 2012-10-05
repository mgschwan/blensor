#brik_funcs.py

# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Marcus Jenkins (Blenderartists user name FunkyWyrm)
# Modified by Kees Brouwer (Blenderartists user name Wraaah)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

"""
This will be a collection of useful functions that can be reused across the different operators.

"""

import bpy

#Create a box based on envelope size (easier matching of box to model proportions)
def create_box_bbone(prefix, armature, poseBone):
    #Thanks to Wraaah for this function
    
    ########################
    #INSERT SHAPE CODE HERE#
    
    #Strange looking code as I am referencing the editbone data from the posebone.
    h = poseBone.bone.bbone_x
    w = poseBone.bone.bbone_z
    l = poseBone.bone.length/2.0
    #The bone points along it's y axis so head is -y and tail is +y
    verts = [[h,-l, w],[h,-l,-w],[-h,-l,-w],[-h,-l,w],\
            [h,l,w],[h,l,-w],[-h,l,-w],[-h,l,w]]
    edges = [[0,1],[1,2],[2,3],[3,0],\
            [4,5],[5,6],[6,7],[7,4],\
            [0,4],[1,5],[2,6],[3,7]]
    faces = [[3,2,1,0],[4,5,6,7],[0,4,7,3],[1,5,4,0],[2,6,5,1],[3,7,6,2]]
    
    ########################
    
    #Create the mesh
    mesh = bpy.data.meshes.new(prefix + poseBone.name)
    mesh.from_pydata(verts, edges, faces)
    
    #Create an object for the mesh and link it to the scene
    box = bpy.data.objects.new(prefix + poseBone.name, mesh)
    bpy.context.scene.objects.link(box)
    
    #Move the hit box so that when parented the object centre is at the bone centre
    box.location.y = -poseBone.length/2
    volume = h * l * w * 8.0 
    return(box, volume)
    
#Create a box based on envelope size (easier matching of box to model proportions)
def create_box_envelope(prefix, armature, poseBone):
    ########################
    #INSERT SHAPE CODE HERE#
    
    #Strange looking code as I am referencing the editbone data from the posebone.
    l = poseBone.bone.length/2
    h = poseBone.bone.head_radius
    t = poseBone.bone.tail_radius
    #The bone points along it's y axis so head is -y and tail is +y
    verts = [[h,-l, h],[h,-l,-h],[-h,-l,-h],[-h,-l,h],\
            [t,l,t],[t,l,-t],[-t,l,-t],[-t,l,t]]
    edges = [[0,1],[1,2],[2,3],[3,0],\
            [4,5],[5,6],[6,7],[7,4],\
            [0,4],[1,5],[2,6],[3,7]]
    faces = [[3,2,1,0],[4,5,6,7],[0,4,7,3],[1,5,4,0],[2,6,5,1],[3,7,6,2]]
    
    ########################
    
    #Create the mesh
    mesh = bpy.data.meshes.new(prefix + poseBone.name)
    mesh.from_pydata(verts, edges, faces)
    
    #Create an object for the mesh and link it to the scene
    box = bpy.data.objects.new(prefix + poseBone.name, mesh)
    bpy.context.scene.objects.link(box)
    
    #Move the hit box so that when parented the object centre is at the bone centre
    box.location.y = -poseBone.length/2
    volume = (((2*h)**2 + (2*t)**2)/2) * (2*l)
    return(box, volume)
    
#Create a box based on bone size (manual resizing of bones)
def create_box(prefix, length, width, armature, bone):
    scene = bpy.context.scene
    
    height = bone.length
    #gap = height * self.hit_box_length      #The distance between two boxes
    box_length = bone.length * length
    box_width = bone.length * width
    
    x = box_width/2
    y = box_length/2
    z = box_width/2
    
    verts = [[x,-y,z],[x,-y,-z],[-x,-y,-z],[-x,-y,z],\
             [x,y,z],[x,y,-z],[-x,y,-z],[-x,y,z]]
    edges = [[0,1],[1,2],[2,3],[3,0],\
            [4,5],[5,6],[6,7],[7,4],\
            [0,4],[1,5],[2,6],[3,7]]
    faces = [[3,2,1,0],[4,5,6,7],[0,4,7,3],[1,5,4,0],[2,6,5,1],[3,7,6,2]]
    
    #Create the mesh
    mesh = bpy.data.meshes.new(prefix + bone.name)
    mesh.from_pydata(verts, edges, faces)
    
    #Create an object for the mesh and link it to the scene
    obj = bpy.data.objects.new(prefix + bone.name, mesh)
    scene.objects.link(obj)
    
    volume = x*y*z
    
    return(obj, volume)

#Function to select only the correct bones from an armature
#so only deform bones in the selected bone group(s)
def bone_group_list(armature):
    bones = armature.pose.bones
    scn = bpy.context.scene
    bone_groups = scn.brik_bone_groups
    
    #Check if bone is part of the selected bone group(s)
    bone_list = []
    for bone in bones:
        use_bone = True
        #Check bone group membership
        if bone_groups != "All":
            if bone.bone_group:
                if bone.bone_group.name != bone_groups:
                    use_bone = False
            else:
                use_bone = False
        #Check deform bone
        if bone.bone.use_deform == False:
            use_bone = False
            
        if use_bone == True:
            bone_list = bone_list + [bone]
        
    #Return list of bones to be used
    return bone_list

#Orient the box to the bone and set the box object centre to the bone location
def position_box( armature, bone, box):
    #scene = bpy.context.scene
    
    #Set the box to the bone orientation and location
    box.matrix_world = bone.matrix
    box.location = armature.location + ( bone.bone.head_local + bone.bone.tail_local ) / 2


        
def select_name( name = "", extend = True ):
    if extend == False:
        bpy.ops.object.select_all(action='DESELECT')
    ob = bpy.data.objects.get(name)
    ob.select = True
    bpy.context.scene.objects.active = ob

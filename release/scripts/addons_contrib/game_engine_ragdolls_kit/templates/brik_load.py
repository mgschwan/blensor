#brik_load_0_1.py

# ***** BEGIN MIT LICENSE BLOCK *****
#
#Script Copyright (c) 2010 Marcus P. Jenkins (Blenderartists user name FunkyWyrm)
# Modified by Kees Brouwer (Blenderartists user name Wraaah)
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.
#
# ***** END MIT LICENCE BLOCK *****
# --------------------------------------------------------------------------
"""
This script loads the necessary data from a text file and stores it in the
appropriate locations.

It should run once at the very start of the game/level to avoid issues with
frame rate later on.

This is a load better than my first attempt at parsing a text file, but could
probably still be optimised more.

FOR MULTIPLE RAGDOLLS IN THE SAME SCENE:

The correct armature data fileS need to be loaded at the start of the game.
To do this, the name of the text file in the brik_ragdoll_data controller needs
to be changed so it corresponds with the correct armature.

This needs to be done when brik creates the logic.
A separate spawn point should be created for each new ragdoll structure that is
added to the scene. Each spawn point would load the data for it's corresponding
ragdoll.
    Alternatively, the brik_load.py script should iterate through all ragdoll
    structures and load them in turn.
    
    The spawn point would need a new property that is a list of all ragdoll armatures
    in the scene.
    
    For each ragdoll:
        Set the data controller to use the correct data file.
        Load the data.
    
    This would allow for a single spawn point to load all structure data.
"""
print('###########################')
print('RUNNING brik_load_0_1.py')

import bge
import mathutils
from mathutils import Vector, Quaternion
    
scene = bge.logic.getCurrentScene()
cont = bge.logic.getCurrentController()

objects = scene.objectsInactive

spawn_point = cont.owner

def load_data(data_cont):

    data_file = data_cont.script
    #remove whitespaces
    data_file = data_file.replace(" ", "")
    lines = data_file.splitlines(False)
    
    bone_hitbox = {}
    bone_rigidbody = {}
    bone_loc = {}
    constraint_settings = {}
    constraint_settings["constraint_name"] = ""
    constraints = {}
    
    for line in lines:
        
        if (len(line) == 0) or (line.count("''") != 0):
            #ignore short lines or lines (starting) with ''
            pass
        elif line.count(":") != 0:
            #bone, hitbox, rigidbody link
            items = line.split(":")
            bone_name = items[0]
            bone_hitbox[bone_name] = items[1]
            bone_rigidbody[bone_name] = items[2]
            if len(items) == 4:
                bone_loc[bone_name] = items[3]
            
        elif line.count("=") == 1:
            #Constraint settings
            par, value = line.split("=")
            if par == "constraint_name":
                prev_name = constraint_settings["constraint_name"]
                if prev_name != "":
                    #save previous constraint
                    constraints[prev_name] = constraint_settings
                    
                    constraint_settings = {}
            constraint_settings[par] = value
            
        else:
            #main settings
            armature_name = line
    #save last constraint
    constraints[constraint_settings["constraint_name"]] = constraint_settings

    return bone_hitbox, bone_rigidbody, bone_loc, constraints, armature_name
#    spawn_point['mob_object'] = armature.name
    
def main():
#    mob_total = spawn_point['brik_mob_count']
            
#    for count in range(0, mob_total+1):
    
    for cont in spawn_point.controllers:
#       #if cont.name[:-8] == 'brik_ragdoll_data_'+str(count):
        if cont.name[:] == 'brik_ragdoll_data_0':#removed -8,Wraaah
            data_cont = cont
                
            bone_hitbox, bone_rigidbody, bone_loc, constraints, armature_name = load_data(data_cont)
            armature = objects[armature_name]
            armature["bone_hitbox"] = bone_hitbox
            armature["bone_rigidbody"] = bone_rigidbody
            armature["bone_loc"] = bone_loc
            armature["constraints"] = constraints
        
if __name__ == '__main__':
    main()

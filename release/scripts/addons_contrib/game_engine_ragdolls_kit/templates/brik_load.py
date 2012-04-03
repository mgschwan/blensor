#brik_load_0_1.py

# ***** BEGIN MIT LICENSE BLOCK *****
#
#Script Copyright (c) 2010 Marcus P. Jenkins (Blenderartists user name FunkyWyrm)
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
'''
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
'''
print('###########################')
print('RUNNING brik_load_0_1.py')

import bge
import mathutils
from mathutils import Vector, Quaternion

class Data:
    ARMATURE            = 0
    BASE                = 1
    BONE                = 2

class Arm:
    NAME                = 0

class Base:
    BONE_NAME           = 0
    BOX_NAME            = 1
    JOINT_TARGET_NAME   = 2
    HIT_BOX_NAME        = 3

class Box:
    BONE_NAME           = 0
    BOX_NAME            = 1
    JOINT_TARGET_NAME   = 2
    HIT_BOX_NAME        = 3
    JOINT_POSITION_X    = 4
    JOINT_POSITION_Y    = 5
    JOINT_POSITION_Z    = 6
    ###################################################
    #should no longer need to do this.
    JOINT_LIMIT_MAX_X   = 7
    JOINT_LIMIT_MAX_Y   = 8
    JOINT_LIMIT_MAX_Z   = 9
    JOINT_LIMIT_MIN_X   = 10
    JOINT_LIMIT_MIN_Y   = 11
    JOINT_LIMIT_MIN_Z   = 12
    

scene = bge.logic.getCurrentScene()
cont = bge.logic.getCurrentController()

objects = scene.objectsInactive

spawn_point = cont.owner

def load_data(data_cont):

    data_file = data_cont.script
    #print(data_file)
    bone_dict = {}
    optimal_order = []
    armature_data = []
    bone_data = []
    bone_name = ''
    
    line = ''
    data_count = 0
    item_count = 0
    for char in data_file:
        if not char == '\n':
            line += char
        else:
            if line == "'''":   #Ignore the first and last lines with the triple quote.
                line = ''
            else:
                #Store armature data for later assignment to the armature.
                if data_count == Data.ARMATURE:
                    if not item_count == Arm.NAME:
                        armature_data.append(line)
                        line = ''
                        item_count += 1
                    elif item_count == Arm.NAME:    #The last item for the armature.
                        armature_data.append(line)
                        line = ''
                        item_count = 0
                        data_count += 1
                #Store data for objects associated with the base bone. This is unique
                #since it does not need to deal with a parent.
                elif data_count == Data.BASE:
                    if item_count == Base.BONE_NAME:
                        bone_name = line
                        bone_data.append(line)
                        optimal_order.append(line)
                        line = ''
                        item_count += 1
                    elif not item_count == Base.HIT_BOX_NAME:
                        bone_data.append(line)
                        line = ''
                        item_count += 1
                    elif item_count == Base.HIT_BOX_NAME: #The last item for the base bone.
                        bone_data.append(line)
                        bone_dict[bone_name] = bone_data
                        line = ''
                        bone_name = ''
                        bone_data = []
                        item_count = 0
                        data_count +=1
                #Store data for objects associated with all other bones in turn.
                elif data_count == Data.BONE:
                    if item_count == Box.BONE_NAME:
                        bone_name = line
                        optimal_order.append(line)
                        bone_data.append(line)
                        line = ''
                        item_count += 1
                    elif not item_count == Box.JOINT_LIMIT_MIN_Z:
                        bone_data.append(line)
                        line = ''
                        item_count += 1
                    elif item_count == Box.JOINT_LIMIT_MIN_Z:   #The last item for this bone.
                        bone_data.append(line)
                        bone_dict[bone_name] = bone_data
                        line = ''
                        bone_name = ''
                        bone_data = []
                        item_count = 0
    #Armature data assignment
    armature = objects[armature_data[Arm.NAME]]
    
    armature['optimal_order'] = optimal_order
    armature['bone_box_dict'] = {}
    armature['bone_hit_box_dict'] = {}
    
    #Assignment of bone data and associated objects.
    for key in optimal_order:
        data = bone_dict[key]
        if len(data) == 4:      #The number of data items in the Base class
            box = objects[data[Base.BOX_NAME]]
            box['joint_target'] = data[Base.JOINT_TARGET_NAME]
            box['bone_name'] = data[Base.BONE_NAME]
            box['hit_box_name'] = data[Base.HIT_BOX_NAME]
            hit_box = objects[data[Base.HIT_BOX_NAME]]
            hit_box['bone_name'] = data[Base.BONE_NAME]
            armature['bone_box_dict'][box['bone_name']] = box.name
            armature['bone_hit_box_dict'][box['bone_name']] = hit_box.name
        else:
            box = objects[data[Box.BOX_NAME]]
            box['joint_target'] = data[Box.JOINT_TARGET_NAME]
            box['bone_name'] = data[Box.BONE_NAME]
            box['hit_box_name'] = data[Box.HIT_BOX_NAME]
            box['joint_position'] = [float(data[Box.JOINT_POSITION_X]),\
                                     float(data[Box.JOINT_POSITION_Y]),\
                                     float(data[Box.JOINT_POSITION_Z])]
            #############################################
            #should no longer need to do this
            box['limit_rotation_x'] = [float(data[Box.JOINT_LIMIT_MIN_X]),\
                                       float(data[Box.JOINT_LIMIT_MAX_X])]
            box['limit_rotation_y'] = [float(data[Box.JOINT_LIMIT_MIN_Y]),\
                                       float(data[Box.JOINT_LIMIT_MAX_Y])]
            box['limit_rotation_z'] = [float(data[Box.JOINT_LIMIT_MIN_Z]),\
                                       float(data[Box.JOINT_LIMIT_MAX_Z])]
            
            hit_box = objects[data[Box.HIT_BOX_NAME]]
            hit_box['bone_name'] = data[Box.BONE_NAME]
            armature['bone_box_dict'][box['bone_name']] = box.name
            armature['bone_hit_box_dict'][box['bone_name']] = hit_box.name
        
    #Set the spawn point to spawn this armature.
    spawn_point['mob_object'] = armature.name
    
def main():
    mob_total = spawn_point['brik_mob_count']
            
    for count in range(0, mob_total+1):
    
        for cont in spawn_point.controllers:
            if cont.name[:-8] == 'brik_ragdoll_data_'+str(count):
                data_cont = cont
                
        load_data(data_cont)

if __name__ == '__main__':
    main()

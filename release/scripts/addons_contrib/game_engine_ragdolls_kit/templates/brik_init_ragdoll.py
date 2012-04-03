#brik_init_ragdoll.py

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
This script spawns rigid body objects when ragdoll physics is activated.

It spawns the rigid body objects, turns off the mob collision object's dynamics
and makes the mob collision object 'Ghost'.

    Objects cannot have 'Ghost' toggled from within the game. :(
        
    Mobs can probably be static, ghost anyway. If a mob needs to be dynamic
    then it can be parented to a physics mesh and then the physics mesh can be
    removed from the scene by this script to avoid collision conflicts with
    the rigid bodies.

It then sets the orientation and position to that of the hit boxes and links
the rigid body objects together with rigid body joints.

Rest orientations can be taken from the rigid body objects that remain on the
hidden layer. I thought this would be a problem to set. It's so nice when
something turns out easier than expected for a change. :)
'''
debug = False

import bge

scene = bge.logic.getCurrentScene()

objects = scene.objects
hidden_objects = scene.objectsInactive

'''
NOTE:
    If a collision box is used then this will be the main added object
    that is added and so will have the spawn_point and spawn_id
    properties.
    The collision box would need to be removed here.
    In this case, the spawn_id and spawn_point would need to be copied
    to the armature in order to properly identify which object is to be
    ultimately removed from the scene.
'''

def main():

    '''
    Sensor disabled. Using brik_use_ragdoll 'changed' sensor
    '''
    #sens = spawn_boxes_cont.sensors['brik_spawn_boxes_sens']
    #if sens.getKeyStatus(sens.key) == 1:
    
    init_ragdoll_controller = bge.logic.getCurrentController()
    spawn_boxes_act = init_ragdoll_controller.actuators['brik_spawn_boxes_act']
    
    armature = init_ragdoll_controller.owner
    
    
    #########################
    hidden_armature = hidden_objects[armature.name]
    #########################
    
    
    spawn_point = armature['spawn_point']
    spawn_id = armature['spawn_id']
    
    if armature['brik_use_ragdoll'] and armature['brik_init_ragdoll']:

        print('#########################')
        print('SPAWNING RIGID BODY OBJECTS')
        
        for bone_name in armature['optimal_order']:
            box_name = armature['bone_box_dict'][bone_name]
            print('ADDING '+box_name)
            spawn_boxes_act.object = box_name
            spawn_boxes_act.instantAddObject()
            box = spawn_boxes_act.objectLastCreated
            
            hidden_box = hidden_objects[box_name]
            
            #Since the boxes are added to the armature, it is probably not necessary to store spawn info...
            box['spawn_point'] = spawn_point
            box['spawn_id'] = spawn_id
            
            #Add the box to a dictionary on the armature so it can be located in brik_use_doll_0_3.py
            armature['driver_dict'][box_name] = box
            
            #Set the  drivers to the location and orientation of the hit boxes
            hit_box_name = armature['bone_hit_box_dict'][bone_name]
            hit_box = armature.children[hit_box_name]
            box.worldPosition = hit_box.worldPosition
            box.worldOrientation = hit_box.worldOrientation
            
            '''
            I have absolutely NO idea why these next two lines are necessary...
            Without these lines, object rotation appears to be set to the identity.
            Damned weird stuff. =S
            Update... these lines screw things up in version 35733 but leaving them for now
            '''
            #box.suspendDynamics()
            #box.restoreDynamics()
            
            #Set up the rigid body joints for the newly spawned objects.
            if not box['joint_target'] == 'None':
                #Set up the rigid body joints for the newly spawned objects.
                joint_target = armature['driver_dict'][box['joint_target']]
                box_id = box.getPhysicsId()
                joint_target_id = joint_target.getPhysicsId()
                constraint_type = 12 #6DoF joint
                flag = 128 #No collision with joined object.
                pos = box['joint_position']
                joint_rotation = [0.0, 0.0, 0.0]
                joint = bge.constraints.createConstraint(box_id, joint_target_id, constraint_type, pos[0], pos[1], pos[2], 0.0, 0.0, 0.0, flag)
                #Parameters 3 = limit x rotation, 4 = limit y rotation, 5 = limit z rotation
                joint.setParam(3, *box['limit_rotation_x'])
                joint.setParam(4, *box['limit_rotation_y'])
                joint.setParam(5, *box['limit_rotation_z'])
                
                #Set up the copy rotation bone constraint for this driver
                print('######################')
                print('SETTING UP ROT BONE CONSTRAINTS FOR '+box.name)
                print('BONE NAME '+box['bone_name'])
                constraint_rot = armature.constraints[box['bone_name']+':brik_copy_rot']
                constraint_rot.target = box
            else:
                print('######################')
                print('SETTING UP LOC/ROT BONE CONSTRAINTS FOR '+box.name)
                print('BONE NAME '+box['bone_name'])
                #Set up the copy rotation constraint for this driver
                constraint_rot = armature.constraints[box['bone_name']+':brik_copy_rot']
                constraint_rot.target = box
                print(constraint_rot)
                
                #Set up the copy location constraint for the empty parented to this driver
                copy_loc_target = box.children['brik_'+armature.name+'_loc']
                constraint_loc = armature.constraints[box['bone_name']+':brik_copy_loc']
                constraint_loc.target = copy_loc_target
                print(constraint_loc)
            
            box.worldLinearVelocity = hit_box.worldLinearVelocity
            box.worldAngularVelocity = hit_box.worldAngularVelocity
            
            hit_box.endObject()
            
        for act in armature.actuators:
            #There appears to be no direct way of checking that an actuator is an action actuator.
            #act.type would be nice.
            if hasattr(act, 'action'):
                if not act.name == 'brik_use_act':
                    init_ragdoll_controller.deactivate(act)
                
        #Needed to prevent brik_use_changed_sens second pulse from re-triggering the script.
        armature['brik_init_ragdoll'] = False
            
        if debug == True:
            for bone_name in armature['optimal_order']:
                box_name = armature['bone_box_dict'][bone_name]
                driver = armature['driver_dict'][box_name]
                print(driver.name, driver['spawn_point'], driver['spawn_id'])
    
if __name__ == '__main__':
    main()

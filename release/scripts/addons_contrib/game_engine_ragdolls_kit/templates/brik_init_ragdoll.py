#brik_init_ragdoll.py

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
"""
debug = False

import bge

scene = bge.logic.getCurrentScene()

objects = scene.objects
hidden_objects = scene.objectsInactive

"""
NOTE:
    If a collision box is used then this will be the main added object
    that is added and so will have the spawn_point and spawn_id
    properties.
    The collision box would need to be removed here.
    In this case, the spawn_id and spawn_point would need to be copied
    to the armature in order to properly identify which object is to be
    ultimately removed from the scene.
"""

def main():

    """
    Sensor disabled. Using brik_use_ragdoll 'changed' sensor
    """
    #sens = spawn_boxes_cont.sensors['brik_spawn_boxes_sens']
    #if sens.getKeyStatus(sens.key) == 1:
    
    init_ragdoll_controller = bge.logic.getCurrentController()
    spawn_boxes_act = init_ragdoll_controller.actuators['brik_spawn_boxes_act']
    
    armature = init_ragdoll_controller.owner
    
    
    #########################
#    hidden_armature = hidden_objects[armature.name]
    #########################
    
    
#    spawn_point = armature['spawn_point']
#    spawn_id = armature['spawn_id']
    
    if armature['brik_use_ragdoll'] and armature['brik_init_ragdoll']:

        print('#########################')
        print('SPAWNING RIGID BODY OBJECTS')
        spawn_boxes_act.instantAddObject()
        scene = bge.logic.getCurrentScene()
        objects = scene.objects
        objects.reverse()
        
        #Expand existing group
        group_objects = armature["group"]
        
        group = spawn_boxes_act.object
        for ob in objects:
            group_objects[ob.name] = ob
            ob["pivot"] = armature
            if ob.name == group.name:
                #Stop for loop once group start point is found
                break
                
#        armature_name = spawn_empty["armature_name"]
#        armature = group_objects[ armature_name ]
        armature["group"] = group_objects

        #Set up constraints
        constraints = armature["constraints"]
        for constraint in constraints:
            settings = constraints[constraint]
            constraint_name = settings.get("constraint_name", None)
            print("Create 6DOF constraint")
            print(constraint_name)
            object = group_objects[ settings.get("object", None) ]
            object_id = object.getPhysicsId()
            target = group_objects[ settings.get("target", None) ]
            target_id = target.getPhysicsId()
            print(object)
            print(target)
            
            piv_x = float( settings.get("pivot_x", 0.0) )           
            piv_y = float( settings.get("pivot_y", 0.0) )            
            piv_z = float( settings.get("pivot_z", 0.0) )           

            piv_Rx = float( settings.get("pivot_Rx", 0.0) )           
            piv_Ry = float( settings.get("pivot_Ry", 0.0) )           
            piv_Rz = float( settings.get("pivot_Rz", 0.0) )           
                
            constraint_type = 12 #6DoF joint
            flag = 128 #No collision with joined object.
            joint = bge.constraints.createConstraint(object_id, target_id, constraint_type, piv_x, piv_y, piv_z, piv_Rx, piv_Ry, piv_Rz, flag)
            joint.setParam(0, float( settings.get("x_min", 0.0) ), float( settings.get("x_max", 0.0) ) )
            joint.setParam(1, float( settings.get("y_min", 0.0) ), float( settings.get("y_max", 0.0) ) )
            joint.setParam(2, float( settings.get("z_min", 0.0) ), float( settings.get("z_max", 0.0) ) )
            #Parameters 3 = limit x rotation, 4 = limit y rotation, 5 = limit z rotation
            if settings.get("Rx_min", None):
                joint.setParam(3, float( settings.get("Rx_min", 0.0) ), float( settings.get("Rx_max", 0.0) ) )
            if settings.get("Ry_min", None):
                joint.setParam(4, float( settings.get("Ry_min", 0.0) ), float( settings.get("Ry_max", 0.0) ) )
            if settings.get("Rz_min", None):
                joint.setParam(5, float( settings.get("Rz_min", 0.0) ), float( settings.get("Rz_max", 0.0) ) )
                
            #Translational motor
            #setParam(type, vel, maxForce)
            if settings.get("x_mot", None):
                joint.setParam(6, float( settings.get("x_mot", 0.0) ), float( settings.get("x_mot_max", 999.0) ) )
            if settings.get("y_mot", None):
                joint.setParam(7, float( settings.get("y_mot", 0.0) ), float( settings.get("y_mot_max", 999.0) ) )
            if settings.get("z_mot", None):
                joint.setParam(8, float( settings.get("z_mot", 0.0) ), float( settings.get("z_mot_max", 999.0) ) )
            #Rotational motor
            #setParam(type, angVel, maxForce)
            if settings.get("Rx_mot", None):
                joint.setParam(9, float( settings.get("Rx_mot", 0.0) ), float( settings.get("Rx_mot_max", 999.0) ) )
            if settings.get("Ry_mot", None):
                joint.setParam(10, float( settings.get("Ry_mot", 0.0) ), float( settings.get("Ry_mot_max", 999.0) ) )
            if settings.get("Rz_mot", None):
                joint.setParam(11, float( settings.get("Rz_mot", 0.0) ), float( settings.get("Rz_mot_max", 999.0) ) )

            #Translational spring
            #setParam(type, stiffness, reset)
            if settings.get("x_spring", None):
                joint.setParam(12, float( settings.get("x_spring", 0.0) ), float( settings.get("x_spring_reset", 0) ) )
            if settings.get("y_spring", None):
                joint.setParam(13, float( settings.get("y_spring", 0.0) ), float( settings.get("y_spring_reset", 0) ) )
            if settings.get("z_spring", None):
                joint.setParam(14, float( settings.get("z_spring", 0.0) ), float( settings.get("z_spring_reset", 0) ) )
            #Rotational spring
            #setParam(type, stiffness, reset)
            if settings.get("Rx_spring", None):
                joint.setParam(15, float( settings.get("Rx_spring", 0.0) ), float( settings.get("Rx_spring_reset", 0) ) )
            if settings.get("Ry_spring", None):
                joint.setParam(16, float( settings.get("Ry_spring", 0.0) ), float( settings.get("Ry_spring_reset", 0) ) )
            if settings.get("Rz_spring", None):
                joint.setParam(17, float( settings.get("Rz_spring", 0.0) ), float( settings.get("Rz_spring_reset", 0) ) )
            
            #Store joint in object, can be used to change the parameter settings
            #For example when a joint is broken you can widen the angle rotations
            #Also possible to sever the joint completely but CLEAR THE VARIABLE FIRST
            #BEFORE REMOVING THE JOINT else BGE CRASHES
            object[constraint_name] = joint

        #Copy hitbox positions + remove hitboxes, activate armature constraints
        bone_hitbox = armature["bone_hitbox"] 
        bone_rigidbody = armature["bone_rigidbody"]
        bone_loc = armature["bone_loc"]
        
        for bone_name in bone_hitbox:
            hitbox = group_objects[ bone_hitbox[ bone_name ] ]
            rigidbody = group_objects[ bone_rigidbody[ bone_name ] ]
            
            rigidbody.worldPosition = hitbox.worldPosition
            rigidbody.worldOrientation = hitbox.worldOrientation
            
            #Set up the copy rotation bone constraint for this driver
            print('######################')
            print('SETTING UP ROT BONE CONSTRAINTS FOR '+rigidbody.name)
            print('BONE NAME ' + bone_name)
            constraint_rot = armature.constraints[bone_name+":brik_copy_rot"]
            constraint_rot.target = rigidbody
            constraint_rot.enforce = 1.0
            
            copy_loc_target = bone_loc.get(bone_name, None)
            if copy_loc_target:
                #Set up the copy location constraint 
                constraint_loc = armature.constraints[bone_name+':brik_copy_loc']
                constraint_loc.target = group_objects[ copy_loc_target ]
                constraint_loc.enforce = 1.0
            
            rigidbody.worldLinearVelocity = hitbox.worldLinearVelocity
            rigidbody.worldAngularVelocity = hitbox.worldAngularVelocity
            
            hitbox.endObject()
            
        #for act in armature.actuators:
            #There appears to be no direct way of checking that an actuator is an action actuator.
            #act.type would be nice.
        #    if hasattr(act, 'action'):
        #        if not act.name == 'brik_use_act':
        #            init_ragdoll_controller.deactivate(act)
        #==> Why needed?
        
        #Needed to prevent brik_use_changed_sens second pulse from re-triggering the script.
        armature['brik_init_ragdoll'] = False
            
        #if debug == True:
    
if __name__ == '__main__':
    main()

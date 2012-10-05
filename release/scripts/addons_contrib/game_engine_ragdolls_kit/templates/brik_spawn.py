#brik_spawn_init.py

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

import bge

def initialize():
    spawn_point = bge.logic.getCurrentController().owner
    
    #This is a list of all objects added by this spawn point.
    spawn_point['added_objects'] = []
    
    #This is the total number of objects added by this spawn point.
    #It is used to supply a unique Id to each added object.
    spawn_point['add_count'] = 0
    
def main():

    cont = bge.logic.getCurrentController()
    #Best replace sensor with message?
    sens = cont.sensors['brik_Tab_sens']
    
    if sens.getKeyStatus(sens.key) == 1:
        print('#########################')
        print('SPAWNING MOB AND HIT BOXES')
        
        spawn_act = cont.actuators['brik_spawn_act']
        
        #scene = bge.logic.getCurrentScene()
        #objects = scene.objects
        #hidden_objects = scene.objectsInactive
        
        spawn_empty = cont.owner
        
        #mob_object = hidden_objects[spawn_empty['mob_object']]
        #mob_object = hidden_objects['Armature.001']
        
        #spawn_act.object = mob_object.name
        spawn_act.instantAddObject()
        scene = bge.logic.getCurrentScene()
        objects = scene.objects
        objects.reverse()

        group_objects = {}
        group = spawn_act.object
        for ob in objects:
            group_objects[ob.name] = ob
#            ob["pivot"] = "test_pivot"
            if ob.name == group.name:
                #Stop for loop once group start point is found
                break
                
        armature_name = spawn_empty["armature_name"]
        armature = group_objects[ armature_name ]
        armature["group"] = group_objects
        
        for ob_name in group_objects:
            ob = group_objects[ob_name]
            ob["pivot"] = armature
            
#        last_spawned = spawn_act.objectLastCreated
        #print(dir(last_spawned))
#        spawn_empty['added_objects'].append(last_spawned)
#        spawn_empty['add_count'] += 1
        
        #This is used to identify which spawn point the spawned object was added by.
#        last_spawned['spawn_point'] = spawn_empty.name
        #This is a unique Id used to identify the added object.
#        last_spawned['spawn_id'] = spawn_empty['add_count']
        #This is the dictionary of drivers that are unique to the added object.
        """
        Originally this dictionary was defined in the brik_load.py script, but since
        dictionaries are stored as a reference, and the added objects are copies of the
        hidden object, the added objects had a copy of the reference to the dictionary
        and all used the same dictionary.
        Defining the dictionary after the objects are added to the scene ensures that
        they each have a unique dictionary.
        """
#        last_spawned['driver_dict'] = {}

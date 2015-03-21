import bpy
import math


#def export(filename, fps=24, startframe=0, stopframe=250):
def export(filename, fps=24, frame=0, append=False):
    """
        Export the position and motion data for all, or all selected objects
        for the given framerange.
    """

    mode ="w"
    if append:
        mode = "a+"
    fh = open(filename,mode)

    object_list = bpy.data.objects
    if len(bpy.context.selected_objects) > 0:
        object_list = bpy.context.selected_objects
    
    bpy.context.scene.frame_set(frame)
    #bpy.context.scene.update()
    
    for o in object_list:
        trans = o.matrix_world.to_translation()
        rot = o.matrix_world.to_euler()
        fh.write ("timestamp: %.4f object: %s x: %.10f y: %.10f z: %.10f rx: %.10f ry: %.10f rz: %.10f\n"%(float(frame)/float(fps),
                   o.name, trans.x, trans.y, trans.z, rot.x, rot.y, rot.z))

    fh.close()


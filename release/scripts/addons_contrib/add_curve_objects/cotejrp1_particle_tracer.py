'''# tickertape.py (c) 2011 Phil Cote (cotejrp1)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

"""
How to use:
1.  Set up a scene object with an emitter particle system.
2.  Adjust for the unborn, alive, and dead particle lifecycle.
3.  Advance the timeline til the particles are in the desired position.
4.  MAKE SURE you select the emitter object AFTER you'vbe advanced the timeline.
5.  In the tools menu in the 3D view, click "Make Curve" under the Particle Tracer Panel
6.  Adjust for what kind of what life state of particles to include as well as the curve thickness bevel.
"""

# BUG? : You do have to make sure you select the emitter object AFTER you've
# advanced the timeline.  If you don't, the current frame changes on you 
# when you change the particle tracer options.
'''
bl_info = {
    'name': 'Particle Tracer',
    'author': 'Phil Cote, cotejrp1, (http://www.blenderaddons.com)',
    'version': (0,1),
    "blender": (2, 5, 8),
    "api": 37702,
    'location': '',
    'description': 'Creates curves based on location of particles at a specific point in time.',
    'warning': '', # used for warning icon and text in addons panel
    'category': 'Add Curve'}

import bpy

def getParticleSys( ob ):
    """
    Grab the first particle system available or None if there aren't any.
    """
    if ob == None:
        return None
    
    pSysList = [ mod for mod in ob.modifiers if mod.type == 'PARTICLE_SYSTEM']
    if len( pSysList ) == 0:
        return None
    
    pSys = pSysList[0].particle_system
    return pSys


def buildLocationList( psys, includeAlive, includeDead, includeUnborn ):
    """
    Build a flattened list of locations for each of the particles which the curve creation
    code will act on.
    Which particles get included it dictated by the user choice of any combo of unborn, alive, or dead.
    """
    locList = []
    aliveList = []
    deadList = []
    unbornList = []
    
    def listByAliveState( psys, aliveArg ):
    
        newList = []
        for p in psys.particles:
            if p.alive_state == aliveArg:
                newList.extend( list( p.location ) )
                
        return newList
     
    aliveList = listByAliveState( psys, "ALIVE" )
    deadList = listByAliveState( psys, "DEAD" )
    unbornList = listByAliveState( psys, "UNBORN" )
        
        
    if includeAlive:
        locList = locList + aliveList
    if includeDead:
        locList = locList + deadList
    if includeUnborn:
        locList = locList + unbornList
           
    return locList    
    
    
class PTracerOp(bpy.types.Operator):
    '''Tooltip'''
    bl_idname = "curve.particle_tracer"
    bl_label = "Particle Tracer Options"
    bl_region_type = "VIEW_3D"
    bl_context = "tools"
    bl_options = { "REGISTER", "UNDO" }
    
    curveName = bpy.props.StringProperty( name = "Curve Name", default="ptracecurve" )
    includeAlive = bpy.props.BoolProperty( name="Alive Particles", default=True )
    includeDead = bpy.props.BoolProperty( name = "Dead Particles", default = True )
    includeUnborn = bpy.props.BoolProperty( name="Unborn Particles", default = True )
    thickness = bpy.props.FloatProperty( name = "Thickness", min=0, max=1 )

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if getParticleSys( ob ) == None:
            return False
        return True
    

    def execute(self, context):
        
        ob = context.active_object
        psys = getParticleSys( ob )
        locList = buildLocationList( psys, self.includeAlive, self.includeDead, self.includeUnborn )
        
        crv = bpy.data.curves.new( self.curveName, type="CURVE" )
        spline = crv.splines.new( type="BEZIER" )
        crv.bevel_depth = self.thickness
        
        pointCount = len( locList ) / 3
        if pointCount > 0:
            spline.bezier_points.add( pointCount - 1 )
            
        spline.bezier_points.foreach_set( "co", locList )
        
        for point in spline.bezier_points:
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
       
        scn = context.scene
        crvob = bpy.data.objects.new( self.curveName, crv )
        scn.objects.link( crvob )
        
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(PTracerOp)

def unregister():
    bpy.utils.unregister_class(PTracerOp)

if __name__ == "__main__":
    register()

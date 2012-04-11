'''
# string_it.py (c) 2011 Phil Cote (cotejrp1)
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

bl_info = {
    'name': 'String It',
    'author': 'Phil Cote, cotejrp1, (http://www.blenderpythontutorials.com)',
    'version': (0,1),
    "blender": (2, 5, 8),
    "api": 37702,
    'location': '',
    'description': 'Run a curve through each selected object in a scene.',
    'warning': '', # used for warning icon and text in addons panel
    'category': 'Add Curve'}
'''
import bpy

def makeBezier( spline, vertList ):
    numPoints = ( len( vertList ) / 3 ) - 1
    spline.bezier_points.add( numPoints )
    spline.bezier_points.foreach_set( "co", vertList )
    for point in spline.bezier_points:
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    
def makePoly( spline, vertList ):
    numPoints = ( len( vertList ) / 4 ) - 1
    spline.points.add( numPoints )
    spline.points.foreach_set( "co", vertList )
    

class StringItOperator(bpy.types.Operator):
    '''Creates a curve that runs through the centers of each selected object.'''
    bl_idname = "curve.string_it_operator"
    bl_label = "String It Options"
    bl_options = { "REGISTER", "UNDO" }
    
    splineOptionList = [  ( 'poly', 'poly', 'poly' ), ( 'bezier', 'bezier', 'bezier' ), ]
    splineChoice = bpy.props.EnumProperty( name="Spline Type", items=splineOptionList )
    closeSpline = bpy.props.BoolProperty( name="Close Spline?", default=False )
        
    @classmethod   
    def poll( self, context ):
        totalSelected = len( [ob for ob in context.selectable_objects if ob.select] )
        return totalSelected > 1
    
    def execute(self, context):
        
        splineType = self.splineChoice.upper()
        scn = context.scene
        obList = [ ob for ob in scn.objects if ob.select ]

        # build the vert data set to use to make the curve
        vertList = []
        for sceneOb in obList:
            vertList.append( sceneOb.location.x )
            vertList.append( sceneOb.location.y )
            vertList.append( sceneOb.location.z )
            if splineType == 'POLY':
                vertList.append( 0 )

        # build the curve itself.
        crv = bpy.data.curves.new( "curve", type = "CURVE" )
        crv.splines.new( type = splineType )
        spline = crv.splines[0]
        if splineType == 'BEZIER':
            makeBezier( spline, vertList )
                
        else: #polyline case.
            makePoly( spline, vertList )
        
        spline.use_cyclic_u = self.closeSpline
        
        # add the curve to the scene.
        crvOb = bpy.data.objects.new( "curveOb", crv )
        scn.objects.link( crvOb )            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(StringItOperator)

def unregister():
    bpy.utils.unregister_class(StringItOperator)

if __name__ == "__main__":
    register()

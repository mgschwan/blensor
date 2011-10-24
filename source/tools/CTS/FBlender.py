# Written by Nathan Letwory: Letwory Interactive | Studio Lumikuu
# http://www.letworyinteractive.com/b | http://www.lumikuu.com
# for Blender Foundation

import os.path

import Core.Common.FUtils as FUtils
from Core.Logic.FSettingEntry import *
from Scripts.FApplication import *

class FBlender(FApplication):
    """Presents Blender to the testing framework"""
    
    __SCRIPT_EXTENSION = ".py"
    
    def __init__(self, configDict):
        """__init__() -> FBlender"""
        FApplication.__init__(self, configDict)
        self.__script = None
        self.__blenderScript = None
        self.__currentFilename = None
        self.__currentImageName = None
        self.__currentImportProperName = None
        self.__testImportCount = 0
        self.__testRenderCount = 0
        self.__blenderCommandLine = None
        self.__workingDir = None
    
    def GetPrettyName(self):
        """GetPrettyName() -> str
        
        Implements FApplication.GetPrettyName()
        
        """
        return "Blender 2.59"
    
    def GetSettingsForOperation(self, operation):
        """GetSettingsForOperation(operation) -> list_of_FSettingEntry
        
        Implements FApplication.GetSettingsForOperation()

	TODO: Figure out how we can/should use these, esp. for animation tests
        
        """
        if (operation == IMPORT):
            return []
        elif (operation == EXPORT):
            return []
        elif (operation == RENDER): 
            return []
        else:
            return []
    
    def BeginScript(self, workingDir):
        """BeginScript(workingDir) -> None'
        
        Implements FApplication.BeginScript()
        
        """
        pyFilename = ("script" + str(self.applicationIndex) + 
                FBlender.__SCRIPT_EXTENSION)
        blenderPyFilename = ("blenderScript" + str(self.applicationIndex) + 
                FBlender.__SCRIPT_EXTENSION)
        self.__script = open(os.path.join(workingDir, pyFilename), "w")
        self.__blenderScript = open(os.path.join(workingDir, blenderPyFilename), "w")
        self.WriteCrashDetectBegin(self.__script)

        self.__blenderScript.write(
            """import bpy
import bpy.ops
import sys

import_dae = sys.argv[-1]
export_dae = sys.argv[-3]
default_dae = sys.argv[-4]

print("default .dea for testing: {}\\n".format(default_dae))

print("importing: {}\\n".format(import_dae))
img=sys.argv[-2]
img=img.replace("\\\\", "\\\\\\\\")
bpy.ops.wm.collada_import(filepath=import_dae)
for o in bpy.data.objects:
    print("\\t{}\\n".format(o.name))

if len(bpy.data.cameras)==0:
    print("no camera found, importing {}".format(default_dae))
    bpy.ops.wm.collada_import(filepath=default_dae)
    for o in bpy.data.objects:
        o.select = True if o.name == 'delete_me' else False
    print("cleaning after {} import".format(default_dae))
    bpy.ops.object.delete()

print("making sure we have an active camera... ")
c = None
for o in bpy.data.objects:
    if o.type=='CAMERA' and o.name=='testCamera':
        c = o
        print("...camera set")
if not c:
    print("... ERROR: no camera found!")

bpy.data.scenes[0].camera = c

bpy.data.scenes[0].render.resolution_x = 512
bpy.data.scenes[0].render.resolution_y = 512
bpy.data.scenes[0].render.resolution_percentage = 100
bpy.data.scenes[0].render.use_antialiasing = False
bpy.data.scenes[0].render.alpha_mode = 'STRAIGHT'

bpy.ops.render.render(animation=False, write_still=True)

bpy.ops.wm.collada_export(filepath=export_dae)

print("\\n\\ndone testing.\\n\\n")"""
        )
        
        self.__testImportCount = 0
        self.__testRenderCount = 0
        self.__workingDir = workingDir
    
    def EndScript(self):
        """EndScript() -> None
        
        Implements FApplication.EndScript()
        
        """
        self.__blenderScript.close()
        self.__script.close()
    
    def RunScript(self):
        """RunScript() -> None
        
        Implements FApplication.RunScript()
        
        """
        if (not os.path.isfile(self.configDict["blenderPath"])):
            print "Blender does not exist"
            return True
        
        print ("start running " + os.path.basename(self.__script.name))
        command = ("\"" + self.configDict["pythonExecutable"] + "\" " +
                   "\"" + self.__script.name + "\"")
        
        returnValue = subprocess.call(command)
        
        if (returnValue == 0):
            print "finished running " + os.path.basename(self.__script.name)
        else:
            print "crashed running " + os.path.basename(self.__script.name)
        
        return (returnValue == 0)
    
    def WriteImport(self, filename, logname, outputDir, settings, isAnimated, cameraRig, lightingRig):
        """WriteImport(filename, logname, outputDir, settings, isAnimated, cameraRig, lightingRig) -> list_of_str
                
        """
        outputFormat = ".png"
        
        command = ("\"" + self.configDict["blenderPath"] + "\" --background -noaudio \"" + self.configDict["blenderEmpty"] + "\" -o ")
        
        baseName = FUtils.GetProperFilename(filename)
        self.__currentImportProperName = baseName
        outputFilename = os.path.join(outputDir, baseName + "_out" + ".dae")
        self.__currentFilename = outputFilename
        imageFilename = os.path.join(outputDir, "result" + outputFormat)
        self.__currentImageName = imageFilename
        command = (command + "\"" + imageFilename + "\" --python \"" + self.__blenderScript.name + "\" -- \""+ self.configDict["blenderDefaultDae"] +"\" \"" + outputFilename + "\" \"" + imageFilename + "\" \"" + filename+"\"")
        
        print "***Importing: %s" % (filename)
        print "   Command %s" % (command)        

        self.__blenderCommandLine = command
        
        self.WriteCrashDetect(self.__script, command, logname)
        
        self.__testImportCount = self.__testImportCount + 1
        
        return [os.path.normpath(outputFilename)]
        
    
    def WriteRender(self, logname, outputDir, settings, isAnimated, cameraRig, lightingRig):
        """WriteRender(logname, outputDir, settings, isAnimated, cameraRig, lightingRig) -> list_of_str
        
        Implements FApplication.WriteRender()
        
        """
        print "***Render outputDir: %s" % (outputDir)

        command = self.__blenderCommandLine
        
        print "***Rendering: %s" % (self.__currentImageName)
        print "   Command %s" % (command)        

        self.WriteCrashDetect(self.__script, command, logname)
        
        self.__testRenderCount = self.__testRenderCount + 1        
        return [os.path.normpath(self.__currentImageName),]

    
    def WriteExport(self, logname, outputDir, settings, isAnimated, cameraRig, lightingRig):
        """WriteImport(logname, outputDir, settings, isAnimated, cameraRig, lightingRig) -> list_of_str
        
        Implements FApplication.WriteExport()
        
        """
        print "***Export outputDir: %s" % (outputDir)
        command = self.__blenderCommandLine
        print "   Command %s" % (command)        
        self.WriteCrashDetect(self.__script, command, logname)
        
        return [os.path.normpath(self.__currentFilename)]

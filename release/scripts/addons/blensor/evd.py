import sys
import traceback
import struct

PCL_HEADER = """# .PCD v.7 - Exported by BlenSor
VERSION .7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH %d
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS %d
DATA ascii
"""


frame_counter = 0





WRITER_MODE_EVD = 1
WRITER_MODE_PCL = 2

class evd_file:
    buffer = []
    filename = ""


    def __init__(self, filename):
        self.filename = filename
        self.buffer = []
        self.mode = WRITER_MODE_EVD
        try:
          if self.filename[-4:] == ".pcd":
            self.mode = WRITER_MODE_PCL
            self.filename = self.filename[:-4]
        except:
          pass


    def addEntry(self, timestamp=0.0, yaw=0.0, pitch=0.0, distance=0.0, 
                 distance_noise=0.0, x=0.0, y=0.0, z=0.0,
                 x_noise = 0.0, y_noise = 0.0, z_noise = 0.0, object_id=0, color=(1.0,1.0,1.0)):
        self.buffer.append([timestamp, yaw, pitch, distance,distance_noise,
                       x,y,z,x_noise,y_noise,z_noise,object_id,(int(255*color[0]),int(255*color[1]),int(255*color[2]))])

    def writeEvdFile(self):
        if self.mode == WRITER_MODE_PCL:
          self.writePCLFile()
        else:
          evd = open(self.filename,"w")
          evd.buffer.write(struct.pack("i", len(self.buffer)))

          for e in self.buffer:
              evd.buffer.write(struct.pack("14dQ", float(e[0]),float(e[1]),float(e[2]),float(e[3]),float(e[4]),float(e[5]),float(e[6]),float(e[7]),float(e[8]),float(e[9]),float(e[10]), float(e[12][0]),float(e[12][1]),float(e[12][2]),int(e[11])))
          evd.close()

    def appendEvdFile(self):
        if self.mode == WRITER_MODE_PCL:
          self.writePCLFile()
        else:
          evd = open(self.filename,"a")
          evd.buffer.write(struct.pack("i", len(self.buffer)))
          idx = 0
          for e in self.buffer:
              idx = idx + 1
              evd.buffer.write(struct.pack("14dQ", float(e[0]),float(e[1]),float(e[2]),float(e[3]),float(e[4]),float(e[5]),float(e[6]),float(e[7]),float(e[8]),float(e[9]),float(e[10]), float(e[12][0]),float(e[12][1]),float(e[12][2]),int(e[11])))
          print ("Written: %d entries"%idx)
          evd.close()


    def writePCLFile(self):
      global frame_counter    #Not nice to have it global but it needs to persist
      try:
        pcl = open("%s%05d.pcd"%(self.filename,frame_counter),"w")
        pcl_noisy = open("%s_noisy%05d.pcd"%(self.filename,frame_counter),"w")
        pcl.write(PCL_HEADER%(len(self.buffer),len(self.buffer)))
        pcl_noisy.write(PCL_HEADER%(len(self.buffer),len(self.buffer)))
        idx = 0
        for e in self.buffer:
          idx = idx + 1
          color_uint32 = 0xFF000000 + (e[12][0]<<16) + (e[12][1]<<8) + e[12][2]
          pcl.write("%f %f %f %f\n"%(float(e[5]),float(e[6]),float(e[7]), color_uint32))        
          pcl_noisy.write("%f %f %f %f\n"%(float(e[8]),float(e[9]),float(e[10]), color_uint32))        
        pcl.close()
        pcl_noisy.close()
      except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)





    def finishEvdFile(self):
        evd = open(self.filename,"a")
        evd.buffer.write(struct.pack("i", -1))
        evd.close()


class evd_reader:
  rayIndex = 0
  raysInScan = 0
  fileHandle = None
  def __init__(self, filename):
    self.openEvdFile(filename)

  def openEvdFile(self, filename):
    self.fileHandle = open(filename,"rb")
    
  def getNextRay(self):
    if self.rayIndex >= self.raysInScan:
      data = struct.unpack("i", self.fileHandle.read(4))
      self.raysInScan = data[0]
    ray = struct.unpack("14dQ", self.fileHandle.read(15*8))
    self.rayIndex += 1
    return ray
    

        

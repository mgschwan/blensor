import sys
import traceback
import struct
import math

PCL_HEADER = """# .PCD v.7 - Exported by BlenSor
VERSION .7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH %d
HEIGHT %d
VIEWPOINT 0 0 0 1 0 0 0
POINTS %d
DATA ascii
"""

PCL_HEADER_WITH_LABELS = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z rgb label
SIZE 4 4 4 4 4
TYPE F F F F U
COUNT 1 1 1 1 1
WIDTH %d
HEIGHT %d
VIEWPOINT 0 0 0 1 0 0 0
POINTS %d
DATA ascii
"""



PGM_VALUE_RANGE = 65535

PGM_HEADER ="""P2
#BlenSor output
%d %d
%d
"""

INVALID_POINT = [0.0, 0.0, 0.0, float('NaN'), float('NaN'),
                 float('NaN'),float('NaN'),float('NaN'),float('NaN'),
                 float('NaN'),float('NaN'),-1,(0,0,0),-1]


#Globals (should be removed at some point)
output_labels = True
frame_counter = 0




WRITER_MODE_EVD = 1
WRITER_MODE_PCL = 2
WRITER_MODE_PGM = 3
WRITER_MODE_NUMPY = 4


class evd_file:
    filename = ""
    width  = 0
    height = 0
    max_depth=1.0

    def __init__(self, filename, width=0, height=0, max_depth=1.0):
        self.filename = filename
        self.buffer = []
        self.extension = ""
        self.mode = WRITER_MODE_EVD
        self.output_labels = output_labels
        self.width = width
        self.height = height
        try:
          if self.filename[-4:] == ".pcd":
            self.mode = WRITER_MODE_PCL
            self.filename = self.filename[:-4]
          elif self.filename[-6:] == ".numpy":
            self.mode = WRITER_MODE_NUMPY
            self.filename = self.filename[:-6]
            self.extension = ".numpy"
          elif self.filename[-9:] == ".numpy.gz":
            self.mode = WRITER_MODE_NUMPY
            self.filename = self.filename[:-9]
            self.extension = ".numpy.gz"
          elif self.filename[-4:] == ".pgm":
            if width==0 or height==0:
              raise Exception("Width or Height not set")
            self.image = [0.0]*(width*height)
            self.image_noisy = [0.0]*(width*height)
            self.max_depth=max_depth
            self.mode = WRITER_MODE_PGM
            self.filename = self.filename[:-4]
        except:
          pass

    def fromMesh(self, mesh):
      import bmesh
      bm = bmesh.new()
      bm.from_mesh(mesh)
      bm.verts.ensure_lookup_table()
      
      data_layers = {"timestamp": None,
                     "yaw": None,
                     "pitch": None,
                     "distance": None,
                     "color_red": None, 
                     "color_green": None, 
                     "color_blue": None,
                     "object_id": None, 
                     "point_index": None}


      data = dict.fromkeys(data_layers.keys(), 0.0)

      for i in range(len(bm.verts.layers.float)):
        l = bm.verts.layers.float[i]
        if l.name in data_layers:
              data_layers[l.name] = l
      
      print ("Data layers: %s"%str(data_layers))

      for v in bm.verts:
        (x,y,z) = v.co
        for dk in data_layers.keys():
          if data_layers[dk]:
            data[dk] = v[data_layers[dk]]
        self.addEntry(timestamp=data.get("timestamp",0.0),
                      yaw=data.get("yaw",0.0),
                      pitch=data.get("pitch",0.0),
                      distance=data.get("distance",0.0),
                      x=x,y=y,z=z,
                      object_id=data.get("object_id",0.0),
                      color=(data.get("color_red",0.0),
                             data.get("color_green",0.0),
                             data.get("color_blue",0.0)),
                      idx=data.get("point_index"))

      bm.free()

    def addEntry(self, timestamp=0.0, yaw=0.0, pitch=0.0, distance=0.0, 
                 distance_noise=0.0, x=0.0, y=0.0, z=0.0,
                 x_noise = 0.0, y_noise = 0.0, z_noise = 0.0, object_id=0, color=(1.0,1.0,1.0), idx=0):
        idx = int(idx) #If the index is a numpy.float (from the kinect)
        if self.mode == WRITER_MODE_PGM:
          if idx >=0 and idx < len(self.image):
            self.image[idx]=distance
            self.image_noisy[idx]=distance_noise
        
        
        self.buffer.append([timestamp, yaw, pitch, distance,distance_noise,
                       x,y,z,x_noise,y_noise,z_noise,object_id,int(255*color[0]),int(255*color[1]),int(255*color[2]),idx])

    def writeEvdFile(self):
        if self.mode == WRITER_MODE_PCL:
          self.writePCLFile()
        if self.mode == WRITER_MODE_NUMPY:
              self.writeNUMPYFile()
        elif self.mode == WRITER_MODE_PGM:
          self.writePGMFile()
        else:
          evd = open(self.filename,"w")
          evd.buffer.write(struct.pack("i", len(self.buffer)))
          for e in self.buffer:
              #The evd format does not allow negative object ids
              evd.buffer.write(struct.pack("14dQ", float(e[0]),float(e[1]),float(e[2]),float(e[3]),float(e[4]),float(e[5]),float(e[6]),float(e[7]),float(e[8]),float(e[9]),float(e[10]), float(e[12]),float(e[13]),float(e[14]),max(0,int(e[11]))))
          evd.close()

    def appendEvdFile(self):
        if self.mode == WRITER_MODE_PCL:
          self.writePCLFile()
        if self.mode == WRITER_MODE_NUMPY:
              self.writeNUMPYFile()
        elif self.mode == WRITER_MODE_PGM:
          self.writePGMFile()
        else:
          evd = open(self.filename,"a")
          evd.buffer.write(struct.pack("i", len(self.buffer)))
          idx = 0
          for e in self.buffer:
              #The evd format does not allow negative object ids
              evd.buffer.write(struct.pack("14dQ", float(e[0]),float(e[1]),float(e[2]),float(e[3]),float(e[4]),float(e[5]),float(e[6]),float(e[7]),float(e[8]),float(e[9]),float(e[10]), float(e[12]),float(e[13]),float(e[14]),max(0,int(e[11])))) 
              idx = idx + 1
          print ("Written: %d entries"%idx)
          evd.close()
  
    def write_point(self, pcl, pcl_noisy, e, output_labels):
      #Storing color values packed into a single floating point number??? 
      #That is really required by the pcl library!
      color_uint32 = (e[12]<<16) | (e[13]<<8) | (e[14])
      values=struct.unpack("f",struct.pack("I",color_uint32))

      if output_labels:
        pcl.write("%f %f %f %.15e %d\n"%(float(e[5]),float(e[6]),float(e[7]), values[0], int(e[11])))        
        pcl_noisy.write("%f %f %f %.15e %d\n"%(float(e[8]),float(e[9]),float(e[10]), values[0], int(e[11])))        
      else:
        pcl.write("%f %f %f %.15e\n"%(float(e[5]),float(e[6]),float(e[7]), values[0]))        
        pcl_noisy.write("%f %f %f %.15e\n"%(float(e[8]),float(e[9]),float(e[10]), values[0]))        


    def writePCLFile(self):
      global frame_counter    #Not nice to have it global but it needs to persist
      
      sparse_mode = True #Write only valid points
      if self.width == 0 or self.height == 0:
        width=len(self.buffer)
        height = 1
      else:
        sparse_mode = False # Write all points
        width = self.width
        height = self.height
      try:
        pcl = open("%s%05d.pcd"%(self.filename,frame_counter),"w")
        pcl_noisy = open("%s_noisy%05d.pcd"%(self.filename,frame_counter),"w")
        if self.output_labels:
          pcl.write(PCL_HEADER_WITH_LABELS%(width,height,width*height))
          pcl_noisy.write(PCL_HEADER_WITH_LABELS%(width,height,width*height))
        else:
          pcl.write(PCL_HEADER%(width,height,width*height))
          pcl_noisy.write(PCL_HEADER%(width,height,width*height))
        idx = 0
        for e in self.buffer:
          if e[15] > idx and not sparse_mode: # e[15] is the idx of the point
            for i in range(idx, e[15]):
              self.write_point(pcl, pcl_noisy, INVALID_POINT, self.output_labels)
              idx += 1
          
          idx += 1
          self.write_point(pcl, pcl_noisy, e, self.output_labels)
      
        if idx < width*height:
          for i in range(idx, width*height):
            self.write_point(pcl, pcl_noisy, INVALID_POINT, self.output_labels)
      
      
        pcl.close()
        pcl_noisy.close()
      except Exception as e:
        traceback.print_exc()      

    def writeNUMPYFile(self):
      global frame_counter    #Not nice to have it global but it needs to persist
      
      sparse_mode = True #Write only valid points
      if self.width == 0 or self.height == 0:
        width=len(self.buffer)
        height = 1
      else:
        sparse_mode = False # Write all points
        width = self.width
        height = self.height
      try:
        import numpy as np
        data = np.array(self.buffer)
        if not sparse_mode:
          tmp = np.zeros((width*height,data.shape[1]),dtype=np.float64)
          tmp[np.int64(data[:,-1])] = data
          data = tmp
        np.savetxt("%s%05d%s"%(self.filename,frame_counter,self.extension), data)
      except Exception as e:
        traceback.print_exc()      

    def writePGMFile(self):
      global frame_counter    #Not nice to have it global but it needs to persist
      try:
        print ("Writing PGM file %s%05d.pgm"%(self.filename,frame_counter))
        pgm = open("%s%05d.pgm"%(self.filename,frame_counter),"w")
        pgm_noisy = open("%s_noisy%05d.pgm"%(self.filename,frame_counter),"w")
        pgm.write(PGM_HEADER%(self.width,self.height, PGM_VALUE_RANGE))
        pgm_noisy.write(PGM_HEADER%(self.width,self.height, PGM_VALUE_RANGE))
        for val in range(len(self.image)):
          if not math.isnan(self.image[val]):
            ival = int(PGM_VALUE_RANGE*self.image[val]/self.max_depth)
          else:
            ival = 0
          pgm.write("%d\n"%(ival if ival < PGM_VALUE_RANGE else PGM_VALUE_RANGE))
        for val in range(len(self.image_noisy)):
          if not math.isnan(self.image_noisy[val]):
            ival = int(PGM_VALUE_RANGE*self.image_noisy[val]/self.max_depth)
          else:
            ival = 0
          pgm_noisy.write("%d\n"%(ival if ival < PGM_VALUE_RANGE else PGM_VALUE_RANGE))
        
        pgm.close()
        pgm_noisy.close()
      except Exception as e:
        traceback.print_exc()


    def finishEvdFile(self):
        evd = open(self.filename,"a")
        evd.buffer.write(struct.pack("i", -1))
        evd.close()

    def isEmpty(self):
      return (len(self.buffer) == 0)

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
    

        

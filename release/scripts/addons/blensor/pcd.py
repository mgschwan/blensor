fieldnames = ["x","y","z","rgb"]

class PCDObject:
  points = []
  fields = 3  #3D Point
  width = 0
  height = 0 
  def __init__(self, fields, width=0, height=0):
    if fields < 1 or fields > 4:
      raise Exception("Number of fields must be between 1 and 4")
    self.fields = fields
    self.width = width
    self.height = height

  def addPoint(self, point):
    if len(point) == self.fields: 
      self.points.append(point)
    else:
      raise ValueError("Wrong number of fields. Should be %d"%self.fields)

  def save(self,filename):
    fh = open(filename,"wb")
    fh.write("# .PCD v.7 - Point Cloud Data file format\n")
    fh.write("VERSION .7\n")
    fh.write("FIELDS")

    size_str=""
    type_str=""
    count_str=""
    for i in range(self.fields):
      fh.write(" %s"%fieldnames[i])
      size_str+=" 4"
      type_str+=" F"
      count_str+=" 1"
    fh.write("\n")

    fh.write("SIZE %s\n"%size_str)
    fh.write("TYPE %s\n"%type_str)
    fh.write("COUNT %s\n"%count_str)

    if self.width>0:
      fh.write("WIDTH %s\n"%self.width)
    if self.height>0:
      fh.write("HEIGHT %s\n"%self.height)
    fh.write("VIEWPOINT 0 0 0 1 0 0 0\n")
    fh.write("POINTS %d\n"%len(self.points))
    fh.write("DATA ascii\n")
    for p in self.points:
       fh.write("%.10f %.10f %.10f\n"%(p[0],p[1],p[2]))

    fh.close()




#include <iostream>
#include <pcl/io/pcd_io.h>
#include <pcl/point_types.h>
#include <pcl/filters/passthrough.h>
#include <pcl/filters/voxel_grid.h>
#include <string>
#include <cstdio>

using namespace std;


int
 main (int argc, char** argv)
{
  bool binary = false;

  if (argc < 3)
  {
    cout << "Usage: pcd_filter <input-cloud>  <output-cloud> [binary]" << endl;
    return 0; 
  }
  if (argc > 3 && (string(argv[3]) == "binary")) binary = true;

  pcl::PointCloud<pcl::PointXYZRGB> *cloud1(new  pcl::PointCloud<pcl::PointXYZRGB>());
  pcl::PointCloud<pcl::PointXYZRGB>::ConstPtr cloud1_ptr(cloud1);

  pcl::PCDReader reader;
  reader.read(string(argv[1]),*cloud1);
  
  pcl::PCDWriter writer;
  writer.write(string(argv[2]), *cloud1, binary);
  cout << "Finished"<<endl;
  return (0);
}

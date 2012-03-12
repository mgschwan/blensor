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

  if (argc < 4)
  {
    cout << "Usage: pcd_filter <input-cloud> <leaf-size (i.e 0.01)> <output-cloud> [binary]" << endl;
    return 0; 
  }
  if (argc > 4 && (string(argv[4]) == "binary")) binary = true;




  pcl::PointCloud<pcl::PointXYZRGB> *cloud1(new  pcl::PointCloud<pcl::PointXYZRGB>());
  pcl::PointCloud<pcl::PointXYZRGB> outputCloud;
  pcl::PointCloud<pcl::PointXYZRGB>::ConstPtr cloud1_ptr(cloud1);



  pcl::PCDReader reader;
  reader.read(string(argv[1]),*cloud1);
  float leafsize = 0.01;
  sscanf(argv[2],"%f",&leafsize);

  pcl::VoxelGrid<pcl::PointXYZRGB> grid;
  grid.setLeafSize(leafsize,leafsize,leafsize);
  grid.setInputCloud(cloud1_ptr);
  grid.filter(outputCloud);

  std::cout << "Cloud size befor/after:  "<<cloud1->size()<<"/"<<outputCloud.size() << std::endl;
  
  pcl::PCDWriter writer;
  cout << "Writing to " << argv[3] << endl;
  writer.write(string(argv[3]), outputCloud, binary);
  cout << "Finished"<<endl;
  return (0);
}

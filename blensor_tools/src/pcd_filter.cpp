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

  pcl::PointCloud<pcl::PointXYZ> *cloud1(new  pcl::PointCloud<pcl::PointXYZ>());
  pcl::PointCloud<pcl::PointXYZ> outputCloud;
  pcl::PointCloud<pcl::PointXYZ>::ConstPtr cloud1_ptr(cloud1);



  pcl::PCDReader reader;
  reader.read(string(argv[1]),*cloud1);
  float leafsize = 0.01;
  sscanf(argv[2],"%f",&leafsize);
  if (string(argv[4]) == "binary") binary = true;

  pcl::VoxelGrid<pcl::PointXYZ> grid;
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

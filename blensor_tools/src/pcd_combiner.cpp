#include <iostream>
#include <pcl/io/pcd_io.h>
#include <pcl/point_types.h>
#include <pcl/filters/passthrough.h>
#include <pcl/filters/voxel_grid.h>
#include <string>

using namespace std;


int
 main (int argc, char** argv)
{
  pcl::PointCloud<pcl::PointXYZ> *cloud1(new  pcl::PointCloud<pcl::PointXYZ>());
  pcl::PointCloud<pcl::PointXYZ> cloud2;
  pcl::PointCloud<pcl::PointXYZ> outputCloud;
  pcl::PointCloud<pcl::PointXYZ>::ConstPtr cloud1_ptr(cloud1);



  pcl::PCDReader reader;
  reader.read(string(argv[1]),*cloud1);
  reader.read(string(argv[2]),cloud2);
 

  *cloud1 += cloud2;

  pcl::VoxelGrid<pcl::PointXYZ> grid;
  grid.setLeafSize(0.01,0.01,0.01);
  grid.setInputCloud(cloud1_ptr);
  grid.filter(outputCloud);


  std::cout << "Cloud size befor/after:  "<<cloud1->size()<<"/"<<outputCloud.size() << std::endl;
  
  pcl::PCDWriter writer;
  cout << "Writing to " << argv[3] << endl;
  writer.write(string(argv[3]), outputCloud, false);
  cout << "Finished"<<endl;
  return (0);
}

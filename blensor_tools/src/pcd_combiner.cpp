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
  if (argc < 4)
  {
    cout << "Usage: pcd_combiner <input-cloud1> <input-cloud1> <output-cloud> [binary]" << endl;
    return 0; 
  }
  


  bool binary = false;



  pcl::PointCloud<pcl::PointXYZRGB> *cloud1(new  pcl::PointCloud<pcl::PointXYZRGB>());
  pcl::PointCloud<pcl::PointXYZRGB> cloud2;
  pcl::PointCloud<pcl::PointXYZRGB> outputCloud;
  pcl::PointCloud<pcl::PointXYZRGB>::ConstPtr cloud1_ptr(cloud1);



  pcl::PCDReader reader;
  reader.read(string(argv[1]),*cloud1);
  reader.read(string(argv[2]),cloud2);
  if (argc > 4)
  {
    if (string(argv[4]) == "binary") binary = true;
  } 


  *cloud1 += cloud2;

  
  pcl::PCDWriter writer;
  cout << "Writing to " << argv[3] << endl;
  writer.write(string(argv[3]), *cloud1, binary);
  cout << "Finished"<<endl;
  return (0);
}

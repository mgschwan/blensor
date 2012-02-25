all: pcd_combiner


pcd_combiner: pcd_combiner.cpp
	g++ -o ../bin/pcd_combiner pcd_combiner.cpp -I /opt/pcl/include/pcl-1.5/ -I /opt/pcl/include/ -I /usr/include/eigen3/ -L /opt/pcl/lib/ -lpcl_common -lpcl_io -lpcl_filters



clean:
	rm ../bin/pcd_combiner

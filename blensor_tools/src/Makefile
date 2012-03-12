all: pcd_combiner pcd_filter



LIBS=`pkg-config pcl_common-1.5 --libs` -lpcl_io -lpcl_filters


CFLAGS=`pkg-config pcl_common-1.5 --cflags`


pcd_combiner: pcd_combiner.cpp
	g++ -o pcd_combiner pcd_combiner.cpp ${CFLAGS} -I /usr/include/eigen3/  ${LIBS}

pcd_filter: pcd_filter.cpp
	g++ -o pcd_filter pcd_filter.cpp ${CFLAGS} -I /usr/include/eigen3/  ${LIBS}




clean:
	rm pcd_combiner
	rm pcd_filter

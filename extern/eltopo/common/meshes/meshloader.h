#ifndef MESH_LOADER_H
#define MESH_LOADER_H

#include "ObjLoader.hpp"

#include <string>
#include <vector>
#include "vec.h"

enum MeshType {DEFAULT, OBJ, PLY};

class MeshFile;

class MeshLoader 
{
   
   MeshFile* mesh;
   
public:
   MeshLoader(const std::string& file_path, MeshType type = DEFAULT);
   ~MeshLoader();

   void get_triangles(std::vector<Vec3ui>& tris) const;
   void get_vertices(std::vector<Vec3d>& verts) const;

private:
   MeshLoader( const MeshLoader& );
   MeshLoader operator=( const MeshLoader& );
   
};

//base class for all mesh formats we want to support
class MeshFile {
public:
   virtual void get_triangles(std::vector<Vec3ui>& tris) const = 0;
   virtual void get_vertices(std::vector<Vec3d>& verts) const = 0;
   virtual ~MeshFile() {}
};

//Alias Wavefront OBJ format, courtesy of Nate Robins glm.h
class ObjFile : public MeshFile {
   GLMmodel* mesh;
public:
   ObjFile(const std::string& file_path);
   ~ObjFile();
   void get_triangles(std::vector<Vec3ui>& tris) const;
   void get_vertices(std::vector<Vec3d>& verts) const;
   
private:
   ObjFile( const ObjFile& );
   ObjFile operator=( const ObjFile& );
};

//UNC/Stanford's PLY format, courtesy of Greg Turk's PLY Tools
/*
class PlyFileData : public MeshFile {
   // Couldn't call it just PlyFile since that name is used by the PLY Tools internally
   std::vector<Vec3ui> stored_tris;
   std::vector<Vec3d> stored_verts;
   
public:
   PlyFileData(const std::string& file_path);
   ~PlyFileData();
   void get_triangles(std::vector<Vec3ui>& tris) const;
   void get_vertices(std::vector<Vec3d>& verts) const;
   
};
*/

#endif


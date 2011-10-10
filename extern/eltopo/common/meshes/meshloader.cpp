#include "meshloader.h"
#include <iostream>

using namespace std;

MeshLoader::MeshLoader(const std::string& filepath, MeshType type)  :
   mesh(NULL)
{
   ifstream stream(filepath.c_str());
   if (stream.good())
   {
      stream.close();

      if(type == DEFAULT) {
         std::string ending = filepath.substr(filepath.length()-3);
         if(ending == "OBJ" || ending == "obj") {
            type = OBJ;
         }
         else {
            cout << "ERROR: Unrecognized file format: ." << ending << "\nAssuming OBJ type.\n";
            type = OBJ;
         }
      }

      if(type == OBJ) {
         mesh = new ObjFile(filepath);
      }
      else {
         cout << "ERROR: Unknown type parameter. Giving up.\n";
         mesh = 0;
      }
   }
   else 
   {
      assert(0);
      stream.close();
      mesh = 0;
   }
}

void MeshLoader::get_triangles(std::vector<Vec3ui>& tris) const {
   mesh->get_triangles(tris);
}

void MeshLoader::get_vertices(std::vector<Vec3d>& verts) const {
   mesh->get_vertices(verts);
}

MeshLoader::~MeshLoader() {
   delete mesh;
}
//------------------------------------------
// OBJ File format
//------------------------------------------

ObjFile::ObjFile(const std::string& filepath) :
   mesh( glmReadOBJ((char*)filepath.c_str()) )
{
}

void ObjFile::get_triangles(std::vector<Vec3ui>& tris) const {
   tris.clear();
   for(unsigned int i = 0; i < mesh->numtriangles; ++i) {
      _GLMtriangle triangle = mesh->triangles[i];
      Vec3ui tri3ui(triangle.vindices[0]-1, triangle.vindices[1]-1, triangle.vindices[2]-1);
      tris.push_back(tri3ui);
   }
}

void ObjFile::get_vertices(std::vector<Vec3d>& verts) const {
   verts.clear();
   for(unsigned int i = 1; i <= mesh->numvertices; ++i) {
      Vec3d vertex(
         mesh->vertices[i*3],  
         mesh->vertices[i*3+1],
         mesh->vertices[i*3+2]);
      verts.push_back( vertex );
   }
}

ObjFile::~ObjFile() {
   glmDelete(mesh);
}

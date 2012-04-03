// ---------------------------------------------------------
//
//  fileio.cpp
//  Tyson Brochu 2009
//
// ---------------------------------------------------------

#include "fileio.h"

#include <bfstream.h>

const unsigned int NUM_RAYTRACER_BOOLEAN_PARAMETERS = 2;
const unsigned int NUM_RAYTRACER_FLOAT_PARAMETERS = 9;

// ---------------------------------------------------------
///
/// Write mesh in binary format
///
// ---------------------------------------------------------

bool write_mesh_file( double curr_t,
                     unsigned int nverts,
                     const double* verts,
                     const double* masses,
                     unsigned int ntris,
                     const unsigned int* tris,
                     const char *filename_format, ...)
{
    va_list ap;
    va_start(ap, filename_format);   
    bofstream outfile( filename_format, ap );
    va_end(ap);
    
    outfile.write_endianity();
    
    outfile << curr_t;
    
    outfile << nverts;
    for ( unsigned int i = 0; i < nverts; ++i )
    {
        outfile << verts[3*i+0];
        outfile << verts[3*i+1];
        outfile << verts[3*i+2];
    }
    
    for ( unsigned int i = 0; i < nverts; ++i )
    {
        outfile << masses[i];
    }
    
    outfile << ntris;
    
    for ( unsigned int t = 0; t < ntris; ++t )
    {
        outfile << tris[3*t+0];
        outfile << tris[3*t+1];
        outfile << tris[3*t+2];
    }
    
    outfile.close();
    
    return outfile.good();
}


// ---------------------------------------------------------
///
/// Write mesh in binary format, with per-vertex velocities
///
// ---------------------------------------------------------
bool write_mesh_file_with_velocities( double curr_t,
                                     unsigned int nverts,
                                     const double* verts,
                                     const double* velocities,
                                     const double* masses,
                                     unsigned int ntris,
                                     const unsigned int* tris,
                                     const char *filename_format, ...)
{
    
    va_list ap;
    va_start(ap, filename_format);   
    bofstream outfile( filename_format, ap );
    va_end(ap);
    
    outfile.write_endianity();
    
    outfile << curr_t;
    
    outfile << nverts;
    for ( unsigned int i = 0; i < nverts; ++i )
    {
        outfile << verts[3*i+0];
        outfile << verts[3*i+1];
        outfile << verts[3*i+2];
    }
    
    for ( unsigned int i = 0; i < nverts; ++i )
    {
        outfile << velocities[3*i+0];
        outfile << velocities[3*i+1];
        outfile << velocities[3*i+2];
    }
    
    for ( unsigned int i = 0; i < nverts; ++i )
    {
        outfile << masses[i];
    }
    
    outfile << ntris;
    
    for ( unsigned int t = 0; t < ntris; ++t )
    {
        outfile << tris[3*t+0];
        outfile << tris[3*t+1];
        outfile << tris[3*t+2];
    }   
    
    return outfile.good();
}


// ---------------------------------------------------------
///
/// Read mesh in binary format
///
// ---------------------------------------------------------

bool read_mesh_file( double* curr_t,
                    unsigned int* nverts,
                    double** verts,
                    double** masses,
                    unsigned int* ntris,
                    unsigned int** tris,
                    const char *filename_format, ...)
{
    va_list ap;
    va_start(ap, filename_format);   
    bifstream infile( filename_format, ap );
    va_end(ap);
    
    assert( infile.good() );
    
    infile.read_endianity();
    
    infile >> *curr_t;
    
    infile >> *nverts;
    
    *verts = new double[3*(*nverts)];
    
    for ( unsigned int i = 0; i < (*nverts); ++i )
    {
        infile >> (*verts)[3*i+0];
        infile >> (*verts)[3*i+1];
        infile >> (*verts)[3*i+2];
    }
    
    *masses = new double[*nverts];
    
    for ( unsigned int i = 0; i < *nverts; ++i )
    {
        infile >> (*masses)[i];
    }
    
    infile >> *ntris;
    
    *tris = new unsigned int[3*(*ntris)];
    
    for ( unsigned int t = 0; t < *ntris; ++t )
    {
        infile >> (*tris)[3*t+0];
        infile >> (*tris)[3*t+1];
        infile >> (*tris)[3*t+2];
    }
    
    infile.close();
    
    return infile.good();
}


// ---------------------------------------------------------
///
/// Read mesh in binary format, with per-vertex velocities
///
// ---------------------------------------------------------

bool read_mesh_file_with_velocities( double* curr_t,
                                    unsigned int* nverts,
                                    double** verts,
                                    double** velocities,
                                    double** masses,
                                    unsigned int* ntris,
                                    unsigned int** tris,
                                    const char *filename_format, ...)
{
    va_list ap;
    va_start(ap, filename_format);   
    bifstream infile( filename_format, ap );
    va_end(ap);
    
    assert( infile.good() );
    
    infile.read_endianity();
    
    infile >> *curr_t;
    
    infile >> *nverts;
    
    *verts = new double[3*(*nverts)];
    
    for ( unsigned int i = 0; i < (*nverts); ++i )
    {
        infile >> (*verts)[3*i+0];
        infile >> (*verts)[3*i+1];
        infile >> (*verts)[3*i+2];
    }
    
    *velocities = new double[3*(*nverts)];
    
    for ( unsigned int i = 0; i < (*nverts); ++i )
    {
        infile >> (*velocities)[3*i+0];
        infile >> (*velocities)[3*i+1];
        infile >> (*velocities)[3*i+2];
    }
    
    *masses = new double[*nverts];
    
    for ( unsigned int i = 0; i < *nverts; ++i )
    {
        infile >> (*masses)[i];
    }
    
    infile >> *ntris;
    
    *tris = new unsigned int[3*(*ntris)];
    
    for ( unsigned int t = 0; t < *ntris; ++t )
    {
        infile >> (*tris)[3*t+0];
        infile >> (*tris)[3*t+1];
        infile >> (*tris)[3*t+2];
    }
    
    infile.close();
    
    return infile.good();
    
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

void free_mesh_data( double* verts,
                    double* masses,
                    unsigned int* tris )
{
    delete[] verts;
    delete[] masses;
    delete[] tris;
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

void free_mesh_data_with_velocities( double* verts,
                                    double* velocities,
                                    double* masses,
                                    unsigned int* tris )
{
    delete[] verts;
    delete[] velocities;
    delete[] masses;
    delete[] tris;
}

// ---------------------------------------------------------
// ---------------------------------------------------------
// ---------------------------------------------------------


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------


bool write_raytracer_file( const bool *booleanParameters,
                          const float *floatParameters,
                          const char *filename_format, ... )
{
    va_list ap;
    va_start(ap, filename_format);   
    bofstream outfile( filename_format, ap );
    va_end(ap);
    
    outfile.write_endianity();
    
    for ( unsigned int i = 0; i < NUM_RAYTRACER_BOOLEAN_PARAMETERS; ++i )
    {
        outfile << booleanParameters[i];
    }
    
    for ( unsigned int i = 0; i < NUM_RAYTRACER_FLOAT_PARAMETERS; ++i )
    {
        outfile << floatParameters[i];
    }
    
    outfile.close();
    
    return outfile.good();
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------


bool read_raytracer_file( bool **booleanParameters,
                         float **floatParameters,
                         const char *filename_format, ... )
{
    va_list ap;
    va_start(ap, filename_format);   
    bifstream infile( filename_format, ap );
    va_end(ap);
    
    assert( infile.good() );
    
    infile.read_endianity();
    
    *booleanParameters = new bool[NUM_RAYTRACER_BOOLEAN_PARAMETERS];
    
    for ( unsigned int i = 0; i < NUM_RAYTRACER_BOOLEAN_PARAMETERS; ++i )
    {
        infile >> (*booleanParameters)[i];
    }
    
    *floatParameters = new float[NUM_RAYTRACER_FLOAT_PARAMETERS];
    
    for ( unsigned int i = 0; i < NUM_RAYTRACER_FLOAT_PARAMETERS; ++i )
    {
        infile >> (*floatParameters)[i];
    }
    
    infile.close();
    
    return infile.good();
    
}

// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------


void free_raytracer_data( bool *booleanParameters, 
                         float *floatParameters )
{
    delete[] booleanParameters;
    delete[] floatParameters;
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

bool write_marker_particle_file( int nparticles,
                                const float* x,
                                const char *filename_format, ... )
{
    va_list ap;
    va_start(ap, filename_format);   
    bofstream outfile( filename_format, ap );
    va_end(ap);
    
    outfile.write_endianity();
    
    outfile << nparticles;
    
    for ( int i = 0; i < nparticles; ++i )
    {
        outfile << x[3*i+0];
        outfile << x[3*i+1];
        outfile << x[3*i+2];      
    }
    
    outfile.close();
    return outfile.good();
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

bool read_marker_particle_file( int* nparticles,
                               float** x,
                               const char *filename_format, ... )
{
    va_list ap;
    va_start(ap, filename_format);   
    bifstream infile( filename_format, ap );
    va_end(ap);
    
    if ( !infile.good() )
    {
        fprintf( stderr, "bad infile\n" );
        return false;
    }
    
    infile.read_endianity();
    
    infile >> *nparticles;
    
    (*x) = new float[ 3 * (*nparticles) ];
    
    for ( int i = 0; i < *nparticles; ++i )
    {
        infile >> (*x)[3*i+0];
        infile >> (*x)[3*i+1];
        infile >> (*x)[3*i+2];      
    }
    
    infile.close();
    return infile.good();
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------


void free_marker_particle_data( float* x )
{
    delete[] x;
}



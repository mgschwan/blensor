
#ifndef FILEIO_H
#define FILEIO_H

#ifdef __cplusplus
extern "C" {
#endif
    
    extern const unsigned int NUM_RAYTRACER_BOOLEAN_PARAMETERS;
    extern const unsigned int NUM_RAYTRACER_FLOAT_PARAMETERS;
    
    // -----------------------------------------------------------------------
    //
    // Triangle mesh file format:
    //
    // endianity
    // current sim time     (double)
    // number of verts      (unsigned int)
    // verts                (3 * nverts doubles)
    // OPTIONAL: velocities (3 * nverts doubles)
    // masses               (nverts doubles)
    // number of triangles  (unsinged int)
    // triangles            (3 * ntris unsigned ints)
    //
    // -----------------------------------------------------------------------
    
    
    bool write_mesh_file( double curr_t,
                         unsigned int nverts,
                         const double* verts,
                         const double* masses,
                         unsigned int ntris,
                         const unsigned int* tris,
                         const char *filename_format, ...);
    
    bool write_mesh_file_with_velocities( double curr_t,
                                         unsigned int nverts,
                                         const double* verts,
                                         const double* velocities,
                                         const double* masses,
                                         unsigned int ntris,
                                         const unsigned int* tris,
                                         const char *filename_format, ...);
    
    bool read_mesh_file( double* curr_t,
                        unsigned int* nverts,
                        double** verts,
                        double** masses,
                        unsigned int* ntris,
                        unsigned int** tris,
                        const char *filename_format, ...);
    
    bool read_mesh_file_with_velocities( double* curr_t,
                                        unsigned int* nverts,
                                        double** verts,
                                        double** velocities,
                                        double** masses,
                                        unsigned int* ntris,
                                        unsigned int** tris,
                                        const char *filename_format, ...);
    
    void free_mesh_data( double* verts,
                        double* masses,
                        unsigned int* tris );
    
    void free_mesh_data_with_velocities( double* verts,
                                        double* velocities,
                                        double* masses,
                                        unsigned int* tris );
    
    // -----------------------------------------------------------------------
    //
    // Raytracer parameter file format
    // 
    // endianity
    // scatterShader           (bool)
    // diffuseShader           (bool)
    // falloff                 (float)
    // minTransmittance        (float)
    // scatter                 (float)
    // averageSampleInterval   (float)
    // sampleIntervalVariance  (float)
    // whiteLevel              (float)
    // ambientLight            (float)
    // overheadLight           (float)
    // fillLight               (float)
    //
    // -----------------------------------------------------------------------
    
    bool write_raytracer_file( const bool *booleanParameters,
                              const float *floatParameters,
                              const char *filename_format, ... );
    
    bool read_raytracer_file( bool **booleanParameters,
                             float **floatParameters,
                             const char *filename_format, ... );
    
    void free_raytracer_data( bool *booleanParameters, 
                             float *floatParameters );
    
    // -----------------------------------------------------------------------
    //
    // Marker particle file format:
    //
    // endianity
    // number of particles  (int)
    // particle locations   ( 3 * nparticles floats)
    //
    // -----------------------------------------------------------------------
    
    bool write_marker_particle_file( int nparticles,
                                    const float* x,
                                    const char *filename_format, ... );
    
    bool read_marker_particle_file( int* nparticles,
                                   float** x,
                                   const char *filename_format, ... );
    
    void free_marker_particle_data( float* x );
    
    // -----------------------------------------------------------------------
    //
    // Procedural flow field parameters
    //
    // -----------------------------------------------------------------------
    
#ifdef __cplusplus
}
#endif

#endif





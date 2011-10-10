
// ---------------------------------------------------------
//
//  eltopo.h
//  Tyson Brochu 2009
//
//  C-callable API for El Topo
//
// ---------------------------------------------------------

#ifndef ELTOPO_H
#define ELTOPO_H

#ifdef __cplusplus
extern "C" {
#endif
   
// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------
   


// =========================================================
//  STRUCTURES FOR SPECIFYING OPTIONS
// =========================================================   
   
// ---------------------------------------------------------
///
/// Options common to static operations and position integration.
///
// ---------------------------------------------------------
   
struct ElTopoGeneralOptions
{
   int m_verbose;               // whether to output a lot of information to 
                                // the console
   int m_collision_safety;      // whether to enforce an intersection-free mesh
                                // at all times
};

// ---------------------------------------------------------
///
/// Options for static operations (mesh maintenance and topology change)
///
// ---------------------------------------------------------
   
struct ElTopoStaticOperationsOptions
{
   // whether to perform mesh maintenance
   int m_perform_improvement;            

   // whether to allow merging and separation
   int m_allow_topology_changes;     

   // maximum allowable change in volume when performing mesh maintenance
   double m_max_volume_change;       

   // edges shorter than this length will be collapsed
   double m_min_edge_length;              

   // edges longer then this length will be subdivided
   double m_max_edge_length;              

   // edges closer than this distance will merge
   double m_merge_proximity_epsilon;    

   // scheme to use to generate midpoints when collapsing/splitting edges.  
   // Set this to 0 to use default.
   void* m_subdivision_scheme;            
};

// ---------------------------------------------------------
///
/// Options for position integration
///
// ---------------------------------------------------------
   
struct ElTopoIntegrationOptions
{
   // mesh elements closer than this will trigger repulsion forces
   double m_proximity_epsilon;      

   // integration timestep size
   double m_dt;                     
};

   

// =========================================================
//  API FUNCTIONS
// =========================================================   

   
// ---------------------------------------------------------
///
/// Static operations: edge collapse, edge split, edge flip, null-space 
/// smoothing, and topological changes
///
/// Parameters:
///   in_num_vertices:           (Input) Number of input vertices.
///   in_vertex_locations:       (Input) Flattened array of vertex coordinates.
///                                      Elements 0, 1, and 2 are x, y, and z
///                                      coordinates of the first vertex, etc.
///   in_num_triangles           (Input) Number of input triangles.
///   in_triangles               (Input) Triples of vertex indices.  Elements 
///                                      0, 1, and 2 are indices of vertices
///                                      comprising the first triangle, etc.
///   in_masses                  (Input) Input vertex masses.
///   general_otions             (Input) Structure specifying options common to
///                                      static operations and integration.
///   options                    (Input) Structure specifying options specific 
///                                      to static operations.
///   out_num_vertices           (Output) Number of vertices after static 
///                                       operations.
///   out_vertex_locations       (Output, allocated by El Topo) Vertex 
///                                       locations after static operations.
///   out_num_triangles          (Output) Number of triangles after static 
///                                       operations.
///   out_triangles              (Output, allocated by El Topo) Triangles after
///                                       static operations.
///   out_masses                 (Output, allocated by El Topo) Vertex masses 
///                                       after static operations.
///
// ---------------------------------------------------------
   
void el_topo_static_operations( const int in_num_vertices,                   
                          const double* in_vertex_locations,           
                          const int in_num_triangles,                   
                          const int* in_triangles, 
                          const double* in_masses,
                          const struct ElTopoGeneralOptions* general_options,
                          const struct ElTopoStaticOperationsOptions* options, 
                          int* out_num_vertices,                       
                          double** out_vertex_locations,  
                          int* out_num_triangles,
                          int** out_triangles,
                          double** out_masses );

// ---------------------------------------------------------
///
/// Free memory allocated by static operations.
///
// ---------------------------------------------------------
   
void el_topo_free_static_operations_results( double* out_vertex_locations, 
                                             int* out_triangles, 
                                             double* out_masses );

// ---------------------------------------------------------
///
/// Surface vertex position integration.
///
/// Parameters:
///   num_vertices:              (Input) Number of input vertices (not changed 
///                                      by integration).
///   in_vertex_locations:       (Input) Flattened array of vertex coordinates.
///                                      Elements 0, 1, and 2 are x, y, and z
///                                      coordinates of the first vertex, etc.
///   in_new_vertex_locations:   (Input) Predicted vertex coordinates.
///   num_triangles              (Input) Number of input triangles (not changed
///                                      by integration).
///   triangles                  (Input) Triples of vertex indices (not changed
///                                      by integration).  Elements 0, 1, and 
///                                      2 are indices of vertices comprising 
///                                      the first triangle, and so on.
///   masses                     (Input) Input vertex masses (not changed by 
///                                      integration).
///   general_otions             (Input) Structure specifying options common to
///                                      static operations and integration.
///   options                    (Input) Structure specifying options specific 
///                                      to integration.
///   out_vertex_locations       (Output, allocated by El Topo) Vertex 
///                                      locations after integration.
///
// ---------------------------------------------------------
   
void el_topo_integrate( const int num_vertices, 
                        const double *in_vertex_locations, 
                        const double *in_vertex_new_locations, 
                        const int num_triangles, 
                        const int *triangles, 
                        const double *masses,
                        const struct ElTopoGeneralOptions* general_options,
                        const struct ElTopoIntegrationOptions* options,
                        double **out_vertex_locations );
   

// ---------------------------------------------------------
///
/// Free memory allocated by integration.
///
// ---------------------------------------------------------
   
void el_topo_free_integrate_results( double* out_vertex_locations );
   

#ifdef __cplusplus
}
#endif

#endif

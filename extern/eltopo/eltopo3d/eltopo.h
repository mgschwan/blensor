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
        int m_verbose;               // whether to output a lot of information to the console
        int m_collision_safety;      // whether to enforce an intersection-free mesh at all times
        double m_proximity_epsilon;
    };
    
    // ---------------------------------------------------------
    ///
    /// Options for static operations (mesh maintenance and topology change)
    ///
    // ---------------------------------------------------------
    
    struct ElTopoStaticOperationsOptions
    {
        /// whether to perform mesh maintenance
        int m_perform_improvement;            
        
        /// whether to allow merging and separation
        int m_allow_topology_changes;     
        
        /// maximum allowable change in volume when performing mesh maintenance
        double m_max_volume_change;       
        
        /// edges shorter than this length will be collapsed
        double m_min_edge_length;              
        
        /// edges longer then this length will be subdivided
        double m_max_edge_length;              
        
        /// prevent triangles smaller than this area
        double m_min_triangle_area;
        
        /// prevent interior angles smaller than this
        double m_min_triangle_angle;
        
        /// prevent interior angles greater than this
        double m_max_triangle_angle;   
        
        /// boolean, whether to use curvature adaptivity when splitting edges
        int m_use_curvature_when_splitting;

        /// whether to use curvature adaptivity when collapsing edges        
        int m_use_curvature_when_collapsing;
        
        /// clamp curvature scaling to these values
        double m_min_curvature_multiplier;
        
        /// clamp curvature scaling to these values
        double m_max_curvature_multiplier;
        
        /// boolean, whether to allow vertices to move during improvement
        int m_allow_vertex_movement;
        
        /// Minimum edge length improvement in order to flip an edge
        double m_edge_flip_min_length_change;
        
        /// Elements within this distance will trigger a merge attempt   
        double m_merge_proximity_epsilon;
        
        /// Type of subdivision to use when collapsing or splitting (butterfly, quadric error minimization, etc.)
        void *m_subdivision_scheme;   
        
        /// boolean, whether to enforce collision-free surfaces (including during mesh maintenance operations)
        int m_collision_safety;
        
        /// boolean, whether to allow non-manifold (edges incident on more than two triangles)
        int m_allow_non_manifold;
        
    };
    
    // ---------------------------------------------------------
    ///
    /// Options for position integration
    ///
    // ---------------------------------------------------------
    
    struct ElTopoIntegrationOptions
    {
        /// friction coefficient to apply during collision resolution
        double m_friction_coefficient;
        
        /// integration timestep size
        double m_dt;                     
    };
    
    
    // ---------------------------------------------------------
    ///
    /// A mesh object: list of triangles, vertex positions, and vertex masses
    ///
    // ---------------------------------------------------------
    
    struct ElTopoMesh
    {
        
        /// Number of vertices
        int num_vertices;
        
        /// Vertex positions in 3D space.  This array should be shaped like: [x0 y0 z0 x1 y1 z1 ... ]
        double* vertex_locations;
        
        /// Number of traingles
        int num_triangles;
        
        /// Triangles, indexing into the vertex array. [a0 b0 c0 a1 b1 c1 ... ], where triangle i has vertices (ai,bi,ci).
        int* triangles;
        
        /// For each vertex i, array element i is 1 if the vertex is solid, 0 otherwise
        double* vertex_masses;
        
    };
    
    
    // ---------------------------------------------------------
    ///
    /// Defragment information, recording all vertex and triangle operations, and maps from old indices to new ones
    ///
    // ---------------------------------------------------------
    
    struct ElTopoDefragInformation
    {
        /// Number of entries in the vertex change history
        int num_vertex_changes;     // = N
            
        /// Boolean, 0: vertex addition, non-zero: vertex removal
        int* vertex_is_remove;      // size N
        
        /// The index of the affected vertex
        int* vertex_index;          // size N
        
        /// If this is a vertex addition due to splitting, the split edge, stored as pairs of vertex indices
        int* split_edge;            // size 2*N
        
        
        /// Number of entries in the triangle change history
        int num_triangle_changes;  // = N
        
        /// Boolean, 0: triangle addition, non-zero: triangle removal
        int* triangle_is_remove;   // boolean, size N
        
        /// The index of the affected triangle
        int* triangle_index;       // N
        
        /// If this is a triangle addition, the new triangle, stored as a triplet of vertex indices
        int* new_tri;              // 3*N
        
        /// Size of the defragged triangle map
        int defragged_triangle_map_size;    // = N
        
        /// For each triangle, a pair of indices (old, new), where old is the triangle index at before defrag, and new is the 
        /// triangle index after defrag
        int* defragged_triangle_map;        // 2*N

        /// Size of the defragged vertex map
        int defragged_vertex_map_size;      // = N
        
        /// For each vertex, a pair of indices (old, new), where old is the vertex index at before defrag, and new is the vertex
        /// index after defrag        
        int* defragged_vertex_map;          // 2*N
        
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
    ///   input_mesh:                (Input) ElTopoMesh to be operated on
    ///   general_otions             (Input) Structure specifying options common to
    ///                                      static operations and integration.
    ///   options                    (Input) Structure specifying options specific 
    ///                                      to static operations.
    ///   defrag_info                (Output, allocated by El Topo) Change history and defrag maps, recording the operations 
    ///                                       performed at the vertex and triangle level.
    ///   output_mesh                (Output, allocated by El Topo) Mesh data structure after remeshing and topology operations.
    ///
    // ---------------------------------------------------------
    
    void el_topo_static_operations( const struct ElTopoMesh* input_mesh,
                                   const struct ElTopoGeneralOptions* general_options,
                                   const struct ElTopoStaticOperationsOptions* options, 
                                   struct ElTopoDefragInformation* defrag_info, 
                                   struct ElTopoMesh* output_mesh );
    
    // ---------------------------------------------------------
    ///
    /// Free memory allocated by static operations.
    ///
    // ---------------------------------------------------------
    
    void el_topo_free_static_operations_results( struct ElTopoMesh* outputs, struct ElTopoDefragInformation* defrag_info  );
    
    
    // ---------------------------------------------------------
    ///
    /// Surface vertex position integration.
    ///
    /// Parameters:
    ///   input_mesh:               (Input) Mesh data structure to be integrated forward.
    ///   in_vertex_new_locations   (Input) Predicted vertex positions at the end of the time step.  
    ///   general_otions            (Input) Structure specifying options common to
    ///                                      static operations and integration.
    ///   options                   (Input) Structure specifying options specific 
    ///                                      to integration operations.    
    ///   out_vertex_locations      (Output) Final vertex positions after integration.
    ///   out_dt                    (Output) Actual time step taken by the function.
    ///     
    ///
    // ---------------------------------------------------------
    
    void el_topo_integrate(const struct ElTopoMesh* input_mesh,
                           const double* in_vertex_new_locations,
                           const struct ElTopoGeneralOptions* general_options,
                           const struct ElTopoIntegrationOptions* options,
                           double **out_vertex_locations,
                           double *out_dt );
    
    
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

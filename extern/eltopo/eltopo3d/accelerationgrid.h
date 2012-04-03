// ---------------------------------------------------------
//
//  accelerationgrid.h
//  Tyson Brochu 2008
//  
//  A grid-based collision test culling structure.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_ACCELERATIONGRID_H
#define EL_TOPO_ACCELERATIONGRID_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <array3.h>
#include <vec.h>

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Regular grid collision culling structure
///
// --------------------------------------------------------

class AccelerationGrid
{
    
public:
    
    AccelerationGrid();
    ~AccelerationGrid();
    
    // deep copy
    AccelerationGrid(AccelerationGrid& other);
    AccelerationGrid& operator=(const AccelerationGrid& other);
    
    /// Define the grid given, the extents of the domain and the number of voxels along each dimension
    ///
    void set( const Vec3st& dims, const Vec3d& xmin, const Vec3d& xmax );
    
    /// Generate a set of voxel indices from a pair of AABB extents
    ///
    void boundstoindices( const Vec3d& xmin, const Vec3d& xmax, Vec3i& xmini, Vec3i& xmaxi);
    
    /// Add an object with the specified index and AABB to the grid
    ///
    void add_element(size_t idx, const Vec3d& xmin, const Vec3d& xmax);
    
    /// Remove an object with the specified index from the grid
    ///
    void remove_element(size_t idx);
    
    /// Reset the specified object's AABB
    ///
    void update_element(size_t idx, const Vec3d& xmin, const Vec3d& xmax);
    
    /// Remove all elements from the grid
    ///
    void clear();
    
    /// Return the set of elements which have AABBs overlapping the query AABB.
    ///
    void find_overlapping_elements( const Vec3d& xmin, const Vec3d& xmax, std::vector<size_t>& results );
    
    
    /// Each cell contains an array of indices specifying the elements whose AABBs overlap the cell
    ///
    Array3<std::vector<size_t>* > m_cells;
    
    /// For each element, a list of triples, each triple specifying a cell which overlaps the element. 
    ///
    std::vector<std::vector<Vec3st> > m_elementidxs;
    
    /// Element AABBs
    ///
    std::vector<Vec3d> m_elementxmins, m_elementxmaxs;
    
    /// For each element, the timestamp of the last query that examined the element
    ///
    std::vector<unsigned int> m_elementquery;
    
    /// Timestamp of the last query
    ///
    unsigned int m_lastquery;
    
    /// Lower/upper corners of the entire grid
    ///
    Vec3d m_gridxmin, m_gridxmax;
    
    /// Cell dimensions
    ///
    Vec3d m_cellsize;
    
    /// Inverse cell dimensions
    ///
    Vec3d m_invcellsize;
    
};


#endif

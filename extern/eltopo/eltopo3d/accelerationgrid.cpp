// ---------------------------------------------------------
//
//  accelerationgrid.cpp
//  Tyson Brochu 2008
//  
//  A grid-based collision test culling structure.
//
// ---------------------------------------------------------

// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <accelerationgrid.h>

#include <array3.h>
#include <limits>
#include <util.h>
#include <vec.h>
#include <vector>
#include <wallclocktime.h>

// ---------------------------------------------------------
// Global externs
// ---------------------------------------------------------

// ---------------------------------------------------------
// Local constants, typedefs, macros
// ---------------------------------------------------------

// ---------------------------------------------------------
// Static function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Default constructor
///
// --------------------------------------------------------

AccelerationGrid::AccelerationGrid() :
m_cells(0,0,0),
m_elementidxs(0),
m_elementxmins(0),
m_elementxmaxs(0),
m_elementquery(0),
m_lastquery(0),
m_gridxmin(0,0,0),
m_gridxmax(0,0,0),
m_cellsize(0,0,0),
m_invcellsize(0,0,0)
{
    Vec3st dims(1,1,1);
    Vec3d xmin(0,0,0), xmax(1,1,1);
    set(dims, xmin, xmax);
}

// --------------------------------------------------------
///
/// Calls assignment operator, which does a deep copy.
///
// --------------------------------------------------------

AccelerationGrid::AccelerationGrid(AccelerationGrid& other) :
m_cells(0,0,0),
m_elementidxs(0),
m_elementxmins(0),
m_elementxmaxs(0),
m_elementquery(0),
m_lastquery(0),
m_gridxmin(0,0,0),
m_gridxmax(0,0,0),
m_cellsize(0,0,0),
m_invcellsize(0,0,0)
{
    
    // Call assignment operator
    *this = other;
    
}

// --------------------------------------------------------
///
/// Deep copy.
///
// --------------------------------------------------------

AccelerationGrid& AccelerationGrid::operator=( const AccelerationGrid& other)
{
    m_cells.resize( other.m_cells.ni, other.m_cells.nj, other.m_cells.nk, 0 );
    for ( size_t i = 0; i < m_cells.a.size(); ++i )
    {
        if (other.m_cells.a[i])
        {
            m_cells.a[i] = new std::vector<size_t>();
            *(m_cells.a[i]) = *(other.m_cells.a[i]);
        }
    }
    
    m_elementidxs = other.m_elementidxs;
    m_elementxmins = other.m_elementxmins;
    m_elementxmaxs = other.m_elementxmaxs;
    m_elementquery = other.m_elementquery;
    m_lastquery = other.m_lastquery;
    m_gridxmin = other.m_gridxmin;
    m_gridxmax = other.m_gridxmax;
    m_cellsize = other.m_cellsize;
    m_invcellsize = other.m_invcellsize;   
    
    return *this;
}

// --------------------------------------------------------
///
/// Destructor: clear all grids
///
// --------------------------------------------------------

AccelerationGrid::~AccelerationGrid()
{
    clear();
}

// --------------------------------------------------------
///
/// Define the grid, given the extents of the domain and the number of desired voxels along each dimension
///
// --------------------------------------------------------

void AccelerationGrid::set( const Vec3st& dims, const Vec3d& xmin, const Vec3d& xmax )
{
    m_gridxmin = xmin;
    m_gridxmax = xmax;
    
    for(unsigned int i = 0; i < 3; i++)
    {
        m_cellsize[i] = (m_gridxmax[i]-m_gridxmin[i])/dims[i];
        m_invcellsize[i] = 1.0 / m_cellsize[i];
    }
    
    clear();
    
    m_cells.resize(dims[0], dims[1], dims[2]);    
    for(size_t i = 0; i < m_cells.a.size(); i++)
    {
        m_cells.a[i] = 0;
    }   
}

// --------------------------------------------------------
///
/// Generate a set of voxel indices from a pair of AABB extents
///
// --------------------------------------------------------

void AccelerationGrid::boundstoindices(const Vec3d& xmin, const Vec3d& xmax, Vec3i& xmini, Vec3i& xmaxi)
{
    
    xmini[0] = (int) floor((xmin[0] - m_gridxmin[0]) * m_invcellsize[0]);
    xmini[1] = (int) floor((xmin[1] - m_gridxmin[1]) * m_invcellsize[1]);
    xmini[2] = (int) floor((xmin[2] - m_gridxmin[2]) * m_invcellsize[2]);
    
    xmaxi[0] = (int) floor((xmax[0] - m_gridxmin[0]) * m_invcellsize[0]);
    xmaxi[1] = (int) floor((xmax[1] - m_gridxmin[1]) * m_invcellsize[1]);
    xmaxi[2] = (int) floor((xmax[2] - m_gridxmin[2]) * m_invcellsize[2]);
    
    if(xmini[0] < 0) xmini[0] = 0;
    if(xmini[1] < 0) xmini[1] = 0;
    if(xmini[2] < 0) xmini[2] = 0;
    
    if(xmaxi[0] < 0) xmaxi[0] = 0;
    if(xmaxi[1] < 0) xmaxi[1] = 0;
    if(xmaxi[2] < 0) xmaxi[2] = 0;
    
    assert( m_cells.ni < INT_MAX );
    assert( m_cells.nj < INT_MAX );
    assert( m_cells.nk < INT_MAX );
    
    if(xmaxi[0] >= (int)m_cells.ni) xmaxi[0] = (int)m_cells.ni-1;
    if(xmaxi[1] >= (int)m_cells.nj) xmaxi[1] = (int)m_cells.nj-1;
    if(xmaxi[2] >= (int)m_cells.nk) xmaxi[2] = (int)m_cells.nk-1;
    
    if(xmini[0] >= (int)m_cells.ni) xmini[0] = (int)m_cells.ni-1;
    if(xmini[1] >= (int)m_cells.nj) xmini[1] = (int)m_cells.nj-1;
    if(xmini[2] >= (int)m_cells.nk) xmini[2] = (int)m_cells.nk-1;
    
}

// --------------------------------------------------------
///
/// Add an object with the specified index and AABB to the grid
///
// --------------------------------------------------------

void AccelerationGrid::add_element(size_t idx, const Vec3d& xmin, const Vec3d& xmax)
{
    if(m_elementidxs.size() <= idx)
    {
        m_elementidxs.resize(idx+1);
        m_elementxmins.resize(idx+1);
        m_elementxmaxs.resize(idx+1);
        m_elementquery.resize(idx+1);
    }
    
    m_elementxmins[idx] = xmin;
    m_elementxmaxs[idx] = xmax;
    m_elementquery[idx] = 0;
    
    Vec3i xmini, xmaxi;
    boundstoindices(xmin, xmax, xmini, xmaxi);
    
    for(int i = xmini[0]; i <= xmaxi[0]; i++)
    {
        for(int j = xmini[1]; j <= xmaxi[1]; j++)
        {
            for(int k = xmini[2]; k <= xmaxi[2]; k++)
            {
                std::vector<size_t>*& cell = m_cells(i, j, k);
                if(!cell)
                    cell = new std::vector<size_t>();
                
                cell->push_back(idx);
                m_elementidxs[idx].push_back(Vec3st(i, j, k));
            }
        }
    }
}

// --------------------------------------------------------
///
/// Remove an object with the specified index from the grid
///
// --------------------------------------------------------

void AccelerationGrid::remove_element(size_t idx)
{
    
    if ( idx >= m_elementidxs.size() ) { return; }
    
    for(size_t c = 0; c < m_elementidxs[idx].size(); c++)
    {
        Vec3st cellcoords = m_elementidxs[idx][c];
        std::vector<size_t>* cell = m_cells(cellcoords[0], cellcoords[1], cellcoords[2]);
        
        std::vector<size_t>::iterator it = cell->begin();
        while(*it != idx)
        {
            it++;
        }
        
        cell->erase(it);
    }
    
    m_elementidxs[idx].clear();
}

// --------------------------------------------------------
///
/// Reset the specified object's AABB
///
// --------------------------------------------------------

void AccelerationGrid::update_element(size_t idx, const Vec3d& xmin, const Vec3d& xmax)
{
    remove_element(idx);
    add_element(idx, xmin, xmax);
}

// --------------------------------------------------------
///
/// Remove all elements from the grid
///
// --------------------------------------------------------

void AccelerationGrid::clear()
{
    for(size_t i = 0; i < m_cells.a.size(); i++)
    {
        std::vector<size_t>*& cell = m_cells.a[i];  
        if(cell)
        {
            delete cell;
            cell = 0;
        }
    }
    
    m_elementidxs.clear();
    m_elementxmins.clear();
    m_elementxmaxs.clear();
    m_elementquery.clear();
    m_lastquery = 0;
    
}

// --------------------------------------------------------
///
/// Return the set of elements which have AABBs overlapping the query AABB.
///
// --------------------------------------------------------

void AccelerationGrid::find_overlapping_elements( const Vec3d& xmin, const Vec3d& xmax, std::vector<size_t>& results ) 
{
    if(m_lastquery == std::numeric_limits<unsigned int>::max())
    {
        std::vector<unsigned int>::iterator iter = m_elementquery.begin();
        for( ; iter != m_elementquery.end(); ++iter )
        {
            *iter = 0;
        }
        m_lastquery = 0;
    }
    
    ++m_lastquery;
    
    Vec3i xmini, xmaxi;
    boundstoindices(xmin, xmax, xmini, xmaxi);
    
    for(int i = xmini[0]; i <= xmaxi[0]; ++i)
    {
        for(int j = xmini[1]; j <= xmaxi[1]; ++j)
        {
            for(int k = xmini[2]; k <= xmaxi[2]; ++k)
            {
                std::vector<size_t>* cell = m_cells(i, j, k);
                
                if(cell)
                {
                    for( std::vector<size_t>::const_iterator citer = cell->begin(); citer != cell->end(); ++citer)
                    {
                        size_t oidx = *citer;
                        
                        // Check if the object has already been found during this query
                        
                        if(m_elementquery[oidx] < m_lastquery)
                        {
                            
                            // Object has not been found.  Set m_elementquery so that it will not be tested again during this query.
                            
                            m_elementquery[oidx] = m_lastquery;
                            
                            const Vec3d& oxmin = m_elementxmins[oidx];
                            const Vec3d& oxmax = m_elementxmaxs[oidx];
                            
                            if( (xmin[0] <= oxmax[0] && xmin[1] <= oxmax[1] && xmin[2] <= oxmax[2]) &&
                               (xmax[0] >= oxmin[0] && xmax[1] >= oxmin[1] && xmax[2] >= oxmin[2]) )
                            {
                                results.push_back(oidx);
                            }
                            
                        }
                    }
                }
                
            }
        }
    }
}




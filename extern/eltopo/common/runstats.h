/*
 *  runstats.h
 *  eltopo3d_project
 *
 *  Created by tyson on 21/04/11.
 *
 */

// Hold some runtime stats

#ifndef RUNSTATS_H
#define RUNSTATS_H

#include <map>
#include <string>
#  if _MSC_VER < 1600
// stdint.h is not available before VS2010
#if defined(_WIN32) && !defined(__MINGW32__)
/* The __intXX are built-in types of the visual complier! So we don't
   need to include anything else here.
   This typedefs should be in sync with types from MEM_sys_types.h */

typedef signed __int8  int8_t;
typedef signed __int16 int16_t;
typedef signed __int32 int32_t;

typedef unsigned __int8  uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
#endif
typedef __int64 int64_t;
typedef unsigned __int64 uint64_t;
#  else
#    include <stdint.h>
#  endif
#include <vector>

class RunStats
{
    
public:
    
    RunStats() :
    int_stats(),
    double_stats(),
    per_frame_int_stats(),
    per_frame_double_stats()
    {}
    
    
    typedef std::pair<int, int64_t> PerFrameInt;
    typedef std::pair<int, double> PerFrameDouble;
    
    void set_int( std::string name, int64_t value );
    void add_to_int( std::string name, int64_t increment );
    int64_t get_int( std::string name );
    bool get_int( std::string name, int64_t& value );
    void update_min_int( std::string name, int64_t value );
    void update_max_int( std::string name, int64_t value );
    
    void set_double( std::string name, double value );
    void add_to_double( std::string name, double increment );
    double get_double( std::string name );
    bool get_double( std::string name, double& value );
    void update_min_double( std::string name, double value );
    void update_max_double( std::string name, double value );
    
    void add_per_frame_int( std::string name, int frame, int64_t value );   
    bool get_per_frame_ints( std::string name, std::vector<PerFrameInt>& sequence );
    
    void add_per_frame_double( std::string name, int frame, double value );  
    bool get_per_frame_doubles( std::string name, std::vector<PerFrameDouble>& sequence );
    
    void write_to_file( const char* filename );
    
    void clear();
    
private:
    
    std::map<std::string, int64_t> int_stats;
    std::map<std::string, double> double_stats;
    
    std::map<std::string, std::vector<PerFrameInt> > per_frame_int_stats;
    std::map<std::string, std::vector<PerFrameDouble> > per_frame_double_stats;
    
};



#endif

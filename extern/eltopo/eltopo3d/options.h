// ---------------------------------------------------------
//
//  options.h
//  Tyson Brochu 2008
//
//  Constants and macro defines
//
// ---------------------------------------------------------

#ifndef OPTIONS_H
#define OPTIONS_H

// ---------------------------------------------------------
// Preproccessor defines
// ---------------------------------------------------------

// Whether to use an OpenGL GUI, or run command-line style
// (Define NO_GUI in your build to suppress the GUI.)

#ifndef NO_GUI
#define USE_GUI
#endif

#ifndef NO_RAY_TRACER
#define RAY_TRACER
#endif

// ---------------------------------------------------------
// Global constants
// ---------------------------------------------------------

const double UNINITIALIZED_DOUBLE = 0x0F;

extern const double G_EIGENVALUE_RANK_RATIO;    // in dynamicsurface.cpp

#endif


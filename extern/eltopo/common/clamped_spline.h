/*
 *  clamped_spline.h
 *  eltopo2d_project
 *
 *  Created by tyson on 30/10/09.
 *  Copyright 2009 __MyCompanyName__. All rights reserved.
 *
 */


#include <vec.h>

void compute_cubic_spline_coefficients( const std::vector<double>& t, 
                                        const std::vector<double>& f, 
                                        std::vector<Vec4d>& coeffs );


void evaluate_spline( const std::vector<double>& coarse_t, 
                      const std::vector<double>& coarse_f, 
                      const std::vector<Vec4d>& coeffs, 
                      const std::vector<double>& fine_t, 
                      std::vector<double>& fine_f );



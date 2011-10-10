/*
 *  clamped_spline.cpp
 *  eltopo2d_project
 *
 *  Created by tyson on 30/10/09.
 *  Copyright 2009 __MyCompanyName__. All rights reserved.
 *
 */

#include <clamped_spline.h>
#include <sparse_matrix.h>
#include <krylov_solvers.h>

// -------------------------------------------------------------


void compute_cubic_spline_coefficients( const std::vector<double>& t, 
                                        const std::vector<double>& f, 
                                        std::vector<Vec4d>& coeffs )
{

   unsigned int n = f.size();
   
   std::vector<double> h(n-1);
   for ( unsigned int i = 0; i < n-1; ++i )
   {
      h[i] = t[i+1] - t[i];
   }
   
   // build tridiagonal matrix
   
   SparseMatrixDynamicCSR A(n,n);
   
   A(0,0) = 2*h[0];
   A(0,1) = h[0];
   
   for ( unsigned int i = 1; i < n-2; ++i )
   {
      A(i,i-1) = h[i];
      A(i,i) = 2*(h[i] + h[i+1]);
      A(i,i+1) = h[i];
   }
   
   A(n-1, n-2) = h[n-2];
   A(n-1, n-1) = 2*h[n-2];
   
   // right-hand side
   
   double *rhs = new double[n];
   rhs[0] = 3.0*(f[1] - f[0]) / h[0];
   for ( unsigned int i = 1; i < n-2; ++i )
   {
      rhs[i] = 3.0 * (f[i+1] - f[i]) / h[i] - 3.0*(f[i] - f[i-1])/h[i-1];
   }
   rhs[n-1] = -3.0*(f[n-1] - f[n-2]) / h[n-2];
   
   // solve system
   
   double *sol = new double[n];
   CGNR_Solver solver;
      
   solver.max_iterations = 1000;
   KrylovSolverStatus result = solver.solve( A, rhs, sol );
   
   assert( result == KRYLOV_CONVERGED );
   
   // compute coefficients
   
   coeffs.resize( n-1 );
   
   std::cout << std::endl;
   
   for ( unsigned int j = 0; j < n-1; ++j )
   {
      coeffs[j][0] = (sol[j+1] - sol[j]) / (3*h[j]);      
      coeffs[j][1] = sol[j];
      coeffs[j][2] = 1/h[j] * (f[j+1] - f[j]) - h[j]/3 * (2*sol[j] + sol[j+1]);
      coeffs[j][3] = f[j];

//      std::cout << "f_j(t_j) = " << coeffs[j][3] << std::endl;
//      std::cout << "f_j(t_j + dt) = " << coeffs[j][0]*h[j]*h[j]*h[j] + coeffs[j][1]*h[j]*h[j] + coeffs[j][2]*h[j] + coeffs[j][3] << std::endl;

      std::cout << "df_j/dt(t_j) = " << coeffs[j][2] << std::endl;
      std::cout << "df_j/dt(t_j + dt) = " << 3.0*coeffs[j][0]*h[j]*h[j] + 2.0*coeffs[j][1]*h[j] + coeffs[j][2] << std::endl;
   }
      
   delete[] rhs;
   delete[] sol;
   
}



// -------------------------------------------------------------



void evaluate_spline( const std::vector<double>& coarse_t, 
                      const std::vector<double>& coarse_f, 
                      const std::vector<Vec4d>& coeffs, 
                      const std::vector<double>& fine_t, 
                      std::vector<double>& fine_f )
{
   
   fine_f.resize( fine_t.size() );
   
   // for each t in fine t
   
   for ( unsigned int i = 0; i < fine_t.size(); ++i )
   {
      double t = fine_t[i];
   
      // find the suitable subrange
      
      unsigned int j = 0;
      while ( (j < coarse_t.size() - 1) && (coarse_t[j+1] < t) )
      {
         ++j;
      }
      
      assert( t >= coarse_t[j] );
      assert( t <= coarse_t[j+1] );
   
      double x = t - coarse_t[j];
   
      // evaluate using the subrange's coefficients        
      
      fine_f[i] = coeffs[j][0]*x*x*x + coeffs[j][1]*x*x + coeffs[j][2]*x + coeffs[j][3];

   }
   
}






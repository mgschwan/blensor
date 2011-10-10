#ifndef CRSOLVER_H
#define CRSOLVER_H

#include <fstream>
#include "sparse/sparsematrix.h"
#include "sparse/sparseilu.h"
#include "sparse/sparsemilu.h"
#include "wallclocktime.h"
#include "vector_math.h"

//Unpreconditioned Conjugate Residual (variant of MINRES)
//Based off pseudocode in Y. Saad's "Iterative Methods for Sparse Linear Systems" 
//First Edition, Algorithm 6.19

//TODO: Perhaps modify it to more clearly parallel our CG Solver (for consistency)
//TODO: Add support for preconditioning
//TODO: Add debug info as in the CG Solver

//This is ugly, there's probably a smarter/faster way to do this, possibly using swap as in the CGSolver
template<class T> 
void add_scaled2(T alpha, const std::vector<T>& x, std::vector<T>& y) { // y = alpha*y + x
   for(unsigned int i = 0; i < x.size(); ++i)
      y[i] = alpha*y[i] + x[i];

}

template <class T>
class CRSolver {
   
   //CR temporary vectors
   std::vector<T> p, Ap, r, Ar;

   // used within loop
   FixedSparseMatrix<T> fixed_matrix;

public:

   //Parameters
   T tolerance_factor;
   int max_iterations;
  
   CRSolver()
   {
      set_solver_parameters(1e-5f, 100);
   }

   void set_solver_parameters(T tolerance_factor_, int max_iterations_)
   {
      tolerance_factor=tolerance_factor_;
      if(tolerance_factor<1e-30) tolerance_factor=1e-30;
      max_iterations=max_iterations_;
   }

   bool solve(const SparseMatrix<T>& matrix, const std::vector<T> & rhs, std::vector<T> & result, T& residual_out, int& iterations_out) 
   {
      
      if(r.size() != matrix.n) {
         p.resize(matrix.n);
         Ap.resize(matrix.n);
         r.resize(matrix.n);
         Ar.resize(matrix.n);
         zero(r);
         zero(Ar);
         zero(p);
         zero(Ap);
      }

      double time = get_time_in_seconds();
      fixed_matrix.construct_from_matrix(matrix);
      
      zero(result);
      copy(rhs,r); //r = b - A*result, where result is initialized to zero 
      
      residual_out = abs_max(r);
      double tol=tolerance_factor*residual_out;
      
      if(residual_out == 0) {
         printf("CRSolver: Completed. Input was an exact solution.\n");
         iterations_out = 0;
         return true;
      }
      
      copy(r, p);
    
      int iteration;
      double rho;
      multiply(fixed_matrix, r, Ar);
      multiply(fixed_matrix, p, Ap);
      rho = dot(r,Ar);
      
      if(rho==0 || rho!=rho) {
         printf("*** CGSolver: Crashed early! rho = %f ***\n", rho);
         iterations_out = 0;
      }

      for(iteration=0; iteration<max_iterations; ++iteration){
         double alpha = rho/dot(Ap,Ap);

         add_scaled(alpha, p, result);
         add_scaled(-alpha, Ap, r); 
         
         residual_out = abs_max(r);
         if(residual_out <= tol) {
            double time2 = get_time_in_seconds();
            printf("CRSolver: Completed, %d iterations in %f seconds. Remaining residual: %e\n", iteration, time2-time, abs_max(r));     
            iterations_out = iteration + 1;
            return true; 
         }

         double rho_old = rho;
         
         multiply(fixed_matrix, r, Ar); 
         rho = dot(r,Ar);
         double beta = rho/rho_old; 

         add_scaled2(beta,r,p); 
         add_scaled2(beta,Ar,Ap); 
         
      }
      
      iterations_out = iteration;
      printf("*** CRSolver: No convergence after %d iterations! Remaining residual %e ***\n", iteration, abs_max(r));

      return false;
   }


};





#endif

#ifndef CGSOLVER_H
#define CGSOLVER_H

#include <fstream>
#include "sparse/sparsematrix.h"
#include "sparse/sparseilu.h"
#include "sparse/sparsemilu.h"
#include "wallclocktime.h"
#include "vector_math.h"

#define MODIFIED
//#define DEBUG_MATLAB_DUMP


template <class T>
class CGSolver {
   
   //Incomplete cholesky factor
#ifdef MODIFIED
   SparseColumnLowerFactor<T> ic_factor;
#else
   SparseLowerFactor<T> ic_factor;
#endif
   
   //CG temporary vectors
   std::vector<T> m, z, s, r;

   // used within loop
   FixedSparseMatrix<T> fixed_matrix;

public:

   //Parameters
   T tolerance_factor;
   int max_iterations;
   T modified_incomplete_cholesky_parameter;
   T min_diagonal_ratio;

   CGSolver()
   {
      set_solver_parameters(1e-5f, 100, 0.97, 0.25);
   }

   void set_solver_parameters(T tolerance_factor_, int max_iterations_, T modified_incomplete_cholesky_parameter_ = 0.97, T min_diagonal_ratio_=0.25)
   {
      tolerance_factor=tolerance_factor_;
      if(tolerance_factor<1e-30) tolerance_factor=1e-30;
      max_iterations=max_iterations_;
      modified_incomplete_cholesky_parameter=modified_incomplete_cholesky_parameter_;
      min_diagonal_ratio = min_diagonal_ratio_;
   }

   bool solve(const SparseMatrix<T>& matrix, const std::vector<T> & rhs, std::vector<T> & result, T& residual_out, int& iterations_out) 
   {
#ifdef DEBUG_MATLAB_DUMP
      static int suspicious_frame=0;
#endif
      
      if(m.size() != matrix.n) {
         m.resize(matrix.n);
         s.resize(matrix.n);
         z.resize(matrix.n);
         r.resize(matrix.n);
         zero(m);
         zero(s);
         zero(z);
         zero(r);
      }
      copy(rhs,r);
      double t0 = get_time_in_seconds();
      form_preconditioner(matrix);
      double t1 = get_time_in_seconds();
      
      double time = get_time_in_seconds();
      fixed_matrix.construct_from_matrix(matrix);

      zero(result);
      residual_out = abs_max(r);
      double tol=tolerance_factor*residual_out;
      if(residual_out == 0) {
         printf("CGSolver: Completed. Input was an exact solution.\n");
         iterations_out = 0;
         return true;
      }

      apply_preconditioner(r, z);

      copy(z, s);
      double rho=dot(z, r);
      if(rho==0 || rho!=rho) {
         printf("*** CGSolver: Crashed early! rho = %f ***\n", rho);
         iterations_out = 0;
#ifdef DEBUG_MATLAB_DUMP
         char dumpname[100];
         std::sprintf(dumpname, "linearsystem%d.m", suspicious_frame++); 
         std::ofstream output(dumpname);
         output.precision(18);
         fixed_matrix.write_matlab(output, "A");
         ic_factor.write_matlab(output, "L");
         write_matlab(output, rhs, "b");
         write_matlab(output, result, "x");
#endif
         return false;
      }

      int iteration;
      for(iteration=0; iteration<max_iterations; ++iteration){
         multiply(fixed_matrix, s, z);
         double alpha=rho/dot(s, z);
         add_scaled(alpha, s, result);
         add_scaled(-alpha, z, r);
         residual_out = abs_max(r);
         if(residual_out <= tol) {
            double time2 = get_time_in_seconds();
            printf("CGSolver: Completed, %d iterations in %f seconds. Remaining residual: %e\n", iteration, time2-time, abs_max(r));     
            printf("          Time to form preconditioner: %f seconds\n", t1-t0);
            iterations_out = iteration + 1;
#ifdef DEBUG_MATLAB_DUMP
            if(iterations_out==1){
               char dumpname[100];
               std::sprintf(dumpname, "linearsystem%d.m", suspicious_frame++); 
               std::ofstream output(dumpname);
               output.precision(18);
               fixed_matrix.write_matlab(output, "A");
               ic_factor.write_matlab(output, "L");
               write_matlab(output, rhs, "b");
               write_matlab(output, result, "x");
            }
#endif
            return true; 
         }
         
         apply_preconditioner(r, z);

         double rho_new=dot(z, r);
         double beta=rho_new/rho;
         add_scaled(beta, s, z); s.swap(z); // s=beta*s+z
         rho=rho_new;
      }
      
      iterations_out = iteration;
      printf("*** CGSolver: No convergence after %d iterations! Remaining residual %e ***\n", iteration, abs_max(r));
#ifdef DEBUG_MATLAB_DUMP
      char dumpname[100];
      std::sprintf(dumpname, "linearsystem%d.m", suspicious_frame++); 
      std::ofstream output(dumpname);
      output.precision(18);
      fixed_matrix.write_matlab(output, "A");
      ic_factor.write_matlab(output, "L");
      write_matlab(output, rhs, "b");
      write_matlab(output, result, "x");
#endif
      return false;
   }

protected:

   void form_preconditioner(const SparseMatrix<T>& matrix) {
      
#ifdef MODIFIED
      factor_modified_incomplete_cholesky0(matrix, ic_factor);
#else
      factor_incomplete_cholesky0(matrix, ic_factor, min_diagonal_ratio);
#endif
   }

   void apply_preconditioner(const std::vector<T> &x, std::vector<T> &result) {
      solve_lower(ic_factor, x, result);
      solve_lower_transpose_in_place(ic_factor,result);
   }

};





#endif

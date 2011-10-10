#ifndef SPARSEILU_H
#define SPARSEILU_H

#include <cmath>
#include "sparsematrix.h"
#include "incomplete_qr.h"

template<class T>
struct SparseLowerFactor
{
   unsigned int n;
   std::vector<T> invdiag; // reciprocals of diagonal elements
   std::vector<T> value; // values below the diagonal, listed row by row
   std::vector<unsigned int> colindex; // a list of all columns indices, for each row in turn
   std::vector<unsigned int> rowstart; // where each row begins in colindex (plus an extra entry at the end, of #nonzeros)

   explicit SparseLowerFactor(unsigned int n_=0)
      : n(n_), invdiag(n_), rowstart(n_+1)
   {}

   void clear(void)
   {
      n=0;
      invdiag.clear();
      value.clear();
      colindex.clear();
      rowstart.clear();
   }

   void resize(unsigned int n_)
   {
      n=n_;
      invdiag.resize(n);
      rowstart.resize(n+1);
   }

   void write_matlab(std::ostream &output, const char *variable_name)
   {
      output<<variable_name<<"=sparse([";
      for(unsigned int i=0; i<n; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<i+1<<" ";
         }
         output<<i+1<<" ";
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<n; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<colindex[j]+1<<" ";
         }
         output<<i+1<<" ";
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<n; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<value[j]<<" ";
         }
         output<<1/invdiag[i]<<" ";
      }
      output<<"], "<<n<<", "<<n<<");"<<std::endl;
   }
};

typedef SparseLowerFactor<float> SparseLowerFactorf;
typedef SparseLowerFactor<double> SparseLowerFactord;

template<class T>
void factor_incomplete_cholesky0(const SparseMatrix<T> &matrix, SparseLowerFactor<T> &factor,
                                 T min_diagonal_ratio=0.25)
{
   // first copy lower triangle of matrix into factor
   factor.resize(matrix.n);
   factor.value.resize(0);
   factor.colindex.resize(0);
   for(unsigned int i=0; i<matrix.n; ++i){
      factor.rowstart[i]=(unsigned int)factor.colindex.size();
      for(unsigned int j=0; j<matrix.index[i].size(); ++j){
         if(matrix.index[i][j]<i){
            factor.colindex.push_back(matrix.index[i][j]);
            factor.value.push_back(matrix.value[i][j]);
         }else if(matrix.index[i][j]==i)
            factor.invdiag[i]=matrix.value[i][j];
         else
            break;
      }
   }
   int small_pivot_count = 0;
   factor.rowstart[matrix.n]=(unsigned int)factor.colindex.size();
   // now do the incomplete factorization (figure out numerical values)
   for(unsigned int i=0; i<matrix.n; ++i){
      T d=factor.invdiag[i]; // start of computing the diagonal entry L(i,i)
      if(d==0) continue; // null row/column
      // do the offdiagonal entries in row i
      for(unsigned int k=factor.rowstart[i]; k<factor.rowstart[i+1]; ++k){
         unsigned int j=factor.colindex[k];
         // figure out off-diagonal entry L(i,j)=(A(i,j)-L(i,1:j-1)*L(j,1:j-1)')/L(j,j)
         unsigned int a=factor.rowstart[i], b=factor.rowstart[j];
         while(a<k && b<factor.rowstart[j+1]){
            if(factor.colindex[a]==factor.colindex[b]){
               factor.value[k]-=factor.value[a]*factor.value[b];
               ++a;
               ++b;
            }else if(factor.colindex[a]<factor.colindex[b])
               ++a;
            else
               ++b;
         }
         factor.value[k]*=factor.invdiag[j];
         d-=sqr(factor.value[k]);
      }
      // safety check for dangerously small pivots
      if(d<min_diagonal_ratio*factor.invdiag[i]){
         d=factor.invdiag[i]; // drop to Gauss-Seidel in this case
         ++small_pivot_count;
      }
      factor.invdiag[i]=1/std::sqrt(d);
   }
   if(small_pivot_count) {
      printf("Warning: %d small pivots encountered while forming preconditioner.\n", small_pivot_count);
   }
}

// this only works for T=double at the moment!
template<class T>
void factor_incomplete_qr(const FixedSparseMatrix<T> &J, const SparseMatrix<T> &JJtranspose,
                          SparseLowerFactor<T> &factor, T Qdroptol=0.1)
{
   // first copy structure of lower triangle of matrix into factor
   factor.resize(JJtranspose.m);
   factor.colindex.resize(0);
   for(unsigned int i=0; i<JJtranspose.m; ++i){
      factor.rowstart[i]=(unsigned int)factor.colindex.size();
      for(unsigned int j=0; j<JJtranspose.index[i].size(); ++j){
         if(JJtranspose.index[i][j]<i) factor.colindex.push_back(JJtranspose.index[i][j]);
      }
   }
   factor.rowstart[JJtranspose.m]=(unsigned int)factor.colindex.size();
   factor.value.resize(factor.colindex.size());
   // do the incomplete QR factorization (actually LQ, since we're using rows here but the routine is phrased in terms of columns)
   incomplete_qr(J.n, J.m, &J.rowstart[0], &J.colindex[0], &J.value[0], Qdroptol, &factor.rowstart[0], &factor.colindex[0], &factor.value[0], &factor.invdiag[0]);
   // correct for zero diagonal entries
   int small_pivot_count=0;
   for(unsigned int i=0; i<J.m; ++i){
      if(factor.invdiag[i]>0) factor.invdiag[i]=1/factor.invdiag[i];
      else ++small_pivot_count;
   }
   if(small_pivot_count){
      printf("Warning: %d small pivots encountered while forming preconditioner.\n", small_pivot_count);
   }
}

// solve L*result=rhs
template<class T>
void solve_lower(const SparseLowerFactor<T> &factor, const std::vector<T> &rhs, std::vector<T> &result)
{
   assert(factor.n==rhs.size());
   assert(factor.n==result.size());
   for(unsigned int i=0; i<factor.n; ++i){
      T d=0;
      for(unsigned int j=factor.rowstart[i]; j<factor.rowstart[i+1]; ++j){
         d+=factor.value[j]*result[factor.colindex[j]];
      }
      result[i]=(rhs[i]-d)*factor.invdiag[i];
   }
}

// solve L^T*result=rhs
template<class T>
void solve_lower_transpose_in_place(const SparseLowerFactor<T> &factor, std::vector<T> &x)
{
   assert(factor.n==x.size());
   unsigned int i=factor.n;
   do{
      --i;
      x[i]*=factor.invdiag[i];
      for(unsigned int j=factor.rowstart[i]; j<factor.rowstart[i+1]; ++j){
         x[factor.colindex[j]]-=factor.value[j]*x[i]; 
      }
   }while(i!=0);
}

#endif

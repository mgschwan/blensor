#ifndef SPARSEMILU_H
#define SPARSEMILU_H

#include <cmath>
#include "blas_wrapper.h"
#include "sparsematrix.h"

template<class T>
struct SparseColumnLowerFactor{
   unsigned int n;
   std::vector<T> invdiag; // reciprocals of diagonal elements
   std::vector<T> value; // values below the diagonal, listed column by column
   std::vector<unsigned int> rowindex; // a list of all row indices, for each column in turn
   std::vector<unsigned int> colstart; // where each column begins in rowindex (plus an extra entry at the end, of #nonzeros)
   std::vector<T> adiag; // just used in factorization: minimum "safe" diagonal entry allowed

   explicit SparseColumnLowerFactor(unsigned int n_=0)
      : n(n_), invdiag(n_), colstart(n_+1), adiag(n_)
   {}

   void clear(void)
   {
      n=0;
      invdiag.clear();
      value.clear();
      rowindex.clear();
      colstart.clear();
      adiag.clear();
   }

   void resize(unsigned int n_)
   {
      n=n_;
      invdiag.resize(n);
      colstart.resize(n+1);
      adiag.resize(n);
   }

   void write_matlab(std::ostream &output, const char *variable_name)
   {
      output<<variable_name<<"=sparse([";
      for(unsigned int i=0; i<n; ++i){
         output<<" "<<i+1;
         for(unsigned int j=colstart[i]; j<colstart[i+1]; ++j){
            output<<" "<<rowindex[j]+1;
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<n; ++i){
         output<<" "<<i+1;
         for(unsigned int j=colstart[i]; j<colstart[i+1]; ++j){
            output<<" "<<i+1;
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<n; ++i){
         output<<" "<<(invdiag[i]!=0 ? 1/invdiag[i] : 0);
         for(unsigned int j=colstart[i]; j<colstart[i+1]; ++j){
            output<<" "<<value[j];
         }
      }
      output<<"], "<<n<<", "<<n<<");"<<std::endl;
   }
};

typedef SparseColumnLowerFactor<float> SparseColumnLowerFactorf;
typedef SparseColumnLowerFactor<double> SparseColumnLowerFactord;

template<class T>
void factor_modified_incomplete_cholesky0(const SparseMatrix<T> &matrix, SparseColumnLowerFactor<T> &factor,
                                          T modification_parameter=0.97, T min_diagonal_ratio=0.25)
{
   // first copy lower triangle of matrix into factor (Note: assuming A is symmetric of course!)
   factor.resize(matrix.n);
   zero(factor.invdiag); // important: eliminate old values from previous solves!
   factor.value.resize(0);
   factor.rowindex.resize(0);
   zero(factor.adiag);
   for(unsigned int i=0; i<matrix.n; ++i){
      factor.colstart[i]=(unsigned int)factor.rowindex.size();
      for(unsigned int j=0; j<matrix.index[i].size(); ++j){
         if(matrix.index[i][j]>i){
            factor.rowindex.push_back(matrix.index[i][j]);
            factor.value.push_back(matrix.value[i][j]);
         }else if(matrix.index[i][j]==i){
            factor.invdiag[i]=factor.adiag[i]=matrix.value[i][j];
         }
      }
   }
   factor.colstart[matrix.n]=(unsigned int)factor.rowindex.size();
   // now do the incomplete factorization (figure out numerical values)

   // MATLAB code:
   // L=tril(A);
   // for k=1:size(L,2)
   //   L(k,k)=sqrt(L(k,k));
   //   L(k+1:end,k)=L(k+1:end,k)/L(k,k);
   //   for j=find(L(:,k))'
   //     if j>k
   //       fullupdate=L(:,k)*L(j,k);
   //       incompleteupdate=fullupdate.*(A(:,j)~=0);
   //       missing=sum(fullupdate-incompleteupdate);
   //       L(j:end,j)=L(j:end,j)-incompleteupdate(j:end);
   //       L(j,j)=L(j,j)-omega*missing;
   //     end
   //   end
   // end
   int small_pivot_count = 0;
   for(unsigned int k=0; k<matrix.n; ++k){
      if(factor.adiag[k]==0) continue; // null row/column
      // figure out the final L(k,k) entry
      if(factor.invdiag[k]<min_diagonal_ratio*factor.adiag[k]) {
         factor.invdiag[k]=1/sqrt(factor.adiag[k]); // drop to Gauss-Seidel here if the pivot looks dangerously small
         ++small_pivot_count;
      }
      else
         factor.invdiag[k]=1/sqrt(factor.invdiag[k]);
      // finalize the k'th column L(:,k)
      for(unsigned int p=factor.colstart[k]; p<factor.colstart[k+1]; ++p){
         factor.value[p]*=factor.invdiag[k];
      }
      // incompletely eliminate L(:,k) from future columns, modifying diagonals
      for(unsigned int p=factor.colstart[k]; p<factor.colstart[k+1]; ++p){
         unsigned int j=factor.rowindex[p]; // work on column j
         T multiplier=factor.value[p];
         T missing=0;
         unsigned int a=factor.colstart[k];
         // first look for contributions to missing from dropped entries above the diagonal in column j
         unsigned int b=0;
         while(a<factor.colstart[k+1] && factor.rowindex[a]<j){
            // look for factor.rowindex[a] in matrix.index[j] starting at b
            while(b<matrix.index[j].size()){
               if(matrix.index[j][b]<factor.rowindex[a])
                  ++b;
               else if(matrix.index[j][b]==factor.rowindex[a])
                  break;
               else{
                  missing+=factor.value[a];
                  break;
               }
            }
            ++a;
         }
         // adjust the diagonal j,j entry
         if(a<factor.colstart[k+1] && factor.rowindex[a]==j){
            factor.invdiag[j]-=multiplier*factor.value[a];
         }
         ++a;
         // and now eliminate from the nonzero entries below the diagonal in column j (or add to missing if we can't)
         b=factor.colstart[j];
         while(a<factor.colstart[k+1] && b<factor.colstart[j+1]){
            if(factor.rowindex[b]<factor.rowindex[a])
               ++b;
            else if(factor.rowindex[b]==factor.rowindex[a]){
               factor.value[b]-=multiplier*factor.value[a];
               ++a;
               ++b;
            }else{
               missing+=factor.value[a];
               ++a;
            }
         }
         // and if there's anything left to do, add it to missing
         while(a<factor.colstart[k+1]){
            missing+=factor.value[a];
            ++a;
         }
         // and do the final diagonal adjustment from the missing entries
         factor.invdiag[j]-=modification_parameter*multiplier*missing;
      }
   }
   if(small_pivot_count > 0) {
      printf("Warning: %d small pivots encountered while forming preconditioner.\n", small_pivot_count);
   }
}

// solve L*result=rhs
template<class T>
void solve_lower(const SparseColumnLowerFactor<T> &factor, const std::vector<T> &rhs, std::vector<T> &result)
{
   assert(factor.n==rhs.size());
   assert(factor.n==result.size());
   BLAS::copy(factor.n, &rhs[0], &result[0]);
   for(unsigned int i=0; i<factor.n; ++i){
      result[i]*=factor.invdiag[i];
      for(unsigned int j=factor.colstart[i]; j<factor.colstart[i+1]; ++j){
         result[factor.rowindex[j]]-=factor.value[j]*result[i];
      }
   }
}

// solve L^T*result=rhs
template<class T>
void solve_lower_transpose_in_place(const SparseColumnLowerFactor<T> &factor, std::vector<T> &x)
{
   assert(factor.n==x.size());
   assert(factor.n>0);
   unsigned int i=factor.n;
   do{
      --i;
      for(unsigned int j=factor.colstart[i]; j<factor.colstart[i+1]; ++j){
         x[i]-=factor.value[j]*x[factor.rowindex[j]];
      }
      x[i]*=factor.invdiag[i];
   }while(i!=0);
}

#endif

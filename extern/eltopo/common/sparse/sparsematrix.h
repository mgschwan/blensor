#ifndef SPARSEMATRIX_H
#define SPARSEMATRIX_H

// using a variant on CSR format

#include <iostream>
#include <vector>
#include "util.h"
#include <assert.h>

template<class T>
struct SparseMatrix
{
   unsigned int m, n; // dimensions
   std::vector<std::vector<unsigned int> > index; // for each row, a list of all column indices (sorted)
   std::vector<std::vector<T> > value; // values corresponding to index

   explicit SparseMatrix(unsigned int m_=0)
      : m(m_), n(m_), index(m_), value(m_)
   {
      const unsigned int expected_nonzeros_per_row=7;
      for(unsigned int i=0; i<m; ++i){
         index[i].reserve(expected_nonzeros_per_row);
         value[i].reserve(expected_nonzeros_per_row);
      }
   }

   explicit SparseMatrix(unsigned int m_, unsigned int n_, unsigned int expected_nonzeros_per_row)
      : m(m_), n(n_), index(m_), value(m_)
   {
      for(unsigned int i=0; i<m; ++i){
         index[i].reserve(expected_nonzeros_per_row);
         value[i].reserve(expected_nonzeros_per_row);
      }
   }

   void clear(void)
   {
      m=n=0;
      index.clear();
      value.clear();
   }

   void zero(void)
   {
      for(unsigned int i=0; i<m; ++i){
         index[i].resize(0);
         value[i].resize(0);
      }
   }

   void resize(unsigned int m_, unsigned int n_)
   {
      m=m_;
      n=n_;
      index.resize(m);
      value.resize(m);
   }

   T operator()(unsigned int i, unsigned int j) const
   {
      assert(i<m && j<n);
      for(unsigned int k=0; k<index[i].size(); ++k){
         if(index[i][k]==j) return value[i][k];
         else if(index[i][k]>j) return 0;
      }
      return 0;
   }

   void set_element(unsigned int i, unsigned int j, T new_value)
   {
      assert(i<m && j<n);
      unsigned int k=0;
      for(; k<index[i].size(); ++k){
         if(index[i][k]==j){
            value[i][k]=new_value;
            return;
         }else if(index[i][k]>j){
            insert(index[i], k, j);
            insert(value[i], k, new_value);
            return;
         }
      }
      index[i].push_back(j);
      value[i].push_back(new_value);
   }

   void add_to_element(unsigned int i, unsigned int j, T increment_value)
   {
      assert(i<m && j<n);
      unsigned int k=0;
      for(; k<index[i].size(); ++k){
         if(index[i][k]==j){
            value[i][k]+=increment_value;
            return;
         }else if(index[i][k]>j){
            insert(index[i], k, j);
            insert(value[i], k, increment_value);
            return;
         }
      }
      index[i].push_back(j);
      value[i].push_back(increment_value);
   }

   // assumes indices is already sorted
   void add_sparse_row(unsigned int i, const std::vector<unsigned int> &indices, const std::vector<T> &values)
   {
      assert(i<m);
      unsigned int j=0, k=0;
      while(j<indices.size() && k<index[i].size()){
         if(index[i][k]<indices[j]){
            ++k;
         }else if(index[i][k]>indices[j]){
            insert(index[i], k, indices[j]);
            insert(value[i], k, values[j]);
            ++j;
         }else{
            value[i][k]+=values[j];
            ++j;
            ++k;
         }
      }
      for(; j<indices.size(); ++j){
         index[i].push_back(indices[j]);
         value[i].push_back(values[j]);
      }
   }

   // assumes indices is already sorted
   void add_sparse_row(unsigned int i, const std::vector<unsigned int> &indices, T multiplier, const std::vector<T> &values)
   {
      assert(i<m);
      unsigned int j=0, k=0;
      while(j<indices.size() && k<index[i].size()){
         if(index[i][k]<indices[j]){
            ++k;
         }else if(index[i][k]>indices[j]){
            insert(index[i], k, indices[j]);
            insert(value[i], k, multiplier*values[j]);
            ++j;
         }else{
            value[i][k]+=multiplier*values[j];
            ++j;
            ++k;
         }
      }
      for(;j<indices.size(); ++j){
         index[i].push_back(indices[j]);
         value[i].push_back(multiplier*values[j]);
      }
   }

   // assumes matrix has symmetric structure - so the indices in row i tell us which columns to delete i from
   void symmetric_remove_row_and_column(unsigned int i)
   {
      assert(m==n && i<m);
      for(unsigned int a=0; a<index[i].size(); ++a){
         unsigned int j=index[i][a]; // 
         for(unsigned int b=0; b<index[j].size(); ++b){
            if(index[j][b]==i){
               erase(index[j], b);
               erase(value[j], b);
               break;
            }
         }
      }
      index[i].resize(0);
      value[i].resize(0);
   }

   void write_matlab(std::ostream &output, const char *variable_name)
   {
      output<<variable_name<<"=sparse([";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=0; j<index[i].size(); ++j){
            output<<i+1<<" ";
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=0; j<index[i].size(); ++j){
            output<<index[i][j]+1<<" ";
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=0; j<value[i].size(); ++j){
            output<<value[i][j]<<" ";
         }
      }
      output<<"], "<<m<<", "<<n<<");"<<std::endl;
   }
};

typedef SparseMatrix<float> SparseMatrixf;
typedef SparseMatrix<double> SparseMatrixd;

// perform result=matrix*x
template<class T>
void multiply(const SparseMatrix<T> &matrix, const std::vector<T> &x, std::vector<T> &result)
{
   assert(matrix.n==x.size());
   result.resize(matrix.m);
   for(unsigned int i=0; i<matrix.m; ++i){
      result[i]=0;
      for(unsigned int j=0; j<matrix.index[i].size(); ++j){
         result[i]+=matrix.value[i][j]*x[matrix.index[i][j]];
      }
   }
}

// perform result=result-matrix*x
template<class T>
void multiply_and_subtract(const SparseMatrix<T> &matrix, const std::vector<T> &x, std::vector<T> &result)
{
   assert(matrix.n==x.size());
   result.resize(matrix.m);
   for(unsigned int i=0; i<matrix.m; ++i){
      for(unsigned int j=0; j<matrix.index[i].size(); ++j){
         result[i]-=matrix.value[i][j]*x[matrix.index[i][j]];
      }
   }
}

// compute C=A*B (B might equal A)
template<class T>
void multiply_sparse_matrices(const SparseMatrix<T> &A, const SparseMatrix<T> &B, SparseMatrix<T> &C)
{
   assert(A.n==B.m);
   C.resize(A.m, B.n);
   C.zero();
   for(unsigned int i=0; i<A.m; ++i){
      for(unsigned int p=0; p<A.index[i].size(); ++p){
         unsigned int k=A.index[i][p];
         C.add_sparse_row(i, B.index[k], A.value[i][p], B.value[k]);
      }
   }
}

// compute C=A^T*B (B might equal A)
template<class T>
void multiply_AtB(const SparseMatrix<T> &A, const SparseMatrix<T> &B, SparseMatrix<T> &C)
{
   assert(A.m==B.m);
   C.resize(A.n, B.n);
   C.zero();
   for(unsigned int k=0; k<A.m; ++k){
      for(unsigned int p=0; p<A.index[k].size(); ++p){
         unsigned int i=A.index[k][p];
         C.add_sparse_row(i, B.index[k], A.value[k][p], B.value[k]);
      }
   }
}

// compute C=A*D*B (B might equal A)
template<class T>
void multiply_sparse_matrices_with_diagonal_weighting(const SparseMatrix<T> &A, const std::vector<T> &diagD,
                                                      const SparseMatrix<T> &B, SparseMatrix<T> &C)
{
   assert(A.n==B.m);
   assert(diagD.size()==A.n);
   C.resize(A.m, B.n);
   C.zero();
   for(unsigned int i=0; i<A.m; ++i){
      for(unsigned int p=0; p<A.index[i].size(); ++p){
         unsigned int k=A.index[i][p];
         C.add_sparse_row(i, B.index[k], A.value[i][p]*diagD[k], B.value[k]);
      }
   }
}

// compute C=A^T*D*B (B might equal A)
template<class T>
void multiply_AtDB(const SparseMatrix<T> &A, const std::vector<T>& diagD, const SparseMatrix<T> &B, SparseMatrix<T> &C)
{
   assert(A.m==B.m);
   C.resize(A.n, B.n);
   C.zero();
   for(unsigned int k=0; k<A.m; ++k){
      for(unsigned int p=0; p<A.index[k].size(); ++p){
         unsigned int i=A.index[k][p];
         C.add_sparse_row(i, B.index[k], A.value[k][p]*diagD[k], B.value[k]);
      }
   }
}

// set T to the transpose of A
template<class T>
void compute_transpose(const SparseMatrix<T> &A, SparseMatrix<T> &C)
{
   C.resize(A.n, A.m);
   C.zero();
   for(unsigned int i=0; i<A.m; ++i){
      for(unsigned int p=0; p<A.index[i].size(); ++p){
         unsigned int k=A.index[i][p];
         C.index[k].push_back(i);
         C.value[k].push_back(A.value[i][p]);
      }
   }
}

template<class T>
struct FixedSparseMatrix
{
   unsigned int m, n; // dimension
   std::vector<T> value; // nonzero values row by row
   std::vector<unsigned int> colindex; // corresponding column indices
   std::vector<unsigned int> rowstart; // where each row starts in value and colindex (and last entry is one past the end, the number of nonzeros)

   explicit FixedSparseMatrix(unsigned int m_=0)
      : m(m_), n(m_), value(0), colindex(0), rowstart(m_+1)
   {}

   explicit FixedSparseMatrix(unsigned int m_, unsigned int n_)
      : m(m_), n(n_), value(0), colindex(0), rowstart(m_+1)
   {}

   void clear(void)
   {
      m=n=0;
      value.clear();
      colindex.clear();
      rowstart.clear();
   }

   void resize(unsigned int m_, unsigned int n_)
   {
      m=m_;
      n=n_;
      rowstart.resize(m+1);
   }

   void construct_from_matrix(const SparseMatrix<T> &matrix)
   {
      resize(matrix.m, matrix.n);
      rowstart[0]=0;
      for(unsigned int i=0; i<m; ++i){
         rowstart[i+1]=rowstart[i]+matrix.index[i].size();
      }
      value.resize(rowstart[m]);
      colindex.resize(rowstart[m]);
      unsigned int j=0;
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int k=0; k<matrix.index[i].size(); ++k){
            value[j]=matrix.value[i][k];
            colindex[j]=matrix.index[i][k];
            ++j;
         }
      }
   }

   void write_matlab(std::ostream &output, const char *variable_name)
   {
      output<<variable_name<<"=sparse([";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<i+1<<" ";
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<colindex[j]+1<<" ";
         }
      }
      output<<"],...\n  [";
      for(unsigned int i=0; i<m; ++i){
         for(unsigned int j=rowstart[i]; j<rowstart[i+1]; ++j){
            output<<value[j]<<" ";
         }
      }
      output<<"], "<<m<<", "<<n<<");"<<std::endl;
   }
};

typedef FixedSparseMatrix<float> FixedSparseMatrixf;
typedef FixedSparseMatrix<double> FixedSparseMatrixd;

// perform result=matrix*x
template<class T>
void multiply(const FixedSparseMatrix<T> &matrix, const std::vector<T> &x, std::vector<T> &result)
{
   assert(matrix.n==x.size());
   result.resize(matrix.m);
   for(unsigned int i=0; i<matrix.m; ++i){
      result[i]=0;
      for(unsigned int j=matrix.rowstart[i]; j<matrix.rowstart[i+1]; ++j){
         result[i]+=matrix.value[j]*x[matrix.colindex[j]];
      }
   }
}

// perform result=result-matrix*x
template<class T>
void multiply_and_subtract(const FixedSparseMatrix<T> &matrix, const std::vector<T> &x, std::vector<T> &result)
{
   assert(matrix.n==x.size());
   result.resize(matrix.m);
   for(unsigned int i=0; i<matrix.m; ++i){
      for(unsigned int j=matrix.rowstart[i]; j<matrix.rowstart[i+1]; ++j){
         result[i]-=matrix.value[j]*x[matrix.colindex[j]];
      }
   }
}

#endif

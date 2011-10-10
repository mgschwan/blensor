#include <cmath>
#include <list>
#include <vector>
#include "incomplete_qr.h"

/* The MATLAB code for this algorithm:
for i=1:n
   q=A(:,i);
   for j=find(Rpattern(1:i-1,i))'
      R(j,i)=Q(:,j)'*q;
      q=q-Q(:,j)*R(j,i);
   end
   R(i,i)=norm(q);
   q=q.*(abs(q)>Qdroptol*R(i,i));
   Q(:,i)=q/(norm(q)+1e-300);
end
*/

static inline double sqr(double x)
{
   return x*x;
}

struct SparseEntry
{
   int index;
   double value;

   SparseEntry(void) {}
   SparseEntry(int index_, double value_) : index(index_), value(value_) {}
   bool operator<(const SparseEntry &e) const { return index<e.index; }
};

typedef std::list<SparseEntry> DynamicSparseVector;
typedef std::vector<SparseEntry> StaticSparseVector;

static void copy_column(int colstart, int nextcolstart, const int *rowindex, const double *value,
                        DynamicSparseVector &v)
{
   for(int i=colstart; i<nextcolstart; ++i)
      v.push_back(SparseEntry(rowindex[i], value[i]));
}

static double dot_product(const StaticSparseVector &u, const DynamicSparseVector &v)
{
   StaticSparseVector::const_iterator p=u.begin();
   if(p==u.end()) return 0;
   DynamicSparseVector::const_iterator q=v.begin();
   if(q==v.end()) return 0;
   double result=0;
   for(;;){
      if(p->index < q->index){
         ++p; if(p==u.end()) break;
      }else if(p->index > q->index){
         ++q; if(q==v.end()) break;
      }else{ // p->index == q->index
         result+=p->value*q->value;
         ++p; if(p==u.end()) break;
         ++q; if(q==v.end()) break;
      }
   }
   return result;
}

static void add_to_vector(double multiplier, const StaticSparseVector &u, DynamicSparseVector &v)
{
   StaticSparseVector::const_iterator p=u.begin();
   if(p==u.end()) return;
   DynamicSparseVector::iterator q=v.begin();
   for(;;){
      if(q==v.end()) break;
      if(p->index < q->index){
         q=v.insert(q, SparseEntry(p->index, multiplier*p->value));
         ++p; if(p==u.end()) return;
      }else if(p->index > q->index){
         ++q; if(q==v.end()) break;
      }else{ // p->index == q->index){
         q->value+=multiplier*p->value;
         ++p; if(p==u.end()) return;
         ++q; if(q==v.end()) break;
      }
   }
   for(;;){
      v.push_back(SparseEntry(p->index, multiplier*p->value));
      ++p; if(p==u.end()) return;
   }
}

static double vector_norm(const DynamicSparseVector &v)
{
   double norm_squared=0;
   DynamicSparseVector::const_iterator p;
   for(p=v.begin(); p!=v.end(); ++p) norm_squared+=sqr(p->value);
   return std::sqrt(norm_squared);
}

static void copy_large_entries(const DynamicSparseVector &u, double threshhold, StaticSparseVector &v)
{
   DynamicSparseVector::const_iterator p;
   for(p=u.begin(); p!=u.end(); ++p){
      if(std::fabs(p->value)>threshhold) v.push_back(*p);
   }
}

static void normalize(StaticSparseVector &v)
{
   double norm_squared=0;
   StaticSparseVector::iterator p;
   for(p=v.begin(); p!=v.end(); ++p) norm_squared+=sqr(p->value);
   if(norm_squared>0){
      double scale=1/std::sqrt(norm_squared);
      for(p=v.begin(); p!=v.end(); ++p) p->value*=scale;
   }
}

void incomplete_qr(int m, int n, const int *Acolstart, const int *Arowindex, const double *Avalue,
                   double Qdroptol,
                   const int *Rcolstart, const int *Rrowindex, double *Rvalue, double *Rdiag)
{
   // column storage for intermediate Q
   std::vector<StaticSparseVector> Q(n);

   // for each column of Q, how many more times it will be used in making R
   // (once this gets decremented to zero, we can free the column)
   std::vector<int> dependency_count(n,0);
   for(int i=0; i<n; ++i){
      for(int a=Rcolstart[i]; a<Rcolstart[i+1]; ++a){
         int j=Rrowindex[a];
         if(j<i) ++dependency_count[j];
      }
   }

   // construct R a column at a time
   for(int i=0; i<n; ++i){
      DynamicSparseVector q;
      copy_column(Acolstart[i], Acolstart[i+1], Arowindex, Avalue, q);
      for(int a=Rcolstart[i]; a<Rcolstart[i+1]; ++a){
         int j=Rrowindex[a];
         if(j<i){
            Rvalue[a]=dot_product(Q[j], q);
            add_to_vector(-Rvalue[a], Q[j], q);
            --dependency_count[j];
            if(dependency_count[j]==0) Q[j].clear();
         }else // j>i
            Rvalue[a]=0; // ideally structure of R is upper triangular, so this waste of space won't happen
      }
      Rdiag[i]=vector_norm(q);
      copy_large_entries(q, Qdroptol*Rdiag[i], Q[i]);
      normalize(Q[i]);
   }
}


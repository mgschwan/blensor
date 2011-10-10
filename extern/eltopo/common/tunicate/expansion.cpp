// Released into the public-domain by Robert Bridson, 2009.

#include <cmath>
#include "expansion.h"

#define assert

//==============================================================================
static void
two_sum(double a,
        double b,
        double& x,
        double& y)
{
   x=a+b;
   double z=x-a;
   y=(a-(x-z))+(b-z);
}

//==============================================================================
// requires that |a|>=|b|
static void
fast_two_sum(double a,
             double b,
             double& x,
             double& y)
{
   assert(std::fabs(a)>=std::fabs(b));
   x=a+b;
   y=(a-x)+b;
}

//==============================================================================
static void
split(double a,
      double& x,
      double& y)
{
   double c=134217729*a;
   x=c-(c-a);
   y=a-x;
}

//==============================================================================
static void
two_product(double a,
            double b,
            double& x,
            double& y)
{
   x=a*b;
   double a1, a2, b1, b2;
   split(a, a1, a2);
   split(b, b1, b2);
   y=a2*b2-(((x-a1*b1)-a2*b1)-a1*b2);
}

//==============================================================================
void
add(double a, double b, expansion& sum)
{
   sum.resize(2);
   two_sum(a, b, sum[1], sum[0]);
}

//==============================================================================
// a and sum may be aliased to the same expansion for in-place addition
void
add(const expansion& a, double b, expansion& sum)
{
   unsigned int m=a.size();
   sum.reserve(m+1);
   double s;
   for(unsigned int i=0; i<m; ++i){
      two_sum(b, a[i], b, s);
      if(s) sum.push_back(s);
   }
   sum.push_back(b);
}

//==============================================================================
// aliasing a, b and sum is safe
void
add(const expansion& a, const expansion& b, expansion& sum)
{
   /* slow but obvious way of doing it
   add(a, b[0], sum);
   for(unsigned int i=1; i<b.size(); ++i)
      add(sum, b[i], sum); // aliasing sum is safe
   */
   // Shewchuk's fast-expansion-sum
   if(a.empty()){
      sum=b;
      return;
   }else if(b.empty()){
      sum=a;
      return;
   }
   expansion merge(a.size()+b.size(), 0);
   unsigned int i=0, j=0, k=0;
   for(;;){
      if(std::fabs(a[i])<std::fabs(b[j])){
         merge[k++]=a[i++];
         if(i==a.size()){
            while(j<b.size()) merge[k++]=b[j++];
            break;
         }
      }else{
         merge[k++]=b[j++];
         if(j==b.size()){
            while(i<a.size()) merge[k++]=a[i++];
            break;
         }
      }
   }
   sum.reserve(merge.size());
   sum.resize(0);
   double q, r;
   fast_two_sum(merge[1], merge[0], q, r);
   if(r) sum.push_back(r);
   for(i=2; i<merge.size(); ++i){
      two_sum(q, merge[i], q, r);
      if(r) sum.push_back(r);
   }
   if(q) sum.push_back(q);
}

//==============================================================================
void
subtract(const expansion& a, const expansion& b, expansion& difference)
{
   // could improve this a bit!
   expansion c;
   negative(b, c);
   add(a, c, difference);
}

//==============================================================================
void
negative(const expansion& input, expansion& output)
{
   output.resize(input.size());
   for(unsigned int i=0; i<input.size(); ++i)
      output[i]=-input[i];
}

//==============================================================================
void
multiply(double a, double b, expansion& product)
{
   product.resize(2);
   two_product(a, b, product[1], product[0]);
}

//==============================================================================
void
multiply(double a, double b, double c, expansion& product)
{
   expansion ab;
   multiply(a, b, ab);
   multiply(ab, c, product);
}

//==============================================================================
void
multiply(double a, double b, double c, double d, expansion& product)
{
   multiply(a, b, product);
   expansion abc;
   multiply(product, c, abc);
   multiply(abc, d, product);
}

//==============================================================================
void
multiply(const expansion& a, double b, expansion& product)
{
   // basic idea:
   // multiply each entry in a by b (producing two new entries), then
   // two_sum them in such a way to guarantee increasing/non-overlapping output
   product.resize(2*a.size());
   if(a.empty()) return;
   two_product(a[0], b, product[1], product[0]); // finalize product[0]
   double x, y, z;
   for(unsigned int i=1; i<a.size(); ++i){
      two_product(a[i], b, x, y);
      // finalize product[2*i-1]
      two_sum(product[2*i-1], y, z, product[2*i-1]);
      // finalize product[2*i], could be fast_two_sum instead
      fast_two_sum(x, z, product[2*i+1], product[2*i]);
   }
   // multiplication is a prime candidate for producing spurious zeros, so
   // remove them by default
   remove_zeros(product);
}

//==============================================================================
void
multiply(const expansion& a, const expansion& b, expansion& product)
{
   // most stupid way of doing it:
   // multiply a by each entry in b, add each to product
   product.resize(0);
   expansion term;
   for(unsigned int i=0; i<b.size(); ++i){
      multiply(a, b[i], term);
      add(product, term, product);
   }
}

//==============================================================================
void
remove_zeros(expansion& a)
{
   unsigned int i, j;
   for(i=0; i<a.size() && a[i]; ++i)
      ;
   for(++i, j=0; i<a.size(); ++i)
      if(a[i]){
         a[j]=a[i];
         ++j;
      }
   a.resize(j);
}

//==============================================================================
double
estimate(const expansion& a)
{
   double x=0;
   for(unsigned int i=0; i<a.size(); ++i)
      x+=a[i];
   return x;
}

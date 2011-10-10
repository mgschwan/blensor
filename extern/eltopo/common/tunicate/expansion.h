#ifndef EXPANSION_H
#define EXPANSION_H

// Released into the public-domain by Robert Bridson, 2009.
// Simple functions for manipulating multiprecision floating-point
// expansions, with simplicity favoured over speed.

#include <vector>

// The basic type is a vector of *increasing* and *nonoverlapping* doubles,
// apart from allowed zeroes anywhere.
typedef std::vector<double> expansion;

inline expansion
make_expansion(double a)
{ if(a) return expansion(1, a); else return expansion(); }

inline void
make_zero(expansion& e)
{ e.resize(0); }

void
add(double a, double b, expansion& sum);

// a and sum may be aliased to the same expansion for in-place addition
void
add(const expansion& a, double b, expansion& sum);

inline void
add(double a, const expansion& b, expansion& sum)
{ add(b, a, sum); }

// aliasing a, b and sum is safe
void
add(const expansion& a, const expansion& b, expansion& sum);

// aliasing a, b and difference is safe
void
subtract(const expansion& a, const expansion& b, expansion& difference);

// aliasing input and output is safe
void
negative(const expansion& input, expansion& output);

void
multiply(double a, double b, expansion& product);

void
multiply(double a, double b, double c, expansion& product);

void
multiply(double a, double b, double c, double d, expansion& product);

void
multiply(const expansion& a, double b, expansion& product);

inline void
multiply(double a, const expansion& b, expansion& product)
{ multiply(b, a, product); }

void
multiply(const expansion& a, const expansion& b, expansion& product);

void
remove_zeros(expansion& a);

double
estimate(const expansion& a);

#endif

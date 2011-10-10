#ifndef TRIANGLE__INDEX
#define TRIANGLE__INDEX

#include <iostream>
#include <fstream>

#include <vector>

#define EMPTY_TRIANGLE 500000000

class TriangleIndex
{
private :
  GLuint i;
public :
   TriangleIndex() : i(EMPTY_TRIANGLE)
   {}
  
  TriangleIndex(const GLuint x) : i(x)
  {}

  const GLuint getIndex() const
  {
    return i;
  }

  void setIndex(const GLuint x)
  {
    i = x;
  }

  const bool isEmpty() const
  {
    if (i == EMPTY_TRIANGLE)
      return true;
    else return false;
  }

  // ostream
  friend std::ostream& operator << (std::ostream& out, const TriangleIndex& ind)
  {
    out << ind.getIndex();
    return out;
  }
};

class TriangleIDTriplet
{
private :
  TriangleIndex i;
  TriangleIndex j;
  TriangleIndex k;

public :
  TriangleIDTriplet()
   :
   i ( TriangleIndex(EMPTY_TRIANGLE) ),
   j ( TriangleIndex(EMPTY_TRIANGLE) ),
   k ( TriangleIndex(EMPTY_TRIANGLE) )
   {}

  TriangleIDTriplet(const TriangleIndex x, const TriangleIndex y, const TriangleIndex z) : i(x), j(y), k(z)
  {
  }

  const TriangleIndex getFirstIndex() const
  {
    return i;
  }

  const TriangleIndex getSecondIndex() const
  {
    return j;
  }

  const TriangleIndex getThirdIndex() const
  {
    return k;
  }

  void setFirstIndex(const TriangleIndex t)
  {
    i = t;
  }

  void setSecondIndex(const TriangleIndex t)
  {
    j = t;
  }

  void setThirdIndex(const TriangleIndex t)
  {
    k = t;
  }  

  // ostream
  friend std::ostream& operator << (std::ostream& out, const TriangleIDTriplet& tr)
  {
    out << "[" << tr.getFirstIndex() << ", " << tr.getSecondIndex() << ", " <<tr.getThirdIndex() << "]";
    return out;
  }
};

typedef std::vector<TriangleIndex> TriangleIDVector;

#endif

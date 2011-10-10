#ifndef EDGE__HPP
#define EDGE__HPP

#include <iostream>
#include <fstream>


#define EMPTY_VERTEX 500000000

/*
  class VertexIndex
  {
  private :
  GLuint i;
  public :
  VertexIndex()
  {
  i = EMPTY_TRIANGLE;
  }
  
  VertexIndex(const GLuint x) : i(x)
  {
  }

  const GLuint getIndex() const
  {
  return i;
  }

  void setIndex(const GLuint x)
  {
  i = x;
  }

  const bool operator == (const VertexIndex& s) const
  {
  bool temp;
  temp = (i == s.getIndex());
  return temp;  
  }

  const bool operator != (const VertexIndex& s) const
  {
  return (!((*this) == s));
  }

  const bool operator < (const VertexIndex& s) const
  {
  bool temp;
  temp = (i < s.getIndex());
  return temp;  
  }

  // Ostream
  friend std::ostream& operator << (std::ostream& out, const VertexIndex& s)
  {
  out << s.getIndex();
  return out;
  }
  };
*/

/* This class defines a SORTED pair of int */

class Edge
{
   std::pair<int, int> p;
   
public :
  // Default constructor
   Edge() : p() {}
	
  // Copy constructor
  Edge(const Edge& s) : p( s.p.first, s.p.second )
  {
  }

  // Constructor by parameters
   Edge(int s1, int s2) : p()
  {
    if (s1 < s2)
      {
	p.first = s1;
	p.second = s2;
      }
    else
      {
	p.first = s2;
	p.second = s1;
      }
  }

  const bool operator == (const Edge& s) const
  {
    bool temp;
    temp = ((p.first == s.p.first) && (p.second == s.p.second));
    return temp;  
  }

  const bool operator != (const Edge& s) const
  {
    return (!((*this) == s));  
  }

  // Operator <
  const bool operator < (const Edge& s) const
  {
    bool temp;
    temp = (((p.first < s.p.first))
    	    || ((p.first == s.p.first) && (p.second < s.p.second)));
    return temp;  
  }
  
  
  // ostream
  friend std::ostream& operator << (std::ostream& out, const Edge& s)
  {
    out << "["<< s.p.first << ", " << s.p.second << "] ";
    return out;
  }
};

#endif

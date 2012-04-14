/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Michael Gschwandtner
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/python/mathutils/mathutils_eigen.c
 *  \ingroup mathutils
 *
 * This file defines the 'eigen' module, which provides access to some
 * Eigen3 functions
 */


/************************/
/* Blender Eigen Module */
/************************/

#include <Python.h>

#include "structseq.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "MEM_guardedalloc.h"

#include "mathutils.h"
#include "mathutils_eigen.h"

#include <Eigen/Core>
#include <Eigen/QR>
#include <Eigen/SVD>

#include <iostream>

/* This is a first test to write a new python module for blender
 */

/* Utilities */

typedef struct PyMatSize {
  Py_ssize_t rows;
  Py_ssize_t cols;
} PyMatSize;


/* Returns a float from a PyObject that is either a PyFloat or a PyLong.
 * It sets and optional error parameter if the object is incompatible 
 */
double getFloatFromObject(PyObject *obj, bool &error)
{
  if (PyFloat_Check(obj))
  {
      error = false;
      return PyFloat_AsDouble(obj);
  }
  
  if (PyLong_Check(obj))
  {
      error = false;
      return (double)PyLong_AsLong(obj);
  }

  error = true;
  return 0.0;
}


/* Returns the size of a matrix supplied as a list of lists 
 * Sets the error variable if not all rows have the same size
 */
PyMatSize getMatrixSize(PyObject *M, bool &error)
{

  PyMatSize result = {0,0};
  Py_ssize_t rows = PyList_Size(M);
  Py_ssize_t cols = 0;

  for (Py_ssize_t row=0; row < rows; row++)
  {
    PyObject *row_object = PyList_GetItem(M, row);

    if (PyList_Check(row_object))
    {
        if (cols != PyList_Size(row_object))
        {
          if (cols != 0)
          {
            /* The rowsize has changed, that must not happen */
            PyErr_SetString(PyExc_ValueError,"rows must have the same size");
            error = true;
            return result;
          }
          cols = PyList_Size(row_object);
        }
    }        
    else if (PyFloat_Check(row_object) || PyLong_Check(row_object))
    {
      if (cols < 2)
      {
         cols = 1;
      }
      else
      {
        /* The rowsize has changed, that must not happen */
        PyErr_SetString(PyExc_ValueError,"rows must have the same size");
        error = true;
        return result;
      }
    }
    else
    {
      PyErr_SetString(PyExc_ValueError,"row must be number or list");
      error = true;
      return result;
    }
  }
  error = false;
  result.rows = rows;
  result.cols = cols;
  return result;
}


template <typename T>
bool MatrixFromPyToEigen(PyObject *M, T &Mmat)
{
  bool error;
  PyMatSize Msize = getMatrixSize(M, error);
  
  if (error || Msize.rows != Mmat.rows() || Msize.cols != Mmat.cols())
  {
    PyErr_SetString(PyExc_ValueError, "Unknown Matrix error");
    /* Source and destination matrix have incompatible size */
    return false;
  }

  for (int row=0; row < Msize.rows; row++)
  {
    PyObject *row_object = PyList_GetItem(M, row);
    if (PyList_Check(row_object))
    {
      for (int col = 0; col < Msize.cols; col++)
      {
       
        PyObject *item = PyList_GetItem(row_object,col);
        Mmat(row,col) = getFloatFromObject(item, error);
        if (error)
        {
          PyErr_SetString(PyExc_ValueError, "Elements must be float");
          return false;
        }
      }
    }
    else
    {
       Mmat(row,0) = getFloatFromObject(row_object, error);
       if (error)
       {
         PyErr_SetString(PyExc_ValueError, "Elements must be float");
         return false;
       }
    }
  } 
  return true;
}



/*-------------------------DOC STRINGS ---------------------------*/
PyDoc_STRVAR(M_Eigen_doc,
"The Blender Eigen module"
);

/*------------------------------------------------------------*/
/* Python Functions */
/*------------------------------------------------------------*/

PyDoc_STRVAR(M_Eigen_solve_doc,
".. function:: solve(A,b)\n"
"\n"
"   Solves a system of linear equations Ax = b with Eigen::ColPivHouseholderQr\n"
"   Returns the array with the best solution.\n"
"\n"
"   :arg A: A nxm matrix with the coefficients\n"
"   :type: array\n"
"   :arg b: A n dimensional vector with the constants\n"
"   :type: array\n"
"   :arg solver: Which solver to be used (has to be one of eigen.solvers.*)\n"
"   :type: integer\n"
"   :return: The solution vector x\n"
"   :rtype: array\n"
);
static PyObject *M_Eigen_solve(PyObject *UNUSED(self), PyObject *args)
{
  PyObject* A = NULL;
  PyObject* b = NULL;
  PyMatSize Asize;
  PyMatSize bsize;
  int solver = EIGEN_COL_PIV_HOUSEHOLDER;
  bool error;

  if (!PyArg_ParseTuple(args, "O!O!|i", &PyList_Type, &A, &PyList_Type, &b, &solver))
    return 0;

  Asize = getMatrixSize(A, error);
  if (error) return 0;

  bsize = getMatrixSize(b, error);
  if (error)return 0;

  if (bsize.cols != 1 || bsize.rows != Asize.rows)
  {
    //We want to solve Ax=b so b must have exactly as many rows as A
    PyErr_SetString(PyExc_ValueError, "A.rows == b.rows is required");
    return 0;
  }

  /* The basic checks are done, now copy the data */

  Eigen::MatrixXd Amat(Asize.rows, Asize.cols);
  Eigen::VectorXd bvec(bsize.rows);

  if (!MatrixFromPyToEigen(A, Amat) || !MatrixFromPyToEigen(b, bvec))
  {
    return 0;
  }

  Eigen::VectorXd xvec;
  switch (solver)
  {
    case EIGEN_COL_PIV_HOUSEHOLDER:
          xvec = Amat.colPivHouseholderQr().solve(bvec);  
          break;
    case EIGEN_FULL_PIV_HOUSEHOLDER:
          xvec = Amat.fullPivHouseholderQr().solve(bvec);
          break;
    case EIGEN_JACOBI_SVD:
          xvec = Amat.jacobiSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(bvec);
          break;
    case EIGEN_INVALID_SOLVER:
    default:
          PyErr_SetString(PyExc_ValueError, "Invalid solver: Only values from eigen.solvers are allowed");
          return 0;
  }

  PyObject *result= PyList_New(Asize.cols);
  for (Py_ssize_t col=0; col < Asize.cols; col++)
  {
    PyList_SetItem(result, col, PyFloat_FromDouble(xvec(col)));
  }

	return result;
}

static PyMethodDef M_Eigen_methods[] = {
	{"solve", (PyCFunction) M_Eigen_solve, METH_VARARGS, M_Eigen_solve_doc},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef M_Eigen_module_def = {
	PyModuleDef_HEAD_INIT,
	"mathutils.eigen",  /* m_name */
	M_Eigen_doc,  /* m_doc */
	0,     /* m_size */
	M_Eigen_methods,  /* m_methods */
	NULL,  /* m_reload */
	NULL,  /* m_traverse */
	NULL,  /* m_clear */
	NULL,  /* m_free */
};


/*----------------------------MODULE INIT-------------------------*/
PyMODINIT_FUNC PyInit_mathutils_eigen(void)
{
	PyObject *submodule = PyModule_Create(&M_Eigen_module_def);
  PyObject *item_types;

	PyModule_AddObject(submodule, "solvers", (item_types = PyInit_mathutils_eigen_solvers()));
	PyDict_SetItemString(PyThreadState_GET()->interp->modules, "eigen.solvers", item_types);
	Py_INCREF(item_types);
	
	return submodule;
}

/*----------------------------SUBMODULE INIT-------------------------*/
static struct PyModuleDef M_EigenSolvers_module_def = {
	PyModuleDef_HEAD_INIT,
	"mathutils.eigen.solvers",  /* m_name */
	NULL,  /* m_doc */
	0,     /* m_size */
	NULL,  /* m_methods */
	NULL,  /* m_reload */
	NULL,  /* m_traverse */
	NULL,  /* m_clear */
	NULL,  /* m_free */
};

PyMODINIT_FUNC PyInit_mathutils_eigen_solvers(void)
{
	PyObject *submodule = PyModule_Create(&M_EigenSolvers_module_def);

	PyModule_AddIntConstant(submodule, (char *)"COL_PIV_HOUSEHOLDER", EIGEN_COL_PIV_HOUSEHOLDER);
	PyModule_AddIntConstant(submodule, (char *)"FULL_PIV_HOUSEHOLDER", EIGEN_FULL_PIV_HOUSEHOLDER);
	PyModule_AddIntConstant(submodule, (char *)"JACOBI_SVD", EIGEN_JACOBI_SVD);

	return submodule;
}


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

/* This is a first test to write a new python module for blender
 */

/* Utilities */

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
"   :arg A: A n dimensional vector with the constants\n"
"   :type: array\n"
"   :return: The solution vector x\n"
"   :rtype: array\n"
);
static PyObject *M_Eigen_solve(PyObject *UNUSED(self), PyObject *args)
{
  PyObject* A = NULL;
  PyObject* b = NULL;
  Py_ssize_t A_rows = 0;
  Py_ssize_t A_cols = 0;
  Py_ssize_t b_rows = 0;
  int idx;


  if (!PyArg_ParseTuple(args, "O!O!", &PyList_Type, &A, &PyList_Type, &b))
    return 0;

  
  A_rows = PyList_Size(A);
  for (idx=0; idx < A_rows; idx++)
  {
    PyObject *row = PyList_GetItem(A, idx);
    if (!PyList_Check(row))
    {
        PyErr_SetString(PyExc_ValueError, "rows must have size > 0");
        return 0;
    }

    if (A_cols !=  PyList_Size(row))
    {
      if (A_cols != 0)
      {
        PyErr_SetString(PyExc_ValueError, "rows must have the same size");
        return 0;
      }
      A_cols = PyList_Size(row);
    }
  } 
  if (A_cols == 0)
  {
    PyErr_SetString(PyExc_ValueError, "rows must have size > 0");
    return 0;
  }

  b_rows = PyList_Size(b);
  if (b_rows != A_rows)
  {
    //We want to solve Ax=b so b must have exactly as many rows as A
    PyErr_SetString(PyExc_ValueError, "A.rows == b.cols is required");
    return 0;
  }


  /* The basic checks are done, now copy the data */

  Eigen::MatrixXd Amat(A_rows, A_cols);
  Eigen::VectorXd bvec(b_rows);

  for (int row=0; row < A_rows; row++)
  {
    bool error;
    PyObject *row_object = PyList_GetItem(A, row);
    for (int col = 0; col < A_cols; col++)
    {
     
      PyObject *item = PyList_GetItem(row_object,col);
      Amat(row,col) = getFloatFromObject(item, error);
      if (error)
      {
          PyErr_SetString(PyExc_ValueError, "Elements must be float");
          return 0;
      }
    }

    PyObject *item = PyList_GetItem(b, row);
    bvec(row) = getFloatFromObject(item, error);
    if (error)
    {
        PyErr_SetString(PyExc_ValueError, "Elements must be float");
        return 0;
    }
  }

  //Solution
  Eigen::VectorXd xvec = Amat.colPivHouseholderQr().solve(bvec);  



  PyObject *result= PyList_New(A_cols);
  for (Py_ssize_t col=0; col < A_cols; col++)
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
	
	return submodule;
}



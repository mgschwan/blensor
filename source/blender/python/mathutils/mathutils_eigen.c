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

/* This is a first test to write a new python module for blender
 */

/*-------------------------DOC STRINGS ---------------------------*/
PyDoc_STRVAR(M_Eigen_doc,
"The Blender Eigen module"
);

/*------------------------------------------------------------*/
/* Python Functions */
/*------------------------------------------------------------*/

PyDoc_STRVAR(M_Eigen_test_doc,
".. function:: test()\n"
"\n"
"   Returns 0.0.\n"
"\n"
"   :return: The number.\n"
"   :rtype: float\n"
);
static PyObject *M_Eigen_test(PyObject *UNUSED(self), PyObject *args)
{
  PyObject* A = NULL;
  PyObject* b = NULL;
  Py_ssize_t A_rows = 0;
  Py_ssize_t A_cols = 0;
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

  

	return PyFloat_FromDouble(0.0);
}

static PyMethodDef M_Eigen_methods[] = {
	{"test", (PyCFunction) M_Eigen_test, METH_VARARGS, M_Eigen_test_doc},
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



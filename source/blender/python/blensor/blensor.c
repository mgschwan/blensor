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

/** \file blender/python/blensor/blensor.c
 *  \ingroup blensor
 */

#include <Python.h>

#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_dynstr.h"


/*------------------------------------------------------------*/
/* Util Functions */
/*------------------------------------------------------------*/

static uintptr_t blensor_convert_str_to_ptr(char *ptr_str)
{
  int idx=0;
  uintptr_t ptr=0;
  for (idx=0; idx < 16; idx++)
  {
    ptr = ptr << 4;  
    switch(ptr_str[idx])
    {
      case 'F': 
      case 'f': ptr += 15; break;
      case 'E': 
      case 'e': ptr += 14; break;
      case 'D': 
      case 'd': ptr += 13; break;
      case 'C': 
      case 'c': ptr += 12; break;
      case 'B': 
      case 'b': ptr += 11; break;
      case 'A': 
      case 'a': ptr += 10; break;
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9': ptr += ptr_str[idx]-'0';
            break;
      default:
        //You have some ugly data here
        break;
    }
    
  }
  return ptr;
}


PyDoc_STRVAR(M_Blensor_doc,
"This module provides the internal blensor functions."
);

/*------------------------------------------------------------*/
/* Python Functions */
/*------------------------------------------------------------*/

PyDoc_STRVAR(M_Blensor_scan_doc,
".. function:: scan()\n"
"   :return: The scanned distances\n"
"   :rtype: array\n"
);
static PyObject *M_Blensor_scan(PyObject *UNUSED(self), PyObject *args)
{
  PyObject* A = NULL;
  Py_ssize_t elements;
  PyObject *result;
  Py_ssize_t idx;
  
  if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &A))
    return 0;
    
  /* TODO: Look at the pyop_call function from bpy_operators.c to understand
   * how to get the bContext needed for rendering
   */
    
  elements = PyList_Size(A);

  result = PyList_New(elements);
  for (idx=0; idx < elements; idx++)
  {
    PyList_SetItem(result, idx, PyFloat_FromDouble(0.0));
  }

	return result;
}



/*----------------------------MODULE INIT-------------------------*/
static struct PyMethodDef M_Blensor_methods[] = {
	{"scan", (PyCFunction) M_Blensor_scan, METH_VARARGS, M_Blensor_scan_doc},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef M_Blensor_module_def = {
	PyModuleDef_HEAD_INIT,
	"blensor_intern",  /* m_name */
	M_Blensor_doc,  /* m_doc */
	0,  /* m_size */
	M_Blensor_methods,  /* m_methods */
	NULL,  /* m_reload */
	NULL,  /* m_traverse */
	NULL,  /* m_clear */
	NULL,  /* m_free */
};

PyMODINIT_FUNC PyInit_blensor(void)
{
	PyObject *mod;
	PyObject *submodule;
	PyObject *sys_modules = PyThreadState_GET()->interp->modules;

	mod = PyModule_Create(&M_Blensor_module_def);

	return mod;
}

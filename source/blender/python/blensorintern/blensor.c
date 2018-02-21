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
 *  \ingroup blensorintern
 */

#include <Python.h>
#include "RNA_types.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_dynstr.h"
#include "bpy_rna.h"
#include "bpy_capi_utils.h"


#include "blensor_native_code.h"

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


PyDoc_STRVAR(M_Blensorintern_doc,
"This module provides the internal blensor functions."
);

/*------------------------------------------------------------*/
/* Python Functions */
/*------------------------------------------------------------*/

PyDoc_STRVAR(M_Blensorintern_scan_doc,
".. function:: scan(raycount, elements_per_ray, keep_render_setup, shading, maximum_distance, ray_ptr_str, return_ptr_str)\n"
"   :return: status\n"
"   :rtype: integer\n"
);
static PyObject *M_Blensorintern_scan(PyObject *UNUSED(self), PyObject *args)
{
  int raycount, elements_per_ray, keep_render_setup;
  int shading;
  float maximum_distance;
  char *ray_ptr_str, *return_ptr_str;
  bContext *C;
  PyObject *result;
  
  if (!PyArg_ParseTuple(args, "IfIIIss", &raycount, &maximum_distance, &elements_per_ray,
      &keep_render_setup, &shading,  
      &ray_ptr_str, &return_ptr_str))
    return 0;
    
	C = (bContext *)BPy_GetContext();
  screen_blensor_exec(C, raycount, elements_per_ray, keep_render_setup, 
                 shading, maximum_distance, ray_ptr_str, return_ptr_str);

  result = Py_BuildValue("i",0);

	return result;
}

PyDoc_STRVAR(M_Blensorintern_copy_zbuf_doc,
".. function:: copy_zbuf(image)\n"
"   :return: zbuf\n"
"   :rtype: list\n"
);
static PyObject *M_Blensorintern_copy_zbuf(PyObject *UNUSED(self), PyObject *obj)
{
  PyObject *result;
  float *outbuffer;
  int outbuffer_len;
  struct ID *id;
  bContext *C;
  BPy_StructRNA *blender_obj = NULL;
  int status = 0;
  int idx;
  status = pyrna_id_FromPyObject(obj, &id);
  if (status)
  {
    blender_obj = (BPy_StructRNA *) obj;
  }

    
	C = (bContext *)BPy_GetContext();
  blensor_Image_copy_zbuf((Image *)blender_obj->ptr.data, C, &outbuffer_len, &outbuffer);

  printf ("Size of buffer %d",outbuffer_len);
  result = PyTuple_New(outbuffer_len);
  for (idx = 0; idx < outbuffer_len; idx++)
  {
    PyTuple_SetItem(result, idx, PyFloat_FromDouble(outbuffer[idx]));
  }
  MEM_freeN(outbuffer);

	return result;
}






/*----------------------------MODULE INIT-------------------------*/
static struct PyMethodDef M_Blensorintern_methods[] = {
	{"scan", (PyCFunction) M_Blensorintern_scan, METH_VARARGS, M_Blensorintern_scan_doc},
	{"copy_zbuf", (PyCFunction) M_Blensorintern_copy_zbuf, METH_O, M_Blensorintern_copy_zbuf_doc},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef M_Blensorintern_module_def = {
	PyModuleDef_HEAD_INIT,
	"blensorintern",  /* m_name */
	M_Blensorintern_doc,  /* m_doc */
	0,  /* m_size */
	M_Blensorintern_methods,  /* m_methods */
	NULL,  /* m_reload */
	NULL,  /* m_traverse */
	NULL,  /* m_clear */
	NULL,  /* m_free */
};

PyMODINIT_FUNC PyInit_blensorintern(void)
{
	PyObject *mod;
	PyObject *submodule;
	PyObject *sys_modules = PyThreadState_GET()->interp->modules;

	mod = PyModule_Create(&M_Blensorintern_module_def);

	return mod;
}

/**
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __MYGLUTKEYHANDLER_H__
#define __MYGLUTKEYHANDLER_H__

#include "common/GlutKeyboardManager.h"
#include "LOD_decimation.h"

class MyGlutKeyHandler : public GlutKeyboardHandler
{
public :
	static
		MyGlutKeyHandler *
	New(
		LOD_Decimation_InfoPtr info
	) {
		return new MyGlutKeyHandler(info);
	}	

		void
	HandleKeyboard(
		GHOST_TKey key,
		int x,
		int y
	){
		int steps = 0;

		switch (key) {
			case GHOST_kKeyD :

				while (steps < 100 && LOD_CollapseEdge(m_info)) {
					steps ++;
				}

				break;

			case GHOST_kKeyEsc :

				// release all the handlers!				
				exit(0);
		}
		
	}
		
	~MyGlutKeyHandler(
	) {
	};

private :

	MyGlutKeyHandler(
		LOD_Decimation_InfoPtr info
	):
		m_info (info)
	{
	}


	LOD_Decimation_InfoPtr m_info;
};

#endif


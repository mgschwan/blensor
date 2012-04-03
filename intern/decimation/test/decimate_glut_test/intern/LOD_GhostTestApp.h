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

#ifndef __LOD_GHOSTTESTAPP_H__
#define __LOD_GHOSTTESTAPP_H__

#include "GHOST_IEventConsumer.h"
#include "MT_Vector3.h"
#include <vector>

class GHOST_IWindow;
class GHOST_ISystem;


class LOD_GhostTestApp :
public GHOST_IEventConsumer
{
public :
	// Construct an instance of the application;

	LOD_GhostTestApp(
	);

	// initialize the applicaton

		bool
	InitApp(
	);

	// Run the application untill internal return.
		void
	Run(
	);
	
	~LOD_GhostTestApp(
	);
	
private :

		void
	UpdateFrame(
	);
	
	// inherited from GHOST_IEventConsumer
	// maps events to GlutXXXHandlers()

		bool 
	processEvent(
		GHOST_IEvent* event
	);

	GHOST_IWindow *m_window;
	GHOST_ISystem *m_system;

	bool m_finish_me_off;
};

#endif


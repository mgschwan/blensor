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

#define TRUE 1
#define FALSE 0

#include "LOD_GhostTestApp.h"

#include "GHOST_ISystem.h"
#include "GHOST_IWindow.h"
#include "common/GlutDrawer.h"
#include "common/GlutKeyboardManager.h"
#include "common/GlutMouseManager.h"

using namespace std;

LOD_GhostTestApp::
LOD_GhostTestApp(
):
	m_window(NULL),
	m_system(NULL),
	m_finish_me_off (false)
{
}

// initialize the applicaton

	bool
LOD_GhostTestApp::
InitApp(
){

	// create a system and window with opengl
	// rendering context.

	GHOST_TSuccess success = GHOST_ISystem::createSystem();
	if (success == GHOST_kFailure) return false;

	m_system = GHOST_ISystem::getSystem();
	if (m_system == NULL) return false;

	m_system->addEventConsumer(this);
	
	m_window = m_system->createWindow(
		"GHOST crud!",
		100,100,640,480,GHOST_kWindowStateNormal,
		GHOST_kDrawingContextTypeOpenGL,
		FALSE
	);

	if (
		m_window == NULL
	) {
		m_system = NULL;
		GHOST_ISystem::disposeSystem();
		return false;
	}

	return true;
}

// Run the application untill internal return.
	void
LOD_GhostTestApp::
Run(
){
	if (m_system == NULL) {
		return;
	}

	while (!m_finish_me_off) {
		m_system->processEvents(TRUE);
		m_system->dispatchEvents();
	};
}

LOD_GhostTestApp::
~LOD_GhostTestApp(
){
	if (m_window) {
		m_system->disposeWindow(m_window);
		m_window = NULL;
		GHOST_ISystem::disposeSystem();
		m_system = NULL;
	}
};


	bool 
LOD_GhostTestApp::
processEvent(
	GHOST_IEvent* event
){

	// map ghost events to the glut schmuk handlers.
	bool handled = false;

	switch(event->getType()) {
		case GHOST_kEventWindowSize:
		case GHOST_kEventWindowActivate:
		case GHOST_kEventWindowUpdate:
			GlutDrawManager::Draw();
			static_cast<GHOST_TEventWindowData *>(event->getData())->window->swapBuffers();

			handled = true;
			break;
		case GHOST_kEventButtonDown:
		{
			int x,y;
			m_system->getCursorPosition(x,y);
	
			int wx,wy;
			m_window->screenToClient(x,y,wx,wy);

			GHOST_TButtonMask button = 
				static_cast<GHOST_TEventButtonData *>(event->getData())->button;
			GlutMouseManager::ButtonDown(m_window,button,wx,wy);
		}
		handled = true;
		break;

		case GHOST_kEventButtonUp:
		{
			int x,y;
			m_system->getCursorPosition(x,y);
	
			int wx,wy;
			m_window->screenToClient(x,y,wx,wy);

			GHOST_TButtonMask button = 
				static_cast<GHOST_TEventButtonData *>(event->getData())->button;
			GlutMouseManager::ButtonUp(m_window,button,wx,wy);
		}
		handled = true;
		break;

		case GHOST_kEventCursorMove:
		{	
			int x,y;
			m_system->getCursorPosition(x,y);
	
			int wx,wy;
			m_window->screenToClient(x,y,wx,wy);

			GlutMouseManager::Motion(m_window,wx,wy);
	
		}	
		handled = true;
		break;

		case GHOST_kEventKeyDown :
		{
			GHOST_TEventKeyData *kd = 
				static_cast<GHOST_TEventKeyData *>(event->getData());

			int x,y;
			m_system->getCursorPosition(x,y);
	
			int wx,wy;
			m_window->screenToClient(x,y,wx,wy);

			GlutKeyboardManager::HandleKeyboard(kd->key,wx,wy);
		}		
		handled = true;
		break;
	
		default :
			break;
	}

	return handled;
}

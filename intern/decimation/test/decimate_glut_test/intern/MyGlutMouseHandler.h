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

#ifndef __MYGLUTMOUSEHANDLER_H__
#define __MYGLUTMOUSEHANDLER_H__

#include "common/GlutMouseManager.h"
#include "GHOST_IWindow.h"

class MyGlutMouseHandler : public GlutMouseHandler
{

public :
 
	static 
		MyGlutMouseHandler *
	New(
	) {
		return new MyGlutMouseHandler();
	}

		void
	ButtonDown(
		GHOST_IWindow * window,
		GHOST_TButtonMask button_mask,
		int x,
		int y
	){
		if (button_mask == GHOST_kButtonMaskLeft) {
			m_moving = true;
			m_begin_x = x;
			m_begin_y = y;	
		}
		window->invalidate();
	}

		void
	ButtonUp(
		GHOST_IWindow * window,
		GHOST_TButtonMask button_mask,
		int x,
		int y
	) {
		if (button_mask == GHOST_kButtonMaskLeft) {
			m_moving = false;
		}
		window->invalidate();
	}

		void
	Motion(
		GHOST_IWindow * window,
		int x,
		int y
	){
		if (m_moving) {
			m_angle_x = m_angle_x + (x - m_begin_x);
			m_begin_x = x;

			m_angle_y = m_angle_y + (y - m_begin_y);
			m_begin_y = y;
		}
		window->invalidate();
	}

	const 
		float
	AngleX(
	) const {
		return m_angle_x;
	}

	const 
		float
	AngleY(
	) const {
		return m_angle_y;
	}

	
private :

	MyGlutMouseHandler (
	) :  
		m_angle_x(0),
		m_angle_y(0),
		m_begin_x(0),
		m_begin_y(0),
		m_moving (false)
	{
	};
		
	float m_angle_x;
	float m_angle_y;
	float m_begin_x;
	float m_begin_y;

	bool m_moving;
	
};

#endif


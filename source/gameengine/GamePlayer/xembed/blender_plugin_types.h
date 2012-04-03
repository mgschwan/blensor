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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * Plugin-instance related data
 */

#ifndef __BLENDER_PLUGIN_TYPES_H__
#define __BLENDER_PLUGIN_TYPES_H__

#include <stdio.h>

#ifdef _WIN32
/* Windows stuff goes here: */
#include <windows.h>

#elif defined(__APPLE__)
/* Apple stuff goes here: */

#else 
/* Unix stuff goes here: */
#include <GL/glx.h>
#include <X11/Intrinsic.h>
#endif

#include "npapi.h"              /* NS related types*/
#include "prlock.h"             /* NSPR locking */

#ifdef __cplusplus
extern "C" {
#endif

	struct netscape_plugin_Plugin;
	
	typedef struct _BlenderPluginInstance
	{
		/** reach back to the browser: needed for file
		 * streaming */
		NPP browser_instance;

		/** The default stream.... */
		NPStream* main_file_stream;

		/** Total bytes expected for main file */
		int stream_total;

		/** Total bytes retrieved for mail file */
		int stream_retrieved;

		/** Mem chunk for the main file */
		void* main_file_store;

		/** URL of the .blend you want to show. Must be set. */
		char* blend_file;

		/** Blenderplayer pid **/
		pid_t pID;

		/** Window ID (used by embedder) **/
		Window window;

		/** Display used by browser **/
		Display* display;


		/** Temp filename used to pass animation data to the player */
		char* temp_mail_file_name;

	} BlenderPluginInstance;
	
#ifdef __cplusplus
}
#endif

# endif


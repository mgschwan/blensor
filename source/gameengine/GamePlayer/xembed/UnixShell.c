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
 * Contributor(s): Enrico Fracasso
 *
 * ***** END GPL LICENSE BLOCK *****
 * NS api template, adapted to link to our own internals.
 */

#define MOZ_X11 1

/* -*- Mode: C; tab-width: 8; c-set-style: bsd -*- */

/* UnixShell.c was adapted from the template in the Netscape API. */

/* System: */     
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

/* All nsapi stuff. nsapi now needs FILE, so include stdio as well. */
#include <stdio.h>
#include "npapi.h"

/* Native hooks: */
#include "npapi.h"

/* Threading the NSPR way: */
#include "prthread.h"
#include "prlock.h"

#include "blender_plugin_types.h"

#include <signal.h>

/* --------------------------------------------------------------------- */

/** If defined: write to the plugin log file */
#if defined(DEBUG)
#define NZC_GENERATE_LOG
#endif

int32 STREAMBUFSIZE;

/** Generate a log file. */
static void
log_entry(char* msg);


void
execute_blenderplayer(BlenderPluginInstance*);

/* --------------------------------------------------------------------- */
/* Implementations:                                                      */
/* --------------------------------------------------------------------- */

/* NPP_GetMIMEDescription() and NPP_GetValue() are called to determine
 * the mime types supported by this plugin. */
char*
NPP_GetMIMEDescription(void)
{
	log_entry("NPP_GetMIMEDescription");
	return("application/x-blender-plugin:blend:Blender 3D web plugin");
}

NPError
NPP_GetValue(
	NPP instance,
	NPPVariable variable,
	void *value
	)
{
	NPError err = NPERR_NO_ERROR;
	
	log_entry("NPP_GetValue");

	switch (variable) {
	case NPPVpluginNeedsXEmbed:
		log_entry("NPP_GetValue::NPPVpluginNeedsXEmbed");
		*((PRBool *)value) = PR_TRUE;
		break;
	case NPPVpluginNameString:
		log_entry("NPP_GetValue::NPPVpluginNameString");
		*((char **)value) = "Blender";
		break;
	case NPPVpluginDescriptionString:
		log_entry("NPP_GetValue::NPPVpluginDescriptionString");
		*((char **)value) = "Player for interactive 3D content";
		break;
	case NPPVpluginWindowBool:
		log_entry("NPP_GetValue::NPPVpluginWindowBool");
		*((PRBool *)value) = PR_FALSE; //not windowless
		break;
	case NPPVpluginTransparentBool:
		log_entry("NPP_GetValue::NPPVpluginTransparentBool");
		*((PRBool *)value) = PR_FALSE; // not trasparent
		break;
	default:
		err = NPERR_GENERIC_ERROR;
	}
	return err;
}

/* --------------------------------------------------------------------- */
/* Mozilla: NPP_Initialize() is called when
 * starting the browser, and then every time the plugin is started*/
NPError
NPP_Initialize(void)
{
	log_entry("NPP_Initialize");
	return NPERR_NO_ERROR;
}

/* --------------------------------------------------------------------- */

void
NPP_Shutdown(void)
{
	log_entry("NPP_Shutdown");
}


NPError 
NPP_New(
	NPMIMEType pluginType,
	NPP instance,
	uint16 mode,
	int16 argc,
	char* argn[],
	char* argv[],
	NPSavedData* saved
	)
{
	BlenderPluginInstance* This  = NULL;
	int i = 0;
	int retval = 0;

	log_entry("NPP_New");
	
	if (instance == NULL)
		return NPERR_INVALID_INSTANCE_ERROR;
	
	instance->pdata = NPN_MemAlloc(sizeof(BlenderPluginInstance));
	if (instance->pdata == 0)
		return NPERR_OUT_OF_MEMORY_ERROR;
	
	This = (BlenderPluginInstance*) instance->pdata;
	This->browser_instance = instance;
	This->pID = 0;
	This->blend_file = 0;
	This->temp_mail_file_name = 0;
	This->main_file_store = 0;
	This->display = NULL;
	This->window = 0;

	/* Parse the options from the file. Should I do this in the
	 * implementation file maybe? Now we do a lot with
	 * instance-specific data. */
	/*
	while (i <argc ) {
		if (!strcmp(argn[i],"src")) {
			The blend file to load. 
			int url_len = strlen(argv[i]);
			if ((url_len > 0) && (url_len < 4096) ) {
				This->blend_file = NPN_MemAlloc(url_len + 1);
				if (This->blend_file == 0)
					return NPERR_OUT_OF_MEMORY_ERROR;
				strcpy(This->blend_file, argv[i]);
				
				retval = NPN_GetURL(This->browser_instance,
						    This->blend_file,
						    NULL);
				if (retval != NPERR_NO_ERROR) {
					log_entry("Cannot read animation");
					NPN_Status(instance, "Cannot read animation file");
					This->blend_file = NULL;
					return NPERR_NO_ERROR;
				}
				else {
					log_entry("Animation loaded");
				}
			}
		} 		
		i++;
	}*/
		
	if (This != NULL) {
		return NPERR_NO_ERROR;
	}
	else {
		return NPERR_OUT_OF_MEMORY_ERROR;
	}
}


NPError 
NPP_Destroy( NPP instance, NPSavedData** save )
{
	BlenderPluginInstance* This;

	log_entry("NPP_Destroy");

	if (instance == NULL)
		return NPERR_INVALID_INSTANCE_ERROR;

	This = (BlenderPluginInstance*) instance->pdata;
	printf("NPP_Destroy ID:  0x%x %d\n", This->window, This->window);

	if (This != NULL) {

		if (This->pID != 0) {
#ifdef WITH_PRIVSEP
			kill(This->pID, SIGTERM);
#else 
			kill(This->pID, SIGKILL); //if I have to kill blenderplayer directly I need to send SIGKILL
#endif
			wait(This->pID);
			unlink(This->temp_mail_file_name);
		}

		// sometimes FF doesn't delete it's own window...
		//printf("%s\n", NPN_UserAgent(instance));
		/*if (This->display != NULL && This->window != 0)
			XDestroyWindow(This->display, This->window);
		*/
		if (This->blend_file) NPN_MemFree(This->blend_file);
		if (This->temp_mail_file_name) NPN_MemFree(This->temp_mail_file_name);
		if (This->main_file_store) NPN_MemFree(This->main_file_store);
		NPN_MemFree(instance->pdata);
		instance->pdata = NULL;
	}	

	return NPERR_NO_ERROR;
}



NPError 
NPP_SetWindow( NPP instance,NPWindow* window ) 
{
	BlenderPluginInstance* This;

	log_entry("NPP_SetWindow");

	if (instance == NULL)
		return NPERR_INVALID_INSTANCE_ERROR;

	/* window handle */ 
	if ((window == NULL) || (window->window == NULL)) {
		return NPERR_NO_ERROR; /* mmmmmm  */
	}
	
	if (window->ws_info == NULL)
		return NPERR_NO_ERROR; /* mmmmmm  */

	This = (BlenderPluginInstance*) instance->pdata;

	if (This) {
		This->window = (Window) window->window;

		NPSetWindowCallbackStruct* window_info = window->ws_info;
		This->display = window_info->display;

		printf("ID window 0x%x %d\n", window->window, window->window);
		return NPERR_NO_ERROR;
	}
	else {
		return NPERR_INVALID_INSTANCE_ERROR;
	}
}


NPError 
NPP_NewStream(
	NPP instance,
	NPMIMEType type,
	NPStream *stream, 
	NPBool seekable,
	uint16 *stype
	)
{
	//NPByteRange range;
	BlenderPluginInstance* This;

	log_entry("NPP_NewStream");
	
	if (instance == NULL)
		return NPERR_INVALID_INSTANCE_ERROR;

	This = (BlenderPluginInstance*) instance->pdata;

	if (!This) 
		return NPERR_INVALID_INSTANCE_ERROR;

	printf("Loading main file %s (%s)\n", stream->url, type);
	if ( strcmp(type,"text/html") == 0 ) // original HTML file 
		return NPERR_NO_ERROR;
	
	This->stream_total = stream->end;
	This->stream_retrieved = 0;
	This->main_file_store = NPN_MemAlloc(stream->end*sizeof(unsigned char));
	if (!This->main_file_store) {
		fprintf(stderr, "Blender plugin: Out of memory! "
			"Cannot get chunk for loading animation.\n");
		return NPERR_OUT_OF_MEMORY_ERROR;
	}

	This->main_file_stream = stream;

	return NPERR_NO_ERROR;
		
}


/* PLUGIN DEVELOPERS:
 *	These next 2 functions are directly relevant in a plug-in which
 *	handles the data in a streaming manner. If you want zero bytes
 *	because no buffer space is YET available, return 0. As long as
 *	the stream has not been written to the plugin, Navigator will
 *	continue trying to send bytes.  If the plugin doesn't want them,
 *	just return some large number from NPP_WriteReady(), and
 *	ignore them in NPP_Write().  For a NP_ASFILE stream, they are
 *	still called but can safely be ignored using this strategy.
 */

int32 STREAMBUFSIZE = 0X0FFFFFFF; /* If we are reading from a file in NPAsFile
				   * mode so we can take any size stream in our
				   * write call (since we ignore it) */

int32 
NPP_WriteReady(
	NPP instance,
	NPStream *stream
	)
{
	BlenderPluginInstance* This = NULL;
	int acceptable = 0;
	
	log_entry("NPP_WriteReady");

	if (instance == NULL)	
		return NPERR_INVALID_INSTANCE_ERROR;

	This = (BlenderPluginInstance*) instance->pdata;

	if (This == NULL)	
		return NPERR_INVALID_INSTANCE_ERROR;

	/* Check whether buffers already exist: */

	if ((This->main_file_stream && This->main_file_store)) {
		acceptable = STREAMBUFSIZE;
	}
	
	
	return acceptable;
}


int32 
NPP_Write(
	NPP instance,
	NPStream *stream,
	int32 offset,
	int32 len,
	void *buffer
	)
{
	BlenderPluginInstance* This = NULL;
	int accepted = 0;
	
	log_entry("NPP_Write");

	if (instance == NULL)	
		return NPERR_INVALID_INSTANCE_ERROR;
	
	This = (BlenderPluginInstance*) instance->pdata;

	if (This == NULL)	
		return NPERR_INVALID_INSTANCE_ERROR;

	
	if (stream == This->main_file_stream) {
		log_entry("NPP_Write: loading main_file_stream"); 
		memcpy(((unsigned char*)This->main_file_store) + This->stream_retrieved, buffer, len);
		accepted = len;
		This->stream_retrieved += len;
		if (This->stream_retrieved >= This->stream_total) {
			log_entry("NPP_Write: main_file_stream loaded"); 
			execute_blenderplayer(This);
		}
	}
	else {
		/* the stream ref wasn't set yet..*/
		log_entry("NPP_Write: not main stream"); 
		log_entry(stream->url);

		accepted = len;
	}

	return accepted;
}



NPError 
NPP_DestroyStream(
	NPP instance,
	NPStream *stream,
	NPError reason
	)
{
	BlenderPluginInstance* This = NULL;

	log_entry("NPP_DestroyStream");

	if (instance == NULL)
		return NPERR_INVALID_INSTANCE_ERROR;
	This = (BlenderPluginInstance*) instance->pdata;

	if (This) {
		if (reason != NPRES_DONE) {
			if (stream == This->main_file_stream) {				
				// stream destroyed by NPP_Destroy
				NPN_Status(instance, "Cannot read animation file");
				//main_file_failed(This->application);
			}
		}
		return NPERR_NO_ERROR;
	}
	else {
		return NPERR_INVALID_INSTANCE_ERROR;
	}

}


/* Not supposed to be called anymore... Anyway, we don't need the
 * results. Some Moz implementations will call this one regardless the
 * desired transfer mode! */
void 
NPP_StreamAsFile(NPP instance, NPStream *stream, const char* fname )
{
/* 	log_entry("NPP_StreamAsFile"); */
}


void 
NPP_Print(NPP instance, NPPrint* printInfo ) 
{
	
	log_entry("NPP_Print");
	if (printInfo == NULL)
		return;
	if (instance != NULL) {
		if (printInfo->mode == NP_FULL) {
			printInfo->print.fullPrint.pluginPrinted = FALSE;
		}
		else {	/* If not fullscreen, we must be embedded */
		}
	}
}


void
execute_blenderplayer(BlenderPluginInstance* instance)
{

	char file_name[] = "/tmp/blender.XXXXXX";
	int fd = mkstemp(file_name);

	ssize_t real_size = write(fd, instance->main_file_store, instance->stream_retrieved);
	close(fd);

	instance->temp_mail_file_name = NPN_MemAlloc(strlen(file_name) + 1);
	strcpy(instance->temp_mail_file_name, file_name);

	instance->pID = fork();
	//XSelectInput(This->display , This->window, SubstructureNotifyMask);
	//XSync(This->display, FALSE);
	

#if defined(WITH_APPARMOR)
	const char* executable = "blenderplayer-web"; 
#elif defined(WITH_PRIVSEP)
	const char* executable = "blenderplayer-wrapper";
#else   
	const char* executable = "blenderplayer";
#endif

	if (instance->pID == 0) {              // child
		char window_id[50];
		sprintf(window_id, "%d", instance->window);
		//exit(0);
#ifdef WITH_PRIVSEP
		execlp(executable, executable, file_name, window_id, (char*)NULL);
#else 
		execlp(executable, executable, "-i", window_id, file_name, (char*)NULL);
#endif
	
	}
	else if (instance->pID < 0) {           // failed to fork
		printf("Failed to fork!!!\n");					
	}

	/*XEvent e;
	int started = 0;
	while (!started) {
		XNextEvent(This->display, &e);
		printf("Event type %d\n", e.type);					
		if (e.type == MapNotify) {
			started = 1;
			XCreateWindowEvent event =  e.xcreatewindow;
			printf("Created window x:%d, y: %d, h: %d, w: %d\n", event.x, event.y, event.height, event.width);
		}
	}*/

}


/* --------------------------------------------------------------------- */

static void
log_entry(char* msg)
{
#ifdef NZC_GENERATE_LOG 
	FILE* fp = fopen("/tmp/plugin_log","a");
	if (!fp) return;
	fprintf(fp, "--> Unixshell:: %s\n",
		msg); 
	fflush(fp);
	fclose (fp);
#endif
}

/* --------------------------------------------------------------------- */

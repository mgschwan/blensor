# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# The Original Code is Copyright (C) 2006, Blender Foundation
# All rights reserved.
#
# Contributor(s): Enrico Fracasso.
#
# ##### END GPL LICENSE BLOCK #####

message(STATUS "Configuring WebPlugin")

# Enable build flag
string(TOUPPER ${WEBPLUGIN_SANDBOX_MODE} WEBPLUGIN_SANDBOX_MODE_UPPER)

if(WEBPLUGIN_SANDBOX_MODE_UPPER STREQUAL "APPARMOR")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DWITH_APPARMOR ")
endif()

if(WEBPLUGIN_SANDBOX_MODE_UPPER STREQUAL "PRIVSEP")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DWITH_PRIVSEP ")
	add_executable(blenderplayer-wrapper blenderplayer-wrapper.c)
endif()

# set output path
set(LIBRARY_OUTPUT_PATH  ${CMAKE_BINARY_DIR}/webplugin)

set(INC
	${GECKO_DIR}/include/
)

set(SRC 
	npunix.c 
	UnixShell.c 
)

blender_include_dirs("${INC}")
add_library(blender_plugin SHARED ${SRC})



/**
 * $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_scene_types.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "BKE_context.h"
#include "BKE_global.h"

void *rna_Scene_objects_get(CollectionPropertyIterator *iter)
{
	ListBaseIterator *internal= iter->internal;

	/* we are actually iterating a Base list, so override get */
	return ((Base*)internal->link)->object;
}

static void rna_Scene_layer_set(PointerRNA *ptr, int index, int value)
{
	Scene *scene= (Scene*)ptr->data;

	if(value) scene->lay |= (1<<index);
	else {
		scene->lay &= ~(1<<index);
		if(scene->lay == 0)
			scene->lay |= (1<<index);
	}
}

static void rna_Scene_start_frame_set(PointerRNA *ptr, int value)
{
	Scene *data= (Scene*)ptr->data;
	CLAMP(value, 1, data->r.efra);
	data->r.sfra= value;
}

static void rna_Scene_end_frame_set(PointerRNA *ptr, int value)
{
	Scene *data= (Scene*)ptr->data;
	CLAMP(value, data->r.sfra, MAXFRAME);
	data->r.efra= value;
}

static void rna_Scene_frame_update(bContext *C, PointerRNA *ptr)
{
	//Scene *scene= ptr->id.data;
	//update_for_newframe();
}

#else

void rna_def_sculpt(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Sculpt", NULL);
	RNA_def_struct_nested(brna, srna, "Scene");
	RNA_def_struct_ui_text(srna, "Sculpt", "");

	prop= RNA_def_property(srna, "symmetry_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_X);
	RNA_def_property_ui_text(prop, "Symmetry X", "Mirror brush across the X axis.");

	prop= RNA_def_property(srna, "symmetry_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Y);
	RNA_def_property_ui_text(prop, "Symmetry Y", "Mirror brush across the Y axis.");

	prop= RNA_def_property(srna, "symmetry_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SYMM_Z);
	RNA_def_property_ui_text(prop, "Symmetry Z", "Mirror brush across the Z axis.");

	prop= RNA_def_property(srna, "lock_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_X);
	RNA_def_property_ui_text(prop, "Lock X", "Disallow changes to the X axis of vertices.");

	prop= RNA_def_property(srna, "lock_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Y);
	RNA_def_property_ui_text(prop, "Lock Y", "Disallow changes to the Y axis of vertices.");

	prop= RNA_def_property(srna, "lock_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Z);
	RNA_def_property_ui_text(prop, "Lock Z", "Disallow changes to the Z axis of vertices.");

	prop= RNA_def_property(srna, "show_brush", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DRAW_BRUSH);
	RNA_def_property_ui_text(prop, "Show Brush", "");

	prop= RNA_def_property(srna, "partial_redraw", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DRAW_FAST);
	RNA_def_property_ui_text(prop, "Partial Redraw", "Optimize sculpting by only refreshing modified faces.");
}

void rna_def_tool_settings(BlenderRNA  *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ToolSettings", NULL);
	RNA_def_struct_nested(brna, srna, "Scene");
	RNA_def_struct_ui_text(srna, "Tool Settings", "");
	
	prop= RNA_def_property(srna, "sculpt", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Sculpt");
	RNA_def_property_ui_text(prop, "Sculpt", "");

	rna_def_sculpt(brna);
}

void RNA_def_scene(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static EnumPropertyItem prop_mode_items[] ={
		{PROP_SMOOTH, "SMOOTH", "Smooth", ""},
		{PROP_SPHERE, "SPHERE", "Sphere", ""},
		{PROP_ROOT, "ROOT", "Root", ""},
		{PROP_SHARP, "SHARP", "Sharp", ""},
		{PROP_LIN, "LINEAR", "Linear", ""},
		{PROP_CONST, "CONSTANT", "Constant", ""},
		{PROP_RANDOM, "RANDOM", "Random", ""},
		{0, NULL, NULL, NULL}};
	static EnumPropertyItem unwrapper_items[] = {
		{0, "CONFORMAL", "Conformal", ""},
		{1, "ANGLEBASED", "Angle Based", ""}, 
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "Scene", "ID");
	RNA_def_struct_ui_text(srna, "Scene", "Scene consisting objects and defining time and render related settings.");

	prop= RNA_def_property(srna, "camera", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Active Camera", "Active camera used for rendering the scene.");

	prop= RNA_def_property(srna, "cursor_location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "cursor");
	RNA_def_property_ui_text(prop, "Cursor Location", "3D cursor location.");
	RNA_def_property_ui_range(prop, -10000.0, 10000.0, 10, 4);

	prop= RNA_def_property(srna, "objects", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "base", NULL);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Objects", "");
	RNA_def_property_collection_funcs(prop, 0, 0, 0, "rna_Scene_objects_get", 0, 0, 0, 0);

	prop= RNA_def_property(srna, "visible_layers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lay", 1);
	RNA_def_property_array(prop, 20);
	RNA_def_property_ui_text(prop, "Visible Layers", "Layers visible when rendering the scene.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Scene_layer_set");

	prop= RNA_def_property(srna, "proportional_editing_falloff", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "prop_mode");
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Proportional Editing Falloff", "Falloff type for proportional editing mode.");

	prop= RNA_def_property(srna, "current_frame", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.cfra");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME);
	RNA_def_property_ui_text(prop, "Current Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_FRAME, "rna_Scene_frame_update");
	
	prop= RNA_def_property(srna, "start_frame", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.sfra");
	RNA_def_property_int_funcs(prop, NULL, "rna_Scene_start_frame_set", NULL);
	RNA_def_property_ui_text(prop, "Start Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);
	
	prop= RNA_def_property(srna, "end_frame", PROP_INT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_ANIMATEABLE);
	RNA_def_property_int_sdna(prop, NULL, "r.efra");
	RNA_def_property_int_funcs(prop, NULL, "rna_Scene_end_frame_set", NULL);
	RNA_def_property_ui_text(prop, "End Frame", "");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "stamp_note", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "r.stamp_udata");
	RNA_def_property_ui_text(prop, "Stamp Note", "User define note for the render stamping.");
	RNA_def_property_update(prop, NC_SCENE|ND_RENDER_OPTIONS, NULL);

	prop= RNA_def_property(srna, "unwrapper", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "toolsettings->unwrapper");
	RNA_def_property_enum_items(prop, unwrapper_items);
	RNA_def_property_ui_text(prop, "Unwrapper", "Unwrap algorithm used by the Unwrap tool.");
	
	prop= RNA_def_property(srna, "nodetree", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Node Tree", "Compositing node tree.");
	
	prop= RNA_def_property(srna, "sequence_editor", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ed");
	RNA_def_property_struct_type(prop, "SequenceEditor");
	RNA_def_property_ui_text(prop, "Sequence Editor", "");

	prop= RNA_def_property(srna, "radiosity", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "radio");
	RNA_def_property_ui_text(prop, "Radiosity", "");

	prop= RNA_def_property(srna, "tool_settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "toolsettings");
	RNA_def_property_struct_type(prop, "ToolSettings");
	RNA_def_property_ui_text(prop, "Tool Settings", "");

	rna_def_tool_settings(brna);
}

#endif


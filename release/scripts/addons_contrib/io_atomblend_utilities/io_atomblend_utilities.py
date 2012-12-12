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
# ##### END GPL LICENSE BLOCK #####

import os
import bpy
import bmesh

# This variable contains the path of the XYZ file.
# It is used almost everywhere, which explains why it
# should stay global. First, it is empty and gets 'filled' directly
# after having chosen the XYZ file (see 'class LoadXYZ' further below).


# -----------------------------------------------------------------------------
#                                                  Atom and element data


# This is a list that contains some data of all possible elements. The structure
# is as follows:
#
# 1, "Hydrogen", "H", [0.0,0.0,1.0], 0.32, 0.32, 0.32 , -1 , 1.54   means
#
# No., name, short name, color, radius (used), radius (covalent), radius (atomic),
#
# charge state 1, radius (ionic) 1, charge state 2, radius (ionic) 2, ... all
# charge states for any atom are listed, if existing.
# The list is fixed and cannot be changed ... (see below)

ELEMENTS_DEFAULT = (
( 1,      "Hydrogen",        "H", (  1.0,   1.0,   1.0), 0.32, 0.32, 0.79 , -1 , 1.54 ),
( 2,        "Helium",       "He", ( 0.85,   1.0,   1.0), 0.93, 0.93, 0.49 ),
( 3,       "Lithium",       "Li", (  0.8,  0.50,   1.0), 1.23, 1.23, 2.05 ,  1 , 0.68 ),
( 4,     "Beryllium",       "Be", ( 0.76,   1.0,   0.0), 0.90, 0.90, 1.40 ,  1 , 0.44 ,  2 , 0.35 ),
( 5,         "Boron",        "B", (  1.0,  0.70,  0.70), 0.82, 0.82, 1.17 ,  1 , 0.35 ,  3 , 0.23 ),
( 6,        "Carbon",        "C", ( 0.56,  0.56,  0.56), 0.77, 0.77, 0.91 , -4 , 2.60 ,  4 , 0.16 ),
( 7,      "Nitrogen",        "N", ( 0.18,  0.31,  0.97), 0.75, 0.75, 0.75 , -3 , 1.71 ,  1 , 0.25 ,  3 , 0.16 ,  5 , 0.13 ),
( 8,        "Oxygen",        "O", (  1.0,  0.05,  0.05), 0.73, 0.73, 0.65 , -2 , 1.32 , -1 , 1.76 ,  1 , 0.22 ,  6 , 0.09 ),
( 9,      "Fluorine",        "F", ( 0.56,  0.87,  0.31), 0.72, 0.72, 0.57 , -1 , 1.33 ,  7 , 0.08 ),
(10,          "Neon",       "Ne", ( 0.70,  0.89,  0.96), 0.71, 0.71, 0.51 ,  1 , 1.12 ),
(11,        "Sodium",       "Na", ( 0.67,  0.36,  0.94), 1.54, 1.54, 2.23 ,  1 , 0.97 ),
(12,     "Magnesium",       "Mg", ( 0.54,   1.0,   0.0), 1.36, 1.36, 1.72 ,  1 , 0.82 ,  2 , 0.66 ),
(13,     "Aluminium",       "Al", ( 0.74,  0.65,  0.65), 1.18, 1.18, 1.82 ,  3 , 0.51 ),
(14,       "Silicon",       "Si", ( 0.94,  0.78,  0.62), 1.11, 1.11, 1.46 , -4 , 2.71 , -1 , 3.84 ,  1 , 0.65 ,  4 , 0.42 ),
(15,    "Phosphorus",        "P", (  1.0,  0.50,   0.0), 1.06, 1.06, 1.23 , -3 , 2.12 ,  3 , 0.44 ,  5 , 0.35 ),
(16,        "Sulfur",        "S", (  1.0,   1.0,  0.18), 1.02, 1.02, 1.09 , -2 , 1.84 ,  2 , 2.19 ,  4 , 0.37 ,  6 , 0.30 ),
(17,      "Chlorine",       "Cl", ( 0.12,  0.94,  0.12), 0.99, 0.99, 0.97 , -1 , 1.81 ,  5 , 0.34 ,  7 , 0.27 ),
(18,         "Argon",       "Ar", ( 0.50,  0.81,  0.89), 0.98, 0.98, 0.88 ,  1 , 1.54 ),
(19,     "Potassium",        "K", ( 0.56,  0.25,  0.83), 2.03, 2.03, 2.77 ,  1 , 0.81 ),
(20,       "Calcium",       "Ca", ( 0.23,   1.0,   0.0), 1.74, 1.74, 2.23 ,  1 , 1.18 ,  2 , 0.99 ),
(21,      "Scandium",       "Sc", ( 0.90,  0.90,  0.90), 1.44, 1.44, 2.09 ,  3 , 0.73 ),
(22,      "Titanium",       "Ti", ( 0.74,  0.76,  0.78), 1.32, 1.32, 2.00 ,  1 , 0.96 ,  2 , 0.94 ,  3 , 0.76 ,  4 , 0.68 ),
(23,      "Vanadium",        "V", ( 0.65,  0.65,  0.67), 1.22, 1.22, 1.92 ,  2 , 0.88 ,  3 , 0.74 ,  4 , 0.63 ,  5 , 0.59 ),
(24,      "Chromium",       "Cr", ( 0.54,   0.6,  0.78), 1.18, 1.18, 1.85 ,  1 , 0.81 ,  2 , 0.89 ,  3 , 0.63 ,  6 , 0.52 ),
(25,     "Manganese",       "Mn", ( 0.61,  0.47,  0.78), 1.17, 1.17, 1.79 ,  2 , 0.80 ,  3 , 0.66 ,  4 , 0.60 ,  7 , 0.46 ),
(26,          "Iron",       "Fe", ( 0.87,   0.4,   0.2), 1.17, 1.17, 1.72 ,  2 , 0.74 ,  3 , 0.64 ),
(27,        "Cobalt",       "Co", ( 0.94,  0.56,  0.62), 1.16, 1.16, 1.67 ,  2 , 0.72 ,  3 , 0.63 ),
(28,        "Nickel",       "Ni", ( 0.31,  0.81,  0.31), 1.15, 1.15, 1.62 ,  2 , 0.69 ),
(29,        "Copper",       "Cu", ( 0.78,  0.50,   0.2), 1.17, 1.17, 1.57 ,  1 , 0.96 ,  2 , 0.72 ),
(30,          "Zinc",       "Zn", ( 0.49,  0.50,  0.69), 1.25, 1.25, 1.53 ,  1 , 0.88 ,  2 , 0.74 ),
(31,       "Gallium",       "Ga", ( 0.76,  0.56,  0.56), 1.26, 1.26, 1.81 ,  1 , 0.81 ,  3 , 0.62 ),
(32,     "Germanium",       "Ge", (  0.4,  0.56,  0.56), 1.22, 1.22, 1.52 , -4 , 2.72 ,  2 , 0.73 ,  4 , 0.53 ),
(33,       "Arsenic",       "As", ( 0.74,  0.50,  0.89), 1.20, 1.20, 1.33 , -3 , 2.22 ,  3 , 0.58 ,  5 , 0.46 ),
(34,      "Selenium",       "Se", (  1.0,  0.63,   0.0), 1.16, 1.16, 1.22 , -2 , 1.91 , -1 , 2.32 ,  1 , 0.66 ,  4 , 0.50 ,  6 , 0.42 ),
(35,       "Bromine",       "Br", ( 0.65,  0.16,  0.16), 1.14, 1.14, 1.12 , -1 , 1.96 ,  5 , 0.47 ,  7 , 0.39 ),
(36,       "Krypton",       "Kr", ( 0.36,  0.72,  0.81), 1.31, 1.31, 1.24 ),
(37,      "Rubidium",       "Rb", ( 0.43,  0.18,  0.69), 2.16, 2.16, 2.98 ,  1 , 1.47 ),
(38,     "Strontium",       "Sr", (  0.0,   1.0,   0.0), 1.91, 1.91, 2.45 ,  2 , 1.12 ),
(39,       "Yttrium",        "Y", ( 0.58,   1.0,   1.0), 1.62, 1.62, 2.27 ,  3 , 0.89 ),
(40,     "Zirconium",       "Zr", ( 0.58,  0.87,  0.87), 1.45, 1.45, 2.16 ,  1 , 1.09 ,  4 , 0.79 ),
(41,       "Niobium",       "Nb", ( 0.45,  0.76,  0.78), 1.34, 1.34, 2.08 ,  1 , 1.00 ,  4 , 0.74 ,  5 , 0.69 ),
(42,    "Molybdenum",       "Mo", ( 0.32,  0.70,  0.70), 1.30, 1.30, 2.01 ,  1 , 0.93 ,  4 , 0.70 ,  6 , 0.62 ),
(43,    "Technetium",       "Tc", ( 0.23,  0.61,  0.61), 1.27, 1.27, 1.95 ,  7 , 0.97 ),
(44,     "Ruthenium",       "Ru", ( 0.14,  0.56,  0.56), 1.25, 1.25, 1.89 ,  4 , 0.67 ),
(45,       "Rhodium",       "Rh", ( 0.03,  0.49,  0.54), 1.25, 1.25, 1.83 ,  3 , 0.68 ),
(46,     "Palladium",       "Pd", (  0.0,  0.41,  0.52), 1.28, 1.28, 1.79 ,  2 , 0.80 ,  4 , 0.65 ),
(47,        "Silver",       "Ag", ( 0.75,  0.75,  0.75), 1.34, 1.34, 1.75 ,  1 , 1.26 ,  2 , 0.89 ),
(48,       "Cadmium",       "Cd", (  1.0,  0.85,  0.56), 1.48, 1.48, 1.71 ,  1 , 1.14 ,  2 , 0.97 ),
(49,        "Indium",       "In", ( 0.65,  0.45,  0.45), 1.44, 1.44, 2.00 ,  3 , 0.81 ),
(50,           "Tin",       "Sn", (  0.4,  0.50,  0.50), 1.41, 1.41, 1.72 , -4 , 2.94 , -1 , 3.70 ,  2 , 0.93 ,  4 , 0.71 ),
(51,      "Antimony",       "Sb", ( 0.61,  0.38,  0.70), 1.40, 1.40, 1.53 , -3 , 2.45 ,  3 , 0.76 ,  5 , 0.62 ),
(52,     "Tellurium",       "Te", ( 0.83,  0.47,   0.0), 1.36, 1.36, 1.42 , -2 , 2.11 , -1 , 2.50 ,  1 , 0.82 ,  4 , 0.70 ,  6 , 0.56 ),
(53,        "Iodine",        "I", ( 0.58,   0.0,  0.58), 1.33, 1.33, 1.32 , -1 , 2.20 ,  5 , 0.62 ,  7 , 0.50 ),
(54,         "Xenon",       "Xe", ( 0.25,  0.61,  0.69), 1.31, 1.31, 1.24 ),
(55,       "Caesium",       "Cs", ( 0.34,  0.09,  0.56), 2.35, 2.35, 3.35 ,  1 , 1.67 ),
(56,        "Barium",       "Ba", (  0.0,  0.78,   0.0), 1.98, 1.98, 2.78 ,  1 , 1.53 ,  2 , 1.34 ),
(57,     "Lanthanum",       "La", ( 0.43,  0.83,   1.0), 1.69, 1.69, 2.74 ,  1 , 1.39 ,  3 , 1.06 ),
(58,        "Cerium",       "Ce", (  1.0,   1.0,  0.78), 1.65, 1.65, 2.70 ,  1 , 1.27 ,  3 , 1.03 ,  4 , 0.92 ),
(59,  "Praseodymium",       "Pr", ( 0.85,   1.0,  0.78), 1.65, 1.65, 2.67 ,  3 , 1.01 ,  4 , 0.90 ),
(60,     "Neodymium",       "Nd", ( 0.78,   1.0,  0.78), 1.64, 1.64, 2.64 ,  3 , 0.99 ),
(61,    "Promethium",       "Pm", ( 0.63,   1.0,  0.78), 1.63, 1.63, 2.62 ,  3 , 0.97 ),
(62,      "Samarium",       "Sm", ( 0.56,   1.0,  0.78), 1.62, 1.62, 2.59 ,  3 , 0.96 ),
(63,      "Europium",       "Eu", ( 0.38,   1.0,  0.78), 1.85, 1.85, 2.56 ,  2 , 1.09 ,  3 , 0.95 ),
(64,    "Gadolinium",       "Gd", ( 0.27,   1.0,  0.78), 1.61, 1.61, 2.54 ,  3 , 0.93 ),
(65,       "Terbium",       "Tb", ( 0.18,   1.0,  0.78), 1.59, 1.59, 2.51 ,  3 , 0.92 ,  4 , 0.84 ),
(66,    "Dysprosium",       "Dy", ( 0.12,   1.0,  0.78), 1.59, 1.59, 2.49 ,  3 , 0.90 ),
(67,       "Holmium",       "Ho", (  0.0,   1.0,  0.61), 1.58, 1.58, 2.47 ,  3 , 0.89 ),
(68,        "Erbium",       "Er", (  0.0,  0.90,  0.45), 1.57, 1.57, 2.45 ,  3 , 0.88 ),
(69,       "Thulium",       "Tm", (  0.0,  0.83,  0.32), 1.56, 1.56, 2.42 ,  3 , 0.87 ),
(70,     "Ytterbium",       "Yb", (  0.0,  0.74,  0.21), 1.74, 1.74, 2.40 ,  2 , 0.93 ,  3 , 0.85 ),
(71,      "Lutetium",       "Lu", (  0.0,  0.67,  0.14), 1.56, 1.56, 2.25 ,  3 , 0.85 ),
(72,       "Hafnium",       "Hf", ( 0.30,  0.76,   1.0), 1.44, 1.44, 2.16 ,  4 , 0.78 ),
(73,      "Tantalum",       "Ta", ( 0.30,  0.65,   1.0), 1.34, 1.34, 2.09 ,  5 , 0.68 ),
(74,      "Tungsten",        "W", ( 0.12,  0.58,  0.83), 1.30, 1.30, 2.02 ,  4 , 0.70 ,  6 , 0.62 ),
(75,       "Rhenium",       "Re", ( 0.14,  0.49,  0.67), 1.28, 1.28, 1.97 ,  4 , 0.72 ,  7 , 0.56 ),
(76,        "Osmium",       "Os", ( 0.14,   0.4,  0.58), 1.26, 1.26, 1.92 ,  4 , 0.88 ,  6 , 0.69 ),
(77,       "Iridium",       "Ir", ( 0.09,  0.32,  0.52), 1.27, 1.27, 1.87 ,  4 , 0.68 ),
(78,     "Platinium",       "Pt", ( 0.81,  0.81,  0.87), 1.30, 1.30, 1.83 ,  2 , 0.80 ,  4 , 0.65 ),
(79,          "Gold",       "Au", (  1.0,  0.81,  0.13), 1.34, 1.34, 1.79 ,  1 , 1.37 ,  3 , 0.85 ),
(80,       "Mercury",       "Hg", ( 0.72,  0.72,  0.81), 1.49, 1.49, 1.76 ,  1 , 1.27 ,  2 , 1.10 ),
(81,      "Thallium",       "Tl", ( 0.65,  0.32,  0.30), 1.48, 1.48, 2.08 ,  1 , 1.47 ,  3 , 0.95 ),
(82,          "Lead",       "Pb", ( 0.34,  0.34,  0.38), 1.47, 1.47, 1.81 ,  2 , 1.20 ,  4 , 0.84 ),
(83,       "Bismuth",       "Bi", ( 0.61,  0.30,  0.70), 1.46, 1.46, 1.63 ,  1 , 0.98 ,  3 , 0.96 ,  5 , 0.74 ),
(84,      "Polonium",       "Po", ( 0.67,  0.36,   0.0), 1.46, 1.46, 1.53 ,  6 , 0.67 ),
(85,      "Astatine",       "At", ( 0.45,  0.30,  0.27), 1.45, 1.45, 1.43 , -3 , 2.22 ,  3 , 0.85 ,  5 , 0.46 ),
(86,         "Radon",       "Rn", ( 0.25,  0.50,  0.58), 1.00, 1.00, 1.34 ),
(87,      "Francium",       "Fr", ( 0.25,   0.0,   0.4), 1.00, 1.00, 1.00 ,  1 , 1.80 ),
(88,        "Radium",       "Ra", (  0.0,  0.49,   0.0), 1.00, 1.00, 1.00 ,  2 , 1.43 ),
(89,      "Actinium",       "Ac", ( 0.43,  0.67,  0.98), 1.00, 1.00, 1.00 ,  3 , 1.18 ),
(90,       "Thorium",       "Th", (  0.0,  0.72,   1.0), 1.65, 1.65, 1.00 ,  4 , 1.02 ),
(91,  "Protactinium",       "Pa", (  0.0,  0.63,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.13 ,  4 , 0.98 ,  5 , 0.89 ),
(92,       "Uranium",        "U", (  0.0,  0.56,   1.0), 1.42, 1.42, 1.00 ,  4 , 0.97 ,  6 , 0.80 ),
(93,     "Neptunium",       "Np", (  0.0,  0.50,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.10 ,  4 , 0.95 ,  7 , 0.71 ),
(94,     "Plutonium",       "Pu", (  0.0,  0.41,   1.0), 1.00, 1.00, 1.00 ,  3 , 1.08 ,  4 , 0.93 ),
(95,     "Americium",       "Am", ( 0.32,  0.36,  0.94), 1.00, 1.00, 1.00 ,  3 , 1.07 ,  4 , 0.92 ),
(96,        "Curium",       "Cm", ( 0.47,  0.36,  0.89), 1.00, 1.00, 1.00 ),
(97,     "Berkelium",       "Bk", ( 0.54,  0.30,  0.89), 1.00, 1.00, 1.00 ),
(98,   "Californium",       "Cf", ( 0.63,  0.21,  0.83), 1.00, 1.00, 1.00 ),
(99,   "Einsteinium",       "Es", ( 0.70,  0.12,  0.83), 1.00, 1.00, 1.00 ),
(100,       "Fermium",       "Fm", ( 0.70,  0.12,  0.72), 1.00, 1.00, 1.00 ),
(101,   "Mendelevium",       "Md", ( 0.70,  0.05,  0.65), 1.00, 1.00, 1.00 ),
(102,      "Nobelium",       "No", ( 0.74,  0.05,  0.52), 1.00, 1.00, 1.00 ),
(103,    "Lawrencium",       "Lr", ( 0.78,   0.0,   0.4), 1.00, 1.00, 1.00 ),
(104,       "Vacancy",      "Vac", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
(105,       "Default",  "Default", (  1.0,   1.0,   1.0), 1.00, 1.00, 1.00),
(106,         "Stick",    "Stick", (  0.5,   0.5,   0.5), 1.00, 1.00, 1.00),
)

# This list here contains all data of the elements and will be used during
# runtime. It is a list of classes.
# During executing Atomic Blender, the list will be initialized with the fixed
# data from above via the class structure below (ElementProp). We
# have then one fixed list (above), which will never be changed, and a list of
# classes with same data. The latter can be modified via loading a separate
# custom data file for instance.
ELEMENTS = []

# This is the class, which stores the properties for one element.
class ElementProp(object):
    __slots__ = ('number', 'name', 'short_name', 'color', 'radii', 'radii_ionic')
    def __init__(self, number, name, short_name, color, radii, radii_ionic):
        self.number = number
        self.name = name
        self.short_name = short_name
        self.color = color
        self.radii = radii
        self.radii_ionic = radii_ionic


# -----------------------------------------------------------------------------
#                                                          Some small routines

# This function measures the distance between two objects (atoms),
# which are active.
def distance():

    # In the 'Edit mode'
    if bpy.context.mode == 'EDIT_MESH':

        obj = bpy.context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)
        locations = []

        for v in bm.verts:
            if v.select:
                locations.append(obj.matrix_world * v.co)
                
        if len(locations) > 1:
            location1 = locations[0]
            location2 = locations[1]        
        else:
            return "N.A"
    # In the object mode
    else:

        if len(bpy.context.selected_bases) > 1:
            location1 = bpy.context.selected_objects[0].location
            location2 = bpy.context.selected_objects[1].location
        else:
            return "N.A."

    dv = location2 - location1
    dist = str(dv.length)
    pos = str.find(dist, ".")
    dist = dist[:pos+4]
    dist = dist + " A"
  
    return dist


def choose_objects(how, who, radius_all, radius_pm, radius_type):

    if who == "ALL_IN_LAYER":

        # Determine all selected layers.
        layers = []
        for i, layer in enumerate(bpy.context.scene.layers):
            if layer == True:
                layers.append(i)
                
        # Put all objects, which are in the layers, into a list.
        change_objects = []
        for obj in bpy.context.scene.objects:
            for layer in layers:
                if obj.layers[layer] == True:
                    change_objects.append(obj)
                    
        # Consider all objects, which are in the list 'change_objects'.
        for obj in change_objects:
            if len(obj.children) != 0:
                if obj.children[0].type in {'SURFACE', 'MESH', 'META'}:
                    modify_objects(how, 
                                   obj.children[0],
                                   radius_all, 
                                   radius_pm, 
                                   radius_type)
            else:
                if obj.type in {'SURFACE', 'MESH', 'META'}:
                    modify_objects(how, 
                                   obj,  
                                   radius_all, 
                                   radius_pm, 
                                   radius_type)
    if who == "ALL_ACTIVE":
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                if obj.children[0].type in {'SURFACE', 'MESH', 'META'}:
                    modify_objects(how, 
                                   obj.children[0],
                                   radius_all, 
                                   radius_pm, 
                                   radius_type)
            else:
                if obj.type in {'SURFACE', 'MESH', 'META'}:
                    modify_objects(how, 
                                   obj,
                                   radius_all, 
                                   radius_pm, 
                                   radius_type)



# Routine to modify the radii in picometer of a specific type of atom
def modify_objects(how, obj, radius_all, radius_pm, radius_type):

    # Radius pm 
    if how == "radius_pm":
        if radius_pm[0] in obj.name:
            obj.scale = (radius_pm[1]/100,) * 3
            
    # Radius all 
    if how == "radius_all":
        obj.scale *= radius_all      
              
    # Radius type 
    if how == "radius_type":
        for element in ELEMENTS:
            if element.name in obj.name:
                obj.scale = (element.radii[int(radius_type)],) * 3


# Read the default element list.
def read_elements():

    del ELEMENTS[:]

    for item in ELEMENTS_DEFAULT:

        # All three radii into a list
        radii = [item[4],item[5],item[6]]
        # The handling of the ionic radii will be done later. So far, it is an
        # empty list.
        radii_ionic = []

        li = ElementProp(item[0],item[1],item[2],item[3],
                                     radii,radii_ionic)
        ELEMENTS.append(li)


# Change color and radii by uisnf the list of elements.
def custom_datafile_change_atom_props():

    for obj in bpy.context.selected_objects:
        if len(obj.children) != 0:
            child = obj.children[0]
            if child.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in obj.name:
                        child.scale = (element.radii[0],) * 3
                        child.active_material.diffuse_color = element.color
        else:
            if obj.type in {'SURFACE', 'MESH', 'META'}:
                for element in ELEMENTS:
                    if element.name in obj.name:
                        obj.scale = (element.radii[0],) * 3
                        obj.active_material.diffuse_color = element.color


# This reads a custom data file.
def custom_datafile(path_datafile):

    if path_datafile == "":
        return False

    path_datafile = bpy.path.abspath(path_datafile)

    if os.path.isfile(path_datafile) == False:
        return False

    # The whole list gets deleted! We build it new.
    del ELEMENTS[:]

    # Read the data file, which contains all data
    # (atom name, radii, colors, etc.)
    data_file_p = open(path_datafile, "r")

    for line in data_file_p:

        if "Atom" in line:

            line = data_file_p.readline()
            # Number
            line = data_file_p.readline()
            number = line[19:-1]
            # Name
            line = data_file_p.readline()
            name = line[19:-1]
            # Short name
            line = data_file_p.readline()
            short_name = line[19:-1]
            # Color
            line = data_file_p.readline()
            color_value = line[19:-1].split(',')
            color = [float(color_value[0]),
                     float(color_value[1]),
                     float(color_value[2])]
            # Used radius
            line = data_file_p.readline()
            radius_used = float(line[19:-1])
            # Atomic radius
            line = data_file_p.readline()
            radius_atomic = float(line[19:-1])
            # Van der Waals radius
            line = data_file_p.readline()
            radius_vdW = float(line[19:-1])
            radii = [radius_used,radius_atomic,radius_vdW]
            radii_ionic = []

            element = ElementProp(number,name,short_name,color,
                                              radii, radii_ionic)

            ELEMENTS.append(element)

    data_file_p.close()

    return True


# Routine for separating atoms from a dupliverts strucutre.
def separate_atoms(scn):

    # Get first all important properties from the atoms, which the user
    # has chosen: location, color, scale
    obj = bpy.context.edit_object
        
    # Do nothing if it is not a dupliverts structure.
    if not obj.dupli_type == "VERTS":
       return {'FINISHED'}
        
    bm = bmesh.from_edit_mesh(obj.data)

    locations = []

    for v in bm.verts:
        if v.select:
            locations.append(obj.matrix_world * v.co)

    bm.free()
    del(bm)

    name  = obj.name
    scale = obj.children[0].scale
    material = obj.children[0].active_material

    # Separate the vertex from the main mesh and create a new mesh.
    bpy.ops.mesh.separate()
    new_object = bpy.context.scene.objects[0]
    # And now, switch to the OBJECT mode such that we can ...
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # ... delete the new mesh including the separated vertex
    bpy.ops.object.select_all(action='DESELECT')
    new_object.select = True
    bpy.ops.object.delete()  

    # Create new atoms/vacancies at the position of the old atoms
    current_layers=bpy.context.scene.layers

    # For all selected positions do:
    for location in locations:
        # For any ball do ...
        if "Vacancy" not in name:
            # NURBS ball
            if obj.children[0].type == "SURFACE":
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                    view_align=False, enter_editmode=False,
                                    location=location,
                                    rotation=(0.0, 0.0, 0.0),
                                    layers=current_layers)
                # Mesh ball                    
            elif obj.children[0].type == "MESH":
                bpy.ops.mesh.primitive_uv_sphere_add(
                                segments=32,
                                ring_count=32,                    
                                #segments=scn.mesh_azimuth,
                                #ring_count=scn.mesh_zenith,
                                size=1, view_align=False, enter_editmode=False,
                                location=location,
                                rotation=(0, 0, 0),
                                layers=current_layers)
                # Metaball
            elif obj.children[0].type == "META":
                bpy.ops.object.metaball_add(type='BALL', view_align=False, 
                            enter_editmode=False, location=location, 
                            rotation=(0, 0, 0), layers=current_layers)
        # If it is a vacancy create a cube ...                    
        else:
            bpy.ops.mesh.primitive_cube_add(
                           view_align=False, enter_editmode=False,
                           location=location,
                           rotation=(0.0, 0.0, 0.0),
                           layers=current_layers)
                               
        new_atom = bpy.context.scene.objects.active
        # Scale, material and name it.
        new_atom.scale = scale
        new_atom.active_material = material
        new_atom.name = name + "_sep"
        new_atom.select = True

    bpy.context.scene.objects.active = obj
    #bpy.ops.object.select_all(action='DESELECT')

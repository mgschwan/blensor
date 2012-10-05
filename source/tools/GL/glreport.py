#!/usr/bin/env python
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
import re

# note: this could certainly be more elegant
# 1) this kind of thing could work for other kinds of complex libraries, but
#    so far this is really tied to OpenGL only
# 2) for C and C++ a real parser like clang would allow a more thorough analysis
# 3) violations of "Don't Repeat Yourself" (DRY)


# configuration

# files containing the category data for OpenGL tokens
core_filepath       = "core.gl"
deprecated_filepath = "deprecated.gl"
agl_filepath        = "agl.gl"
cgl_filepath        = "cgl.gl"
egl_filepath        = "egl.gl"
glX_filepath        = "glX.gl"
wgl_filepath        = "wgl.gl"
libraries_filepath  = "libraries.gl"
extensions_filepath = "extensions.gl"
es11_filepath       = "es11.gl"
es20_filepath       = "es20.gl"

# location of source code to be scanned relative to this script
source_location = "../../../"
report_filepath = "report.txt"
    
# these files contain practically the entire OpenGL api
# scraping them spams the resulting report and makes it less useful
stop_files = [
    os.path.join('extern', 'glew', 'include', 'GL', 'glew.h'),
    os.path.join('extern', 'glew', 'include', 'GL', 'glxew.h'),
    os.path.join('extern', 'glew', 'include', 'GL', 'wglew.h'),
    os.path.join('extern', 'glew', 'src', 'glew.c'),
    os.path.join('source', 'blender', 'python', 'generic', 'bgl.h'),
    os.path.join('source', 'blender', 'python', 'generic', 'bgl.c')]

# for_all_files will visit every file in a file hierarchy
# doDirCallback  - called on each directory
# doFileCallback - called on each file
# doSkipDir      - should return true if a directory should be skipped
# doSkipFile     - should return true if a file should be skipped

def for_all_files(dir, doDirCallback, doFileCallback, doSkipDir, doSkipFile):
    for_all_files_(dir, dir, doDirCallback, doFileCallback, doSkipDir, doSkipFile)

def for_all_files_(prefix, dir, doDirCallback, doFileCallback, doSkipDir, doSkipFile):
    unprefixed_dir = dir[len(prefix):]

    if doDirCallback:
        doDirCallback(dir, unprefixed_dir)

    subdirlist = []

    for item in os.listdir(dir):
        path = os.path.join(dir, item)

        unprefixed_path = path[len(prefix):]

        if os.path.isfile(path) and (not doSkipFile or not doSkipFile(path, unprefixed_path, item)):
            if doFileCallback:
                doFileCallback(path, unprefixed_path, item)
        elif os.path.isdir(path) and (not doSkipDir or not doSkipDir(path, unprefixed_path, item)):
            subdirlist.append(path)

    subdirlist.sort()

    for subdir in subdirlist:
        for_all_files_(prefix, subdir, doDirCallback, doFileCallback, doSkipDir, doSkipFile)



def printDirectory(dir, unprefixed_dir):
    print("Entering: " + unprefixed_dir + " ...")



def printFilename(path, unprefixed_path, item):
    print(os.path.basename(path))



def isSvn(path, unprefixed_path, item):
    return item == ".svn"


# matches C, C++, and Objective C files
source_file = re.compile(".*\\.c$|.*\\.cpp$|.*\\.h$|.*\\.m$|.*\\.mm$")

def isNotSourceFile(path, unprefixed_path, item):
    return not source_file.match(item)



def isStopFile(path, unprefixed_path, item):
    return unprefixed_path in stop_files



def isNotGLUserFile(path, unprefixed_path, item):
    return isNotSourceFile(path, unprefixed_path, item) or isStopFile(path, unprefixed_path, item)



def never(path, unprefixed_path, item):
    return false


# This regular expression recognizes almost all tokens introduced by OpenGL
# It is careful to exclude tokens like "glow" or "GLARE", but makes sure to
# catche "fake" OpenGL identifiers that should be avoided like "glHerpDerp".

# XXX: TODO: It may be better to make an explicit list of allowed symbols so this can be simplified somewhat later

tokenizer = re.compile(r'''
    \b(?:
        # entry points
        (?:(?:gl|glu|glut|glew|glX|wgl|agl|CGL|glm)[A-Z_][a-zA-Z0-9_]*)|

        # enums
        (?:(?:GL|GLU|GLUT|GLEW|GLX|WGL|AGL|GLM)_[a-zA-Z0-9_]*])|

        # lower-case types
        (?:(?:GL|GLU|GLM)[a-z0-9_][a-zA-Z0-9_]*)|

        # camel-case types
        (?:(?:AGL|CGL|kCGL|GLX)[a-zA-Z0-9_]*)|

        # possible fakes
        (?:(?:glx|wgl|WGL|agl|AGL|glew|GLEW|CGL)[a-zA-Z0-9_]+)|

        # misc
        ChoosePixelFormat|
        DescribePixelFormat|
        GetEnhMetaFilePixelFormat|
        GetPixelFormat|
        SetPixelFormat|
        SwapBuffers|
        GLYPHMETRICSFLOAT|
        LAYERPLANEDESCRIPTOR|
        PIXELFORMATDESCRIPTOR|
        POINTFLOAT|
        GLDEBUGPROCAMD|
        GLDEBUGPROCARB
      )\b''', re.X)

summaryExtensions = set()
summaryTokens     = set()
summaryUnknown    = {}

database      = {}
platform_es11 = {}
platform_es20 = {}

report = {}

def add_report_entry(path, unprefixed_path, item):
    global summaryExtensions
    global summaryTokens
    global summaryUnknown

    global database
    global platform_es11
    global platform_es20

    global report

    print("Scanning: " + unprefixed_path + " ...");

    f = open(path)
    s = f.read()
    f.close()

    matches = tokenizer.findall(s)

    if matches:
        tokens = set(matches)

        extensions = set()

        unknownTokens = set()

        non_es11 = set()
        non_es20 = set()

        for token in tokens:
            summaryTokens.add(token)

            if token in database:
                extensions.update(database[token])
                summaryExtensions.update(database[token])

                if not token in platform_es11:
                    non_es11.add(token)

                if not token in platform_es20:
                    non_es20.add(token)

            else:
                unknownTokens.add(token)

                if not token in summaryUnknown:
                    summaryUnknown[token] = set()

                summaryUnknown[token].add(unprefixed_path)

        extensionsTokens = {}

        for token in tokens:
            for extension in extensions:
                if token in database and extension in database[token]:
                    if not extension in extensionsTokens:
                        extensionsTokens[extension] = set()

                    extensionsTokens[extension].add(token)

        report[unprefixed_path] = (extensionsTokens, extensions, tokens, unknownTokens, non_es11, non_es20)



def sorted_list(seq):
    outList = list(seq)
    outList.sort()

    return outList



# files are of the format "category: set([tokens...])"
# because this is smaller on disk and easier to read
# but it is easier to use "token: set([categories])"
# so this function "pivots" the database
def pivot_database(db_out, db_in):
    for label in db_in:
        tokens = db_in[label]

        for token in tokens:
            if not token in db_out:
                db_out[token] = set()

            db_out[token].add(label)

            
            
def read_database():
    global core_filepath
    global deprecated_filepath
    global agl_filepath
    global cgl_filepath
    global egl_filepath
    global glX_filepath
    global wgl_filepath
    global libraries_filepath
    global extensions_filepath
    global es11_filepath
    global es20_filepath

    core_file       = open(core_filepath)
    deprecated_file = open(deprecated_filepath)
    extensions_file = open(extensions_filepath)
    agl_file        = open(agl_filepath)
    cgl_file        = open(cgl_filepath)
    egl_file        = open(egl_filepath)
    glX_file        = open(glX_filepath)
    wgl_file        = open(wgl_filepath)
    libraries_file  = open(libraries_filepath)
    es11_file       = open(es11_filepath)
    es20_file       = open(es20_filepath)

    core_str       = core_file.read()
    deprecated_str = deprecated_file.read()
    extensions_str = extensions_file.read()
    agl_str        = agl_file.read()
    cgl_str        = cgl_file.read()
    egl_str        = egl_file.read()
    glX_str        = glX_file.read()
    wgl_str        = wgl_file.read()
    libraries_str  = libraries_file.read()
    es11_str       = es11_file.read()
    es20_str       = es20_file.read()

    # fill the database with all categories
    # database is used to classify tokens
    database_str = '{ %s %s %s %s %s %s %s %s %s }' % (
        core_str, deprecated_str, extensions_str,
        agl_str, cgl_str, egl_str, glX_str, wgl_str,
        libraries_str)

    global database
    pivot_database(database, eval(database_str))

    # platform_es11 and platform_es20 contain platforms
    # they are used to find tokens that do not belong on a particular platform
    # library functions included because otherwise library functions would be
    # considered to all be incompatible with each platform, 
    # which is noisy and not particularly true
    platform_es11_str = '{ %s %s %s %s %s %s %s }' % (
        es11_str, agl_str, cgl_str, egl_str, glX_str, wgl_str, libraries_str)

    global platform_es11
    pivot_database(platform_es11, eval(platform_es11_str))

    platform_es20_str = '{ %s %s %s %s %s %s %s }' %  (
        es20_str, agl_str, cgl_str, egl_str, glX_str, wgl_str, libraries_str)

    global platform_es20
    pivot_database(platform_es20, eval(platform_es20_str))



def make_report():
    global source_location
    for_all_files(source_location, printDirectory, add_report_entry, isSvn, isNotGLUserFile)



def write_plain_text_report(filepath):
    global summaryExtensions
    global summaryTokens
    global summaryUnknown

    global database
    global platform_es11
    global platform_es20

    global report
    
    out = open(filepath, "w")

    out.write("Files That Appear to Use OpenGL: " + str(len(report)) + "\n")

    sorted_report = sorted_list(report)

    for report_key in sorted_report:
        out.write("\t" + report_key + "\n")

    out.write("\n")

    out.write("All Categories Found:\n")

    for extension in sorted_list(summaryExtensions):
        out.write("\t" + extension + "\n")

    out.write("\n")

    out.write("All Tokens Used (categories in parenthesis):\n")

    for token in sorted_list(summaryTokens):
        if token in database:
            out.write("\t" + token + " (" + ", ".join(sorted_list(database[token])) + ")\n")
        else:
            out.write("\t" + token + "\n")

    out.write("\n")

    out.write("All Unknown Tokens (paths in parenthesis):\n")

    for token in sorted_list(summaryUnknown):
        out.write("\t" + token + " (" + ", ".join(sorted_list(summaryUnknown[token])) + ")\n")

    out.write("\n")

    for report_key in sorted_report:
        entry = report[report_key]

        out.write("Detail: " + report_key + ":\n")

        (extensionsTokens, extensions, tokens, unknownTokens, non_es11, non_es20) = entry

        for extension in sorted_list(extensionsTokens):
            out.write("\t" + extension + "\n")

            extensionTokens = extensionsTokens[extension]

            for extensionToken in sorted_list(extensionTokens):
                out.write("\t\t" + extensionToken + "\n")

            out.write("\n")

        if unknownTokens:
            out.write("\tUnknown Tokens\n")

            for unknownToken in sorted_list(unknownTokens):
                out.write("\t\t" + unknownToken + "\n")

            out.write("\n")

        if non_es11:
            out.write("\tIncompatible OpenGL ES 1.1 Tokens\n")

            for non_es_token in sorted_list(non_es11):
                out.write("\t\t" + non_es_token + "\n")

            out.write("\n")

        if non_es20:
            out.write("\tIncompatible OpenGL ES 2.0 Tokens\n")

            for non_es_token in sorted_list(non_es20):
                out.write("\t\t" + non_es_token + "\n")

            out.write("\n")

    out.close()

    
# main
read_database()
make_report()
write_plain_text_report(report_filepath)

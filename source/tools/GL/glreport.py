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
core_filename       = "core.gl"
system_filename     = "system.gl"
extensions_filename = "extensions.gl"
es11_filename       = "es11.gl"
es20_filename       = "es20.gl"

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

# these are the directories containing the original opengl spec data
# for now you will need to edit the script to regenerate the .gl files
# also, you'll have get those files from jwilkins
core_raw_dir       = "d:/glreport/core"
system_raw_dir     = "d:/glreport/system"
extensions_raw_dir = "d:/glreport/extensions"
es11_raw_dir       = "d:/glreport/es11"
es20_raw_dir       = "d:/glreport/es20"

do_regenerate_database = False

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

token_re = re.compile(r'''
    \b(?:
        # entry points
        (?:(?:gl|glu|glut|glew|glX|wgl|agl|glm)[A-Z_][a-zA-Z0-9_]*)|

        # enums
        (?:(?:GL|GLU|GLUT|GLEW|GLX|WGL|AGL|GLM)_[a-zA-Z0-9_]*])|

        # types
        (?:(?:GL|GLU|AGL|GLM)[a-z0-9_][a-zA-Z0-9_]*)|

        # possible fakes
        (?:(?:glx|GLX|wgl|WGL|agl|AGL|glew|GLEW)[a-zA-Z0-9_]+)
      )\b''', re.X)

summaryExtensions = set()
summaryTokens     = set()
summaryUnknown    = {}

database      = {}
database_es11 = {}
database_es20 = {}

report = {}

def add_report_entry(path, unprefixed_path, item):
    global summaryExtensions
    global summaryTokens
    global summaryUnknown

    global database
    global database_es11
    global database_es20

    global report

    print("Scanning: " + unprefixed_path + " ...");

    f = open(path)
    s = f.read()
    f.close()

    matches = token_re.findall(s)

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

                if not token in database_es11:
                    non_es11.add(token)

                if not token in database_es20:
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


# old function that read a pivoted database directly from the raw files
# def add_database_entries_from_fileFromFile(path, unprefixed_path, item):
    # print("Scanning: " + , unprefixed_path + " ...");

    # f = open(path)
    # s = f.read()
    # f.close()

    # matches = token_re.findall(s)

    # if matches:
        # tokens = set(matches)
        # basename = os.path.basename(path)

        # for token in tokens:
            # if not token in database:
                # database[token] = set()

            # database[token].add(basename)



def sorted_list(seq):
    outList = list(seq)
    outList.sort()

    return outList



def writeDatabaseEntry(path, unprefixed_path, item):
    print("Scanning: " + unprefixed_path + " ...");

    f = open(path)
    tokens = set(token_re.findall(f.read()))
    f.close()

    global db_out
    db_out.write("'" + os.path.basename(path) + "': set([\n\t'")
    db_out.write("',\n\t'".join(sorted_list(tokens)))
    db_out.write("']),\n\n")



def writeDatabase(inputDir, outputFile):
    global db_out
    db_out = open(outputFile, "w")
    db_out.write("# This file is generated by a script.\n")
    db_out.write("# If you edit it directly then your changes may be lost!\n\n")
    for_all_files(inputDir, printDirectory, writeDatabaseEntry, isSvn, None)
    db_out.close()
    db_out = None


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

            
            
def regenerate_database():
    writeDatabase(core_raw_dir,       core_filename)
    writeDatabase(system_raw_dir,     system_filename)
    writeDatabase(extensions_raw_dir, extensions_filename)
    writeDatabase(es11_raw_dir,       es11_filename)
    writeDatabase(es20_raw_dir,       es20_filename)



def read_database():
    core_file       = open('core.gl')
    system_file     = open('system.gl')
    extensions_file = open('extensions.gl')
    es11_file       = open('es11.gl')
    es20_file       = open('es20.gl')

    core_str       = core_file.read()
    system_str     = system_file.read()
    extensions_str = extensions_file.read()
    es11_str       = es11_file.read()
    es20_str       = es20_file.read()

    # fill the database with all categories
    # database is used to classify tokens
    global database
    pivot_database(database, eval('{' + core_str + system_str + extensions_str + es11_str + es20_str + '}'))

    # database_es11 and database_es20 contain platforms
    # they are used to find tokens that do not belong on a particular platform
    # system is included because otherwise system functions are
    # considered to all be incompatible with each platform
    global database_es11
    global database_es20
    pivot_database(database_es11, eval('{' + es11_str + system_str + '}'))
    pivot_database(database_es20, eval('{' + es20_str + system_str + '}'))


# old function kept for reference, used to read raw data directly into database
# def read_database_from_file()
     # for_all_files("./core",       printDirectory, add_database_entries_from_file, isSvn, isDummy)
     # for_all_files("./system",     printDirectory, add_database_entries_from_file, isSvn, isDummy)
     # for_all_files("./extensions", printDirectory, add_database_entries_from_file, isSvn, isDummy)
     # for_all_files("./es11",       printDirectory, add_database_entries_from_file, isSvn, isDummy)
     # for_all_files("./es20",       printDirectory, add_database_entries_from_file, isSvn, isDummy)


# insert a couple of symbols by hand
def fixup_database():
    global database

    # The GL[A-Z]+ style symbol would conflict too easily with legit tokens
    database["GLDEBUGPROCAMD"] = "GL_AMD_debug_output"
    database["GLDEBUGPROCARB"] = "GL_ARB_debug_output"

    # OpenCL interop
    database["cl_context"] = "GL_ARB_cl_event"
    database["cl_event"] = "GL_ARB_cl_event"


def make_report():
    global source_location
    for_all_files(source_location, printDirectory, add_report_entry, isSvn, isNotGLUserFile)

def write_plain_text_report(filepath):
    global summaryExtensions
    global summaryTokens
    global summaryUnknown

    global database
    global database_es11
    global database_es20

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

    

if do_regenerate_database:
   regenerate_database()

read_database()
fixup_database()
make_report()
write_plain_text_report(report_filepath)

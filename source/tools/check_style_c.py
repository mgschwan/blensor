#!/usr/bin/env python3.2

# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton
#
# #**** END GPL LICENSE BLOCK #****

# <pep8 compliant>

"""
This script runs outside of blender and scans source

python3.2 source/tools/check_source_c.py source/
"""

# TODO
#
# Add checks for:
# - space around operators
# - macro brace use
# - spaces around brackets with function call: func(args)
# - braces with function definitions
# - braces with typedefs
# - line length - in a not-too-annoying way
#   (allow for long arrays in struct definitions, PyMethodDef for eg)

from pygments import highlight, lex
from pygments.lexers import CLexer
from pygments.formatters import RawTokenFormatter

from pygments.token import Token

import argparse

PRINT_QTC_TASKFORMAT = False

TAB_SIZE = 4
LIN_SIZE = 120

global filepath
tokens = []


# could store index here too, then have prev/next methods
class TokStore:
    __slots__ = ("type", "text", "line")

    def __init__(self, type, text, line):
        self.type = type
        self.text = text
        self.line = line


def tk_range_to_str(a, b):
    return "".join([tokens[i].text for i in range(a, b + 1)])


def tk_item_is_newline(tok):
    return tok.type == Token.Text and tok.text == "\n"


def tk_item_is_ws_newline(tok):
    return (tok.type == Token.Text and tok.text.isspace()) or \
           (tok.type in Token.Comment)


def tk_item_is_ws(tok):
    return (tok.type == Token.Text and tok.text != "\n" and tok.text.isspace()) or \
           (tok.type in Token.Comment)


# also skips comments
def tk_advance_ws(index, direction):
    while tk_item_is_ws(tokens[index + direction]) and index > 0:
        index += direction
    return index


def tk_advance_ws_newline(index, direction):
    while tk_item_is_ws_newline(tokens[index + direction]) and index > 0:
        index += direction
    return index + direction


def tk_match_backet(index):
    backet_start = tokens[index].text
    assert(tokens[index].type == Token.Punctuation)
    assert(backet_start in "[]{}()")

    if tokens[index].text in "({[":
        direction = 1
        backet_end = {"(": ")", "[": "]", "{": "}"}[backet_start]
    else:
        direction = -1
        backet_end = {")": "(", "]": "[", "}": "{"}[backet_start]

    level = 1
    index_match = index + direction
    while True:
        item = tokens[index_match]
        if item.type == Token.Punctuation:
            if item.text == backet_start:
                level += 1
            elif item.text == backet_end:
                level -= 1
                if level == 0:
                    break

        index_match += direction

    return index_match


def tk_index_is_linestart(index):
    index_prev = tk_advance_ws_newline(index, -1)
    return tokens[index_prev].line < tokens[index].line


def extract_statement_if(index_kw):
    # assert(tokens[index_kw].text == "if")

    # seek back
    i = index_kw

    i_start = tk_advance_ws(index_kw - 1, direction=-1)

    # seek forward
    i_next = tk_advance_ws_newline(index_kw, direction=1)

    # print(tokens[i_next])

    if tokens[i_next].type != Token.Punctuation or tokens[i_next].text != "(":
        print("Error line: %d" % tokens[index_kw].line)
        print("if (\n"
              "   ^\n"
              ""
              "Character not found, insetad found:")
        print(tk_range_to_str(i_start, i_next))
        return None

    i_end = tk_match_backet(i_next)

    return (i_start, i_end)


def extract_operator(index_op):
    op_text = ""
    i = 0
    while tokens[index_op + i].type == Token.Operator:
        op_text += tokens[index_op + i].text
        i += 1
    return op_text, index_op + (i - 1)


def warning(message, index_kw_start, index_kw_end):
    if PRINT_QTC_TASKFORMAT:
        print("%s\t%d\t%s\t%s" % (filepath, tokens[index_kw_start].line, "comment", message))
    else:
        print("%s:%d: warning: %s" % (filepath, tokens[index_kw_start].line, message))

    # print(tk_range_to_str(index_kw_start, index_kw_end))


# ------------------------------------------------------------------
# Own Blender rules here!

def blender_check_kw_if(index_kw_start, index_kw, index_kw_end):

    # check if we have: 'if('
    if not tk_item_is_ws(tokens[index_kw + 1]):
        warning("no white space between '%s('" % tokens[index_kw].text, index_kw_start, index_kw_end)

    # check for: ){
    index_next = tk_advance_ws_newline(index_kw_end, 1)
    if tokens[index_next].type == Token.Punctuation and tokens[index_next].text == "{":
        if not tk_item_is_ws(tokens[index_kw + 1]):
            warning("no white space between trailing bracket '%s (){'" % tokens[index_kw].text, index_kw_start, index_kw_end)

        # check for: if ()
        #            {
        # note: if the if statement is multi-line we allow it
        if ((tokens[index_kw].line == tokens[index_kw_end].line) and
            (tokens[index_kw].line == tokens[index_next].line - 1)):

            warning("if body brace on a new line '%s ()\\n{'" % tokens[index_kw].text, index_kw, index_kw_end)
    else:
        # no '{' on a multi-line if
        if tokens[index_kw].line != tokens[index_kw_end].line:
            warning("multi-line if should use a brace '%s (\\n\\n) statement;'" % tokens[index_kw].text, index_kw, index_kw_end)


def blender_check_kw_else(index_kw):
    # for 'else if' use the if check.
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # else{
    if index_kw + 1 == i_next:
        warning("else has no space between following brace 'else{'", index_kw, i_next)

    # check if there are more then 1 spaces after else, but nothing after the following brace
    # else     {
    #     ...
    #
    # check for this case since this is needed sometimes:
    # else     { a = 1; }
    if ((tokens[index_kw].line == tokens[i_next].line) and
        (tokens[index_kw + 1].type == Token.Text) and
        (len(tokens[index_kw + 1].text) > 1) and
        (tokens[index_kw + 1].text.isspace())):

        # check if the next data after { is on a newline
        i_next_next = tk_advance_ws_newline(i_next, 1)
        if tokens[i_next].line != tokens[i_next_next].line:
            warning("unneeded whitespace before brace 'else ... {'", index_kw, i_next)

    # this check only tests for:
    # else
    # {
    # ... which is never OK

    if tokens[i_next].type == Token.Punctuation and tokens[i_next].text == "{":
        if tokens[index_kw].line < tokens[i_next].line:
            warning("else body brace on a new line 'else\\n{'", index_kw, i_next)


def blender_check_comma(index_kw):
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # ,sometext
    if index_kw + 1 == i_next:
        warning("comma has no space after it ',sometext'", index_kw, i_next)

    if tokens[index_kw - 1].type == Token.Text and tokens[index_kw - 1].text.isspace():
        warning("comma space before it 'sometext ,", index_kw, i_next)


def _is_ws_pad(index_start, index_end):
    return (tokens[index_start - 1].text.isspace() and
            tokens[index_end + 1].text.isspace())


def blender_check_operator(index_start, index_end, op_text):
    if op_text == "->":
        # allow compiler to handle
        return

    if len(op_text) == 1:
        if op_text in {"+", "-"}:
            # detect (-a) vs (a - b)
            if     (not tokens[index_start - 1].text.isspace() and
                    tokens[index_start - 1].text not in {"[", "(", "{"}):
                warning("no space before operator '%s'" % op_text, index_start, index_end)
            if     (not tokens[index_end + 1].text.isspace() and
                    tokens[index_end + 1].text not in {"]", ")", "}"}):
                # TODO, needs work to be useful
                # warning("no space after operator '%s'" % op_text, index_start, index_end)
                pass

        elif op_text in {"/", "%", "^", "|", "=", "<", ">"}:
            if not _is_ws_pad(index_start, index_end):
                warning("no space around operator '%s'" % op_text, index_start, index_end)
        elif op_text == "&":
            pass  # TODO, check if this is a pointer reference or not
        elif op_text == "*":
            pass  # TODO, check if this is a pointer reference or not
    elif len(op_text) == 2:
        # todo, remove operator check from `if`
        if op_text in {"+=", "-=", "*=", "/=", "&=", "|=", "^=",
                       "&&", "||",
                       "==", "!=", "<=", ">=",
                       "<<", ">>",
                       "%=",
                       # not operators, pointer mix-ins
                       ">*", "<*", "-*", "+*", "=*", "/*", "%*", "^*", "!*", "|*",
                       }:
            if not _is_ws_pad(index_start, index_end):
                warning("no space around operator '%s'" % op_text, index_start, index_end)

        elif op_text in {"++", "--"}:
            pass  # TODO, figure out the side we are adding to!
            '''
            if     (tokens[index_start - 1].text.isspace() or
                    tokens[index_end   + 1].text.isspace()):
                warning("spaces surrounding operator '%s'" % op_text, index_start, index_end)
            '''
        elif op_text == "!!":
            if tokens[index_end + 1].text.isspace():
                warning("spaces after operator '%s'" % op_text, index_start, index_end)

        elif op_text == "**":
            pass  # handle below
        else:
            warning("unhandled operator A '%s'" % op_text, index_start, index_end)
    else:
        #warning("unhandled operator B '%s'" % op_text, index_start, index_end)
        pass

    if len(op_text) > 1:
        if op_text[0] == "*" and op_text[-1] == "*":
            if not tokens[index_start - 1].text.isspace():
                warning("no space before pointer operator '%s'" % op_text, index_start, index_end)
            if tokens[index_end + 1].text.isspace():
                warning("space before pointer operator '%s'" % op_text, index_start, index_end)

    # check if we are first in the line
    if op_text[0] == "!":
        # if (a &&
        #     !b)
        pass
    elif op_text[0] == "*" and tokens[index_start + 1].text.isspace() == False:
        pass  # *a = b
    elif len(op_text) == 1 and op_text[0] == "-" and tokens[index_start + 1].text.isspace() == False:
        pass  # -1
    elif len(op_text) == 1 and op_text[0] == "&":
        # if (a &&
        #     &b)
        pass
    elif len(op_text) == 1 and op_text[0] == "~":
        # C++
        # ~ClassName
        pass
    elif len(op_text) == 1 and op_text[0] == "?":
        # (a == b)
        # ? c : d
        pass
    elif len(op_text) == 1 and op_text[0] == ":":
        # a = b ? c
        #      : d
        pass
    else:
        if tk_index_is_linestart(index_start):
            warning("operator starts a new line '%s'" % op_text, index_start, index_end)


def blender_check_linelength(index_start, index_end, length):
    if length > LIN_SIZE:
        text = "".join([tokens[i].text for i in range(index_start, index_end + 1)])
        for l in text.split("\n"):
            l = l.expandtabs(TAB_SIZE)
            if len(l) > LIN_SIZE:
                warning("line length %d > %d" % (len(l), LIN_SIZE), index_start, index_end)


def scan_source(fp, args):
    # print("scanning: %r" % fp)

    global filepath

    filepath = fp

    #print(highlight(code, CLexer(), RawTokenFormatter()).decode('utf-8'))
    code = open(filepath, 'r', encoding="utf-8").read()

    tokens[:] = []
    line = 1

    for ttype, text in lex(code, CLexer()):
        tokens.append(TokStore(ttype, text, line))
        line += text.count("\n")

    col = 0  # track line length
    index_line_start = 0

    for i, tok in enumerate(tokens):
        #print(tok.type, tok.text)
        if tok.type == Token.Keyword:
            if tok.text in {"switch", "while", "if", "for"}:
                item_range = extract_statement_if(i)
                if item_range is not None:
                    blender_check_kw_if(item_range[0], i, item_range[1])
            elif tok.text == "else":
                blender_check_kw_else(i)
        elif tok.type == Token.Punctuation:
            if tok.text == ",":
                blender_check_comma(i)
        elif tok.type == Token.Operator:
            # we check these in pairs, only want first
            if tokens[i - 1].type != Token.Operator:
                op, index_kw_end = extract_operator(i)
                blender_check_operator(i, index_kw_end, op)

        # ensure line length
        if (not args.no_length_check) and tok.type == Token.Text and tok.text == "\n":
            # check line len
            blender_check_linelength(index_line_start, i - 1, col)

            col = 0
            index_line_start = i + 1
        else:
            col += len(tok.text.expandtabs(TAB_SIZE))
                
        #elif tok.type == Token.Name:
        #    print(tok.text)

        #print(ttype, type(ttype))
        #print((ttype, value))

    #for ttype, value in la:
    #    #print(value, end="")


def scan_source_recursive(dirpath, args):
    import os
    from os.path import join, splitext

    def source_list(path, filename_check=None):
        for dirpath, dirnames, filenames in os.walk(path):

            # skip '.svn'
            if dirpath.startswith("."):
                continue

            for filename in filenames:
                filepath = join(dirpath, filename)
                if filename_check is None or filename_check(filepath):
                    yield filepath

    def is_source(filename):
        ext = splitext(filename)[1]
        return (ext in {".c", ".inl", ".cpp", ".cxx", ".hpp", ".hxx", ".h"})

    for filepath in source_list(dirpath, is_source):
        if "datafiles" in filepath:
            continue
        if     (filepath.endswith(".glsl.c") or
                filepath.endswith("DirectDrawSurface.cpp") or
                filepath.endswith("fnmatch.c") or
                filepath.endswith("smoke.c") or
                filepath.endswith("md5.c")):
            continue

        scan_source(filepath, args)


if __name__ == "__main__":
    import sys
    import os

    if 0:
        SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))))
        #scan_source_recursive(os.path.join(SOURCE_DIR, "source", "blender", "bmesh"))
        scan_source_recursive(os.path.join(SOURCE_DIR, "source", "blender", "modifiers"))
        sys.exit(0)

    desc = 'Check C/C++ code for conformance with blenders style guide:\nhttp://wiki.blender.org/index.php/Dev:Doc/CodeStyle)'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("paths", nargs='+', help="list of files or directories to check")
    parser.add_argument("-l", "--no-length-check", action="store_true",
                        help="skip warnings for long lines")
    args = parser.parse_args()

    for filepath in args.paths:
        if os.path.isdir(filepath):
            # recursive search
            scan_source_recursive(filepath, args)
        else:
            # single file
            scan_source(filepath, args)

#!/usr/bin/env python3

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

python3 source/tools/check_source_c.py source/
"""

import os

from check_style_c_config import IGNORE, IGNORE_DIR, SOURCE_DIR
IGNORE = tuple([os.path.join(SOURCE_DIR, ig) for ig in IGNORE])
IGNORE_DIR = tuple([os.path.join(SOURCE_DIR, ig) for ig in IGNORE_DIR])
WARN_TEXT = False


def is_ignore(f):
    for ig in IGNORE:
        if f == ig:
            return True
    for ig in IGNORE_DIR:
        if f.startswith(ig):
            return True
    return False

print("Scanning:", SOURCE_DIR)

# TODO
#
# Add checks for:
# - macro brace use
# - line length - in a not-too-annoying way
#   (allow for long arrays in struct definitions, PyMethodDef for eg)

from pygments import lex  # highlight
from pygments.lexers import CLexer
from pygments.formatters import RawTokenFormatter

from pygments.token import Token

import argparse

PRINT_QTC_TASKFORMAT = False
if "USE_QTC_TASK" in os.environ:
    PRINT_QTC_TASKFORMAT = True

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
    return tok.type == Token.Text and tok.text.strip("\t ") == "\n"


def tk_item_is_ws_newline(tok):
    return (tok.text == "") or \
           (tok.type == Token.Text and tok.text.isspace()) or \
           (tok.type in Token.Comment)


def tk_item_is_ws(tok):
    return (tok.text == "") or \
           (tok.type == Token.Text and tok.text.strip("\t ") != "\n" and tok.text.isspace()) or \
           (tok.type in Token.Comment)


# also skips comments
def tk_advance_ws(index, direction):
    while tk_item_is_ws(tokens[index + direction]) and index > 0:
        index += direction
    return index


def tk_advance_no_ws(index, direction):
    index += direction
    while tk_item_is_ws(tokens[index]) and index > 0:
        index += direction
    return index


def tk_advance_ws_newline(index, direction):
    while tk_item_is_ws_newline(tokens[index + direction]) and index > 0:
        index += direction
    return index + direction


def tk_advance_line_start(index):
    """ Go the the first non-whitespace token of the line.
    """
    while tokens[index].line == tokens[index - 1].line and index > 0:
        index -= 1
    return tk_advance_no_ws(index, 1)


def tk_advance_line(index, direction):
    line = tokens[index].line
    while tokens[index + direction].line == line or tokens[index].text == "\n":
        index += direction
    return index


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

    # ignore preprocessor
    i_linestart = tk_advance_line_start(index_kw)
    if tokens[i_linestart].text.startswith("#"):
        return None

    if tokens[i_next].type != Token.Punctuation or tokens[i_next].text != "(":
        warning("no '(' after '%s'" % tokens[index_kw].text, i_start, i_next)
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


def extract_cast(index):
    # to detect a cast is quite involved... sigh
    # assert(tokens[index].text == "(")

    # TODO, comment within cast, but thats rare
    i_start = index
    i_end = tk_match_backet(index)

    # first check we are not '()'
    if i_start + 1 == i_end:
        return None

    # check we have punctuation before the cast
    i = i_start - 1
    while tokens[i].text.isspace():
        i -= 1
    i_prev_no_ws = i
    if tokens[i].type in {Token.Keyword, Token.Name}:
        # avoids  'foo(bar)test'
        # but not ' = (bar)test'
        return None

    # validate types
    tokens_cast = [tokens[i] for i in range(i_start + 1, i_end)]
    for t in tokens_cast:
        if t.type == Token.Keyword:
            return None
        elif t.type == Token.Operator and t.text != "*":
            # prevent '(a + b)'
            # note, we could have '(float(*)[1+2])' but this is unlikely
            return None
        elif t.type == Token.Punctuation and t.text not in '()[]':
            # prevent '(a, b)'
            return None
    tokens_cast_strip = []
    for t in tokens_cast:
        if t.type in Token.Comment:
            pass
        elif t.type == Token.Text and t.text.isspace():
            pass
        else:
            tokens_cast_strip.append(t)
    # check token order and types
    if not tokens_cast_strip:
        return None
    if tokens_cast_strip[0].type not in {Token.Name, Token.Type, Token.Keyword.Type}:
        return None
    t_prev = None
    for t in tokens_cast_strip[1:]:
        # prevent identifiers after the first: '(a b)'
        if t.type in {Token.Keyword.Type, Token.Name, Token.Text}:
            return None
        # prevent: '(a * 4)'
        # allow:   '(a (*)[4])'
        if t_prev is not None and t_prev.text == "*" and t.type != Token.Punctuation:
            return None
        t_prev = t
    del t_prev

    # debug only
    '''
    string = "".join(tokens[i].text for i in range(i_start, i_end + 1))
    #string = "".join(tokens[i].text for i in range(i_start + 1, i_end))
    #types = [tokens[i].type for i in range(i_start + 1, i_end)]
    types = [t.type for t in tokens_cast_strip]

    print("STRING:", string)
    print("TYPES: ", types)
    print()
    '''

    return (i_start, i_end)


def warning(message, index_kw_start, index_kw_end):
    if PRINT_QTC_TASKFORMAT:
        print("%s\t%d\t%s\t%s" % (filepath, tokens[index_kw_start].line, "comment", message))
    else:
        print("%s:%d: warning: %s" % (filepath, tokens[index_kw_start].line, message))
        if WARN_TEXT:
            print("".join([tokens[i].text for i in range(index_kw_start, index_kw_end + 1)]))


def warning_lineonly(message, line):
    if PRINT_QTC_TASKFORMAT:
        print("%s\t%d\t%s\t%s" % (filepath, line, "comment", message))
    else:
        print("%s:%d: warning: %s" % (filepath, line, message))

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
        if not tk_item_is_ws(tokens[index_next - 1]):
            warning("no white space between trailing bracket '%s (){'" % tokens[index_kw].text, index_kw_start, index_kw_end)

        # check for: if ()
        #            {
        # note: if the if statement is multi-line we allow it
        if     ((tokens[index_kw].line == tokens[index_kw_end].line) and
                (tokens[index_kw].line == tokens[index_next].line - 1)):

            warning("if body brace on a new line '%s ()\\n{'" % tokens[index_kw].text, index_kw, index_kw_end)
    else:
        # no '{' on a multi-line if
        if tokens[index_kw].line != tokens[index_kw_end].line:
            warning("multi-line if should use a brace '%s (\\n\\n) statement;'" % tokens[index_kw].text, index_kw, index_kw_end)

    # check for: if (a &&
    #                b) { ...
    # brace should be on a newline.
    if (tokens[index_kw].line != tokens[index_kw_end].line):
        if tokens[index_kw_end].line == tokens[index_next].line:
            warning("multi-line should use a on a new line '%s (\\n\\n) {'" % tokens[index_kw].text, index_kw, index_kw_end)

    # check for: if () { ... };
    #
    # no need to have semicolon after brace.
    if tokens[index_next].text == "{":
        index_final = tk_match_backet(index_next)
        index_final_step = tk_advance_no_ws(index_final, 1)
        if tokens[index_final_step].text == ";":
            warning("semi-colon after brace '%s () { ... };'" % tokens[index_kw].text, index_final_step, index_final_step)


def blender_check_kw_else(index_kw):
    # for 'else if' use the if check.
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # else{
    if index_kw + 1 == i_next:
        warning("else has no space between following brace 'else{'", index_kw, i_next)

    # check if there are more than 1 spaces after else, but nothing after the following brace
    # else     {
    #     ...
    #
    # check for this case since this is needed sometimes:
    # else     { a = 1; }
    if     ((tokens[index_kw].line == tokens[i_next].line) and
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
    #
    # ... except if you have
    # else
    # #preprocessor
    # {

    if tokens[i_next].type == Token.Punctuation and tokens[i_next].text == "{":
        if tokens[index_kw].line < tokens[i_next].line:
            # check for preproc
            i_newline = tk_advance_line(index_kw, 1)
            if tokens[i_newline].text.startswith("#"):
                pass
            else:
                warning("else body brace on a new line 'else\\n{'", index_kw, i_next)

    # this check only tests for:
    # else
    # if
    # ... which is never OK
    if tokens[i_next].type == Token.Keyword and tokens[i_next].text == "if":
        if tokens[index_kw].line < tokens[i_next].line:
            warning("else if is split by a new line 'else\\nif'", index_kw, i_next)

    # check
    # } else
    # ... which is never OK
    i_prev = tk_advance_no_ws(index_kw, -1)
    if tokens[i_prev].type == Token.Punctuation and tokens[i_prev].text == "}":
        if tokens[index_kw].line == tokens[i_prev].line:
            warning("else has no newline before the brace '} else'", i_prev, index_kw)


def blender_check_kw_sizeof(index_kw):
    if tokens[index_kw + 1].text != "(":
        warning("expected '%s('" % tokens[index_kw].text, index_kw, index_kw + 1)


def blender_check_cast(index_kw_start, index_kw_end):
    # detect: '( float...'
    if tokens[index_kw_start + 1].text.isspace():
        warning("cast has space after first bracket '( type...'", index_kw_start, index_kw_end)
    # detect: '...float )'
    if tokens[index_kw_end - 1].text.isspace():
        warning("cast has space before last bracket '... )'", index_kw_start, index_kw_end)
    # detect no space before operator: '(float*)'

    for i in range(index_kw_start + 1, index_kw_end):
        if tokens[i].text == "*":
            # allow: '(*)'
            if tokens[i - 1].type == Token.Punctuation:
                pass
            elif tokens[i - 1].text.isspace():
                pass
            else:
                warning("cast has no preceeding whitespace '(type*)'", index_kw_start, index_kw_end)


def blender_check_comma(index_kw):
    i_next = tk_advance_ws_newline(index_kw, 1)

    # check there is at least one space between:
    # ,sometext
    if index_kw + 1 == i_next:
        warning("comma has no space after it ',sometext'", index_kw, i_next)

    if tokens[index_kw - 1].type == Token.Text and tokens[index_kw - 1].text.isspace():
        warning("comma space before it 'sometext ,", index_kw, i_next)


def blender_check_period(index_kw):
    # check we're now apart of ...
    if (tokens[index_kw - 1].text == ".") or (tokens[index_kw + 1].text == "."):
        return

    # 'a.b'
    if tokens[index_kw - 1].type == Token.Text and tokens[index_kw - 1].text.isspace():
        warning("period space before it 'sometext .", index_kw, index_kw)
    if tokens[index_kw + 1].type == Token.Text and tokens[index_kw + 1].text.isspace():
        warning("period space after it '. sometext", index_kw, index_kw)


def _is_ws_pad(index_start, index_end):
    return (tokens[index_start - 1].text.isspace() and
            tokens[index_end + 1].text.isspace())


def blender_check_operator(index_start, index_end, op_text, is_cpp):
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
                if not (is_cpp and ("<" in op_text or ">" in op_text)):
                    warning("no space around operator '%s'" % op_text, index_start, index_end)
        elif op_text == "&":
            pass  # TODO, check if this is a pointer reference or not
        elif op_text == "*":
           # This check could be improved, its a bit fuzzy
            if     ((tokens[index_start - 1].type in Token.Number) or
                    (tokens[index_start + 1].type in Token.Number)):
                warning("no space around operator '%s'" % op_text, index_start, index_end)
            elif not (tokens[index_start - 1].text.isspace() or tokens[index_start - 1].text in {"(", "[", "{"}):
                warning("no space before operator '%s'" % op_text, index_start, index_end)
    elif len(op_text) == 2:
        # todo, remove operator check from `if`
        if op_text in {"+=", "-=", "*=", "/=", "&=", "|=", "^=",
                       "&&", "||",
                       "==", "!=", "<=", ">=",
                       "<<", ">>",
                       "%=",
                       # not operators, pointer mix-ins
                       ">*", "<*", "-*", "+*", "=*", "/*", "%*", "^*", "|*",
                       }:
            if not _is_ws_pad(index_start, index_end):
                if not (is_cpp and ("<" in op_text or ">" in op_text)):
                    warning("no space around operator '%s'" % op_text, index_start, index_end)

        elif op_text in {"++", "--"}:
            pass  # TODO, figure out the side we are adding to!
            '''
            if     (tokens[index_start - 1].text.isspace() or
                    tokens[index_end   + 1].text.isspace()):
                warning("spaces surrounding operator '%s'" % op_text, index_start, index_end)
            '''
        elif op_text in {"!!", "!*"}:
            # operators we _dont_ want whitespace after (pointers mainly)
            # we can assume these are pointers
            if tokens[index_end + 1].text.isspace():
                warning("spaces after operator '%s'" % op_text, index_start, index_end)

        elif op_text == "**":
            pass  # handle below
        elif op_text == "::":
            pass  # C++, ignore for now
        elif op_text == ":!*":
            pass  # ignore for now
        elif op_text == "*>":
            pass  # ignore for now, C++ <Class *>
        else:
            warning("unhandled operator A '%s'" % op_text, index_start, index_end)
    else:
        #warning("unhandled operator B '%s'" % op_text, index_start, index_end)
        pass

    if len(op_text) > 1:
        if op_text[0] == "*" and op_text[-1] == "*":
            if     ((not tokens[index_start - 1].text.isspace()) and
                    (not tokens[index_start - 1].type == Token.Punctuation)):
                warning("no space before pointer operator '%s'" % op_text, index_start, index_end)
            if tokens[index_end + 1].text.isspace():
                warning("space before pointer operator '%s'" % op_text, index_start, index_end)

    # check if we are first in the line
    if op_text[0] == "!":
        # if (a &&
        #     !b)
        pass
    elif op_text[0] == "*" and tokens[index_start + 1].text.isspace() is False:
        pass  # *a = b
    elif len(op_text) == 1 and op_text[0] == "-" and tokens[index_start + 1].text.isspace() is False:
        pass  # -1
    elif len(op_text) == 2 and op_text == "++" and tokens[index_start + 1].text.isspace() is False:
        pass  # ++a
    elif len(op_text) == 2 and op_text == "--" and tokens[index_start + 1].text.isspace() is False:
        pass  # --a
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


def blender_check_function_definition(i):
    # Warning, this is a fairly slow check and guesses
    # based on some fuzzy rules

    # assert(tokens[index] == "{")

    # check function declaration is not:
    #  'void myfunc() {'
    # ... other uses are handled by checks for statements
    # this check is rather simplistic but tends to work well enough.

    i_prev = i - 1
    while tokens[i_prev].text == "":
        i_prev -= 1

    # ensure this isnt '{' in its own line
    if tokens[i_prev].line == tokens[i].line:

        # check we '}' isnt on same line...
        i_next = i + 1
        found = False
        while tokens[i_next].line == tokens[i].line:
            if tokens[i_next].text == "}":
                found = True
                break
            i_next += 1
        del i_next

        if found is False:

            # First check this isnt an assignment
            i_prev = tk_advance_no_ws(i, -1)
            # avoid '= {'
            #if tokens(index_prev).text != "="
            # print(tokens[i_prev].text)
            # allow:
            # - 'func()[] {'
            # - 'func() {'

            if tokens[i_prev].text in {")", "]"}:
                i_prev = i - 1
                while tokens[i_prev].line == tokens[i].line:
                    i_prev -= 1
                split = tokens[i_prev].text.rsplit("\n", 1)
                if len(split) > 1 and split[-1] != "":
                    split_line = split[-1]
                else:
                    split_line = tokens[i_prev + 1].text

                if split_line and split_line[0].isspace():
                    pass
                else:
                    # no whitespace!
                    i_begin = i_prev + 1

                    # skip blank
                    if tokens[i_begin].text == "":
                        i_begin += 1
                    # skip static
                    if tokens[i_begin].text == "static":
                        i_begin += 1
                    while tokens[i_begin].text.isspace():
                        i_begin += 1
                    # now we are done skipping stuff

                    warning("function's '{' must be on a newline", i_begin, i)


def quick_check_indentation(code):
    """
    Quick check for multiple tab indents.
    """
    t_prev = -1
    m_comment_prev = False
    ls_prev = ""

    for i, l in enumerate(code.split("\n")):
        skip = False

        # skip blank lines
        ls = l.strip()

        # comment or pre-processor
        if ls:
            # #ifdef ... or ... // comment
            if (ls[0] == "#" or ls[0:2] == "//"):
                skip = True
            # label:
            elif (':' in ls and l[0] != '\t'):
                skip = True
            # /* comment */
            #~ elif ls.startswith("/*") and ls.endswith("*/"):
            #~     skip = True
            # /* some comment...
            elif ls.startswith("/*"):
                skip = True
            # line ending a comment: */
            elif ls == "*/":
                skip = True
            # * middle of multi line comment block
            elif ls.startswith("* "):
                skip = True
            # exclude muli-line defines
            elif ls.endswith("\\") or ls.endswith("(void)0") or ls_prev.endswith("\\"):
                skip = True

        ls_prev = ls

        if skip:
            continue

        if ls:
            ls = l.lstrip("\t")
            tabs = l[:len(l) - len(ls)]
            t = len(tabs)
            if (t > t_prev + 1) and (t_prev != -1):
                warning_lineonly("indentation mis-match (indent of %d) '%s'" % (t - t_prev, tabs), i + 1)
            t_prev = t


def scan_source(fp, args):
    # print("scanning: %r" % fp)

    global filepath

    is_cpp = fp.endswith((".cpp", ".cxx"))

    filepath = fp

    #if "displist.c" not in filepath:
    #    return

    filepath_base = os.path.basename(filepath)

    #print(highlight(code, CLexer(), RawTokenFormatter()).decode('utf-8'))
    code = open(filepath, 'r', encoding="utf-8").read()

    quick_check_indentation(code)
    # return

    del tokens[:]
    line = 1

    for ttype, text in lex(code, CLexer()):
        if text:
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
            elif tok.text == "sizeof":
                blender_check_kw_sizeof(i)
        elif tok.type == Token.Punctuation:
            if tok.text == ",":
                blender_check_comma(i)
            elif tok.text == ".":
                blender_check_period(i)
            elif tok.text == "[":
                # note, we're quite relaxed about this but
                # disallow 'foo ['
                if tokens[i - 1].text.isspace():
                    if is_cpp and tokens[i + 1].text == "]":
                        # c++ can do delete []
                        pass
                    else:
                        warning("space before '['", i, i)
            elif tok.text == "(":
                # check if this is a cast, eg:
                #  (char), (char **), (float (*)[3])
                item_range = extract_cast(i)
                if item_range is not None:
                    blender_check_cast(item_range[0], item_range[1])
            elif tok.text == "{":
                # check previous character is either a '{' or whitespace.
                if (tokens[i - 1].line == tok.line) and not (tokens[i - 1].text.isspace() or tokens[i - 1].text == "{"):
                    warning("no space before '{'", i, i)

                blender_check_function_definition(i)

        elif tok.type == Token.Operator:
            # we check these in pairs, only want first
            if tokens[i - 1].type != Token.Operator:
                op, index_kw_end = extract_operator(i)
                blender_check_operator(i, index_kw_end, op, is_cpp)
        elif tok.type in Token.Comment:
            doxyfn = None
            if "\\file" in tok.text:
                doxyfn = tok.text.split("\\file", 1)[1].strip().split()[0]
            elif "@file" in tok.text:
                doxyfn = tok.text.split("@file", 1)[1].strip().split()[0]

            if doxyfn is not None:
                doxyfn_base = os.path.basename(doxyfn)
                if doxyfn_base != filepath_base:
                    warning("doxygen filename mismatch %s != %s" % (doxyfn_base, filepath_base), i, i)

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
        return (ext in {".c", ".inl", ".cpp", ".cxx", ".hpp", ".hxx", ".h", ".osl"})

    for filepath in sorted(source_list(dirpath, is_source)):
        if is_ignore(filepath):
            continue
        # for quick tests
        #~ if not filepath.endswith("creator.c"):
        #~     continue

        scan_source(filepath, args)


if __name__ == "__main__":
    import sys
    import os

    desc = 'Check C/C++ code for conformance with blenders style guide:\nhttp://wiki.blender.org/index.php/Dev:Doc/CodeStyle)'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("paths", nargs='+', help="list of files or directories to check")
    parser.add_argument("-l", "--no-length-check", action="store_true",
                        help="skip warnings for long lines")
    args = parser.parse_args()

    if 0:
        SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))))
        #scan_source_recursive(os.path.join(SOURCE_DIR, "source", "blender", "bmesh"))
        scan_source_recursive(os.path.join(SOURCE_DIR, "source/blender/makesrna/intern"), args)
        sys.exit(0)

    for filepath in args.paths:
        if os.path.isdir(filepath):
            # recursive search
            scan_source_recursive(filepath, args)
        else:
            # single file
            scan_source(filepath, args)

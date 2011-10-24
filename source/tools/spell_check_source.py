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

# <pep8 compliant>

"""
Script for checking source code spelling.

   python3 spell_check_source.py some_soure_file.py


Currently only python source is checked.
"""

import enchant
dict_spelling = enchant.Dict("en_US")

from spell_check_source_config import (dict_custom,
                                       dict_ignore,
                                       )


def words_from_text(text):
    """ Extract words to treat as English for spell checking.
    """
    text = text.strip("#'\"")
    text = text.replace("/", " ")
    text = text.replace("-", " ")
    words = text.split()

    # filter words
    words[:] = [w.strip("*?!:;.,'\"`") for w in words]

    def word_ok(w):
        # check for empty string
        if not w:
            return False

        # check for string with no characters in it
        is_alpha = False
        for c in w:
            if c.isalpha():
                is_alpha = True
                break
        if not is_alpha:
            return False

        # check for prefix/suffix which render this not a real word
        # example '--debug', '\n'
        # TODO, add more
        if w[0] in "%-+\\":
            return False

        # check for code in comments
        for c in "<>{}[]():._0123456789":
            if c in w:
                return False

        # check for words which contain lower case but have upper case
        # ending chars eg - 'StructRNA', we can ignore these.
        if len(w) > 1:
            has_lower = False
            for c in w:
                if c.islower():
                    has_lower = True
                    break
            if has_lower and (not w[1:].islower()):
                return False

        return True
    words[:] = [w for w in words if word_ok(w)]

    # text = " ".join(words)

    # print(text)
    return words


class Comment:
    __slots__ = ("file",
                 "text",
                 "line",
                 "type",
                 )

    def __init__(self, file, text, line, type):
        self.file = file
        self.text = text
        self.line = line
        self.type = type

    def parse(self):
        return words_from_text(self.text)


def extract_py_comments(filepath):

    import sys
    import token
    import tokenize

    source = open(filepath)

    comments = []

    prev_toktype = token.INDENT

    tokgen = tokenize.generate_tokens(source.readline)
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if toktype == token.STRING and prev_toktype == token.INDENT:
            comments.append(Comment(filepath, ttext, slineno, 'DOCSTRING'))
        elif toktype == tokenize.COMMENT:
            # non standard hint for commented CODE that we can ignore
            if not ttext.startswith("#~"):
                comments.append(Comment(filepath, ttext, slineno, 'COMMENT'))
        prev_toktype = toktype
    return comments


def spell_check_py_comments(filepath):

    comment_list = extract_py_comments(sys.argv[1])

    for comment in comment_list:
        for w in comment.parse():
            w_lower = w.lower()
            if w_lower in dict_custom or w_lower in dict_ignore:
                continue

            if not dict_spelling.check(w):
                print("%s:%d: %s, suggest (%s)" %
                      (comment.file,
                       comment.line,
                       w,
                       " ".join(dict_spelling.suggest(w)),
                       ))

import sys

if __name__ == "__main__":
    spell_check_py_comments(sys.argv[1])

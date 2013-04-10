#!/usr/bin/env python3

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
This script generates a credits list for:

   http://www.blender.org/development/credits


To use this script you'll need to set 2 variables (below)

eg:

   svn_log = "somelog.xml"
   tracker_csv = "tracker_report-2011-09-02.csv"


The first is the result of running this:

   svn log https://svn.blender.org/svnroot/bf-blender/trunk/blender -v --xml

The csv file must be saved from the tracker, be sure to select all patches
not just open ones. Go to the patch tracker URL and add append &func=downloadcsv
to the URL.


Running this script will create a file called 'credits.html',
the resulting data is then be copied into the Development/Credits page
in blender.org's typo3.


Example execution commands:

   svn log https://svn.blender.org/svnroot/bf-blender/trunk/blender -v --xml > ~/svn_log_bfb.xml
   svn log https://svn.blender.org/svnroot/bf-extensions/trunk/py/scripts/addons -v --xml > ~/svn_log_ext.xml
   python3 intern/tools/credits_svn_gen.py --svn_log_bfb=~/svn_log.xml --svn_log_ext=~/svn_log_ext.xml --tracker_csv=~/tracker_report-2012-10-03.csv
"""

# -----------------------------------------------------------------------------
# Generic Class and parsing code, could be useful for all sorts of cases


class SvnCommit:
    """Just data store really"""
    __slots__ = ("revision",
                 "author",
                 "date",
                 "message",
                 "paths",
                 )

    def __init__(self, xml):
        self.revision = int(xml.attributes["revision"].nodeValue)

        elems = xml.getElementsByTagName("author")
        self.author = elems[0].firstChild.nodeValue

        elems = xml.getElementsByTagName("date")
        self.date = elems[0].firstChild.nodeValue

        # treat the message
        # possible there is no message
        elems = xml.getElementsByTagName("msg")
        message = getattr(elems[0].firstChild, "nodeValue", "")
        message = " ".join(message.split())
        self.message = message

        # for now we ignore: elem.attributes["kind"]
        self.paths = [(elem.attributes["action"].value,
                       elem.firstChild.nodeValue,
                       )
                      for elem in xml.getElementsByTagName("path")]

    def __repr__(self):
        repr_dict = {}
        for attr in self.__slots__:
            repr_dict[attr] = getattr(self, attr)
        return repr(repr_dict)


def parse_commits(filepath, min_rev=0):
    from xml.dom.minidom import parse

    svn_xml = parse(filepath)
    # almost certainly only 1 but, just incase

    commits = []

    for log_list in svn_xml.getElementsByTagName("log"):
        log_entries = log_list.getElementsByTagName("logentry")
        for commit_xml in log_entries:

            # get all data from the commit into a dict for more easy checking.
            commit = SvnCommit(commit_xml)
            if commit.revision > min_rev:
                commits.append(commit)

    return commits


# -----------------------------------------------------------------------------
# Special checks to extract the credits

# TODO, there are for sure more companies then are currently listed.
# 1 liners for in wiki syntax
contrib_companies = [
    "<b>Unity Technologies</b> - FBX Exporter",
    "<b>BioSkill GmbH</b> - H3D compatibility for X3D Exporter, "
    "OBJ Nurbs Import/Export",
    "<b>AutoCRC</b> - Improvements to fluid particles, vertex color baking",
]

# ignore commits containing these messages
ignore_msg = (
    "SVN maintenance",
    )

# ignore these paths
# implicitly ignore anything _not_ in /trunk/blender
ignore_dir = (
    "/trunk/blender/extern/",
    "/trunk/blender/scons/",
    "/trunk/blender/intern/opennl/",
    "/trunk/blender/intern/moto/",
    )

ignore_revisions = {2,  # initial commit by Hans
                    }

# important, second value _must_ be the name used by projects.blender.org
# anyone who ever committed to blender
author_name_mapping = {
    "alexk": "Alexander Kuznetsov",
    "aligorith": "Joshua Leung",
    "antont": "Toni Alatalo",
    "aphex": "Simon Clitherow",
    "apinzonf": "Alexander Pinzon",
    "artificer": "Ben Batt",
    "ascotan": "Joseph Gilbert",
    "bdiego": "Diego Borghetti",
    "bebraw": "Juho Vepsalainen",
    "ben2610": "Benoit Bolsee",
    "billrey": "William Reynish",
    "bjornmose": "Jens Ole Wund",
    "blendix": "Brecht Van Lommel",
    "briggs": "Geoffrey Bantle",
    "broadstu": "Stuart Broadfoot",
    "broken": "Matt Ebb",
    "campbellbarton": "Campbell Barton",
    "cessen": "Nathan Vegdahl",
    "cmccad": "Casey Corn",
    "cyborgmuppet": "Ove Murberg Henriksen",
    "dail": "Justin Dailey",
    "damien78": "Damien Plisson",
    "damir": "Damir Prebeg",
    "desoto": "Chris Burt",
    "dfelinto": "Dalai Felinto",
    "dingto": "Thomas Dinges",
    "djcapelis": "D.J. Capelis",
    "dna": "Dan Eicher",
    "domino": "Domino Marama",
    "dougal2": "Doug Hammond",
    "eeshlo": "Alfredo de Greef",
    "elubie": "Andrea Weikert",
    "ender79": "Andrew Wiggin",  # an alias, not real name.
    "erwin": "Erwin Coumans",
    "frank": "Frank van Beek",
    "gaiaclary": "Gaia Clary",
    "genscher": "Daniel Genrich",
    "goofster": "Roel Spruit",
    "gsrb3d": "gsr b3d",
    "guignot": "Jacques Guignot",
    "guitargeek": "Johnny Matthews",
    "h_xnan": "Hans Lambermont",
    "halley": "Ed Halley",
    "hans": "Hans Lambermont",
    "harkyman": "Roland Hess",
    "hos": "Chris Want",
    "howardt": "Howard Trickey",
    "ianwill": "Willian Padovani Germano",
    "imbusy": "Lukas Steiblys",
    "intrr": "Alexander Ewering",
    "jaguarandi": "Andre Susano Pinto",
    "jandro": "Alejandro Conty Estevez",
    "jason_hays22": "Jason Hays",
    "jbakker": "Jeroen Bakker",
    "jbinto": "Jacques Beuarain",
    "jensverwiebe": "Jens Verwiebe",
    "jesterking": "Nathan Letwory",
    "jhk": "Janne Karhu",
    "jiri": "Jiri Hnidek",
    "joeedh": "Joseph Eagar",
    "jwilkins": "Jason Wilkins",
    "kakbarnf": "Robin Allen",
    "kanttori": "Juha Mäki-Kanto",
    "kazanbas": "Arystanbek Dyussenov",
    "keir": "Keir Mierle",
    "kester": "Kester Maddock",
    "khughes": "Ken Hughes",
    "kupoman": "Daniel Stokes",
    "kwk": "Konrad Kleine",
    "larstiq": "Wouter van Heyst",
    "letterrip": "Tom Musgrove",
    "lfrisken": "Luke Frisken",
    "lmg": "M.G. Kishalmi",
    "lockal": "Sv. Lockal",
    "loczar": "Francis Laurence",  # not 100% sure on this.
    "lonetech": "Yann Vernier",
    "lukastoenne": "Lukas Toenne",
    "lukep": "Jean-Luc Peurière",
    "lusque": "Ervin Weber",
    "maarten": "Maarten Gribnau",
    "mal_cando": "Mal Duffin",
    "mdewanchand": "Monique Dewanchand",
    "mein": "Kent Mein",
    "merwin": "Mike Erwin",
    "mfoxdogg": "Michael Fox",
    "mfreixas": "Marc Freixas",
    "michel": "Michel Selten",
    "migius": "Remigiusz Fiedler",
    "miikah": "Miika Hamalainen",
    "mikasaari": "Mika Saari",
    "mindrones": "Luca Bonavita",
    "mmikkelsen": "Morten Mikkelsen",
    "moguri": "Mitchell Stokes",
    "mokazon": "Matthew Smith",
    "mont29": "Bastien Montagne",
    "n_t": "Nils Thuerey",
    "nazgul": "Sergey Sharybin",
    "nexyon": "Joerg Mueller",
    "nicholas_rishel": "Nicholas Rishel",
    "nicholasbishop": "Nicholas Bishop",
    "phaethon": "Frederick Lee",
    "phase": "Rob Haarsma",
    "phlo": "Florian Eggenberger",
    "pidhash": "Joilnen Leite",
    "psy-fi": "Antony Riakiotakis",
    "rwenzlaff": "Robert Wenzlaff",
    "sateh": "Stefan Arentz",
    "schlaile": "Peter Schlaile",
    "scourage": "Robert Holcomb",
    "sergof": "Sergej Reich",
    "sgefant": "Stefan Gartner",
    "shul": "Shaul Kedem",
    "sirdude": "Kent Mein",
    "smerch": "Alex Sytnik",
    "snailrose": "Charlie Carley",
    "stiv": "Stephen Swaney",
    "theeth": "Martin Poirier",
    "themyers": "Ricki Myers",
    "ton": "Ton Roosendaal",
    "trumanblending": "Andrew Hale",
    "vekoon": "Elia Sarti",
    "xat": "Xavier Thomas",
    "xercesblue": "Francisco De La Cruz",
    "xglasyliax": "Peter Larabell",
    "xiaoxiangquan": "Xiao Xiangquan",
    "z0r": "Alex Fraser",
    "zaghaghi": "Hamed Zaghaghi",
    "zanqdo": "Daniel Salazar",
    "zuster": "Daniel Dunbar",

    # TODO, find remaining names
    "nlin": "",

    # added for 'author_overrides'
    "farny": "Mike Farnsworth",

    # --------------------
    # Extension Developers
    "aurel": "Aurel Wildfellner",
    "axon_d": "Dany Lebel",
    "bartekskorupa": "Bartek Skorupa",
    "bassamk": "Bassam Kurdali",
    "benjycook": "Benjy Cook",
    "beta-tester": "Alexander Nussbaumer",
    "blendphys": "Clemens Barth",
    "codemanx": "Sebastian Nell",
    "conz": "Constantin Rahn",
    "cotejrp1": "Philip Cote",
    "crouch": "Bart Crouch",
    "darknet": "John Phan",
    "dmbasso": "Daniel M. Basso",
    "dreampainter": "Gerwin Damsteegt",
    "eclectiel": "Eclectiel L",  # TODO, full name?
    "frigi": "Fabian Fricke",
    "gabhead": "Gabriel Beaudin",
    "gekko": "Jesse Kaukonen",
    "guillaum": "Bouchard Guillaume",
    "haikalle": "Kalle-Samuli Riihikoski",
    "imoverclocked": "Tim Spriggs",
    "jacepriester": "Jace Priester",
    "jaydez": "Jonathan Smith",
    "jcbdigger": "John Brown",
    "ken9": "Ken Nign",
    "kiravakaan": "Chris Foster",
    "kroopson": "Michael Krupa",
    "lichtwerk": "Philipp Oeser",
    "loolarge": "Ivo Grigull",
    "mauriceraybaud": "Maurice Raybaud",
    "meta-androcto": "Brendon Murphy",
    "michaelw": "Michael Williamson",
    "muraj": "Cory Perry",
    "paulo_gomes": "Paulo Gomes",
    "plasmasolutions": "Thomas Beck",
    "pontiac": "Martin Buerbaum",
    "seminumerical": "Morgan Mörtsell",
    "spudmn": "Aaron Keith",
    "testscreenings": "Florian Meyer",
    "tetron": "Peter Amstutz",
    "thomasl": "Thomas Larsson",
    "vencax": "Vaclav Klecanda",
    "venomgfx": "Pablo Vazquez",
    "wiseman303": "Adam Wiseman",
    }


# lame, fill in empty key/values
empty = []
for key, value in author_name_mapping.items():
    if not value:
        empty.append(key)
e = None
for e in empty:
    author_name_mapping[e] = e.title()
del empty, e

# useful reverse lookup RealName -> UnixName
author_name_mapping_reverse = {}
for key, value in author_name_mapping.items():
    author_name_mapping_reverse[value] = key

# store users we complained about missing already
alert_users = set()

# ----------------------------------------------------------------------------
# Since we cant detect some authors to credits, store spesific revisions
author_overrides_bfb = {
    "farny": (43567, 44698),
    "damir": (37043, 40311, 44550, 45295),
    "plasmasolutions": (52074, ),
    "lichtwerk": (51650, 51850, 51861),
    }

author_overrides_ext = {
    "vencax": (30897, ),
    }


def build_patch_name_map(filepath):
    """ Uses the CSV from the patch tracker to build a
        patch <-> author name mapping.
    """
    patches = {}
    import csv
    tracker = csv.reader(open(filepath, 'r', encoding='utf-8'),
                         delimiter=';',
                         quotechar='|')

    for i, row in enumerate(tracker):
        if i == 0:
            id_index = row.index("artifact_id")
            author_index = row.index("submitter_name")
            date_index = row.index("open_date")
            status_index = row.index("status_name")  # Open/Closed
            min_len = max(id_index, author_index, status_index, date_index)
        else:
            if len(row) < min_len:
                continue

            # lets just store closed patches, saves time
            if row[status_index].strip("\"") == 'Closed':
                patches[int(row[id_index])] = {
                    "author": row[author_index].strip("\"").strip().title(),
                    "date": row[date_index].strip("\""),
                    }
    return patches


def patch_numbers_from_log(msg):
    """ Weak method to pull patch numbers out of a commit log.
        rely on the fact that its unlikely any given number
        will match up with a closed patch but its possible.
    """
    patches = []
    msg = msg.replace(",", " ")
    msg = msg.replace(".", " ")
    msg = msg.replace("-", " ")
    for w in msg.split():
        if      (w[0].isdigit() or
                (len(w) > 2 and w[0] == "[" and w[1] == "#") or
                (len(w) > 1 and w[0] == "#")):

            try:
                num = int(w.strip("[]#"))
            except ValueError:
                num = -1

            if num != -1:
                patches.append(num)

    return patches


def patch_find_author(commit, patch_map):
    patches = patch_numbers_from_log(commit.message)
    for p in patches:
        if p in patch_map:
            patch = patch_map[p]

            '''
            print("%r committing patch for %r %d" % (
                  author_name_mapping[commit.author],
                  patch["author"],
                  commit.revision,
                  ))
            '''

            return p, patch["author"]

    return None, None


class Credit(object):
    __slots__ = ("commits",
                 "is_patch"
                 )

    def __init__(self):
        self.commits = []
        self.is_patch = False

    def contribution_years(self):
        years = [int(commit.date.split("-")[0]) for commit in self.commits]
        return min(years), max(years)


def is_credit_commit_valid(commit):

    if commit.revision in ignore_revisions:
        return False

    for msg in ignore_msg:
        if msg in commit.message:
            return False

    def is_path_valid(path):
        if not (path.startswith("/trunk/blender/") or path.startswith("/trunk/py/scripts/addons")):
            return False
        for p in ignore_dir:
            if path.startswith(p):
                return False
        return True

    has_valid_path = False
    for action, path in commit.paths:
        if is_path_valid(path):
            has_valid_path = True
            break

    if not has_valid_path:
        return False

    # couldnt prove invalid, must be valid
    return True


def main_credits(min_rev_bfb=0, min_rev_ext=0):

    # ------------------------------------------------------------------------
    # Parse Args

    import sys
    import os
    import argparse

    usage_text = (
            "Run Script: %s [options]" % os.path.basename(__file__))

    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument("-s", "--svn_log_bfb", dest="svn_log_bfb",
            metavar='FILE', required=True,
            help="File path pointing to svn log, "
                 "generated by 'svn log . -v --xml'")
    parser.add_argument("-se", "--svn_log_ext", dest="svn_log_ext",
            metavar='FILE', required=True,
            help="File path pointing to svn log (for extensions), "
                 "generated by 'svn log . -v --xml'")
    parser.add_argument("-c", "--tracker_csv", dest="tracker_csv",
            metavar='FILE', required=True,
            help="File path pointing to CSV file saved by the patch tracker")

    args = parser.parse_args(sys.argv[1:])

    tracker_csv = args.tracker_csv
    svn_log_bfb = args.svn_log_bfb
    svn_log_ext = args.svn_log_ext

    # ------------------------------------------------------------------------
    # Main Logic

    # bf-blender only
    patch_map = build_patch_name_map(tracker_csv)

    credits = {key: Credit() for key in author_name_mapping}

    def commit_to_credit(commits, author_overrides):
        # print(len(commits))
        author_overrides_reverse = {
            revision: author
            for author, revisions in author_overrides.items()
            for revision in revisions}

        for commit in commits:
            if not is_credit_commit_valid(commit):
                continue

            patch_id, patch_author = patch_find_author(commit, patch_map)

            if patch_author is None:
                # will error out if we miss adding new devs
                author = author_overrides_reverse.get(commit.revision,
                                                      commit.author)
                credit = credits.get(author)
                if credit is None:

                    if commit.author not in alert_users:
                        print("warning: '%s' is not in "
                              "'author_name_mapping' !" % commit.author)
                        alert_users.add(commit.author)

                    # will be discarded
                    credit = Credit()

            else:
                # so we dont use again
                del patch_map[patch_id]

                unix_name = author_name_mapping_reverse.get(patch_author)
                if unix_name is None:  # not someone who contributed before
                    author_name_mapping_reverse[patch_author] = patch_author
                    author_name_mapping[patch_author] = patch_author

                    if patch_author not in credits:
                        credits[patch_author] = Credit()

                    credit = credits[patch_author]
                    credit.is_patch = True
                else:
                    credit = credits[unix_name]

            credit.commits.append(commit)

    for (commits, author_overrides) in (
             (parse_commits(svn_log_bfb, min_rev=min_rev_bfb),
              author_overrides_bfb),

             (parse_commits(svn_log_ext, min_rev=min_rev_ext),
              author_overrides_ext)):

        commit_to_credit(commits, author_overrides)
    del commits, author_overrides

    # write out the wiki page
    # sort by name
    is_main_credits = (min_rev_bfb == 0 and min_rev_ext == 0)
    # print(min_rev_bfb, min_rev_ext)
    if is_main_credits:
        filename = "credits.html"
    else:
        filename = "credits_release.html"

    file = open(filename, 'w', encoding="utf-8")

    file.write("<h3>Individual Contributors</h3>\n\n")

    patch_word = "patch", "patches"
    commit_word = "commit", "commits"

    lines = []
    for author in sorted(author_name_mapping.keys()):
        credit = credits[author]

        if not credit.commits:
            continue

        author_real = author_name_mapping.get(author)

        if author_real is None:
            print("warning: '%s' is not in 'author_name_mapping' dict!")
            author_real = author

        if author_real == author:
            name_string = "<b>%s</b>" % author
        else:
            name_string = "<b>%s</b> (%s)" % (author_real, author)

        if is_main_credits:
            credit_range = credit.contribution_years()
            if credit_range[0] != credit_range[1]:
                credit_range_string = "(%d - %d)" % credit_range
            else:
                credit_range_string = "- %d" % credit_range[0]
        else:
            # for a single release its not interesting to show years
            credit_range_string = ""

        is_plural = len(credit.commits) > 1

        commit_term = (patch_word[is_plural] if credit.is_patch
                       else commit_word[is_plural])

        lines.append("%s, %d %s %s<br />\n" %
                     (name_string,
                      len(credit.commits),
                      commit_term,
                      credit_range_string,
                      ))
    lines.sort()
    for line in lines:
        file.write(line)
    del lines

    file.write("\n\n")

    # -------------------------------------------------------------------------
    # Companies, hard coded
    if is_main_credits:
        file.write("<h3>Contributions from Companies & Organizations</h3>\n")
        file.write("<p>\n")
        for line in contrib_companies:
            file.write("%s<br />\n" % line)
        file.write("</p>\n")

        import datetime
        now = datetime.datetime.now()
        fn = __file__.split("\\")[-1].split("/")[-1]
        file.write("<p><center><i>Generated by '%s' %d/%d/%d</i></center></p>\n" %
                   (fn, now.year, now.month, now.day))

    file.close()
    print("written:", filename)


def main():
    main_credits()
    main_credits(min_rev_bfb=52851, min_rev_ext=4072)

if __name__ == "__main__":
    main()

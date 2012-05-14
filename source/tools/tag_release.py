#!/usr/bin/env python3.2

REV_BLENDER = 44136
REV_EXTENSIONS = 2994
REV_LOCALE = 392

TAG_BLENDER = "blender-2.62-release"
TAG_EXTENSIONS = TAG_LOCALE = "2_62_release"

print("\n# Run these commands from the blender source dir:")

# -----------------------------------------------------------------------------
# Blender

print('svn cp '
      'https://svn.blender.org/svnroot/bf-blender/trunk@r%d '
      'https://svn.blender.org/svnroot/bf-blender/tags/%s '
      '-m "tagging blender release: %s, %d"' %
      (REV_BLENDER, TAG_BLENDER, TAG_BLENDER, REV_BLENDER))


# -----------------------------------------------------------------------------
# Extensions

print('svn cp '
      'https://svn.blender.org/svnroot/bf-extensions/trunk@r%d '
      'https://svn.blender.org/svnroot/bf-extensions/tags/%s '
      '-m "tagging blender release: %s, %d"' %
      (REV_EXTENSIONS, TAG_EXTENSIONS, TAG_EXTENSIONS, REV_EXTENSIONS)
      )


# -----------------------------------------------------------------------------
# Translations

print('svn cp '
      'https://svn.blender.org/svnroot/bf-translations/trunk@r%d '
      'https://svn.blender.org/svnroot/bf-translations/tags/%s '
      '-m "tagging blender release: %s, %d"' %
      (REV_LOCALE, TAG_LOCALE, TAG_LOCALE, REV_LOCALE),
      )


# -----------------------------------------------------------------------------
# Change externals

# switch a checkout of trunk into the tag o avoid a second checkout
# windows/osx may want to switch lib too.
print('svn sw '
      'https://svn.blender.org/svnroot/bf-blender/tags/%s/blender' %
      (TAG_BLENDER, )
      )

# Change the extensions location, we can ignore addons_contrib here.
print('svn propset svn:externals '
      '"addons https://svn.blender.org/svnroot/bf-extensions/tags/%s/py/scripts/addons" '
      'release/scripts ' %
      (TAG_EXTENSIONS, )
      )

print('svn propset svn:externals '
      '"locale https://svn.blender.org/svnroot/bf-translations/tags/%s/locale" '
      'release/datafiles' %
      (TAG_LOCALE, )
      )

print('svn ci '
      'release/scripts '
      'release/datafiles '
      '-m "tagging blender release: %s, %d"' %
      (TAG_BLENDER, REV_BLENDER)
      )


# switch back to trunk
print("svn sw https://svn.blender.org/svnroot/bf-blender/trunk/blender")

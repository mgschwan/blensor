OpenGL Tools

OpenGL Report Generator

The script glreport.py will generate a file named report.txt
which contains information about the OpenGL symbols used by
Blender and what OpenGL version and extensions are required.

The report starts with summary information:
    Which files appear to use OpenGL
    All of the "categories" of symbols that were found
    A list of all the tokens found
    A list of all tokens that could not be categorized
    
The remainder of the file is a detailed report for each
source file:
    The tokens found in each category
    A list of unknown tokens
    A list of tokens that are incompatible with each of several "platforms"

A category is just a set of tokens.  An example would be
the tokens introduced in OpenGL version 1.0 but have not
been deprecated.

Another category are system dependent or portable libraries
such as GLX and GLU.

A platform is a set of related functionality, such as
OpenGL ES.  For each file there is a list of tokens that
do not work on each platform.  The currently tested 
platforms are OpenGL ES versions 1.1 and 2.0.

OpenGL 3+ core and compatibility profiles are not tested
in this way.  Currently this is handled by separating
each version of OpenGL into regular and deprecated
categories.

A deprecated function is one that has been or will be
removed from OpenGL in the future.  The category
GL_VERSION_1_2_DEPRECATED does not mean it was deprecated
in OpenGL 2.0, but that it has been deprecated as some
point, but the function was originally introduced with
OpenGL 1.2.  If you do not care about deprecation then
you can simply take it to mean that same thing as
GL_VERSION_1_2.

Another useful category is OLD_TOKEN_NAME.  For example,
OpenGL 1.3 introduced Fog Coordinates, but the token
names given for the enumerations were inconsistent with
OpenGL conventions.  To solve this they renamed the tokens
in version 1.4.  Both names remain valid, however if a
token is in the OLD_TOKEN_NAME_1_4 category it means that
it was renamed in that version of OpenGL.  Unfortunately it
is not easy at this time to tell from the report what
the new name is, so if you do not know you will have to
look at the spec for the version given by the category
name.  The version indicates when the token was renamed,
not the original version that the token was introduced.
The original version can be determined by looking at the
other categories the token is in.

Unfortunately the script does not have a way to catch usage
of extensions that do not introduce new tokens.  For example,
and extension like blend_square or texenv_add only say that
an old enumerant can be used in a new way without generating
an error.

There is still some work to be done creating categories of
tokens that would give us additional information.  An example
might be a class of forbidden functions that should never
be used along with a class of suspicious functions whose
usage should be double checked.

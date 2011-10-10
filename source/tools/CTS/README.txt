== What ==
This directory contains files for usage with the
COLLADA Conformance Test Suite (CTS).

If you haven't got it yet, you can register as
implementor at https://www.khronos.org/implementers/collada
Enter 'Blender Foundation' as the company for which
conformance will be run. When we get to the point all
tests pass and badges are earned, contact Nathan Letwory either
on the bf-committers mailing list or through is website
http://www.letworyinteractive.com/b/

== How-to ==
1. After you have unzipped CTS to some location, like C:\CTS, make
sure to install all required software. These can be found in the
Prerequisites directory: python-2.4.1.msi, PyOpenGL-2.0.1.09.py2.4-numpy23, pywin32-208.win32-py2.4 and pwxPython2.6-win32-unicode-2.6.1.0-py24.

2. Copy FBlender.py to the Scripts directory.

3. Copy empty.blend to the root directory of your CTS installation

4. Modify config.py in the root directory of your CTS installation:

blenderPath		d:\blenderdev\buildcmake\bin\Debug\blender.exe
blenderEmpty		d:\blenderdev\COLLADA\CTS\empty.blend
blenderDefaultDae	d:\blenderdev\COLLADA\CTS\Documentation\CTF_Template.dae

Don't forget to change the paths according to your installation. Also, note that between key and value tabs are used, not spaces!

5. Run COLLADATestSuite.py with the Python 2.4 you've installed. For instructions how to create a test procedure, see the documentation in Documentation/

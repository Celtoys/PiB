
#
# --- MIT Open Source License --------------------------------------------------
# PiB - Python Build System
# Copyright (C) 2011 by Don Williamson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
#
# PiB.py: Entry point for the build system.
#
# TODO:
#
#   Look into cPickle
#   Instead of using input/output FILES, use NODES.
#   Cache explicit dependencies and mix with Windows USN Journal
#   Are configurations enough? Are they too much?
#   Conversion of command-line options to the command-line is a little error-prone
#   vcproj/sln clean?
#   Does the code deal with #include "file.cpp"?
#   Needs to be simpler! I'm sure I've missed some key opportunities in the
#    dependency graph stuff
#   Add profiling and debug output
#
# Functionality tests:
#
#    Build from scratch
#    Modify source files
#    Delete .obj files
#    Delete .exe files
#    File with error
#    Modify implicitly dependent files
#    Clean & build
#    Delete output directories
#

import os
import sys
import Utils


# See if the caller wants to use a custom build script name/location
pibfile = Utils.GetSysArgvProperty("-pf", "pibfile")
Utils.ExecPibfile(pibfile)

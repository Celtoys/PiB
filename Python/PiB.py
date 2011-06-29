
#
# pib.py: Entry point for the build system.
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
# TODO:
#
#   Compiler text not showing up in IDE!
#   Look into cPickle
#   Instead of using input/output FILES, use NODES.
#   Cache explicit dependencies and mix with Windows USN Journal
#   Are configurations enough? Are they too much?
#   Conversion of command-line options to the command-line is a little error-prone
#   Compile steps not outputting to VS window
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
from MSVCPlatform import *
from BuildSystem import *


def LoadBuildScript(env):

    # See if the caller wants to use a custom build script name/location
    pibfile = "pibfile"
    if "-pf" in sys.argv:
        i = sys.argv.index("-pf") + 1
        if i < len(sys.argv):
            pibfile = sys.argv[i]

    # Load the build script file
    if not os.path.exists(pibfile):
        print("ERROR: No pibfile found")
        return None

    # Inject all the needed modules into the build script
    build_script = { }
    exec("from MSVCPlatform import *", build_script)
    exec("from MSVCGeneration import *", build_script)
    exec("from BuildSystem import *", build_script)
    exec("from Utils import *", build_script)

    # Execute each line
    with open(pibfile) as f:
        exec(f.read(), build_script)

    return build_script


def PreBuild(env, build_script):

    if "PreBuild" in build_script:
        build_script["PreBuild"](env)


def Clean(env, build_graphs):

    print("PiB Cleaning...")
    for node in build_graphs:
        env.ExecuteNodeClean(node)


def Build(env, build_graphs):

    print("PiB Building...")
    for node in build_graphs:
        env.ExecuteNodeBuild(node)

    env.SaveFileMetadata()


def PostBuild(env, build_script):

    if "PostBuild" in build_script:
        build_script["PostBuild"](env)

    
# Get the main build environment
env = Environment.New()
if env == None:
    sys.exit(1)

# Load the pibfile
build_script = LoadBuildScript(env)
if build_script == None:
    sys.exit(1)

# Execute any pre build steps
PreBuild(env, build_script)

# Construct the explicit build graphs
build_graphs = build_script["Build"](env)

if "clean" in sys.argv:
    Clean(env, build_graphs)
elif "rebuild" in sys.argv:
    Clean(env, build_graphs)
    Build(env, build_graphs)
else:
    Build(env, build_graphs)

# Execute any post build steps
PostBuild(env, build_script)

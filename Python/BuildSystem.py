
#
# BuildSystem.py: The core dependency graph build/evaluation code and metadata
# management.
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

import os
import sys
import shutil
import Utils


#
# File metadata that persists between builds to aid dependency evaluation and
# track any changes.
#
class FileMetadata:

    def __init__(self):

        self.ModTime = 0
        self.Changed = True
        self.ImplicitDeps = [ ]

    def HasFileChanged(self, filename):

        # Check the cached result
        if self.Changed:
            return True

        # If the file no longer exists, it has changed
        if not os.path.exists(filename):
            self.Changed = True
            return True

        # Compare modification times
        mod_time = os.path.getmtime(filename)
        if mod_time != self.ModTime:
            self.Changed = True

        return self.Changed

    def UpdateModTime(self, filename):

        if self.Changed and os.path.exists(filename):

            self.ModTime = os.path.getmtime(filename)
            self.Changed = False

    def SetImplicitDeps(self, env, deps):

        # Ensure each implicit dependency has a metadata entry
        for dep in deps:
            env.GetFileMetadata(dep.GetInputFile(env))

        self.ImplicitDeps = deps

    def __repr__(self):

        return str(self.ModTime) + "->" + str(self.ImplicitDeps)


#
# Base node for the dependency graph
#
class Node:

    def __init__(self):
        # TODO: Need to force derived class to implement this
        self.Dependencies = [ ]

    def GetInputFile(self, env):
        raise Exception("Derived class hasn't implemented GetInputFile")

    def GetOutputFiles(self, env):
        raise Exception("Derived class hasn't implemented GetOutputFiles")

    def GetTempOutputFiles(self, env):
        return self.GetOutputFiles(env)


#
# A file node is simply an ecapsulation around a file on disk with no build step
#
class FileNode (Node):

    def __init__(self, crc):

        self.CRC = crc
        self.Dependencies = [ ]

    def GetInputFile(self, env):
        return env.GetFilename(self.CRC)

    def GetOutputFiles(self, env):
        return [ env.GetFilename(self.CRC) ]


class CopyNode (Node):

    def __init__(self, output, source, dest):

        self.Dependencies = [ output ]
        self.Source = source
        self.Destination = dest

    def Build(self, env):

        print("Copying from " + self.Source + " to " + self.Destination)
        Utils.Makedirs(os.path.dirname(self.Destination))
        shutil.copyfile(self.Source, self.Destination)

    def GetInputFile(self, env):
        return self.Source

    def GetOutputFiles(self, env):
        return [ self.Destination ]


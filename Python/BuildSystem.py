
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
# BuildSystem.py: Some basic build nodes and file metadata.
#

import os
import sys
import shutil
import pickle
import binascii
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
# Metadata that persists between builds
#
class BuildMetadata:
    
    OutputFilename = "metadata.pib"
    
    def __init__(self):

        self.Version = 1
        self.FileMap = { }
        self.FileMetadata = { }
    
    def Save(self):

        with open(BuildMetadata.OutputFilename, "wb") as f:
            pickle.dump(self, f)

    def Load():

        try:
            # Open and load the metadata file if it exists
            if os.path.exists(BuildMetadata.OutputFilename):
                with open(BuildMetadata.OutputFilename, "rb") as f:
                    data = pickle.load(f)

                    # Return if the version matches
                    if hasattr(data, "Version") and data.Version == 1:
                        return data

                    print("Metadata file version out of date, discarding...")

        # Handle malformed files
        except:
            print("Error loading Metadata file, discarding...")

        # Return empty constructed build metadata if it can't be loaded
        return BuildMetadata()

    def AddToFileMap(self, filename):

        # Generate the CRC
        filename = Utils.NormalisePath(filename)
        crc = binascii.crc32(bytes(filename, "utf-8"))

        # Check for collision
        if crc in self.FileMap and filename != self.FileMap[crc]:
            raise Exception("CRC collision with " + filename + " and " + self.FileMap[crc])

        self.FileMap[crc] = filename
        return crc

    def GetFilename(self, crc):

        return self.FileMap[crc]
        
    def GetFileMetadata(self, target, filename):

        # Create unique file metadata objects for each target so that builds
        # don't interfere with each other
        if target not in self.FileMetadata:
            self.FileMetadata[target] = { }
        file_metadata = self.FileMetadata[target]

        # Return an existing metadata?
        crc = self.AddToFileMap(filename)
        if crc in file_metadata:
            return file_metadata[crc]

        # Otherwise create a new one
        data = FileMetadata()
        file_metadata[crc] = data
        return data

    def UpdateModTimes(self, target):

        # It's safe to update the mod times for any files which were different since the last build
        file_metadata = self.FileMetadata[target]
        for crc, metadata in file_metadata.items():
            metadata.UpdateModTime(self.GetFilename(crc))


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


#
# A file copying node that can be placed anywhere in the dependency chain, always
# returning True on Build
#
class CopyNode (Node):

    def __init__(self, output, source, dest):

        self.Dependencies = [ output ]
        self.Source = source
        self.Destination = dest

    def Build(self, env):

        if not os.path.exists(self.Source):
            print("Skipping copy of " + self.Source + " because it doesn't exist")
            return False

        print("Copying from " + self.Source + " to " + self.Destination)
        Utils.Makedirs(os.path.dirname(self.Destination))
        shutil.copyfile(self.Source, self.Destination)

        return True

    def GetInputFile(self, env):
        return self.Source

    def GetOutputFiles(self, env):
        return [ self.Destination ]



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
import gzip
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
        self.ImplicitDeps = [ ]
        self.ImplicitOutputs = [ ]
        self.CachedModTime = None

    # Custom state implementations for the pickle module to ignore transient data
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["CachedModTime"]
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.CachedModTime = None

    def HasFileChanged(self, filename):

        # As calls into the OS for file times are expensive cache the result as much as possible
        if self.CachedModTime == None:

            # Modtime get will only succeed if the file exists
            try:
                self.CachedModTime = os.path.getmtime(filename)
            except:
        # If the file no longer exists, it has changed
                # Note this path will force the cached mod time to NOT update and call getmtime
                # on each evaluation. This is safe and no slower than the original implementation
                # and only triggered if you delete output files.
            return True

        # Compare modification times
        return self.CachedModTime != self.ModTime

    def UpdateModTime(self, filename):

        if self.CachedModTime != None:
            self.ModTime = self.CachedModTime
        else:
            # Only updates if the file exists
            # Faster than first checking to see if the file exists
            try:
            self.ModTime = os.path.getmtime(filename)
            except:
                pass

    def SetImplicitDeps(self, env, deps):

        # Create file nodes for each dependency
        self.ImplicitDeps = [ ]
        for filename in set(deps):
            filenode = env.NewFile(filename)

            # Ensure each dependency has a metadata entry
            env.GetFileMetadata(filename)
            self.ImplicitDeps.append(filenode)
    
    def SetImplicitOutputs(self, env, outputs):

        # Create file nodes for each dependency
        self.ImplicitOutputs = [ ]
        for filename in set(outputs):
            filenode = env.NewFile(filename)

            # Ensure each dependency has a metadata entry
            env.GetFileMetadata(filename)
            self.ImplicitOutputs.append(filenode)

    def __repr__(self):

        return str(self.ModTime) + "->" + str(self.ImplicitDeps) + "->" + str(self.ImplicitOutputs)


#
# Metadata that persists between builds
#
class BuildMetadata:
    
    OutputFilename = "metadata.pib"
    
    def __init__(self):

        self.Version = 2
        self.FileMap = { }
        self.FileMetadata = { }
        self.UserData = None
    
    def Save(self):

        with gzip.open(BuildMetadata.OutputFilename, "wb") as f:
            pickle.dump(self, f)

    def Load():

        try:
            # Open and load the metadata file if it exists
            if os.path.exists(BuildMetadata.OutputFilename):
                with gzip.open(BuildMetadata.OutputFilename, "rb") as f:
                    data = pickle.load(f)

                    # Return if the version matches
                    if hasattr(data, "Version") and data.Version == 2:
                        return data

                    print("Metadata file version out of date, discarding...")

        # Handle malformed files
        except:
            print("Error loading Metadata file, discarding...")

        # Return empty constructed build metadata if it can't be loaded
        return BuildMetadata()

    def AddToFileMap(self, filename):

        # Ignore empty filenames
        if filename == None:
            return

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

        # Ignore empty filenames
        if filename == None:
            return None

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

        super().__init__()
        self.CRC = crc

    def GetInputFile(self, env):
        return env.GetFilename(self.CRC)

    def GetOutputFiles(self, env):
        return [ env.GetFilename(self.CRC) ]


#
# Used to depend on output files from build steps
# Bound to the environment that generates the output file
#
class OutputFileNode (Node):

    def __init__(self, env, node):

        super().__init__()
        self.Env = env
        self.GetInputFileFunc = node.GetInputFile
        self.GetOutputFilesFunc = node.GetOutputFiles

    def GetInputFile(self, env):

        return self.GetInputFileFunc(self.Env)

    def GetOutputFiles(self, env):

        return self.GetOutputFilesFunc(self.Env)


#
# A file copying node that can be placed anywhere in the dependency chain, always
# returning True on Build
#
class CopyNode (Node):

    def __init__(self, output, source, dest):

        super().__init__()
        self.Dependencies = [ output ]
        self.Source = source
        self.Destination = dest

    def Build(self, env):

        if not os.path.exists(self.Source):
            Utils.Print(env, "   ERROR: Source file doesn't exist")
            return False

        Utils.Print(env, "Copying from " + self.Source + " to " + self.Destination)
        if Utils.Makedirs(os.path.dirname(self.Destination)) == False:
            Utils.Print(env, "   ERROR: destination directories couldn't be created")
            return False
        if Utils.CopyFile(self.Source, self.Destination) == False:
            Utils.Print(env, "   ERROR: Copy operation failed")
            return False

        return True

    def GetInputFile(self, env):
        return self.Source

    def GetOutputFiles(self, env):
        return [ self.Destination ]


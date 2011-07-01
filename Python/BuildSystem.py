
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
import pickle
import shutil
import binascii
import Utils
import MSVCPlatform


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


#
# This may or may not work out in the future but it's a nice convenience that ties building configurations
# with generating project files for the configurations.
#
class Config:

    def __init__(self, name, arg, base_config_options):

        self.Name = name
        self.CmdLineArg = arg
        self.IntermediatePath = "obj/" + name
        self.OutputPath = "bin/" + name
        self.CPPOptions = MSVCPlatform.VCCompileOptions(base_config_options)
        self.LinkOptions = MSVCPlatform.VCLinkOptions(base_config_options)
        self.LibOptions =MSVCPlatform.VCLibOptions(base_config_options)
    
    


#
# The build environment - currently only Visual Studio 2005 is supported.
# Contains the main dependency graph evaluation and a host of other things which
# couldn't be put elsewhere.
#
class Environment:

    def New():

        # Can the default build environment be initialised?
        envvars = MSVCPlatform.GetVisualCEnv()
        if envvars == None:
            return None

        return Environment(envvars)

    def __init__(self, envvars):

        self.EnvironmentVariables = envvars
        
        # Set up some default configurations
        self.Configs = { }
        self.Configs["debug"] = Config("Debug", "debug", MSVCPlatform.VCBaseConfig.DEBUG)
        self.Configs["release"] = Config("Release", "release", MSVCPlatform.VCBaseConfig.RELEASE)
        self.ApplyCommandLineConfig()

        # Load existing file metadata from disk
        self.FileMap = { }
        self.FileMetadata = { }
        if os.path.exists("metadata.pib"):
            with open("metadata.pib", "rb") as f:
                self.FileMap = pickle.load(f)
                self.FileMetadata = pickle.load(f)
    
    def ApplyCommandLineConfig(self):

        # Debug by default, overridden by whatever keyword is found in the list of args
        self.CurrentConfig = self.Configs["debug"]
        for name, config in self.Configs.items():
            if name in sys.argv:
                self.CurrentConfig = config
                break


    def AddToFileMap(self, filename):

        # Generate the CRC
        filename = Utils.NormalisePath(filename)
        crc = binascii.crc32(bytes(filename, "utf-8"))

        # Check for collision
        if crc in self.FileMap and filename != self.FileMap[crc]:
            raise Exception("CRC collision with " + filename + " and " + self.FileMap[crc])

        self.FileMap[crc] = filename
        return crc

    def NewFile(self, filename):

        # Always add to the file map
        crc = self.AddToFileMap(filename)
        return FileNode(crc)

    def CPPFile(self, filename):

        return MSVCPlatform.VCCompileNode(filename)

    def Link(self, filename, obj_files, lib_files = []):

        return MSVCPlatform.VCLinkNode(filename, obj_files, lib_files)

    def Lib(self, filename, dependencies):

        return MSVCPlatform.VCLibNode(filename, dependencies)

    def CopyOutputFile(self, output, index, dest_path):

        source = output.GetOutputFiles(self)[index]
        dest = os.path.join(dest_path, os.path.basename(source))
        return CopyNode(output, source, dest)

    def GetFilename(self, crc):

        return self.FileMap[crc]

    def GetFileMetadata(self, filename):

        # Return an existing metadata?
        crc = self.AddToFileMap(filename)
        if crc in self.FileMetadata:
            return self.FileMetadata[crc]

        # Otherwise create a new one
        data = FileMetadata()
        self.FileMetadata[crc] = data
        return data

    def SaveFileMetadata(self):

        # It's safe to update the mod times for any files which were different since the last build
        for crc, metadata in self.FileMetadata.items():
            metadata.UpdateModTime(self.FileMap[crc])

        # Save to disk
        with open("metadata.pib", "wb") as f:
            pickle.dump(self.FileMap, f)
            pickle.dump(self.FileMetadata, f)

    def DeleteTempOutput(files):

        # If the output file exists then it has been built previously.
        # Delete the output before subsequent builds so that aborts can be detected next build.
        for file in files:
            Utils.RemoveFile(file)

    def MakeOutputDirs(files):

        for file in files:
            # If the output file doesn't exist then this may be the first build attempt.
            # In this case we have to ensure the directories for the output files exist before
            # creating them.
            dirname = os.path.dirname(file)
            if dirname != "":
                Utils.Makedirs(dirname)

    def ExecuteNodeBuild(self, node):

        # Have any of the explicit dependencies changed?
        requires_build = False
        success = True
        for dep in node.Dependencies:
            (a, b) = self.ExecuteNodeBuild(dep)
            requires_build |= a
            success &= b

        # Get some info about the input/output files
        input_filename = node.GetInputFile(self)
        output_filenames = node.GetOutputFiles(self)
        input_metadata = self.GetFileMetadata(input_filename)

        # Have any of the implicit dependencies changed?
        if not requires_build:
            for dep in input_metadata.ImplicitDeps:
                (a, b) = self.ExecuteNodeBuild(dep)
                requires_build |= a
                success &= b

        # If the dependencies haven't changed, check to see if the node itself has been changed
        if not requires_build and input_metadata.HasFileChanged(input_filename):
            requires_build = True

        # If any output files don't exist and no build is required, we must build!
        if not requires_build:
            for output_file in output_filenames:
                if input_filename != output_file and not os.path.exists(output_file):
                    requires_build = True
                    break

        # Execute any build steps
        if requires_build and success:
            if Utils.ObjectHasMethod(node, "Build"):

                # Prepare for build aborts
                Environment.DeleteTempOutput(node.GetTempOutputFiles(self))
                Environment.MakeOutputDirs(node.GetOutputFiles(self))

                # Build will change the mod time so set without checking for faster operation
                input_metadata.Changed = True

                if not node.Build(self):
                    success = False
                

        return (requires_build, success)
    
    def ExecuteNodeClean(self, node):

        for dep in node.Dependencies:
            self.ExecuteNodeClean(dep)

        output_files = node.GetOutputFiles(self)
        for file in output_files:
            Utils.RemoveFile(file)
    
    def Build(self, build_graph):
        
        # Clean outputs?
        if "clean" in sys.argv or "rebuild" in sys.argv:
            print("PiB Cleaning...")
            self.ExecuteNodeClean(build_graph)
        
        # Build the graph?
        if "rebuild" in sys.argv or not "clean" in sys.argv:
            print("PiB Building...")
            self.ExecuteNodeBuild(build_graph)
            self.SaveFileMetadata()
            

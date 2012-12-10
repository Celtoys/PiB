
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
# Environment.py: The core dependency graph build/evaluation code and anything
# else that doesn't fit elsewhere.
#

import os
import sys
import Utils
import BuildSystem
import JDKPlatform
import MSVCPlatform


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
        self.LibOptions = MSVCPlatform.VCLibOptions(base_config_options)

    def SetPaths(self, path):

        path = path.replace("%config", self.Name)
        self.IntermediatePath = path.replace("%type", "obj")
        self.OutputPath = path.replace("%type", "bin")
    
    def SetPaths2(self, intermediate, output):

        self.IntermediatePath = intermediate
        self.OutputPath = output

    def UpdateCommandLines(self):

        self.CPPOptions.UpdateCommandLine()
        self.LinkOptions.UpdateCommandLine()
        self.LibOptions.UpdateCommandLine()


#
# The build environment - currently only Visual Studio 2005 is supported.
# Contains the main dependency graph evaluation and a host of other things which
# couldn't be put elsewhere.
#
class Environment:

    def New():

        # Load the metadata first as that encodes as much of the cached environment state as possible
        metadata = BuildSystem.BuildMetadata.Load()

        # Check to see if the MSVC envvars are in the metadata before figuring them out,
        # as that's quite an expensive operation
        if metadata.UserData == None:
            envvars = MSVCPlatform.GetVisualCEnv()
            if envvars == None:
                return None
            metadata.UserData = envvars

        # Add the JDK
        # TODO: Need to decide whether all environments need to be present, PiB is fault-tolerant or
        # you only need what build environments you try to use at runtime
        # TODO: This envvar modification needs to be done dynamically when the JDK is requested
        #envvars["PATH"] += ";" + JDKPlatform.GetJDKBinPath()
        
        return Environment(metadata.UserData, metadata)

    def __init__(self, envvars, metadata):

        # Construc the environment variables
        self.EnvironmentVariables = envvars

        # Force node builds irrespective of dependencies?
        self.ForceBuild = "-force" in sys.argv
        self.NoToolOutput = "-no_tool_output" in sys.argv
        self.ShowCmdLine = "-show_cmdline" in sys.argv
        self.ConfigName = Utils.GetSysArgvProperty("-config", "debug")
        self.Verbose = "-verbose" in sys.argv

        # Parse any build filters in the command-line
        self.BuildTargets = Utils.GetSysArgvProperties("-target", None)
        self.BuildInputFilter = Utils.GetSysArgvProperty("-input_filter", None)
        if self.BuildInputFilter != None:
            self.BuildInputFilter = self.BuildInputFilter.lower()

        # Set up some default configurations
        self.Configs = { }
        self.Configs["debug"] = Config("Debug", "debug", MSVCPlatform.VCBaseConfig.DEBUG)
        self.Configs["release"] = Config("Release", "release", MSVCPlatform.VCBaseConfig.RELEASE)
        self.CurrentConfig = self.Configs[self.ConfigName]

        # Load existing file metadata from disk
        self.BuildMetadata = metadata
        self.CurrentBuildTarget = None

    def NewFile(self, filename):

        # Always add to the file map
        crc = self.BuildMetadata.AddToFileMap(filename)
        return BuildSystem.FileNode(crc)

    def OutputFile(self, env, node):

        return BuildSystem.OutputFileNode(env, node)

    def CPPFile(self, filename, override_cpp_opts = None):

        return MSVCPlatform.VCCompileNode(filename, override_cpp_opts)

    def Link(self, filename, obj_files, lib_files = []):

        return MSVCPlatform.VCLinkNode(filename, obj_files, lib_files)

    def Lib(self, filename, dependencies, lib_files = []):

        return MSVCPlatform.VCLibNode(filename, dependencies, lib_files)
    
    def JavaFile(self, filename):
        
        return JDKPlatform.JDKCompileNode(filename)

    def CopyFile(self, source, dest_path):

        dest = os.path.join(dest_path, os.path.basename(source))
        output = self.NewFile(source)
        return BuildSystem.CopyNode(output, source, dest)

    def CopyOutputFile(self, output, index, dest_path):

        source = output.GetOutputFiles(self)[index]
        dest = os.path.join(dest_path, os.path.basename(source))
        return BuildSystem.CopyNode(output, source, dest)

    def GetFilename(self, crc):

        return self.BuildMetadata.GetFilename(crc)

    def GetFileMetadata(self, filename):

        return self.BuildMetadata.GetFileMetadata(self.CurrentBuildTarget, filename)

    def SaveFileMetadata(self):

        self.BuildMetadata.Save()

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

    def ExecuteNodeBuild(self, node, tab):

        # Get some info about the input/output files
        input_filename = node.GetInputFile(self)
        output_filenames = node.GetOutputFiles(self)
        input_metadata = self.GetFileMetadata(input_filename)

        if self.Verbose:
            print(tab + "BUILD NODE: " + input_filename)

        # Don't build the same node more than once
        if node in self.BuildResults:
            return self.BuildResults[node]

        # Have any of the explicit dependencies changed?
        requires_build = self.ForceBuild
        success = True
        for dep in node.Dependencies:
            if self.Verbose:
                print(tab + "   Explicit dependency: " + str(dep))
            (a, b) = self.ExecuteNodeBuild(dep, tab + "   ")
            requires_build |= a
            success &= b
            if a and self.Verbose:
                print(tab + "      Changed: " + str(dep))

        # Have any of the implicit dependencies changed?
        if not requires_build:
            for dep in input_metadata.ImplicitDeps:
                (a, b) = self.ExecuteNodeBuild(dep, tab + "   ")
                requires_build |= a
                success &= b
                if a and self.Verbose:
                    print(tab + "Implicit dependency changed: " + str(dep))

        # If the dependencies haven't changed, check to see if the node itself has been changed
        if not requires_build and input_metadata.HasFileChanged(input_filename):
            requires_build = True
            if self.Verbose:
                print(tab + "Input has changed: " + input_filename + ", " + str(node))

        # If any output files don't exist and no build is required, we must build!
        if not requires_build:
            for output_file in output_filenames:
                if input_filename != output_file and not os.path.exists(output_file):
                    requires_build = True
                    if self.Verbose:
                        print(tab + "Output file doesn't exist: " + output_file)
                    break

        # At the last minute, cancel any builds if they're excluded by the input filter
        if requires_build and self.BuildInputFilter != None:
            input_filename = os.path.realpath(input_filename).lower()
            if self.BuildInputFilter not in input_filename:
                requires_build = False

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

        # Record the build result incase this node is visited again in this build step
        self.BuildResults[node] = (requires_build, success)
        return (requires_build, success)
    
    def ExecuteNodeClean(self, node):

        for dep in node.Dependencies:
            self.ExecuteNodeClean(dep)

        # Only clean if there is a build step for this node
        if Utils.ObjectHasMethod(node, "Build"):
            output_files = node.GetOutputFiles(self)
            for file in output_files:
                if self.Verbose:
                    print("Deleting: " + file)
                Utils.RemoveFile(file)
    
    def Build(self, build_graphs, target = None):

        # Apply the current build target
        self.CurrentBuildTarget = self.CurrentConfig.Name + ":"
        if target == None:
            self.CurrentBuildTarget += "PiBDefaultTarget"
        else:
            self.CurrentBuildTarget += target

        # Reset build results on each build
        self.BuildResults = { }

        # Promote to a list if necessary
        if type(build_graphs) != type([]):
            build_graphs = [ build_graphs ]

        # Exclude targets not mentioned on the command-line, if any
        if target != None and len(self.BuildTargets):
            if target not in self.BuildTargets:
                return

        # Determine a printable target name
        target_name = ""
        if target != None:
            target_name = " target '" + target + "'"

        # Clean outputs?
        if "clean" in sys.argv or "rebuild" in sys.argv:
            print("PiB Cleaning" + target_name + "...")
            [ self.ExecuteNodeClean(bg) for bg in build_graphs ]

        # Build the graph?
        if "rebuild" in sys.argv or not "clean" in sys.argv:
            print("PiB Building" + target_name + "...")
            [ self.ExecuteNodeBuild(bg, "") for bg in build_graphs ]

        self.BuildMetadata.UpdateModTimes(self.CurrentBuildTarget)
        self.CurrentBuildTarget = None


if __name__ == '__main__':
    Environment.New()
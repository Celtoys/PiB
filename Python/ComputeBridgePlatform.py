
#
# Uses ComputeBridge (https://github.com/Celtoys/ComputeBridge) to unify compute code for OpenCL/CUDA
#

import os
import Utils
import Process
import BuildSystem


# Require user to set the installation directory
_InstallPath = None
def SetInstallPath(path):
    global _InstallPath
    _InstallPath = path


class Options:

    #
    # TODO: Uses new dirty options checking mechanism.
    #
    def __init__(self):

        # List of include search paths and macros
        self.IncludePaths = [ ]
        self.DefineMacros = [ ]

        self.Dirty = True
        self.CommandLine = [ ]

    def __setattr__(self, name, value):

        # Assign the field and mark the command-line as dirty
        self.__dict__[name] = value
        self.__dict__["Dirty"] = True

    def UpdateCommandLine(self):

        if self.Dirty:

            cmdline = [ ]

            for path in self.IncludePaths:
                cmdline += [ '-i', os.path.normpath(path) ]

            self.FormatDefines(cmdline)

            # Update and mark as not dirty without calling into __setattr__
            self.__dict__["CommandLine"] = cmdline
            self.__dict__["Dirty"] = False

    def FormatDefines(self, cmdline):

        for define in self.DefineMacros:
            if isinstance(define, str):
                cmdline += [ '-d ' + define ]
            else:
                cmdline += [ '-d ' + str(define[0]) + "=" + str(define[1]) ]



class BuildNode (BuildSystem.Node):

    #
    # TODO: Uses new options location system of passing a map from config name to options
    # that are referenced in Build. Means nothing specific to this build node need to
    # be stored in the config object.
    #
    def __init__(self, source, target, options_map):

        super().__init__()
        self.Source = source
        self.Dependencies = [ source ]
        self.Target = target
        self.OptionsMap = options_map

    def Build(self, env):

        # Ensure command -line for current configuration is up-to-date
        options = self.OptionsMap[env.CurrentConfig.CmdLineArg]
        options.UpdateCommandLine()

        output_files = self.GetOutputFiles(env)

        # Build command-line from current configuration
        cmdline = [ os.path.join(_InstallPath, "cbpp.exe") ]
        cmdline += [ self.GetInputFile(env) ]
        cmdline += options.CommandLine
        cmdline += [ "-noheader" ]
        cmdline += [ "-output", output_files[0] ]
        cmdline += [ "-show_includes" ]
        if len(output_files) > 1:
            cmdline += [ "-output_bin", output_files[1] ]
        cmdline += [ "-target", self.Target ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch cbpp with a dependency scanner and wait for it to finish
        scanner = Utils.IncludeScanner(env, 'cpp: included "', None, lambda line, length: line[length:-1])
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.WaitForPipeOutput(process, scanner)

        # Record the implicit dependencies for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Includes)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Source.GetOutputFiles(env)[0]

    def GetOutputFiles(self, env):

        # Get the filename minus path and extension
        # TODO: This only works if this node has another node as input that resides in
        # the same directory as it. Need to evaluate relative path inputs in long chains.
        input_file = self.GetInputFile(env)
        input_file = os.path.split(input_file)[1]
        input_file = os.path.splitext(input_file)[0]

        # Put pre-processed location in intermidate directory
        pp_path = os.path.join(env.CurrentConfig.IntermediatePath, input_file + "." + self.Target + "_cb")
        paths = [ pp_path ]

        # CUDA binary path is the output directory with extension change
        if self.Target == "cuda":
            bin_path = os.path.join(env.CurrentConfig.OutputPath, input_file + ".ckt")
            paths += [ bin_path ]

        return paths

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

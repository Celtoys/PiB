
#
# Uses the OpenCL Precompiler available at https://github.com/Celtoys/oclpc
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


class OpenCLCompileOptions:

    def __init__(self):

        self.Verbose = False

        # Platform/device selection
        self.PlatformIndex = -1
        self.DeviceIndex = -1
        self.PlatformSubstr = None
        self.DeviceSubstr = None

        # Preprocessor options
        self.DefineMacros = [ ]
        self.IncludePaths = [ ]


    def UpdateCommandLine(self):

        cmdline = [ "-noheader" ]

        if self.Verbose: cmdline += [ "-verbose" ]

        if self.PlatformIndex != -1: cmdline += [ "-platform_index " + self.PlatformIndex ]
        if self.DeviceIndex != -1: cmdline += [ "-device_index " + self.DeviceIndex ]
        if self.PlatformSubstr != None: cmdline += [ "-platform_substr " + self.PlatformSubstr ]
        if self.DeviceSubstr != None: cmdline += [ "-device_substr " + self.DeviceSubstr ]

        cmdline += [ "-D " + macro for macro in self.DefineMacros ]
        cmdline += [ "-I " + path for path in self.IncludePaths ]

        self.CommandLine = cmdline


class BuildOpenCLNode (BuildSystem.Node):

    def __init__(self, path):

        super().__init__()
        self.Path = path

    def Build(self, env):

        # Build command-line from current configuration
        cmdline = [ os.path.join(_InstallPath, "oclpc.exe") ]
        cmdline += env.CurrentConfig.OpenCLCompileOptions.CommandLine
        cmdline += [ self.Path ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the compiler and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            print(output)

        # Write a dummy output file on build success
        if process.returncode == 0:
            output_files = self.GetOutputFiles(env)
            with open(output_files[0], "w") as out_file:
                print("Built successfully", file=out_file)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Path

    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(env.CurrentConfig.OutputPath, path)
        return [ path + "_built.txt" ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


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


class BuildNode (BuildSystem.Node):

    def __init__(self, source):

        super().__init__()
        self.Source = source
        self.Dependencies = [ source ]

    def Build(self, env):

        output_files = self.GetOutputFiles(env)

        # Build command-line from current configuration
        cmdline = [ os.path.join(_InstallPath, "cbpp.exe") ]
        cmdline += [ "-noheader" ]
        cmdline += [ self.GetInputFile(env) ]
        cmdline += [ "-output", output_files[0] ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the compiler and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            print(output)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Source.GetOutputFiles(env)[0]

    def GetOutputFiles(self, env):

        # Maintain extension, just point to build output path
        path = os.path.join(env.CurrentConfig.IntermediatePath, self.GetInputFile(env))
        return [ path ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

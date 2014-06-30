
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

    def __init__(self, source, target):

        super().__init__()
        self.Source = source
        self.Dependencies = [ source ]
        self.Target = target

    def Build(self, env):

        output_files = self.GetOutputFiles(env)

        # Build command-line from current configuration
        cmdline = [ os.path.join(_InstallPath, "cbpp.exe") ]
        cmdline += [ self.GetInputFile(env) ]
        cmdline += [ "-noheader" ]
        cmdline += [ "-output", output_files[0] ]
        if len(output_files) > 1:
            cmdline += [ "-output_bin", output_files[1] ]
        cmdline += [ "-target", self.Target ]
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

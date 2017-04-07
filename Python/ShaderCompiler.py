
import os
import Utils
import Process
from DirectXPlatform import FXCompileOptions
from DirectXPlatform import FXCompileNode


# Directory where the shader compiler is located
ShaderCompilerPath = None


def SetCompilerPath(path):
    global ShaderCompilerPath
    ShaderCompilerPath = path


class ShaderCompileOptions(FXCompileOptions):

    def __init__(self):

        super().__init__()

    def UpdateCommandLine(self):

        super().UpdateCommandLine()


class ShaderCompileNode(FXCompileNode):

    def __init__(self, path, profile, path_postfix="", defines=None, entry_point=None):

        if defines is None:
            defines = []
        super().__init__(path, profile, path_postfix, defines, entry_point)

    def Build(self, env):

        # Node entry point takes precedence over config specified entry-point
        entry_point = self.EntryPoint
        if entry_point == None:
            entry_point = env.CurrentConfig.ShaderCompileOptions.EntryPoint

        # Build command line
        cmdline = [ os.path.join(ShaderCompilerPath, "ShaderCompiler.exe") ]
        cmdline += [ '/T' + self.Profile ]
        cmdline += env.CurrentConfig.ShaderCompileOptions.CommandLine
        cmdline += self.DefineCmdLine
        cmdline += self.BuildCommandLine
        if entry_point:
            cmdline += [ '/E' + entry_point ]
        cmdline += [ "/ShowCppOutputs" ]
        cmdline += [ self.Path ]
        Utils.ShowCmdLine(env, cmdline)

        # Create the include scanner and launch the compiler
        scanner = Utils.LineScanner(env)
        scanner.AddLineParser("Includes", "cpp: included", None, lambda line, length: line.lstrip()[15:-1])
        scanner.AddLineParser("Outputs", "cpp: output", None, lambda line, length: line.lstrip()[12:])
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.WaitForPipeOutput(process, scanner)

        # Record the implicit dependencies/outputs for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Includes)
        data.SetImplicitOutputs(env, scanner.Outputs)

        return process.returncode == 0
    
    def GetOutputFiles(self, env):

        return super()._GetOutputFiles(env, env.CurrentConfig.ShaderCompileOptions)
    
    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

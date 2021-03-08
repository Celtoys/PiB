
import os
import sys
import Utils
import Process
from DirectXPlatform import FXCompileOptions
from DirectXPlatform import FXCompileNode


# Directory where the shader compiler is located
# TODO: Should this be in ShaderCompileOptions?
ShaderCompilerPath = None

# Whether to dump internal debugging information from the shader compiler
ShowTrace = "-shader_compiler_trace" in sys.argv


def SetCompilerPath(path):
    global ShaderCompilerPath
    ShaderCompilerPath = path


class ShaderCompileOptions(FXCompileOptions):

    def __init__(self):

        super().__init__()
        self.SourceRoot = None
        self.CppOutputPath = None

    def UpdateCommandLine(self):

        super().UpdateCommandLine()

        if self.SourceRoot:
            self.CommandLine += [ "/SourceRoot" + self.SourceRoot ]
        if self.CppOutputPath:
            self.CommandLine += [ "/CppOutputPath" + self.CppOutputPath ]


class ShaderCompileNode(FXCompileNode):

    def __init__(self, path, profile, path_postfix="", defines=[], entry_point=None):

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
        if ShowTrace:
            cmdline += [ "/trace" ]
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

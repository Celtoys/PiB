
import os
import Utils
import Process
import BuildSystem


# Directory where the clReflect executables are located
_InstallLocation = None


def _MakePath(filename):

    if _InstallLocation:
        return os.path.join(_InstallLocation, filename)
    return filename


class CppExportNode(BuildSystem.Node):
    
    def __init__(self, path, input, map_file):
        
        super().__init__()
        self.Path = path
        self.Input = input
        self.MapFile = map_file
        self.Dependencies = [ input, map_file ]

    def Build(self, env):
        
        input_file = self.GetInputFile(env)
        output_file = self.GetOutputFiles(env)[0]
        Utils.Print(env, "clexport: " + os.path.basename(output_file))

        # Construct the command-line
        cmdline = [ _MakePath("clexport.exe") ]
        cmdline += [ input_file ]
        cmdline += [ "-cpp", output_file ]
        cmdline += [ "-cpp_log", output_file + ".log" ]
        if self.MapFile != None:
            cmdline += [ "-map", self.MapFile.GetOutputFiles(env)[0] ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the exporter and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            Utils.Print(env, output)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Input.GetOutputFiles(env)[0]

    def GetOutputFiles(self, env):

        path = os.path.join(env.CurrentConfig.OutputPath, self.Path)
        return [ path ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


class MergeNode (BuildSystem.Node):
    
    def __init__(self, path, db_files, cpp_codegen):

        super().__init__()
        self.Path = path
        self.Dependencies = db_files
        self.CppCodeGen = cpp_codegen

    def Build(self, env):

        output_file = self.GetOutputFiles(env)[0]
        Utils.Print(env, "clmerge: " + os.path.basename(output_file))

        # Construct the command-line
        cmdline = [ _MakePath("clmerge.exe") ]
        cmdline += [ output_file ]
        if self.CppCodeGen != None:
            cmdline += [ "-cpp_codegen", self.CppCodeGen.GetInputFile(env) ]
        cmdline += [ file.GetOutputFiles(env)[0] for file in self.Dependencies ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the merger and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            Utils.Print(env, output)

        return process.returncode == 0

    def GetInputFile(self, env):

        path = os.path.join(env.CurrentConfig.IntermediatePath, self.Path)
        return path

    def GetOutputFiles(self, env):

        output_files = [ os.path.join(env.CurrentConfig.IntermediatePath, self.Path) ]
        if self.CppCodeGen != None:
            output_files += [ self.CppCodeGen.GetInputFile(env) ]
        return output_files

    def GetTempOutputFiles(self, env):

        # Exclude the output C++ file as we don't want that to be deleted
        temp_files = self.GetOutputFiles(env)[:1]
        return temp_files


class CppScanNode (BuildSystem.Node):

    def __init__(self, sys_include_paths, include_paths, defines, cpp_output):

        super().__init__()
        self.SysIncludePaths = sys_include_paths
        self.IncludePaths = include_paths
        self.CppOutput = cpp_output
        self.Defines = defines
        self.Dependencies = [ cpp_output ]

    def Build(self, env):

        input_file = self.GetInputFile(env)
        output_files = self.GetOutputFiles(env)
        Utils.Print(env, "clscan: " + Utils.GetOSFilename(os.path.basename(input_file)))

        # Construct the command-line
        cmdline = [ _MakePath("clscan.exe") ]
        cmdline += [ input_file ]
        cmdline += [ "--output", output_files[0] ]
        cmdline += [ "--ast_log", output_files[1] ]
        cmdline += [ "--spec_log", output_files[2] ]
        cmdline += [ "--" ]
        cmdline += [ "-fdiagnostics-format=msvc" ]
        cmdline += [ "-D__clcpp_parse__" ]
        cmdline += [ "-m32" ]
        cmdline += [ "-fms-extensions" ]
        cmdline += [ "-fms-compatibility" ]
        cmdline += [ "-mms-bitfields" ]
        cmdline += [ "-fdelayed-template-parsing" ]
        cmdline += [ "-std=c++17" ]
        cmdline += [ "-fno-rtti" ]
        cmdline += [ "-Wno-microsoft-enum-forward-reference" ]
        for path in self.SysIncludePaths:
            cmdline += [ "-isystem", path ]
        for path in self.IncludePaths:
            cmdline += [ "-I", path ]
        for define in self.Defines:
            cmdline += [ "-D", define ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the scanner and wait for it to finish
        output = Utils.LineScanner(env)
        output.AddLineParser("Includes", "Included:", None, lambda line, length: line[length:].lstrip())
        process = Process.OpenPiped(cmdline)
        Process.WaitForPipeOutput(process, output)

        return process.returncode == 0
    
    def GetInputFile(self, env):

        return self.CppOutput.GetInputFile(env)
    
    def GetOutputFiles(self, env):

        path = os.path.splitext(self.GetInputFile(env))[0]
        path = os.path.join(env.CurrentConfig.IntermediatePath, path)
        return [ path + ".csv", path + "_astlog.txt", path + "_speclog.txt" ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


def CppScan(sys_include_paths, include_paths, defines, cpp_output):
    return CppScanNode(sys_include_paths, include_paths, defines, cpp_output)

def Merge(path, db_files, cpp_codegen):
    return MergeNode(path, db_files, cpp_codegen)

def CppExport(path, input, map_file):
    return CppExportNode(path, input, map_file)

def SetInstallLocation(location):
    global _InstallLocation
    _InstallLocation = location
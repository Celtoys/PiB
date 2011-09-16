
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
        self.Dependencies = [ input ]

    def Build(self, env):
        
        input_file = self.GetInputFile(env)
        output_file = self.GetOutputFiles(env)[0]
        print("clexport: " + os.path.basename(output_file))

        # Construct the command-line
        cmdline = [ _MakePath("clexport.exe") ]
        cmdline += [ input_file ]
        cmdline += [ "-cpp", output_file ]
        cmdline += [ "-cpp_log", output_file + ".log" ]
        if self.MapFile != None:
            cmdline += [ "-map", self.MapFile ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the exporter and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            print(output)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Input.GetOutputFiles(env)[0]

    def GetOutputFiles(self, env):

        path = os.path.join(env.CurrentConfig.OutputPath, self.Path)
        return [ path ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


class MergeNode (BuildSystem.Node):
    
    def __init__(self, path, db_files):

        super().__init__()
        self.Path = path
        self.Dependencies = db_files

    def Build(self, env):

        output_file = self.GetOutputFiles(env)[0]
        print("clmerge: " + os.path.basename(output_file))

        # Construct the command-line
        cmdline = [ _MakePath("clmerge.exe") ]
        cmdline += [ output_file ]
        cmdline += [ file.GetOutputFiles(env)[0] for file in self.Dependencies ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the merger and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            print(output)

        return process.returncode == 0

    def GetInputFile(self, env):

        path = os.path.join(env.CurrentConfig.IntermediatePath, self.Path)
        return path

    def GetOutputFiles(self, env):

        path = os.path.join(env.CurrentConfig.IntermediatePath, self.Path)
        return [ path ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


class CppScanNode (BuildSystem.Node):

    def __init__(self, include_paths, cpp_output):

        super().__init__()
        self.IncludePaths = include_paths
        self.CppOutput = cpp_output
        self.Dependencies = [ cpp_output ]

    def Build(self, env):

        input_file = self.GetInputFile(env)
        output_files = self.GetOutputFiles(env)
        print("clscan: " + os.path.basename(input_file))

        # Construct the command-line
        cmdline = [ _MakePath("clscan.exe") ]
        cmdline += [ input_file, "-output_headers" ]
        cmdline += [ "-output", output_files[0] ]
        cmdline += [ "-ast_log", output_files[1] ]
        cmdline += [ "-spec_log", output_files[2] ]
        for path in self.IncludePaths:
            cmdline += [ "-i", path ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the scanner and wait for it to finish
        output = Utils.IncludeScanner(env, "Included:")
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


def CppScan(include_paths, cpp_output):
    return CppScanNode(include_paths, cpp_output)

def Merge(path, db_files):
    return MergeNode(path, db_files)

def CppExport(path, input, map_file):
    return CppExportNode(path, input, map_file)

def SetInstallLocation(location):
    global _InstallLocation
    _InstallLocation = location
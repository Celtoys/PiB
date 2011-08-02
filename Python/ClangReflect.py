
import os
import Utils
import Process
import BuildSystem


class CppExportNode(BuildSystem.Node):
    
    def __init__(self, path, input):
        
        self.Path = path
        self.Input = input
        self.Dependencies = [ input ]

    def Build(self, env):
        
        input_file = self.GetInputFile(env)
        output_file = self.GetOutputFiles(env)[0]
        print("crexport: " + os.path.basename(output_file))

        # Construct the command-line
        # TODO: Relocate
        cmdline = [ "bin/Debug/crexport.exe" ]
        cmdline += [ input_file ]
        cmdline += [ "-cpp", output_file ]
        #print(cmdline)

        # Launch the exporter and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
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

        self.Path = path
        self.Dependencies = db_files

    def Build(self, env):

        output_file = self.GetOutputFiles(env)[0]
        print("crmerge: " + os.path.basename(output_file))

        # Construct the command-line
        # TODO: Relocate
        cmdline = [ "bin/Debug/crmerge.exe" ]
        cmdline += [ output_file ]
        cmdline += [ file.GetOutputFiles(env)[0] for file in self.Dependencies ]
        #print(cmdline)

        # Launch the merger and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
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

        self.IncludePaths = include_paths
        self.CppOutput = cpp_output
        self.Dependencies = [ cpp_output ]

    def Build(self, env):

        input_file = self.GetInputFile(env)
        output_files = self.GetOutputFiles(env)
        print("crscan: " + os.path.basename(input_file))

        # Construct the command-line
        # TODO: Relocate
        cmdline = [ "bin/Debug/crscan.exe" ]
        cmdline += [ input_file, "-output_headers" ]
        cmdline += [ "-output", output_files[0] ]
        cmdline += [ "-ast_log", output_files[1] ]
        cmdline += [ "-spec_log", output_files[2] ]
        for path in self.IncludePaths:
            cmdline += [ "-i", path ]
        #print(cmdline)

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

def CppExport(path, input):
    return CppExportNode(path, input)
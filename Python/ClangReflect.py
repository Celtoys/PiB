
import os
import Utils
import Process
import BuildSystem


class CppScanNode (BuildSystem.Node):

    def __init__(self, cpp_output):

        self.CppOutput = cpp_output
        self.Dependencies = [ cpp_output ]

    def Build(self, env):

        input_file = self.GetInputFile(env)
        output_file = self.GetOutputFiles(env)[0]

        print("crscan: " + os.path.basename(input_file))

        # Construct the command-line
        # TODO: Relocate
        cmdline = [ "bin/Debug/crscan.exe" ]
        cmdline += [ input_file, "-output_headers" ]
        cmdline += [ "-output", output_file ]
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
        return [ path + ".csv" ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

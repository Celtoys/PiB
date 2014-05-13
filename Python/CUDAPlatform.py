
import os
import Utils
import Process
import BuildSystem


# Retrieve the installation directories from the environment
InstallDir = None
if "CUDA_PATH" in os.environ:
    InstallDir = os.environ["CUDA_PATH"]
SampleDir = None
if "NVCUDASAMPLES_ROOT" in os.environ:
    SampleDir = os.environ["NVCUDASAMPLES_ROOT"]


# Setup paths relative to the installation path
IncludeDir = os.path.join(InstallDir, "include") if InstallDir else None
x86LibDir = os.path.join(InstallDir, "lib/Win32") if InstallDir else None
x64LibDir = os.path.join(InstallDir, "lib/x64") if InstallDir else None
BinDir = os.path.join(InstallDir, "bin") if InstallDir else None


# Setup paths relative to the samples path
SampleCommonIncludeDir = os.path.join(SampleDir, "common/inc") if SampleDir else None


#
# Names of nVidia GPU Virtual Architectures for generating up to the PTX stage
#
VirtualArch = Utils.enum(
    compute_10 = 'compute_10',
    compute_11 = 'compute_11',
    compute_12 = 'compute_12',
    compute_13 = 'compute_13',
    compute_20 = 'compute_20',
    compute_30 = 'compute_30',
    compute_32 = 'compute_32',
    compute_35 = 'compute_35',
    compute_50 = 'compute_50',
)

#
# Names of nVidia GPU Real Archtectures for generating final binary images
#
RealArch = Utils.enum(
    sm_10 = 'sm_10',
    sm_11 = 'sm_11',
    sm_12 = 'sm_12',
    sm_13 = 'sm_13',
    sm_20 = 'sm_20',
    sm_21 = 'sm_21',
    sm_30 = 'sm_30',
    sm_32 = 'sm_32',
    sm_35 = 'sm_35',
    sm_50 = 'sm_50',
)


class CUDACompileOptions:

    def __init__(self):

        # Set to 'c', 'c++' or 'cu' to explicitly set input language, rather than using extension
        self.Language = None

        # List of normal/system include search paths
        self.IncludePaths = [ ]
        self.SystemIncludePaths = [ ]

        # List of files to include first during preprocessing 
        self.IncludeFiles = [ ]

        # List of macros to define/undefine for preprocessor
        self.DefineMacros = [ ]
        self.UndefineMacros = [ ]

        # List of library search paths
        self.LibraryPaths = [ ]

        # List of libraries to link with (specified without the library extension)
        self.Libraries = [ ]

        # Specific the path in which the compiler host EXE resides (e.g. MSVC, GCC)
        self.HostCompilerPath = None

        # Set to 'none', 'shared' or 'static' to specify runtime library type - default is 'static'
        self.CUDARuntime = None

        # Generate debug information for host/device code
        self.HostDebug = False
        self.DeviceDebug = False

        # GPU architecture and GPUs to generate code for
        self.GPUArch = VirtualArch.compute_10;
        self.GPUCode = RealArch.sm_10;

        # Math operation behaviour
        self.FlushSingleDenormalsToZero = False
        self.PreciseSingleDivRecip = True
        self.PreciseSingleSqrt = True
        self.FuseMultipleAdds = True
        self.UseFastMath = False

        # Tool options
        self.DisableWarnings = False
        self.SourceInPTX = False
        self.RestrictPointers = False

    def UpdateCommandLine(self):

        cmdline = [ ]

        if self.Language: cmdline += [ '--x=' + self.Language ]

        cmdline += [ '--include-path=' + path for path in self.IncludePaths ]
        cmdline += [ '--system-include=' + path for path in self.SystemIncludePaths ]
        cmdline += [ '--pre-include=' + file for file in self.IncludeFiles ]
        cmdline += [ '--define-macro=' + macro for macro in self.DefineMacros ]
        cmdline += [ '--undefine-macro=' + macro for macro in self.UndefineMacros ]

        cmdline += [ '--library-path=' + lib for lib in self.LibraryPaths ]
        cmdline += [ '--library' + lib for lib in self.Libraries ]

        if self.HostCompilerPath: cmdline += [ '--compiler-bindir=' + self.HostCompilerPath ]
        if self.CUDARuntime: cmdline += [ '--cudart=' + self.CUDARuntime ]

        if self.HostDebug: cmdline += [ '--debug' ]
        if self.DeviceDebug: cmdline += [ '--device-debug' ]

        cmdline += [ '--gpu-architecture=' + self.GPUArch ]
        cmdline += [ '--gpu-code=' + self.GPUCode ]

        cmdline += [ '--ftz=' + ('true' if self.FlushSingleDenormalsToZero else 'false') ]
        cmdline += [ '--prec-div=' + ('true' if self.PreciseSingleDivRecip else 'false') ]
        cmdline += [ '--prec-sqrt=' + ('true' if self.PreciseSingleSqrt else 'false') ]
        cmdline += [ '--fmad=' + ('true' if self.FuseMultipleAdds else 'false') ]
        if self.UseFastMath: cmdline += [ '--use_fast_math' ]

        if self.DisableWarnings: cmdline += [ '--disable-warnings' ]
        if self.SourceInPTX: cmdline += [ '--source-in-ptx' ]
        if self.RestrictPointers: cmdline += [ '--restrict' ]

        self.CommandLine = cmdline


class BuildPTXNode (BuildSystem.Node):

    def __init__(self, path):

        super().__init__()
        self.Path = path

    def Build(self, env):

        # Build command-line from current configuration
        cmdline = [ os.path.join(BinDir, "nvcc.exe") ]
        cmdline += [ '--ptx' ]
        cmdline += env.CurrentConfig.CUDACompileOptions.CommandLine

        # Add the output .ptx file
        output_files = self.GetOutputFiles(env)
        cmdline += [ '--output-file=' + output_files[0] ]

        # Add input file before finishing
        cmdline += [ self.Path ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch the compiler and wait for it to finish
        process = Process.OpenPiped(cmdline)
        output = Process.WaitForPipeOutput(process)
        if not env.NoToolOutput:
            print(output)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Path

    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(env.CurrentConfig.OutputPath, path)
        return [ path + ".ptx" ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

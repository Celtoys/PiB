
import os
import Utils
import Process
import BuildSystem
import WindowsPlatform


# Retrieve the installation directory from the environment
InstallDir = None
if "DXSDK_DIR" in os.environ:
    InstallDir = os.environ["DXSDK_DIR"]

# Setup some common paths relative to that
if InstallDir != None:
    IncludeDirs = os.path.join(InstallDir, "Include")
    x86LibDir = os.path.join(InstallDir, "Lib/x86")
    x64LibDir = os.path.join(InstallDir, "Lib/x64")
    x86BinDir = os.path.join(InstallDir, "Utilities/bin/x86")
    x64BinDir = os.path.join(InstallDir, "Utilities/bin/x64")

# When no install directory has been found, either the SDK is not installed
# or it's bundled as part of the later Windows 8+ SDK. Copy values from that
# to cover those cases.
else:
    IncludeDirs = WindowsPlatform.IncludeDirs
    x86LibDir = WindowsPlatform.x86LibDir
    x64LibDir = WindowsPlatform.x64LibDir
    x86BinDir = WindowsPlatform.x86BinDir
    x64BinDir = WindowsPlatform.x64BinDir

#
# Usage: fxc <options> <files>
# 
#    /?, /help          print this message
# 
#    /T<profile>        target profile
#    /E<name>           entrypoint name
#    /I<include>        additional include path
#    /Vi                display details about the include process
# 
#    /Od                disable optimizations
#    /Op                disable preshaders
#    /O{0,1,2,3}        optimization level 0..3.  1 is default
#    /WX                treat warnings as errors
#    /Vd                disable validation
#    /Zi                enable debugging information
#    /Zpr               pack matrices in row-major order
#    /Zpc               pack matrices in column-major order
# 
#    /Gpp               force partial precision
#    /Gfa               avoid flow control constructs
#    /Gfp               prefer flow control constructs
#    /Gdp               disable effect performance mode
#    /Ges               enable strict mode
#    /Gec               enable backwards compatibility mode
#    /Gis               force IEEE strictness
#    /Gch               compile as a child effect for FX 4.x targets
# 
#    /Fo<file>          output object file
#    /Fc<file>          output assembly code listing file
#    /Fx<file>          output assembly code and hex listing file
#    /Fh<file>          output header file containing object code
#    /Fe<file>          output warnings and errors to a specific file
#    /Vn<name>          use <name> as variable name in header file
#    /Cc                output color coded assembly listings
#    /Ni                output instruction numbers in assembly listings
# 
#    /P<file>           preprocess to file (must be used alone)
# 
#    @<file>            options response file
#    /dumpbin           load a binary file rather than compiling
#    /Qstrip_reflect    strip reflection data from 4_0+ shader bytecode
#    /Qstrip_debug      strip debug information from 4_0+ shader bytecode
# 
#    /compress          compress DX10 shader bytecode from files
#    /decompress        decompress bytecode from first file, output files should
#                       be listed in the order they were in during compression
# 
#    /D<id>=<text>      define macro
#    /LD                Load d3dx9_31.dll
#    /nologo            suppress copyright message
# 
#    <profile>: cs_4_0 cs_4_1 cs_5_0 ds_5_0 fx_2_0 fx_4_0 fx_4_1 fx_5_0 gs_4_0
#       gs_4_1 gs_5_0 hs_5_0 ps_2_0 ps_2_a ps_2_b ps_2_sw ps_3_0 ps_3_sw ps_4_0
#       ps_4_0_level_9_1 ps_4_0_level_9_3 ps_4_0_level_9_0 ps_4_1 ps_5_0 tx_1_0
#       vs_1_1 vs_2_0 vs_2_a vs_2_sw vs_3_0 vs_3_sw vs_4_0 vs_4_0_level_9_1
#       vs_4_0_level_9_3 vs_4_0_level_9_0 vs_4_1 vs_5_0
#
class FXCompileOptions:
    
    def __init__(self):

        self.EntryPoint = None
        self.IncludePaths = [ ]

        self.DisableOptimisations = False
        self.OptimisationLevel = 1
        self.WarningsAsErrors = False
        self.DisableValidation = False
        self.EnableDebugInfo = False
        self.RowMajorMatrices = True

        self.PartialPrecision = False
        self.AvoidFlowControl = False
        self.PreferFlowControl = False
        self.Strict = False
        self.BackCompat = False
        self.IEEEStrict = False

        self.OutputObject = False
        self.OutputAsm = False
        self.OutputAsmHex = False
        self.OutputHeader = False
        self.OutputWarningsErrors = False
        self.HeaderVariableName = None
        self.InstructionNumbers = False

        self.Defines = [ ]
        self.NoLogo = True

    def UpdateCommandLine(self):

        # Start with showing includes for dependency evaluation
        cmdline = [
            '/Vi'
        ]
    
        cmdline += [ '/I' + path for path in self.IncludePaths ]

        if self.DisableOptimisations:
            cmdline += [ '/Od' ]

        cmdline += [ '/O' + str(self.OptimisationLevel) ]

        if self.WarningsAsErrors: cmdline += [ '/WX' ]
        if self.DisableValidation: cmdline += [ '/Vd' ]
        if self.EnableDebugInfo: cmdline += [ '/Zi' ]

        if self.RowMajorMatrices:
            cmdline += [ '/Zpr' ]
        else:
            cmdline += [ '/Zpc' ]

        if self.PartialPrecision: cmdline += [ '/Gpp' ]
        if self.AvoidFlowControl: cmdline += [ '/Gfa' ]
        if self.PreferFlowControl: cmdline += [ '/Gfp' ]
        if self.Strict: cmdline += [ '/Ges' ]
        if self.BackCompat: cmdline += [ '/Gec' ]
        if self.IEEEStrict: cmdline += [ '/Gis' ]
        if self.HeaderVariableName: cmdline += [ '/Vn' + self.HeaderVariableName ]
        if self.InstructionNumbers: cmdline += [ '/Ni' ]

        cmdline += FXCompileOptions.FormatDefines(self.Defines)

        if self.NoLogo:
            cmdline += [ '/nologo' ]

        self.CommandLine = cmdline

    def FormatDefines(defines):

        cmdline = [ ]
        for define in defines:
            cmdline += [ '/D' + str(define[0]) + '=' + str(define[1])]
        return cmdline


class FXCompileNode (BuildSystem.Node):

    def __init__(self, path, profile, path_postfix = "", defines = [ ], entry_point = None):

        super().__init__()
        self.Path = path
        self.Profile = profile
        self.PathPostfix = path_postfix
        self.DefineCmdLine = FXCompileOptions.FormatDefines(defines)
        self.EntryPoint = entry_point

    def Build(self, env):

        output_files = self.GetOutputFiles(env)

        # Node entry point takes precendence over config specified entry-point
        entry_point = self.EntryPoint
        if entry_point == None:
            entry_point = env.CurrentConfig.FXCompileOptions.EntryPoint

        # Build command line
        cmdline = [ os.path.join(x86BinDir, "fxc.exe") ]
        cmdline += [ self.Path, '/T' + self.Profile ]
        cmdline += env.CurrentConfig.FXCompileOptions.CommandLine
        cmdline += self.DefineCmdLine
        cmdline += self.BuildCommandLine
        if entry_point:
            cmdline += [ '/E' + entry_point ]
        Utils.ShowCmdLine(env, cmdline)

        # Create the include scanner and launch the compiler
        scanner = Utils.IncludeScanner(env, "Resolved to [", [ "Opening file [", "Current working dir [" ], lambda line, length: line[length:-1].lstrip())
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.WaitForPipeOutput(process, scanner)

        # Record the implicit dependencies for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Includes)

        return process.returncode == 0
    
    def GetInputFile(self, env):

        return self.Path

    def AddOutputFile(self, option, file):

        self.BuildCommandLine += [ option + file ]
        return [ file ]
    
    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(env.CurrentConfig.OutputPath, path)
        path += self.PathPostfix
        
        # Start a local command-line for use by Build
        self.BuildCommandLine = [ ]

        # Add whatever output files have been specified
        files = [ ]
        opts = env.CurrentConfig.FXCompileOptions
        if opts.OutputObject:
            files += self.AddOutputFile('/Fo', path + ".sobj")
        if opts.OutputAsmHex:
            files += self.AddOutputFile('/Fx', path + ".asm")
        elif opts.OutputAsm:
            files += self.AddOutputFile('/Fc', path + ".asm")
        if opts.OutputHeader:
            files += self.AddOutputFile('/Fh', path + ".h")
        if opts.OutputWarningsErrors:
            files += self.AddOutputFile('/Fe', path + ".elog")

        return files

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)


#options = ShaderCompileOptions()
#options.UpdateCommandLine()
#print(options.CommandLine)
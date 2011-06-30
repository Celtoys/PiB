
#
# MSVCPlatform.py: Command-line parameter abstraction and build nodes for
# Microsoft Visual C++ 2005.
#
# --- MIT Open Source License --------------------------------------------------
# PiB - Python Build System
# Copyright (C) 2011 by Don Williamson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
#
# C/C++ Building Reference (2005):
# http://msdn.microsoft.com/en-us/library/91621w01(v=VS.80).aspx
#
# Compiler Warnings that are Off by Default
# http://msdn.microsoft.com/en-us/library/23k5d385(v=VS.80).aspx
#
# Potentially useful warnings:
#
#   C4191   'operator/operation' : unsafe conversion from 'type of expression' to 'type required'
#   C4242   'identifier' : conversion from 'type1' to 'type2', possible loss of data
#   C4263   'function' : member function does not override any base class virtual member function
#   C4264   'virtual_function' : no override available for virtual member function from base 'class'; function is hidden
#   C4266   'function' : no override available for virtual member function from base 'type'; function is hidden
#   C4287   'operator' : unsigned/negative constant mismatch
#   C4289   nonstandard extension used : 'var' : loop control variable declared in the for-loop is used outside the for-loop scope
#   C4296   'operator' : expression is always false
#   C4302   'conversion' : truncation from 'type 1' to 'type 2'
#   C4365   'action' : conversion from 'type_1' to 'type_2', signed/unsigned mismatch
#

import os
import Utils
import Process
import BuildSystem


#
# There is no direct way in Python to apply the environment of one subprocess to another. The typical solution is
# to generate a batch file at runtime that does the following:
#
#    call ApplyEnvironment.bat
#    RunProcess.exe
#
# Rather than doing this for each call to cl.exe, I'm calling the batch file once at the start and copying the
# resulting environment for use later when calling cl.exe.
#
def GetVisualCEnv():

    # Locate the Visual Studio tools path
    vs_tools_dir = os.getenv("VS80COMNTOOLS")
    if vs_tools_dir == None:
        print("ERROR: Couldn't locate Visual Studio Tools environment variable")
        return None

    # Locate the Visual Studio install path    
    vs_dir = vs_tools_dir
    while vs_dir != "":
        split_path = os.path.split(vs_dir)

        # Detect infinite loop
        if vs_dir == split_path[0]:
            print("ERROR: Visual Studio Tools path is not formatted as expected")
            return None

        vs_dir = split_path[0]
        if split_path[1] == "Common7":
            break

    # Locate the batch file that sets up the Visual C build environment
    vcvars_bat = os.path.join(vs_dir, "VC/vcvarsall.bat")
    if not os.path.exists(vcvars_bat):
        print("ERROR: Visual C environment setup batch file not found")
        return None

    # Run the batch file, output the environment and prepare it for parsing
    process = Process.OpenPiped(vcvars_bat + " & echo ===ENVBEGIN=== & set")
    output = Process.WaitForPipeOutput(process)
    output = output.split("===ENVBEGIN=== \r\n")[1]
    output = output.splitlines()

    # Start with the current environment, override with any parsed environment values
    env = os.environ.copy()
    for line in output:
        var, value = line.split("=")
        env[var.upper()] = value
    
    # This environment variable is defined in the VS2005 IDE and prevents cl.exe output
    # being correctly captured, so remove it!
    if "VS_UNICODE_OUTPUT" in env:
        del env["VS_UNICODE_OUTPUT"]
    
    return env


#
# Visual C++ Compiler (cl.exe)
#
# Options:
#
#    /c                             Compiles without linking
#    /nologo                        Suppresses the logo
#    /showIncludes                  Display a list of all include files during compilation
#    /W{0|1|2|3|4}                  Warning level
#    /WX                            Treat warnings as errors
#    /errorReport:{none|prompt|queue|send}  How to report ICEs to Microsoft
#
#    /O1                            Minimise size (/Og /Os /Oy /Ob2 /Gs /GF /Gy)
#    /O2                            Maximise speed (/Og /Oi /Ot /Oy /Ob2 /Gs /GF /Gy)
#    /Ob{0|1|2}                     Disable inline expansion, expand marked funtions, compiler expands what it wants
#    /Od                            Disable optimisations
#    /Og                            Provides local and global optimisations (DEPRECATED)
#    /Oi                            Generate intrinsic functions
#    /Os                            Favour smaller code
#    /Ot                            Favour faster code
#    /Ox                            Full optimisation - favours speed over size (/Og /Oi /Ot /Ob2 /Oy)
#    /Oy                            Omits frame pointers (X86 ONLY)
#
#    /arch:{SSE|SSE2}               Specifies architecture for code generation (X86 ONLY)
#    /EH{s|a}[c][-]                 Specifies exception handling behaviour
#    /fp:{precise|except[-]|fast|strict}    Specifies floating-point behaviour
#    /Gd                            __cdecl calling convention, except marked (X86 ONLY)
#    /Gr                            __fastcall calling convention, except marked (X86 ONLY)
#    /Gz                            __stdcall calling convention, except marked (X86 ONLY)
#    /GF                            Enable read-only string pooling
#    /GL[-]                         Enable whole program optimisation
#    /Gs                            Controls stack probes
#    /Gy                            Enable function level linking
#    /MD                            References multi-threaded MSVCRT.lib, code is in a DLL. Defines _MT, _DLL.
#    /MDd                           References multi-threaded MSVCRTD.lib, code is in a DLL. Defines _DEBUG, _MT, _DLL.
#    /MT                            References multi-threaded LIBCMT.lib, code is linked statically. Defines _MT.
#    /MTd                           References multi-threaded LIBCMTD.lib, code is linked statically. Defines _DEBUG, _MT.
#
#    /Fopathname                    Specifies the output .obj file
#    /Fppathname                    Provides a path name for a precompiled header instead of using the default payh name
#    /Fdpathname                    Specifies a name for the PDB file
#
#    /GS[-]                         Detects buffer overruns that overwrite the return address (on by default)
#    /RTC{c|s|u}                    Controls runtime error checking
#    /Zi                            Produce debugging info in PDB files
#    /ZI                            Produce debugging info in PDB files with edit and continue (X86 ONLY)
#
#    /D[= | #[{string|number}] ]    Defines a preprocessing symbol for your source file
#    /I[ ]directory                 Adds a directory to the list of directories searched for include files
#
#    /Y-                            Ignores all other PCH compiler options in the current build
#    /Yc[filename]                  Create a PCH
#    /Yu[filename]                  Use a PCH
#
# Typical cl.exe command-lines:
#
#    Debug Windows
#    /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_UNICODE" /D "UNICODE" /Gm /EHsc /RTC1 /MDd /Fo"Debug\\" /Fd"Debug\vc80.pdb" /W3 /nologo /c /Wp64 /ZI /TP /errorReport:prompt
#
#    Release Windows
#    /O2 /GL /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_UNICODE" /D "UNICODE" /FD /EHsc /MD /Fo"Release\\" /Fd"Release\vc80.pdb" /W3 /nologo /c /Wp64 /Zi /TP /errorReport:prompt
#
# Note that DLL builds add "_WINDLL". This may only be needed so that you can decide whether to use declspec dllimport or dllexport.

VCBaseConfig = Utils.enum(
    'DEBUG',
    'RELEASE'
)

VCArchitecture = Utils.enum(
    DEFAULT = None,
    SSE = '/arch:sse',
    SSE2 = '/arch:sse2'
)

VCFloatingPoint = Utils.enum(
    PRECISE = '/fp:precise',
    FAST = '/fp:fast',
    STRICT = '/fp:strict'
)

VCCallingConvention = Utils.enum(
    CDECL = '/Gd',
    FASTCALL = '/Gr',
    STDCALL = '/Gz'
)

VCOptimisations = Utils.enum(
    DISABLE = '/Od',
    SIZE = '/O1',
    SPEED = '/O2'
)

VCDebuggingInfo = Utils.enum(
    DISABLE = None,
    PDB = '/Zi',
    PDBEDITANDCONTINUE = '/ZI'
)


class VCCompileOptions:

    def __init__(self, config):

        # Initialise the requested config settings
        if config == VCBaseConfig.DEBUG:
            self.InitDebug()
        elif config == VCBaseConfig.RELEASE:
            self.InitRelease()

    def InitDebug(self):

        # Default settings for all compiler options
        self.NoLogo = True
        self.WarningLevel = 3
        self.WarningsAsErrors = False
        self.Architecture = VCArchitecture.DEFAULT
        self.FloatingPoint = VCFloatingPoint.PRECISE
        self.FloatingPointExceptions = False
        self.CallingConvention = VCCallingConvention.CDECL
        self.DebuggingInfo = VCDebuggingInfo.PDBEDITANDCONTINUE
        self.RuntimeChecks = True
        self.Optimisations = VCOptimisations.DISABLE
        self.WholeProgramOptimisation = False
        self.Defines = [ 'WIN32', '_WINDOWS' ]
        self.IncludePaths = [ ]
        self.UpdateCommandLine()

    def InitRelease(self):

        # Initialise changes from debug
        self.InitDebug()
        self.DebuggingInfo = VCDebuggingInfo.PDB
        self.RuntimeChecks = False
        self.Optimisations = VCOptimisations.SPEED
        self.WholeProgramOptimisation = True
        self.Defines.extend( [ 'NDEBUG' ])
        self.UpdateCommandLine()

    def UpdateCommandLine(self):

        # Compile only & we need showIncludes for dependency evaluation
        # Complete exception handling
        cmdline = [
            '/c',                   # Compile only
            '/showIncludes',        # Show includes for dependency evaluation
            '/EHsc',                # Synchronous (C++) and Asynchronous (structured) exception handling
            '/errorReport:none'     # Don't send any ICEs to Microsoft
        ]

        # Construct the command line from the set options

        if self.NoLogo:
            cmdline += [ '/nologo' ]

        cmdline += [ "/W" + str(self.WarningLevel) ]

        if self.WarningsAsErrors:
            cmdline += [ "/WX" ]

        if self.Architecture != None:
            cmdline += [ self.Architecture ]

        cmdline += [ self.FloatingPoint ]

        if self.FloatingPointExceptions:
            cmdline += "/fp:except"

        cmdline += [ self.CallingConvention ]

        if self.DebuggingInfo != None:
            cmdline += [ self.DebuggingInfo ]

        if self.RuntimeChecks:
            cmdline += [ "/RTC1" ]

        cmdline += [ self.Optimisations ]

        if self.WholeProgramOptimisation:
            cmdline += [ "/GL" ]

        for define in self.Defines:
            cmdline += [ '/D', define ]

        for include in self.IncludePaths:
            cmdline += [ '/I', include ]

        self.CommandLine = cmdline


#
# Visual C++ Linker (link.exe)
#
# Command-line:
#
#    LINK.exe [options] [files] [@responsefile]
#
# Options:
#
#    /DEBUG                         Creates debugging information
#    /DEFAULTLIB:library            Adds a library that is searched AFTER input libraries but BEFORE the default libraries named in .obj files
#    /DLL                           Builds a DLL
#    /ENTRY:function                Specifies an entry point function
#    /INCREMENTAL[:NO]              By default the linker runs in incremental mode, this allows you to change that
#    /LARGEADDRESSAWARE             Tells the compiler that the application supports addresses larger than 2GB
#    /LIBPATH:dir                   Adds a library search path that gets used before the environment LIB path
#
#    /LTCG[:NOSTATUS|:STATUS|:PGINSTRUMENT|:PGOPTIMIZE|:PGUPDATE]   Link-time Code Generation control
#
#    /MACHINE:{X64|X86}             Specifies the target platform
#    /MAP[:filename]                Generate a MAP file
#    /NOLOGO                        Suppresses the logo
#    /NODEFAULTLIB[:library]        Tells the linker to remove one or more default libraries from the list (the compiler can insert some)
#    /OPT:{REF|NOREF}               Controls the optimisations performed during a build
#    /OPT:{ICF[=iterations]|NOICF}
#    /OPT:{WIN98|NOWIN98}
#    /OUT:filename                  Specifies the output filename
#    /PDB:filename                  Creates a program database file
#    /SUBSYSTEM:{CONSOLE|WINDOWS}   Either command-line or window based application (main or WinMain)
#    /WX[:NO]                       Treat linker warnings as errors
#
# Typical link.exe command-lines:
#
#    Debug Windows EXE
#    /OUT:"D:\dev\projects\TestProject\Debug\TestProject.exe" /INCREMENTAL /NOLOGO /MANIFEST /MANIFESTFILE:"Debug\TestProject.exe.intermediate.manifest" /DEBUG
#    /PDB:"d:\dev\projects\testproject\debug\TestProject.pdb" /SUBSYSTEM:WINDOWS /MACHINE:X86 /ERRORREPORT:PROMPT
#    kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib
#
#    Release Windows EXE
#    /OUT:"D:\dev\projects\TestProject\Release\TestProject.exe" /INCREMENTAL:NO /NOLOGO /MANIFEST /MANIFESTFILE:"Release\TestProject.exe.intermediate.manifest" /DEBUG
#    /PDB:"d:\dev\projects\testproject\release\TestProject.pdb" /SUBSYSTEM:WINDOWS /OPT:REF /OPT:ICF /LTCG /MACHINE:X86 /ERRORREPORT:PROMPT
#    kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib
#

VCMachine = Utils.enum(
    X86 = '/MACHINE:x86',
    X64 = '/MACHINE:x64'
)

VCUnrefSymbols = Utils.enum(
    ELIMINATE = '/OPT:REF',
    KEEP = '/OPT:NOREF'
)

VCDupComdats = Utils.enum(
    FOLD = '/OPT:ICF',
    KEEP = '/OPT:NOICF'
)

VCSubsystem = Utils.enum(
    CONSOLE = '/SUBSYSTEM:CONSOLE',
    WINDOWS = '/SUBSYSTEM:WINDOWS'
)


class VCLinkOptions:

    def __init__(self, config):

        # Initialise the requested config settings
        if config == VCBaseConfig.DEBUG:
            self.InitDebug()
        elif config == VCBaseConfig.RELEASE:
            self.InitRelease()

    def InitDebug(self):

        # Default settings for all linker options
        self.Debug = True
        self.NoLogo = True
        self.DLL = False
        self.EntryPoint = None
        self.Incremental = True
        self.LargeAddressAware = False
        self.LTCG = False
        self.Machine = VCMachine.X86
        self.MapFile = None
        self.UnrefSymbols = VCUnrefSymbols.KEEP
        self.DupComdats = VCDupComdats.KEEP
        self.Subsystem = VCSubsystem.WINDOWS
        self.DefaultLibs = [ ]
        self.NoDefaultLibs = [ ]
        self.LibPaths = [ ]
        self.UpdateCommandLine()

    def InitRelease(self):

        # Initialise changes from debug
        self.InitDebug()
        self.Debug = False
        self.Incremental = False
        self.LTCG = True
        self.UnrefSymbols = VCUnrefSymbols.ELIMINATE
        self.DupComdats = VCDupComdats.FOLD
        self.UpdateCommandLine()

    def UpdateCommandLine(self):

        cmdline = [
            '/ERRORREPORT:NONE',    # Don't send any ICEs to Microsoft
            '/VERBOSE:LIB'          # Show libs searched for dependency evaluation
        ]

        if self.Debug:
            cmdline += [ "/DEBUG" ]

        if self.NoLogo:
            cmdline += [ "/NOLOGO" ]

        if self.DLL:
            cmdline += [ "/DLL" ]

        if self.EntryPoint != None:
            cmdline += [ "/ENTRY:" + self.EntryPoint ]

        # Compiler is incremental by default
        if not self.Incremental:
            cmdline += [ "/INCREMENTAL:NO" ]

        if self.LargeAddressAware:
            cmdline += [ "/LARGEADDRESSAWARE" ]

        if self.LTCG:
            cmdline += [ "/LTCG" ]

        cmdline += [ self.Machine ]

        if self.MapFile != None:
            cmdline += [ "/MAP:" + self.MapFile ]

        cmdline += [ self.UnrefSymbols ]
        cmdline += [ self.DupComdats ]
        cmdline += [ self.Subsystem ]

        for lib in self.DefaultLibs:
            cmdline += [ "/DEFAULTLIB:" + lib ]

        for lib in self.NoDefaultLibs:
            cmdline += [ "/NODEFAULTLIB:" + lib ]

        for path in self.LibPaths:
            cmdline += [ "/LIBPATH:" + path ]

        self.CommandLine = cmdline


#
# Visual C++ Librarian (lib.exe)
#
# Command-line:
#
#    LIB [options] [files]
#
# Options:
#
#    /LIBPATH:dir                   Library path to search for when merging libraries
#    /LTCG                          Enable Link Time Code Generation
#    /MACHINE:{X64|X86}             Specifies the target platform - not normally needed as it's inferred from the .obj file
#    /NODEFAULTLIB[:library]        Tells the librarian to remove one or more default libraries from the list (the compiler can insert some)
#    /NOLOGO                        Suppress the logo
#    /OUT:filename                  Output library file
#    /SUBSYSTEM:{CONSOLE|WINDOWS}   Specifies the platform type
#    /WX[:NO]                       Treat warnings as errors
#
# Typical command-lines:
#
#    Debug
#    /OUT:"D:\dev\projects\TestProject\Debug\TestProject.lib" /NOLOGO
#
#    Release
#    /OUT:"D:\dev\projects\TestProject\Release\TestProject.lib" /NOLOGO /LTCG
#

class VCLibOptions:

    def __init__(self, config):

        # Initialise the requested config settings
        if config == VCBaseConfig.DEBUG:
            self.InitDebug()
        elif config == VCBaseConfig.RELEASE:
            self.InitRelease()

    def InitDebug(self):

        # Default settings for all librarian options
        self.LTCG = False
        self.Machine = VCMachine.X86
        self.NoLogo = True
        self.Subsystem = None
        self.WarningsAsErrors = False
        self.LibPaths = [ ]
        self.NoDefaultLibs = [ ]
        self.UpdateCommandLine()

    def InitRelease(self):

        # Initialise changes from debug
        self.InitDebug()
        self.LTCG = True
        self.UpdateCommandLine()

    def UpdateCommandLine(self):

        cmdline = [
            '/ERRORREPORT:NONE'     # Don't send ICEs to Microsoft
        ]

        if self.LTCG:
            cmdline += [ '/LTCG' ]

        cmdline += [ self.Machine ]

        if self.NoLogo:
            cmdline += [ '/NOLOGO' ]

        # Subsystem is implied
        if self.Subsystem != None:
            cmdline += [ self.Subsystem ]

        if self.WarningsAsErrors:
            cmdline += [ '/WX' ]

        for lib in self.LibPaths:
            cmdline += [ '/LIBPATH:' + lib ]

        for lib in self.NoDefaultLibs:
            cmdline += [ '/NODEFAULTLIB:' + lib]

        self.CommandLine = cmdline


#
# This reads each line of output from cl.exe and decides whether to print it or not.
# If the line reports what file is being included by the .c/.cpp file then it's not printed
# and instead stored locally so that it can report all the files included.
#
class VCIncludeScanner:

    Prefix = "Note: including file:"

    def __init__(self, env):

        self.Includes = [ ]
        self.Env = env

    def __call__(self, line):

        if line == "":
            return

        # Strip newline
        if line.endswith("\r\n"):
            line = line[:-2]

        # Scan for included files and add to the list
        if line.startswith(self.Prefix):
            path = line[len(self.Prefix):].lstrip()
            self.Includes.append(self.Env.NewFile(path))

        else:
            print(line)


#
# A node for compiling a single C/C++ file to a .obj file
#
class VCCompileNode (BuildSystem.Node):

    def __init__(self, path):

        self.Path = path
        self.Dependencies = [ ]

    def Build(self, env):

        output_files = self.GetOutputFiles(env)

        # Construct the command-line
        cmdline = [ "cl.exe" ] + env.CurrentConfig.CPPOptions.CommandLine
        if len(output_files) > 1:
            cmdline += [ "/Fd" + output_files[1] ]
        cmdline += [ "/Fo" + output_files[0], self.GetInputFile(env) ]
        #print(cmdline)

        # Create the include scanner and launch the compiler
        scanner = VCIncludeScanner(env)
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.PollPipeOutput(process, scanner)

        # Record the implicit dependencies for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Includes)

        return process.returncode == 0

    def GetInputFile(self, env):

        return self.Path

    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(env.CurrentConfig.IntermediatePath, path)

        files = [ path + ".obj" ]

        if env.CurrentConfig.CPPOptions.DebuggingInfo != None:
            files += [ os.path.join(env.CurrentConfig.OutputPath, "vc80.pdb") ]       # TODO: This doesn't vary between input files

        if env.CurrentConfig.CPPOptions.DebuggingInfo == VCDebuggingInfo.PDBEDITANDCONTINUE:
            files += [ os.path.join(env.CurrentConfig.OutputPath, "vc80.idb") ]

        return files

    def GetTempOutputFiles(self, env):

        return [ self.GetOutputFiles(env)[0] ]


#
# This reads each line of output from cl.exe and decides whether to print it or not.
# If the line reports what file is being included by the .c/.cpp file then it's not printed
# and instead stored locally so that it can report all the files included.
#
class VCLibScanner:

    Start = "Searching libraries"
    End = "Finished searching libraries"
    Prefix = "    Searching "

    def __init__(self, env):

        self.LibsAdded = { }
        self.Libs = [ ]
        self.Env = env
        self.Scanning = False

    def __call__(self, line):

        if line == "":
            return
        
        # Strip newline
        if line.endswith("\r\n"):
            line = line[:-2]
        
        if self.Scanning == False:
            
            # Either start scanning or report everything
            if line == self.Start:
                self.Scanning = True
            else:
                print(line)
            return
        
        # End of scanning?
        if line == self.End:
            self.Scanning = False
            return
        
        if line.startswith(self.Prefix):
            lib = line[len(self.Prefix):-1]
            if lib not in self.LibsAdded:
                self.Libs += [ self.Env.NewFile(lib) ]
                self.LibsAdded[lib] = True


#
# A node for linking an EXE or DLL given an output path and list of dependencies
#
class VCLinkNode (BuildSystem.Node):

    def __init__(self, path, obj_files, lib_files):

        self.Path = path
        
        # Object files are explicit dependencies, lib files are implicit, scanned during output
        self.Dependencies = obj_files
        self.LibFiles = lib_files

    def Build(self, env):

        output_files = self.GetOutputFiles(env)
        print("Linking: " + output_files[0])

        # Construct the command-line
        cmdline = [ "link.exe" ] + env.CurrentConfig.LinkOptions.CommandLine
        cmdline += [ '/OUT:' + output_files[0] ]
        cmdline.extend(dep.GetOutputFiles(env)[0] for dep in self.Dependencies)
        cmdline.extend(dep.GetOutputFiles(env)[0] for dep in self.LibFiles)
        #print(cmdline)

        # Create the lib scanner and run the link process
        scanner = VCLibScanner(env)
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.PollPipeOutput(process, scanner)
        
        # Record the implicit dependencies for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Libs)

        return process.returncode == 0

    def GetInputFile(self, env):

        path = os.path.join(env.CurrentConfig.OutputPath, self.Path)
        return path

    def GetOutputExecutable(self, config):
        
        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(config.OutputPath, path)
        
        ext = ".exe"
        if config.LinkOptions.DLL:
            ext = ".dll"
        
        return (path, ext)

    def GetOutputFiles(self, env):
        
        # Add the EXE/DLL
        (path, ext) = self.GetOutputExecutable(env.CurrentConfig)
        files = [ path + ext ]

        if env.CurrentConfig.LinkOptions.Debug:
            files += [ path + ".pdb" ]

        if env.CurrentConfig.LinkOptions.Incremental:
            files += [ path + ".ilk" ]

        return files
    
    def __repr__(self):

        return "LINK: " + self.Path


#
# A node for compositing a set of dependencies into a library file
#
class VCLibNode (BuildSystem.Node):

    def __init__(self, path, dependencies):

        self.Path = path
        self.Dependencies = dependencies

    def Build(self, env):

        # Construct the command-line
        cmdline = [ "lib.exe" ] + env.CurrentConfig.LibOptions.CommandLine
        cmdline += [ '/OUT:' + self.GetOutputFiles(env)[0] ]
        cmdline.extend(dep.GetOutputFiles(env)[0] for dep in self.Dependencies)
        #print(cmdline)

        # Run the librarian process
        process = Process.OpenPiped(cmdline, env.EnvironmentVariable)
        Process.PollPipeOutput(process, lambda x: print(x))

        return process.returncode == 0

    def GetInputFile(self, env):

        path = os.path.join(env.CurrentConfig.OutputPath, self.Path)
        return path

    def GetOutputFiles(self, env):

        path = os.path.join(env.CurrentConfig.OutputPath, self.Path)
        return [ path ]


def __RunTests():

    options = VCCompileOptions(VCBaseConfig.DEBUG)
    print(options.BuildCommandLine())
    options = VCCompileOptions(VCBaseConfig.RELEASE)
    print(options.BuildCommandLine())

    options = VCLinkOptions(VCBaseConfig.DEBUG)
    print (options.BuildCommandLine())
    options = VCLinkOptions(VCBaseConfig.RELEASE)
    print (options.BuildCommandLine())

    options = VCLibOptions(VCBaseConfig.DEBUG)
    print (options.BuildCommandLine())
    options = VCLibOptions(VCBaseConfig.RELEASE)
    print (options.BuildCommandLine())


if __name__ == "__main__":
    __RunTests()

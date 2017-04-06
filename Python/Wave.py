
#
# Build Node for Boost.Wave Preprocessor Command-line Driver
# http://www.boost.org/doc/libs/1_55_0/libs/wave/doc/wave_driver.html
#


import os
import string
import Utils
import Process
import BuildSystem


# Directory where the Wave Driver executable is located
_InstallPath = None

def SetInstallPath(location):
    global _InstallPath
    _InstallPath = location


class Options:

    #
    # TODO: Uses new dirty options checking mechanism.
    #
    def __init__(self):

        # List of normal/system include search paths
        self.IncludePaths = [ ]
        self.SystemIncludePaths = [ ]

        # List of macros to define/undefine for preprocessor
        self.DefineMacros = [ ]
        self.UndefineMacros = [ ]

        self.LongLong = True
        self.Variadics = True
        self.C99 = False
        self.Cpp11 = False

        self.Dirty = True
        self.CommandLine = [ ]

    def __setattr__(self, name, value):

        # Assign the field and mark the command-line as dirty
        self.__dict__[name] = value
        self.__dict__["Dirty"] = True

    def UpdateCommandLine(self):

        if self.Dirty:

            cmdline = [ ]
            cmdline += [ ('--include="' + os.path.normpath(path) + '"') for path in self.IncludePaths ]
            cmdline += [ ('--sysinclude="' + os.path.normpath(path) + '"') for path in self.SystemIncludePaths ]
            cmdline += [ '--undefine=' + macro for macro in self.UndefineMacros ]

            self.FormatDefines(cmdline)

            if self.LongLong: cmdline += [ "--long_long" ]
            if self.Variadics: cmdline += [ "--variadics" ]
            if self.C99: cmdline += [ "--c99" ]
            if self.Cpp11: cmdline += [ "--c++11" ]

            # Update and mark as not dirty without calling into __setattr__
            self.__dict__["CommandLine"] = cmdline
            self.__dict__["Dirty"] = False

    def FormatDefines(self, cmdline):

        for define in self.DefineMacros:
            if isinstance(define, str):
                cmdline += [ '-D ' + define ]
            else:
                cmdline += [ '-D ' + str(define[0]) + "=" + str(define[1]) ]



class BuildNode (BuildSystem.Node):

    #
    # TODO: Uses new options location system of passing a map from config name to options
    # that are referenced in Build. Means nothing specific to this build node need to
    # be stored in the config object.
    #
    def __init__(self, source, options_map, extension):

        super().__init__()
        self.Source = source
        self.Dependencies = [ source ]
        self.OptionsMap = options_map
        self.Extension = extension

    def Build(self, env):

        # Ensure command -line for current configuration is up-to-date
        options = self.OptionsMap[env.CurrentConfig.CmdLineArg]
        options.UpdateCommandLine()

        # Augment command-line with current environment
        cmdline = [ os.path.join(_InstallPath, "wave.exe") ]
        cmdline += self.OptionsMap[env.CurrentConfig.CmdLineArg].CommandLine
        cmdline += [ '--output=' + self.GetOutputFiles(env)[0] ]
        cmdline += [ '--listincludes=-' ]
        cmdline += [ self.GetInputFile(env) ]
        Utils.ShowCmdLine(env, cmdline)

        # Launch Wave with a dependency scanner and wait for it to finish
        scanner = Utils.LineScanner(env)
        scanner.AddLineParser("Includes", '"', [ "<" ], lambda line, length: line.split("(")[1].rstrip()[:-1])
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.WaitForPipeOutput(process, scanner)

        # Record the implicit dependencies for this file
        data = env.GetFileMetadata(self.GetInputFile(env))
        data.SetImplicitDeps(env, scanner.Includes)

        return process.returncode == 0

    def GetInputFile(self, env):

        path = self.Source.GetOutputFiles(env)[0]
        return path

    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.GetInputFile(env))[0]
        path = os.path.join(env.CurrentConfig.IntermediatePath, path)
        return [ path + "." + self.Extension ]

    def GetTempOutputFiles(self, env):

        return self.GetOutputFiles(env)

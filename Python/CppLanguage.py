
import Utils


class CppBuild:
    
    def __init__(self, env, dirs, target, ext_libs = [], libs = [], build = True):

        # Gather source/header files
        self.cpp_files = []
        self.hpp_files = []
        for dir in dirs:
            self.cpp_files += Utils.Glob(dir, "*.cpp")
            self.cpp_files += Utils.Glob(dir, "*.c")
            self.hpp_files += Utils.Glob(dir, "*.h")

        # Compile C++ files and create file nodes out of external library references
        self.obj_files = [ env.CPPFile(file) for file in self.cpp_files ]
        self.lib_files = [ env.NewFile(file) for file in ext_libs ]

        # Link or use librarian dependent on output path
        target = target.lower()
        self.output = None
        if target.endswith(".exe"):
            self.output = self.exe = env.Link(target, self.obj_files, self.lib_files + libs)
        elif target.endswith(".dll"):
            self.output = self.dll = env.Link(target, self.obj_files, self.lib_files + libs)
        elif target.endswith(".lib"):
            self.output = self.lib = env.Lib(target, self.obj_files, self.lib_files + libs)

        # Build all the config command lines
        for config in env.Configs.values():
            config.UpdateCommandLines()

        if build:
            env.Build(self.output, target[:-4])


    def OverrideCPPOptions(self, cpp_file_match, override_cpp_opts):

        # Find all C++ files that match the input string and apply the override options
        cpp_file_match = cpp_file_match.lower()
        for obj_file in self.obj_files:
            if cpp_file_match in obj_file.Path.lower():
                obj_file.SetCPPOptions(override_cpp_opts)

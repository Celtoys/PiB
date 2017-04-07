
import Utils


#
# Use this to mark library dependencies as "weak". This means that they will be used as input to a link
# node but won't be used to see if that node needs to be rebuilt if the library changes.
#
CppLinkWeakDep = True


class CppBuild:
    
    def __init__(self, env, dirs, target, ext_libs = None, build = True):

        if ext_libs is None:
            ext_libs = []
        # Gather source/header files
        self.cpp_files = []
        self.hpp_files = []
        for dir in dirs:
            if dir.endswith(".cpp") or dir.endswith("*.c"):
                self.cpp_files += [ dir ]
            elif dir.endswith(".h"):
                self.hpp_files += [ dir ]
            else:
                self.cpp_files += Utils.Glob(dir, "*.cpp")
                self.cpp_files += Utils.Glob(dir, "*.c")
                self.hpp_files += Utils.Glob(dir, "*.h")

        # Create nodes for compiling the C+ files
        self.obj_files = [ env.CPPFile(file) for file in self.cpp_files ]

        # Create file nodes for the input libraries
        # Split into two lists: strong/weak dependencies (see CppLinkWeakDep)
        self.lib_files = [ env.NewFile(file) for file in ext_libs if type(file) != tuple ]
        self.weak_lib_files = [ env.NewFile(file[0]) for file in ext_libs if type(file) == tuple ]

        # Link or use librarian dependent on output path
        self.output = None
        if target.endswith(".exe"):
            self.output = self.exe = env.Link(target, self.obj_files, self.lib_files, self.weak_lib_files)
        elif target.endswith(".dll"):
            self.output = self.dll = env.Link(target, self.obj_files, self.lib_files, self.weak_lib_files)
        elif target.endswith(".lib"):
            self.output = self.lib = env.Lib(target, self.obj_files, self.lib_files)

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

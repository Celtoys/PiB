
import Utils


class CppBuild:
    
    def __init__(self, env, dirs, target, ext_libs = [], libs = [], configs = None, build = True):

        # Gather source/header files
        self.cpp_files = []
        self.hpp_files = []
        for dir in dirs:
            self.cpp_files += Utils.Glob(dir, "*.cpp")
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
            self.output = self.lib = env.Lib(target, self.obj_files)

        # Build all the config command lines
        if configs == None:
            configs = env.Configs
        for config in configs.values():
            config.UpdateCommandLines()

        if build:
            env.Build(self.output, target[:-4], configs)

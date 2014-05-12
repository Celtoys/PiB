
import os
import Utils
import Process
import BuildSystem


# Retrieve the installation directory from the environment
InstallDir = None
if "CUDA_PATH" in os.environ:
    InstallDir = os.environ["CUDA_PATH"]


# Setup some common paths relative to that
IncludeDir = os.path.join(InstallDir, "include")
x86LibDir = os.path.join(InstallDir, "lib/Win32")
x64LibDir = os.path.join(InstallDir, "lib/x64")
BinDir = os.path.join(InstallDir, "bin")


#
# Names of nVidia GPU Virtual Architectures for generating up to the PTX stage
#
VirtualArch = Utils.enum(
	'compute_10',
	'compute_11',
	'compute_12',
	'compute_13',
	'compute_20',
	'compute_30',
	'compute_32',
	'compute_35',
	'compute_50',
)

#
# Names of nVidia GPU Real Archtectures for generating final binary images
#
RealArch = Utils.enum(
	'sm_10',
	'sm_11',
	'sm_12',
	'sm_13',
	'sm_20',
	'sm_21',
	'sm_30',
	'sm_32',
	'sm_35',
	'sm_50',
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

		if self.ExplicitLanguage: cmdline += [ self.Language ]

		cmdline += [ '-I ' + path for path in self.IncludePaths ]
		cmdline += [ '-isystem ' + path for path in self.SystemIncludePaths ]
		cmdline += [ '-include ' + file for file in self.IncludeFiles ]
		cmdline += [ '-D ' + macro for macro in self.DefineMacros ]
		cmdline += [ '-U ' + macro for macro in self.UndefineMacros ]

		cmdline += [ '-L ' + lib for lib in self.LibraryPaths ]
		cmdline += [ '-l ' + lib for lib in self.Libraries ]

		if self.HostCompilerPath: cmdline += [ '-ccbin ' + self.HostCompilerPath ]
		if self.CUDARuntime: cmdline += [ '-cudart ' + self.CUDARuntime ]

		if self.HostDebug: cmdline += [ '-g' ]
		if self.DeviceDebug: cmdline += [ '-G' ]

		cmdline += [ 'arch ' + self.GPUArch ]
		cmdline += [ 'code ' + self.GPUCode ]

		cmdline += [ '-ftz ' + 'true' if self.FlushSingleDenormalsToZero else 'false' ]
		cmdline += [ '-prec-div ' + 'true' if self.PreciseSingleDivRecip else 'false' ]
		cmdline += [ '-prec-sqrt ' + 'true' if self.PreciseSingleSqrt else 'false' ]
		cmdline += [ '-fmad ' + 'true' if self.FuseMultipleAdds else 'false' ]
		cmdline += [ '-use_fast_math ' + 'true' if self.UseFastMath else 'false' ]

		if self.DisableWarnings: cmdline += [ 'w' ]
		if self.SourceInPTX: cmdline += [ 'src-in-ptx' ]
		if self.RestrictPointers: cmdline += [ '-restrict' ]

		self.CommandLine = cmdline

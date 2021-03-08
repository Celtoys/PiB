
import winreg
import os
import string


#
# Big list of known SDK versions and their properties
#
# I wrote some automatic discovery code for building all this (300 lines) but it turns
# out that Windows SDK versions differ enough such that there is no discernible
# pattern to quickly and easily figure what goes where.
#
# Examples:
#
#    * ProductVersion is inconsistent in the registry and not monotonic.
#    * Identifying "latest" SDK thus requires parsing their registry names.
#    * Between 7.1 and 8.x the root "include" directory is no longer used and split into "shared" and "um".
#    * Between 7.1 and 8.x the relative lib paths between x86 and x64 change.
#    * This "bin" directory has the same problem.
#    * Each of 7.1, 8.0 and 8.1 have different root "lib" directories with no pattern.
#    * There is no guarantee that the version names will maintain their pattern.
#
# The logic became convoluted and hard to decipher. Much worse; Microsoft clearly
# have no interest in maintaining installation patterns between versions* so the
# code would only have gotten worse with each new SDK.
#
# Instead, just list everything known and see what is where. Code to parse it
# is simple and easy to understand. Adding exceptions for what we haven't seen before
# is just as easy.
#
# * when you also write the build system, would you? 
#
# Don't be afraid to write the stupid code. Don't be afraid to throw away the clever code once written
#
SDKVersions = [
	{
		"version"  : "7.1",
		"install"  : "Microsoft SDKs\\Windows\\v7.1A",
		"includes" : [ "include" ],
		"lib32"    : "lib",
		"lib64"    : "lib\\x64",
		"bin32"    : "bin",
		"bin64"    : "bin\\x64"
	},
	#{
	#	"version"  : "8.0",
	#	"install"  : "Windows Kits\\8.0",
	#	"includes" : [ "include\\shared", "include\\um" ],
	#	"lib32"    : "lib\\win8\\um\\x86",
	#	"lib64"    : "lib\\win8\\um\\x64",
	#	"bin32"    : "bin\\x86",
	#	"bin64"    : "bin\\x64"
	#},
	{
		"version"  : "8.1",
		"install"  : "Windows Kits\\8.1",
		"includes" : [ "include\\shared", "include\\um" ],
		"lib32"    : "lib\\winv6.3\\um\\x86",
		"lib64"    : "lib\\winv6.3\\um\\x64",
		"bin32"    : "bin\\x86",
		"bin64"    : "bin\\x64"
	},
	{
		"version"  : "10",
		"install"  : "Windows Kits\\10",
		"includes" : [ "include\\10.0.18362.0\\shared", "include\\10.0.18362.0\\um" ],
		"lib32"    : "lib\\10.0.18362.0\\um\\x86",
		"lib64"    : "lib\\10.0.18362.0\\um\\x64",
		"bin32"    : "bin\\10.0.18362.0\\x86",
		"bin64"    : "bin\\10.0.18362.0\\x64",
	},
	{
		"version"  : "10",
		"install"  : "Windows Kits\\10",
		"includes" : [ "include\\10.0.16299.0\\shared", "include\\10.0.16299.0\\um" ],
		"lib32"    : "lib\\10.0.16299.0\\um\\x86",
		"lib64"    : "lib\\10.0.16299.0\\um\\x64",
		"bin32"    : "bin\\10.0.16299.0\\x86",
		"bin64"    : "bin\\10.0.16299.0\\x64",
	},
]


# Locate program files 
ProgramFilesx86 = os.getenv("ProgramFiles(x86)")
if ProgramFilesx86 == None:
	print("ERROR: Couldn't locate Program Files (x86) directory")
	ProgramFilesx86 = ""


SDKDir = None
IncludeDirs = [ ]
x86LibDir = None
x64LibDir = None
x86BinDir = None
x64BinDir = None


# Search SDK version list backwards from most recent
for sdk in reversed(SDKVersions):

	# Is this one installed?
	sdk_dir = os.path.join(ProgramFilesx86, sdk["install"])
	if not os.path.exists(sdk_dir):
		continue

	# Get list of include paths that exist
	includes = sdk["includes"]
	includes = [ os.path.join(sdk_dir, include) for include in includes ]
	includes = [ include for include in includes if os.path.exists(include) ]
	if len(includes) == 0:
		continue

	# Get lib directories
	lib32 = os.path.join(sdk_dir, sdk["lib32"])
	if not os.path.exists(lib32):
		continue
	lib64 = os.path.join(sdk_dir, sdk["lib64"])
	if not os.path.exists(lib64):
		continue

	# Get bin directories
	bin32 = os.path.join(sdk_dir, sdk["bin32"])
	if not os.path.exists(bin32):
		continue
	bin64 = os.path.join(sdk_dir, sdk["bin64"])
	if not os.path.exists(bin64):
		continue

	# Passed all tests, assign this as the installed SDK
	SDKDir = sdk_dir
	IncludeDirs = includes
	x86LibDir = lib32
	x64LibDir = lib64
	x86BinDir = bin32
	x64BinDir = bin64
	break

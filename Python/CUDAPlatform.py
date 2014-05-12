
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

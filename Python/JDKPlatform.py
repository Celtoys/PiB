
import os
import sys
import winreg
import Process
import BuildSystem


#
# Wrapper for returning None if the key doesn't exist
#
def OpenKey(key, sub_key):
    
    try:
        key = winreg.OpenKey(key, sub_key)
    except EnvironmentError:
        return None
    return key


def GetSubKeyNames(key):
    
    names = [ ]
    
    try:
        
        # Loop until an exception is thrown, indicating no more data
        # Quite an odd way of enumerating a sequence!
        index = 0
        while True:
            name = winreg.EnumKey(key, index)
            names += [ name ]
            index += 1
    
    except WindowsError:
        pass
    
    return names


def GetJDKPath():
    
    # Get a sorted list of available JDK version numbers
    key = OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\JavaSoft\Java Development Kit")
    if key == None:
        print("ERROR: Couldn't find the JDK registry key")
        return None
    names = sorted(GetSubKeyNames(key))
    
    # Open the key for the most up-to-date version
    version = names[-1]
    version_key = OpenKey(key, version)
    if version_key == None:
        print("ERROR: Failed to open the JDK version registry sub-key")
        return None
    
    # Read the install path for the JDK
    try:
        (value, type) = winreg.QueryValueEx(version_key, "JavaHome")
    except WindowsError:
        print("ERROR: JDK version sub-key doesn't contain the JavaHome value")
        return None
    
    # Close all opened keys
    winreg.CloseKey(version_key)
    winreg.CloseKey(key)
    
    return value


def GetJDKBinPath():
    
    return os.path.join(GetJDKPath(), "bin")


def JavaCLineFilter(line):
    
    if line == "":
        return
    
    print(line.strip("\r\n"))


class JDKCompileNode (BuildSystem.Node):

    def __init__(self, path):
        
        self.Path = path
        self.Dependencies = [ ]
    
    def Build(self, env):
        
        # Construct the command-line
        output_path = os.path.dirname(self.GetOutputFiles(env)[0])
        cmdline = [ "javac.exe", self.Path ]
        cmdline += [ "-d", output_path ]

        # Compile the file
        print(self.Path)
        process = Process.OpenPiped(cmdline, env.EnvironmentVariables)
        Process.PollPipeOutput(process, JavaCLineFilter)
        
        return process.returncode == 0

    def GetInputFile(self, env):
        
        return self.Path
    
    def GetOutputFiles(self, env):

        # Get the relocated path minus extension
        path = os.path.splitext(self.Path)[0]
        path = os.path.join(env.CurrentConfig.OutputPath, path)

        return [ path + ".class" ]


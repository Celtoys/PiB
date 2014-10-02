
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
# Utils.py: Some shared utility functions.
#

import os
import sys
import errno
import fnmatch
import shutil


#
# Create an enumeration type by assigning each value:
#    Type = enum(ONE=1, TWO=2, THREE='three')
#
def enum(**enums):
    return type('Enum', (), enums)


#
# Create an enumeration type with each value uniquely assigned:
#    Type = enum('ONE', 'TWO', 'THREE')
#
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def NormalisePath(path):

    path = os.path.normpath(path)
    path = os.path.normcase(path)
    return path


#
# Quick shortcut for finding out if a python class type contains a callable method
#
def ObjectHasMethod(object, method):

    # New-style classes: does the type contain the method?
    t = type(object)
    if method not in t.__dict__:
        return False

    # It's a method only if it's callable
    return callable(t.__dict__[method])


#
# Instead of checking for the existence of a file before removing it, this will remove
# the file and react to any thrown exceptions instead. This requires one less call into
# the file system.
#
# Returns True if the file was removed.
#
def RemoveFile(filename):

    try:
        os.remove(filename)
        return True
    except OSError as exc:
        return False


#
# Copies files, returning True/False for whether the operation succeeded.
#
def CopyFile(source, dest):

    try:
        shutil.copyfile(source, dest)
        return True
    except IOError as exc:
        return False


#
# Instead of checking for existence of a path before creating it, this will try to
# create the path and react to any thrown exceptions instead. This requires one less
# call into the file system.
#
def Makedirs(path):

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            return False

    return True


def Glob(path, pattern):

    matches = [ ]
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


#
# Searches the command-line for the given argument, returning the value passed
# after that argument if it exists. Can return a specified default value if
# the argument wasn't found.
#
def GetSysArgvProperty(name, default=None, index=0):

    nb_args = len(sys.argv)
    for i in range(nb_args):
        arg = sys.argv[i]
        if arg == name:
            if i < nb_args - 1 and index == 0:
                return sys.argv[i + 1]
            index -= 1

    return default


#
# Searches the command-line for the given argument that is repeated,
# returning the values passed as a list.
#
def GetSysArgvProperties(name, default=None):

    props = [ ]
    index = 0

    while True:
        prop = GetSysArgvProperty(name, default, index)
        if prop == default:
            break
        props += [ prop ]
        index += 1

    return props


#
# This reads each line of output from a compiler and decides whether to print it or not.
# If the line reports what file is being included by the .c/.cpp file then it's not printed
# and instead stored locally so that it can report all the files included.
#
# NOTE: This is the only util in this file to depend on Environment.
#
class IncludeScanner:

    def __init__(self, env, prefix, ignore_prefixes, parser):

        self.Includes = set()
        self.Env = env
        self.Prefix = prefix
        self.IgnorePrefixes = ignore_prefixes
        self.Parser = parser

    def __call__(self, line):

        if line == "":
            return

        # Strip newline/whitespace
        line = line.strip("\r\n")
        line = line.lstrip()

        # Prioritise checking for ignored lines
        if self.IgnoreLine(line):
            return

        # Scan for included files and add to the list
        elif line.startswith(self.Prefix):
            #path = line[len(self.Prefix):self.StripOffset].lstrip()
            path = self.Parser(line, len(self.Prefix))
            path = NormalisePath(path)
            self.Includes.add(path)
            #self.Includes.add(self.Env.NewFile(path))
            #self.Includes.append(self.Env.NewFile(path))

        elif not self.Env.NoToolOutput:
            print(line)
    
    def IgnoreLine(self, line):

        if self.IgnorePrefixes:
            for prefix in self.IgnorePrefixes:
                if line.startswith(prefix):
                    return True

        return False


def ShowCmdLine(env, cmdline):
    
    if env.ShowCmdLine:
        print(cmdline)
        
        for cmd in cmdline:
            print(cmd, end=" ")
        print("")

def ExecPibfile(pibfile, global_symbols = { }):

    # Load the build script file
    if not os.path.exists(pibfile):
        print("ERROR: No '" + pibfile + "' found")
        sys.exit(1)
    code = None
    with open(pibfile) as f:
        code = f.read()

    # Switch to the directory of the pibfile
    cur_dir = os.getcwd()
    pibfile_dir = os.path.dirname(pibfile)
    if pibfile_dir != "":
        os.chdir(pibfile_dir)

    global_symbols["__file__"] = os.path.realpath(pibfile)

    # Compile the environment initialisation code
    prologue = """
from BuildSystem import *
from Environment import *
from Utils import *
from MSVCGeneration import *
from CppLanguage import *

env = Environment.New()
if env == None:
    sys.exit(1)
    """
    prologue_compiled = compile(prologue, "<prologue>", "exec")

    # Compile the shutdown code    
    epilogue = """
env.SaveFileMetadata()
    """
    epilogue_compiled = compile(epilogue, "<epilogue>", "exec")

    # Compile the user code
    code_compiled = compile(code, pibfile, "exec")

    # Execute the compiled code in an isolated namespace
    exec(prologue_compiled, global_symbols)
    exec(code_compiled, global_symbols)
    exec(epilogue_compiled, global_symbols)

    # Restore initial directory
    os.chdir(cur_dir)

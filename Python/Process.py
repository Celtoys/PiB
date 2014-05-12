
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
# Process.py: Functions for launching processes and capturing their output.
#

import subprocess
import os


def OpenPiped(args, env = None):

    # Even if the executable is in the path of the modified environment, you need to specify the full path to execute it
    # This is because Popen uses the existing environment to find the executable, applying the modified environment after
    if env != None:

        # Split all paths
        paths = env["PATH"]
        paths = paths.split(";")

        # Try and find a path that hosts the executable and modify the input
        for path in paths:
            file = os.path.join(path, args[0])
            if os.path.exists(file):
                args[0] = file
                break

    # Send output to a pipe, push stderr through stdout to ensure they're ordered correctly
    #print (args)
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)


def WaitForPipeOutput(process, line_handler=None):

    # Note that the output from stdout is a bytearray and Python 3.0 strings are now Unicode
    # Need to "decode" the byte array: http://stackoverflow.com/questions/606191/convert-byte-array-to-python-string
    #
    # DO NOT USE process.wait -> communicate!
    # See: http://bugs.python.org/issue1236, http://scons.tigris.org/source/browse/scons/trunk/src/engine/SCons/Tool/MSCommon/common.py?revision=4958&view=markup
    #
    # process.wait()
    # output = process.communicate()[0]

    if line_handler != None:

        # Use a line handler if specified
        output = process.stdout.readlines()
        for line in output:
            line_handler(bytearray(line).decode())

        # Force commit of the returncode parameter in process
        while process.returncode == None:
            process.poll()

    else:

        output = process.stdout.read()

        # Force commit of the returncode parameter in process
        while process.returncode == None:
            process.poll()

        return bytearray(output).decode()


#
# TODO: This function has SEVERE problems capturing output - sometimes it
# early-aborts before receiving output, sometimes it doesn't. The problem is
# time-based and likely to be a threading issue. NEED TO WRITE A CUSTOM
# VERSION TO HANDLE LONG PERIODS OF OUTPUT!
#
def PollPipeOutput(process, line_handler):

    # Loop while the process is running
    while process.poll() is None:

        # Note that the output from stdout is a bytearray and Python 3.0 strings are now Unicode
        # Need to "decode" the byte array: http://stackoverflow.com/questions/606191/convert-byte-array-to-python-string
        line = process.stdout.readline()
        line = bytearray(line).decode()

        line_handler(line)

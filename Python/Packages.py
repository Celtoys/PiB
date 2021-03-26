
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
# Packages.py: Experimental, simple package "manager"
#

import os
import shutil
import tempfile
import urllib.request
import zipfile

import Process
import Utils

def DownloadFile(url):
    # Generate a temporary download location
    filename = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))

    # Download the file
    print(f"   Downloading {url}")
    with urllib.request.urlopen(url) as response, open(filename, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    return filename

def ExtractZipFileTo(filename, path):
    # Extract entire zip file
    print(f"   Extracting to {path}")
    with zipfile.ZipFile(filename) as zf:
        zf.extractall(path)

    return path

def ExtractZipFile(filename):
    # Generate a temporary extract location
    path = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
    return ExtractZipFileTo(filename, path)

# 7-Zip not installed by default
SevenZipExe = None

def Install7Zip(version, path):
    # See if 7zip is already there first
    SevenZipExe = os.path.join(path, f"7zip\\{version}\\7za.exe")
    if not os.path.exists(SevenZipExe):

        # Download and extract the whole thing
        stripped_ver = version.replace(".", "")
        SevenZipUrl = f"https://www.7-zip.org/a/7za{stripped_ver}.zip"
        downloaded = DownloadFile(SevenZipUrl)
        extracted = ExtractZipFile(downloaded)

        # Copy just the executable
        Utils.Makedirs(os.path.dirname(SevenZipExe))
        Utils.CopyFile(os.path.join(extracted, "7za.exe"), SevenZipExe)

def Extract7ZipFileTo(filename, path):
    if SevenZipExe == None:
        print("ERROR: 7-Zip has not been installed. Call Install7Zip first.")
        return

    # Use previously-installed 7zip
    command_line = f"{SevenZipExe} x -o{path} {filename}"
    process = Process.OpenPiped(command_line)
    Process.PollPipeOutput(process, lambda t: print(t.strip("\r\n")))

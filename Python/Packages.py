
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

import io
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

    print(f"Downloading {url}")

    # Query server for download
    response = urllib.request.urlopen(url)
    length = response.getheader("content-length")

    # Determine download block size for progress
    if length:
        print(f"   Size: {length} bytes")
        length = int(length)
        block_size = max(4096, length // 100)
    else:
        print("   Size Unknown")
        block_size = 1024 * 1024

    # Download in blocks
    buffer = io.BytesIO()
    size = 0
    while True:
        block_buffer = response.read(block_size)
        if not block_buffer:
            break
        buffer.write(block_buffer)
        size += len(block_buffer)

        # Display progress percentage
        if length:
            print(f"\t{int(size / length * 100)} %\r", end="")

    # Clear progress line
    print()

    # Write download to file
    with open(filename, "wb") as f:
        f.write(buffer.getbuffer())

    return filename

def ExtractZipFileTo(filename, path):
    # Extract entire zip file
    print(f"Extracting {filename} to {path}")
    with zipfile.ZipFile(filename) as zf:
        zf.extractall(path)

    return path

def ExtractZipFile(filename):
    # Generate a temporary extract location
    path = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
    return ExtractZipFileTo(filename, path)

def ExtractMsiFileTo(filename, path):
    print(f"Extracting {filename} to {path}")
    os.system(f"msiexec /a {filename} /qb TARGETDIR={path}")
    return path

def ExtractMsiFile(filename):
    path = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
    return ExtractMsiFileTo(filename, path)

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

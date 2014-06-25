
import winreg
import os


# Read Windows SDK install path from the registry
SDKDir = None
LibDir = None
IncludeDir = None
try:
	with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as reg:
		with winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Microsoft SDKs\\Windows") as key:
			SDKDir = winreg.QueryValueEx(key, "CurrentInstallFolder")[0]
			LibDir = os.path.join(SDKDir, "lib")
			IncludeDir = os.path.join(SDKDir, "include")
except:
	SDKDir = None

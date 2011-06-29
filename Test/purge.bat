@echo off
del *.pib /s
attrib -h * /s
del *.suo /s
del *.ncb /s
del *.sln /s
del *.vcproj /s
del *.vcproj.* /s
rmdir /s /q bin
rmdir /s /q obj
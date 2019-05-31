call "D:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat"

msbuild "test.vcxproj" /t:Rebuild /p:Configuration=Debug /m

pause


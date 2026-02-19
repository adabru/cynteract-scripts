@echo off
setlocal

rem Check if a folder was dragged onto the script
if "%~1"=="" (
    echo Please drag and drop a folder onto this script.
    pause
    exit /b
)

rem Get the folder path
set "folder=%~1"

rem Get the folder name without the path
for %%F in ("%folder%") do set "folderName=%%~nxF"

rem Get the parent directory of the folder
for %%F in ("%folder%") do set "parentDir=%%~dpF"

rem Define the output zip file name in the parent directory
set "zipFile=%parentDir%%folderName%.zip"

rem Compress the folder contents
powershell -command "Compress-Archive -Path \"%folder%\*\" -DestinationPath \"%zipFile%\" -Force"

echo Folder "%folderName%" has been zipped to "%zipFile%".

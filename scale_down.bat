@echo off
setlocal

rem Check if a video was dragged onto the script
if "%~1"=="" (
    echo Please drag and drop a video onto this script.
    pause
    exit /b
)

rem Get the video path
set "video=%~1"

rem Define the output video file name in the parent directory
set "outputFile=%video:.mp4=%_reduced.mp4"

rem Scale down the video contents
powershell -command "ffmpeg -i \"%video%\" -vf \"scale=ceil(iw/2/2)*2:ceil(ih/2/2)*2\" \"%outputFile%\""

echo video "%video%" has been scaled down to "%outputFile%".
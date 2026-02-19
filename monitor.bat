@echo off
setlocal enabledelayedexpansion

echo Searching for matching COM ports...

:: Use PowerShell to find and extract (COMx)
for /f "delims=" %%C in ('powershell -NoProfile -Command ^
  "Get-WmiObject Win32_PnPEntity | Where-Object { $_.PNPDeviceID -match 'VID_10C4.*PID_EA60' -or $_.PNPDeviceID -match 'VID_303A.*PID_1001' } | ForEach-Object { if ($_.Name -match '\(COM\d+\)') { $matches[0] } }"') do (
    echo Matched port string: %%C
    set "COMPORT=%%C"
)

:: Clean parentheses
set "COMPORT=!COMPORT:(=!"
set "COMPORT=!COMPORT:)=!"

if "!COMPORT!"=="" (
    echo No matching COM port found.
    pause
    exit /b 1
)

echo Detected COM port: !COMPORT!

:: Use PowerShell to open the serial port and display data
powershell -Command ^
  $port = new-Object System.IO.Ports.SerialPort('!COMPORT!', 230400, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One); ^
  $port.Open(); ^
  while ($true) { ^
    if ($port.IsOpen) { ^
      $data = $port.ReadLine(); ^
      Write-Host $data; ^
    } ^
  }

pause
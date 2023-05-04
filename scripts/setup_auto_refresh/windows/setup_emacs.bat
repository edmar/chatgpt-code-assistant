@echo off

set EMACS_CONFIG_PATH=%USERPROFILE%\.emacs

if exist "%ProgramFiles(x86)%\emacs\bin\emacs.exe" (
  if exist "%EMACS_CONFIG_PATH%" (
    echo Configuring auto-revert-mode for Emacs...
    powershell -Command "Add-Content '%EMACS_CONFIG_PATH%' ';; Enable auto-revert-mode`n(global-auto-revert-mode 1)'"
    echo Emacs auto-revert-mode enabled.
  ) else (
    echo Error: .emacs not found. Please create it before running this script.
  )
) else (
  echo Emacs not found.
)


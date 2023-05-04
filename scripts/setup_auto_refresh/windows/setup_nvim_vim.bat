@echo off

set NEOVIM_CONFIG_PATH=%LOCALAPPDATA%\nvim\init.vim
set VIM_CONFIG_PATH=%USERPROFILE%\_vimrc

:install_autoread_plugin
if exist "%1" (
  echo Installing vim-autoread plugin for %~nx1...
  powershell -Command "(Get-Content '%1') -replace 'call plug#end', \"Plug 'djoshea/vim-autoread'`nlet g:auto_read = 1`ncall plug#end\" | Set-Content '%1'"
  echo vim-autoread plugin installed successfully.
) else (
  echo Error: %~nx1 not found. Please create it before running this script.
)

if exist "%LOCALAPPDATA%\nvim\nvim.exe" (
  call :install_autoread_plugin "%NEOVIM_CONFIG_PATH%"
) else (
  echo Neovim not found.
)

if exist "%USERPROFILE%\vim\vim82\vim.exe" (
  call :install_autoread_plugin "%VIM_CONFIG_PATH%"
) else (
  echo Vim not found.
)

echo Please run :PlugInstall in your Vim/Neovim to complete the plugin installation.


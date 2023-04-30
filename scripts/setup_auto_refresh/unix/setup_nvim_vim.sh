#!/bin/bash

# Check for Neovim and Vim
NEOVIM_CONFIG_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/nvim/init.vim"
VIM_CONFIG_PATH="$HOME/.vimrc"

install_autoread_plugin() {
  local config_file="$1"
  if [ -f "$config_file" ]; then
    echo "Installing vim-autoread plugin for $(basename $config_file)..."
    sed -i.bak '/call plug#begin/,/call plug#end/ { /vim-autoread/! { /call plug#end/i \
    Plug '\''djoshea/vim-autoread'\''\
    let g:auto_read = 1
    } }' "$config_file"
    echo "vim-autoread plugin installed successfully."
  else
    echo "Error: $(basename $config_file) not found. Please create it before running this script."
  fi
}

if command -v nvim >/dev/null 2>&1; then
  install_autoread_plugin "$NEOVIM_CONFIG_PATH"
else
  echo "Neovim not found."
fi

if command -v vim >/dev/null 2>&1; then
  install_autoread_plugin "$VIM_CONFIG_PATH"
else
  echo "Vim not found."
fi

echo "Please run :PlugInstall in your Vim/Neovim to complete the plugin installation."


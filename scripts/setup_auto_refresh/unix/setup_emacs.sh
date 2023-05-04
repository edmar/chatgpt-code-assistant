#!/bin/bash

EMACS_CONFIG_PATH="$HOME/.emacs"

if command -v emacs >/dev/null 2>&1; then
  if [ -f "$EMACS_CONFIG_PATH" ]; then
    echo "Configuring auto-revert-mode for Emacs..."
    echo -e "\n;; Enable auto-revert-mode\n(global-auto-revert-mode 1)" >> "$EMACS_CONFIG_PATH"
    echo "Emacs auto-revert-mode enabled."
  else
    echo "Error: .emacs not found. Please create it before running this script."
  fi
else
  echo "Emacs not found."
fi


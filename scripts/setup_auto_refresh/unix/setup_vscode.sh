#!/bin/bash

if command -v code >/dev/null 2>&1; then
  echo "Installing Auto-Refresh extension for VSCode..."
  code --install-extension "blackmist.LinkExternalEditor"
  echo "VSCode Auto-Refresh extension installed."
else
  echo "VSCode not found."
fi


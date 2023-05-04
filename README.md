# ChatGPT Code Assistant Plugin

As an avid coder, I embarked on a personal experiment to enhance my coding experience and boost my productivity. I found ChatGPT to be a valuable tool, but copying and pasting generated code into my editor often proved inconvenient and disrupted my creative flow.

I also faced challenges due to ChatGPT's inability to access my local file system and external documentation, as it couldn't utilize my current project's code as context. This meant I had to manually copy my code to the website for further generation.

To overcome these limitations, I decided to create the ChatGPT Code Assistant Plugin. By granting ChatGPT access to both my local file system and the internet, it can now effortlessly:

- Reference online documentation to provide accurate API calls and avoid guesswork.
- Incorporate the code from my current project as context, generating more relevant and coherent suggestions.
- Read and utilize files within my project to improve overall code integration.
- Directly write to files in my project, streamlining the coding process and eliminating the need for manual copy-pasting.

Through this personal experiment, I have experienced the enhanced capabilities of the ChatGPT Code Assistant Plugin and revolutionized the way I code. I hope others can also benefit from this solution and transform their coding journeys.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the following command to start the server:

```bash
uvicorn main:app --reload
```

Now, use ngrok to expose the server to the internet.
Ngrok is needed because the chatgpt plugins requires an https url to work.

```bash
ngrok http 8000
```

![ngrok](ngrok.png)

Use the ngrok url to set the server url in the plugin settings.

![plugin settings](add-plugin.png)

Here is a demo of the plugin in action:

![demo](demo.png)



## Auto-refresh Setup

This section provides instructions for setting up your text editor to automatically refresh when a file is updated by the Plugin. You can either use the provided scripts, or follow the manual configuration steps for your platform and editor.

### Quick Setup Scripts

Run the appropriate script for your platform and editor:

##### Neovim and Vim

- Linux and macOS: `./scripts/setup_auto_refresh/unix/setup_nvim_vim.sh`
- Windows: `./scripts/windows/setup_auto_refresh/setup_nvim_vim.bat`

##### Emacs

- Linux and macOS: `./scripts/setup_auto_refresh/unix/setup_emacs.sh`
- Windows: `./scripts/setup_auto_refresh/windows/setup_emacs.bat`

#### Visual Studio Code

- Linux and macOS: `./scripts/setup_auto_refresh/setup_vscode.sh`
- Windows: `./scripts/setup_auto_refresh/setup_vscode.bat`

These scripts will automatically configure your text editor for auto-refresh functionality when the ChatGPT Plugin "Code Assistant" updates a file.


### Manual Configuration

#### Neovim

1. Install the vim-plug plugin manager if you haven't already by following the instructions [here](https://github.com/junegunn/vim-plug).
2. Add the following lines to your `init.vim` configuration file (usually located in `~/.config/nvim/init.vim`):

   ```vim
   call plug#begin()
   Plug 'djoshea/vim-autoread'
   call plug#end()

   let g:auto_read = 1
   ```

3. Save the file and run `:PlugInstall` in Neovim.

#### Vim

1. Install the vim-plug plugin manager if you haven't already by following the instructions [here](https://github.com/junegunn/vim-plug).
2. Add the following lines to your `vimrc` configuration file (usually located in `~/.vimrc`):

   ```vim
   call plug#begin()
   Plug 'djoshea/vim-autoread'
   call plug#end()

   let g:auto_read = 1
   ```

3. Save the file and run `:PlugInstall` in Vim.

#### Emacs

1. Install the `auto-revert-mode` package by running `M-x package-install RET auto-revert-mode RET`.
2. Add the following line to your Emacs configuration file (usually located in `~/.emacs.d/init.el` or `~/.emacs`):

   ```emacs-lisp
   (global-auto-revert-mode 1)
   ```

3. Save the file and restart Emacs.

#### Visual Studio Code

1. Open Visual Studio Code.
2. Go to the Extensions view by clicking on the square icon in the Activity Bar on the side of the window or by pressing `Ctrl+Shift+X`.
3. Search for "Auto Refresh" by Gruntfuggly.
4. Click the Install button to install the extension.
5. After installation, open the settings for the extension by clicking the gear icon next to the extension in the Extensions view.
6. Enable the "Auto Refresh: Enabled" setting by checking the box.

With these configurations, your editor should automatically refresh when a file is updated by the Plugin. 

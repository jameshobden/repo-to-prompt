# README for `prompt.py`

## Overview

`prompt.py` is a free, open-source tool inspired by the functionality of commercial directory-to-prompt generators.

This script provides a similar experience to paid tools, but is independently developed and freely available.

`prompt.py` is a Python script that generates a structured representation of file and directory contents, suitable for use in prompts (e.g., for AI assistants like Grok). It creates a `<file_map>` section showing the directory structure and a `<file_contents>` section containing the readable contents of text-based files. The output is copied to the clipboard for easy use.

## Features

-   Builds a tree-like file map of directories or individual files.
-   Extracts and formats the contents of text files (e.g., `.py`, `.txt`, `.json`).
-   Ignores common irrelevant files and directories (e.g., `.git`, `node_modules`, `.pyc`).
-   Handles JSON files with proper formatting.
-   Skips binary files (e.g., images, PDFs) with a placeholder `[Binary file]`.
-   Copies the output to the macOS clipboard using `pbcopy`.

## Requirements

-   Python 3.x
-   macOS (for clipboard integration via `pbcopy`)
-   No additional Python packages required (uses standard library).

## Usage

Run the script from the command line with one or more file or directory paths as arguments:

```bash
python3 prompt.py /path/to/file_or_directory
```

-   The script processes the provided paths, generates the file map and contents, and copies the result to the clipboard.
-   If a path doesn’t exist or no paths are provided, it will exit with an error message.

## Output Format

The output consists of two sections:

1. `<file_map>`: A tree-like structure of the files and directories.
2. `<file_contents>`: The readable contents of text files, wrapped in code blocks.

## Ignored Patterns

The script skips files and directories matching common patterns, such as:

-   `.git`, `node_modules`, `__pycache__`
-   `.DS_Store`, `.pyc`, `.exe`
-   See `IGNORE_PATTERNS` in the script for the full list.

## Logging

The script uses Python’s `logging` module at the `DEBUG` level to log its operations. Logs are output to the console by default.

---

# Instructions: Using `prompt.py` with Automator as a Right-Click Service

Here’s how to set up `prompt.py` as a macOS service using Automator, so you can right-click files or folders in Finder and generate the prompt directly.

### Step 1: Prepare the Script

1. Save `prompt.py` in a convenient location, e.g., `/Users/yourusername/bin/prompt.py`.
2. Ensure it’s executable:

    ```bash
    chmod +x /Users/yourusername/bin/prompt.py
    ```

### Step 2: Create the Automator Service

1. Open **Automator** (search for it in Spotlight).
2. Choose **File > New** and select **Service** (or **Quick Action** on macOS Mojave and later).
3. Configure the service:
    - Set **Service receives selected** to **Files or Folders** in **Finder**.
    - Check **Output replaces selected text** (optional, but not critical here).
4. Add a **Run Shell Script** action:
    - Drag **Run Shell Script** from the left sidebar (or search for it).
    - Set **Shell** to `/bin/bash`.
    - Set **Pass input** to **as arguments**.
5. Enter the following script in the text box:

    ```bash
    /usr/bin/python3 "/Users/yourusername/bin/prompt.py" "$@"
    ```

    - Replace `/Users/yourusername/bin/prompt.py` with the actual path to your script.

6. Save the service:
    - Go to **File > Save** and name it something like `Generate Prompt`.

### Step 3: Test the Service

1. In Finder, right-click a file or folder.
2. Look for **Generate Prompt** under **Services** in the context menu (or under **Quick Actions** on newer macOS versions).
3. Select it, and the script will run, copying the output to your clipboard.
4. Paste the result (e.g., in a text editor or chat) to verify it works.

### Step 4: Optional Adjustments

-   **Permissions**: If you encounter permission issues, ensure `prompt.py` and the Automator workflow have appropriate permissions.
-   **Keyboard Shortcut**: To assign a shortcut:
    -   Open **System Preferences > Keyboard > Shortcuts > Services**.
    -   Find `Generate Prompt` under **Files and Folders**, and assign a key combination.

## Notes

-   The service will process all selected files/folders when you right-click multiple items.
-   If the script doesn’t work, check the path to `python3` (use `which python3` in Terminal to confirm) and adjust the shell script accordingly.

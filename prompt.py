#!/usr/bin/env python3
import os
import sys
import json
import mimetypes
from pathlib import Path
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Files and directories to ignore
IGNORE_PATTERNS = {
    '.DS_Store', '.Spotlight-V100', '.Trashes', '.fseventsd', '.AppleDouble',
    'node_modules', 'vendor', '.git', '.svn', '.hg', 'dist',
    '__pycache__', '.pyc', '.pyo', '.pyd', '.cache', '.idea', '.vscode', '.pytest_cache',
    '.o', '.obj', '.so', '.dylib', '.dll', '.exe', '.env'
}

def should_ignore(path):
    """Check if a path should be ignored"""
    path = str(path)
    return any(pattern in path.split(os.sep) for pattern in IGNORE_PATTERNS)

def get_file_contents(file_path):
    """Read contents of text-based files, return appropriate content"""
    file_path = Path(file_path)
    logger.debug(f"Processing file: {file_path}")
    
    if should_ignore(file_path):
        logger.debug(f"Ignoring file: {file_path}")
        return None
    
    file_type, _ = mimetypes.guess_type(str(file_path))
    is_binary = file_type and ('image' in file_type or 'binary' in file_type or 'pdf' in file_type)
    
    if is_binary:
        logger.debug(f"Binary file detected: {file_path}")
        return "[Binary file]"
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"Successfully read content from {file_path}, length: {len(content)}")
            if file_path.suffix == '.json':
                try:
                    parsed = json.loads(content)
                    return json.dumps(parsed, indent=4)
                except json.JSONDecodeError:
                    logger.debug(f"JSON parsing failed for {file_path}, using raw content")
                    return content
            return content
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        return ""

def build_file_map(paths):
    """Build the file structure map for multiple paths"""
    map_lines = ["<file_map>\n"]
    
    for path in paths:
        path = Path(path)
        logger.debug(f"Mapping path: {path}")
        map_lines.append(f"{path}\n")
        
        if path.is_dir():
            for root, dirs, files in os.walk(path, topdown=True):
                if should_ignore(root):
                    dirs[:] = []
                    continue
                    
                rel_root = Path(root).relative_to(path)
                level = len(rel_root.parts)
                
                for dir_name in sorted(dirs):
                    if not should_ignore(os.path.join(root, dir_name)):
                        indent = "    " * level
                        map_lines.append(f"{indent}├── {dir_name}\n")
                
                for file_name in sorted(files):
                    if not should_ignore(os.path.join(root, file_name)):
                        indent = "    " * level
                        map_lines.append(f"{indent}├── {file_name}\n")
        else:
            map_lines.append(f"├── {path.name}\n")
    
    map_lines.append("</file_map>\n")
    return "".join(map_lines)

def build_file_contents(paths):
    """Build the file contents section for multiple paths"""
    content_lines = ["<file_contents>\n"]
    
    for path in paths:
        path = Path(path)
        logger.debug(f"Processing path for contents: {path}")
        
        if path.is_dir():
            # Walk through all files in the directory recursively
            for root, _, files in os.walk(path):
                if should_ignore(root):
                    logger.debug(f"Skipping ignored directory: {root}")
                    continue
                    
                root_path = Path(root)
                for file_name in sorted(files):
                    file_path = root_path / file_name
                    if should_ignore(file_path):
                        logger.debug(f"Skipping ignored file: {file_path}")
                        continue
                        
                    # Calculate relative path from the original input path
                    rel_path = file_path.relative_to(path)
                    content = get_file_contents(file_path)
                    if content is not None:
                        content_lines.append(f"File: {rel_path}\n")
                        content_lines.append(f"```\n{content}\n```\n\n")
                    else:
                        logger.debug(f"No content returned for {file_path}")
        else:
            # Handle single file
            content = get_file_contents(path)
            if content is not None:
                rel_path = path.name  # Just the filename for single files
                content_lines.append(f"File: {rel_path}\n")
                content_lines.append(f"```\n{content}\n```\n\n")
            else:
                logger.debug(f"No content returned for single file {path}")
    
    content_lines.append("</file_contents>")
    return "".join(content_lines)

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

def main():
    if len(sys.argv) < 2:
        print("Please provide at least one file or folder path")
        sys.exit(1)
    
    paths = sys.argv[1:]
    valid_paths = [p for p in paths if os.path.exists(p)]
    
    if not valid_paths:
        print("No valid paths provided")
        sys.exit(1)
    
    logger.debug(f"Valid paths: {valid_paths}")
    file_map = build_file_map(valid_paths)
    file_contents = build_file_contents(valid_paths)
    prompt = f"{file_map}\n{file_contents}"
    
    logger.debug(f"Generated prompt:\n{prompt}")
    copy_to_clipboard(prompt)
    print("Prompt copied to clipboard")

if __name__ == "__main__":
    main()
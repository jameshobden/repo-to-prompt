#!/usr/bin/env python3
import os
import sys
import json
import mimetypes
from pathlib import Path
import subprocess
import logging
from fnmatch import fnmatch

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Files and directories to ignore (original set)
IGNORE_PATTERNS = {
    '.DS_Store', '.Spotlight-V100', '.Trashes', '.fseventsd', '.AppleDouble',
    'node_modules', 'vendor', '.git', '.svn', '.hg', 'dist',
    '__pycache__', '.pyc', '.pyo', '.pyd', '.cache', '.idea', '.vscode', '.pytest_cache',
    '.o', '.obj', '.so', '.dylib', '.dll', '.exe', '.env'
}

class GitIgnore:
    """Handle .gitignore pattern matching"""
    def __init__(self):
        self.patterns = []

    def load(self, gitignore_path):
        """Load patterns from a .gitignore file"""
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.patterns.append(line)
            logger.debug(f"Loaded .gitignore patterns from {gitignore_path}: {self.patterns}")
        except Exception as e:
            logger.debug(f"No .gitignore found or error reading {gitignore_path}: {str(e)}")

    def matches(self, path, root):
        """Check if a path matches any gitignore pattern"""
        rel_path = str(Path(path).relative_to(root))
        for pattern in self.patterns:
            if pattern.startswith('/'):
                pattern = pattern[1:]
            if fnmatch(rel_path, pattern) or fnmatch(os.path.basename(path), pattern):
                return True
        return False

def should_ignore(path, gitignore_cache=None):
    """Check if a path should be ignored based on static patterns and .gitignore"""
    path = str(path)
    
    # Check static ignore patterns
    if any(pattern in path.split(os.sep) for pattern in IGNORE_PATTERNS):
        return True
    
    # Check .gitignore patterns if cache is provided
    if gitignore_cache and path in gitignore_cache:
        return gitignore_cache[path]
        
    return False

def get_file_contents(file_path, gitignore_cache=None):
    """Read contents of text-based files, return appropriate content"""
    file_path = Path(file_path)
    logger.debug(f"Processing file: {file_path}")
    
    if should_ignore(file_path, gitignore_cache):
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
    gitignore_cache = {}
    
    for path in paths:
        path = Path(path)
        logger.debug(f"Mapping path: {path}")
        map_lines.append(f"{path}\n")
        
        if path.is_dir():
            # Load .gitignore if present
            gitignore = GitIgnore()
            gitignore_path = path / '.gitignore'
            if gitignore_path.exists():
                gitignore.load(gitignore_path)
            
            for root, dirs, files in os.walk(path, topdown=True):
                root_path = Path(root)
                if should_ignore(root, gitignore_cache):
                    dirs[:] = []
                    continue
                
                # Cache gitignore matches for this directory
                for item in dirs + files:
                    full_path = root_path / item
                    if gitignore.patterns and gitignore.matches(full_path, path):
                        gitignore_cache[str(full_path)] = True
                    else:
                        gitignore_cache[str(full_path)] = should_ignore(full_path)
                
                rel_root = root_path.relative_to(path)
                level = len(rel_root.parts)
                
                for dir_name in sorted(dirs):
                    dir_path = os.path.join(root, dir_name)
                    if not gitignore_cache.get(dir_path, False):
                        indent = "    " * level
                        map_lines.append(f"{indent}├── {dir_name}\n")
                
                for file_name in sorted(files):
                    file_path = os.path.join(root, file_name)
                    if not gitignore_cache.get(file_path, False):
                        indent = "    " * level
                        map_lines.append(f"{indent}├── {file_name}\n")
        else:
            map_lines.append(f"├── {path.name}\n")
    
    map_lines.append("</file_map>\n")
    return "".join(map_lines)

def build_file_contents(paths):
    """Build the file contents section for multiple paths"""
    content_lines = ["<file_contents>\n"]
    gitignore_cache = {}
    
    for path in paths:
        path = Path(path)
        logger.debug(f"Processing path for contents: {path}")
        
        if path.is_dir():
            # Load .gitignore if present
            gitignore = GitIgnore()
            gitignore_path = path / '.gitignore'
            if gitignore_path.exists():
                gitignore.load(gitignore_path)
            
            for root, _, files in os.walk(path):
                root_path = Path(root)
                if should_ignore(root, gitignore_cache):
                    logger.debug(f"Skipping ignored directory: {root}")
                    continue
                
                # Cache gitignore matches for this directory
                for file_name in files:
                    full_path = root_path / file_name
                    if gitignore.patterns and gitignore.matches(full_path, path):
                        gitignore_cache[str(full_path)] = True
                    else:
                        gitignore_cache[str(full_path)] = should_ignore(full_path)
                
                for file_name in sorted(files):
                    file_path = root_path / file_name
                    if not gitignore_cache.get(str(file_path), False):
                        rel_path = file_path.relative_to(path)
                        content = get_file_contents(file_path, gitignore_cache)
                        if content is not None:
                            content_lines.append(f"File: {rel_path}\n")
                            content_lines.append(f"```\n{content}\n```\n\n")
                        else:
                            logger.debug(f"No content returned for {file_path}")
        else:
            content = get_file_contents(path, gitignore_cache)
            if content is not None:
                rel_path = path.name
                content_lines.append(f"File: {rel_path}\n")
                content_lines.append(f"```\n{content}\n```\n\n")
    
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
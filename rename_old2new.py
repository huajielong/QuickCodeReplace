import os
import re
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Union
from concurrent.futures import ThreadPoolExecutor
from words_replacer import WordsReplacer, read_config_file

# Global replacement rules for euv to xuv conversion
REPLACEMENT_RULES = {
    'Hello world': 'hello everyone',
    'Hello': 'hello',
    'Cat': 'Dog'
}

def apply_replacement_rules(text: str) -> str:
    """
    Apply all replacement rules to the given text
    
    Args:
        text: The text to apply replacements to
        
    Returns:
        The text with all replacements applied
    """
    result = text
    for old, new in REPLACEMENT_RULES.items():
        result = result.replace(old, new)
    return result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_current_script_abspath():
    return os.path.abspath(__file__)
    
def get_current_script_basename():
    script_path = get_current_script_abspath()
    script_basename = os.path.basename(script_path)
    return script_basename

def get_project_root():
    current_dir = os.path.dirname(get_current_script_abspath())
    while True:
        git_dir = os.path.join(current_dir, '.git')
        if os.path.exists(git_dir):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return None

def get_rename_filepaths(code_path: Union[str, Path]):
    """
    Scan code directory and generate file renaming mapping
    
    Args:
        code_path: Code directory path
    
    Returns:
        Dictionary containing old file paths and new file paths {old_path: new_path}
    """
    SKIP_FILES = {
        get_current_script_basename(),
        'launch.json',
        'Doxyfile'
    } 

    rename_files_dict = {}
    rename_dirs_dict = {}
    code_path = Path(code_path)
    
    def should_process(file_path: Path) -> bool:
        """Determine if the file should be processed"""
        return (
            '.git' not in file_path.parts
            and file_path.name not in SKIP_FILES
        )

    # Traverse all files
    for file_path in code_path.rglob('*'):
        if not should_process(file_path):
            continue
        
        new_base = abbreviate_words(file_path.stem)
        new_name = new_base + file_path.suffix
        
        
        if new_name != file_path.name:
            old_path = str(file_path)
            new_path = str(file_path.with_name(new_name))
            if  file_path.is_file():
                rename_files_dict[old_path] = new_path
            else:
                rename_dirs_dict[old_path] = new_path
            logger.info(f'Will rename to: {new_name}')
            
    rename_files_dict = dict(sorted(rename_files_dict.items(), key=lambda item: (-len(str(item[1])), item[1])))
    rename_dirs_dict = dict(sorted(rename_dirs_dict.items(), key=lambda item: (-len(str(item[1])), item[1])))
    return rename_files_dict,rename_dirs_dict

def abbreviate_words(base): 
    result = base
    for key, value in REPLACEMENT_RULES.items():
        if key in result:
            result = re.sub(key, value, result)    
    return result

def rename_context(code_path,rename_files_dict, rename_dirs_dict):
    
    max_workers = 20     # Use 20 worker threads
    buffer_size = 16384  # 16KB buffer size
    
    file_words_dict = {}
    for key, value in rename_files_dict.items():
        file_words_dict[os.path.basename(key)] = os.path.basename(value)
        
    fileReplacer = WordsReplacer(
        code_path=code_path,
        words_dict=file_words_dict,
        max_workers=max_workers, 
        buffer_size=buffer_size
    )
    fileReplacer.run()
    
    dir_words_dict = {}
    for key, value in rename_dirs_dict.items():
        old_rel_path = os.path.relpath(key, os.path.dirname(code_path))
        new_rel_path = os.path.relpath(value, os.path.dirname(code_path))
        dir_words_dict[old_rel_path] = apply_replacement_rules(new_rel_path)
    
    # Add the base replacement rules
    dir_words_dict.update(REPLACEMENT_RULES)

    dirReplacer = WordsReplacer(
        code_path=code_path,
        words_dict=dir_words_dict,
        max_workers=max_workers, 
        buffer_size=buffer_size
    )
    dirReplacer.run()

def rename_single(old_path: str, new_path: str) -> bool:
    """Rename a single file
    
    Args:
        old_path: Original file path
        new_path: New file path
        
    Returns:
        bool: True if rename succeeded, False otherwise
    """
    try:
        if not os.path.exists(old_path):
            logger.error(f"Source file not found: {old_path}")
            return False
            
        # Ensure target directory exists
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        
        # Remove target file if exists
        if os.path.exists(new_path):
            os.remove(new_path)
            
        os.rename(old_path, new_path)
        logger.info(f"Successfully renamed: {old_path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to rename {old_path}: {str(e)}")
        return False
                
def batch_rename_filename(code_path: str, rename_files: Dict[str, str], max_workers: int = 4) -> None:
    """Multi-threaded batch file renaming
    
    Args:
        code_path: Source code root directory
        rename_files: Rename mapping dictionary {old_path: new_path}
        max_workers: Maximum number of worker threads
    """
    
    # Convert to absolute paths
    code_path = os.path.abspath(code_path)
    
    # Create absolute path mapping
    rename_map = {
        os.path.join(code_path, old): os.path.join(code_path, new)
        for old, new in rename_files.items()
    }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda x: rename_single(x[0], x[1]), 
            rename_map.items()
        ))
    
    # Report statistics
    success = sum(results)
    failed = len(results) - success
    logger.info(f"Rename completed: {success} succeeded, {failed} failed")

def serial_rename_dirname(code_path: str, rename_dirs: Dict[str, str]) -> None:
    try:
        recode_path = apply_replacement_rules(code_path)
        
        if recode_path != code_path:
            rename_dirs[code_path] = recode_path 
             
        for old,new in rename_dirs.items():
            if old != new:
                if os.path.exists(old):
                    os.rename(old, new)
                    logger.info(f"Successfully renamed: {old} -> {new}")
        
    except Exception as e:
        logger.error(f"Failed to rename dirname: {str(e)}")
        return False           
 
if __name__ == "__main__":
    
    # Create a parser
    parser = argparse.ArgumentParser(description='Rename code files')
    parser.add_argument('code_path', type=str, help='Path to the code directory')
    parser.add_argument('--record_file', type=str, help='File to store the rename result')
    
    args = parser.parse_args()
    logger.info(f"input: {args}")
    
    code_path = os.path.abspath(args.code_path) 

    if not os.path.exists(code_path):
        logger.error(f"Error: code_path={args.code_path} not exist")
        sys.exit(-1)
    
    if not os.path.isdir(code_path):
        logger.error(f"Error: code_path={args.code_path} not directory")
        sys.exit(-2)

    project_root = get_project_root()
    
    rename_files_dict, rename_dirs_dict= get_rename_filepaths(code_path)
    
    rename_context(code_path, rename_files_dict, rename_dirs_dict)
    
    batch_rename_filename(code_path,rename_files_dict)
    serial_rename_dirname(code_path,rename_dirs_dict)
    
    sys.exit(0) 
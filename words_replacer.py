import os
import re
import sys
import logging
import argparse
import subprocess
from io import StringIO
from pathlib import Path
from typing import Dict, Tuple
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class WordsReplacer:
    def __init__(self, code_path: str, words_dict: dict, max_workers: int = None, buffer_size: int = 8192):
        """
        Initialize the word replacer
        :param code_path: Source code directory path
        :param words_dict: Replacement dictionary {old_word: new_word}
        :param max_workers: Number of CPU worker threads
        :param buffer_size: Read buffer size
        """
        self.code_path = Path(code_path)
        self.words_dict = words_dict
        self.max_workers = max_workers
        self.buffer_size = buffer_size

    def _get_file_encoding(self, file_path: str) -> Tuple[str, str]:
        """Get file encoding"""
        try:
            # Check if we're on Windows
            if os.name == 'nt':
                # On Windows, we'll try to open the file as text
                # and use utf-8 as default encoding
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Try to read a small portion to test encoding
                        f.read(100)
                    return file_path, 'utf-8'
                except UnicodeDecodeError:
                    # If utf-8 fails, try with utf-8-sig (for files with BOM)
                    try:
                        with open(file_path, 'r', encoding='utf-8-sig') as f:
                            f.read(100)
                        return file_path, 'utf-8-sig'
                    except UnicodeDecodeError:
                        # If both fail, it might be a binary file
                        return file_path, 'binary'
            else:
                # On Unix/Linux, use the file command as before
                output = subprocess.check_output(
                    ['file', '-i', file_path], 
                    stderr=subprocess.STDOUT
                ).decode().strip()
                
                if match := re.search(r'charset=([^\s,]+)', output):
                    encoding = match.group(1)
                elif 'application/octet-stream' in output:
                    encoding = 'binary'
                else:
                    encoding = None
                    
                return file_path, encoding
        except Exception as e:
            logger.error(f"Failed to get file encoding {file_path}: {str(e)}")
            # Fall back to utf-8 for text files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(100)
                return file_path, 'utf-8'
            except:
                return file_path, None

    def _collect_text_files(self) -> Dict[str, str]:
        """Collect all non-binary text files and their encodings"""
        all_files = {}
        file_paths = [str(f) for f in self.code_path.rglob('*') if f.is_file()]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(self._get_file_encoding, file_paths)
            
            for file_path, encoding in results:
                if encoding not in ('binary', None):
                    all_files[file_path] = encoding
        
        return all_files

    def _process_file(self, file_info: Tuple[str, str]):
        """Process replacement operations for a single file"""
        file_path, encoding = file_info
        try:
            # Use StringIO as buffer
            output_buffer = StringIO()
            content_changed = False

            # Read file content using buffer
            with open(file_path, 'r', encoding=encoding, buffering=self.buffer_size) as f:
                while chunk := f.read(self.buffer_size):
                    # Replace words in current chunk
                    new_chunk = chunk
                    for old_word, new_word in self.words_dict.items():
                        if old_word in new_chunk:
                            new_chunk = new_chunk.replace(old_word, new_word)
                            content_changed = True
                    
                    # Write to buffer
                    output_buffer.write(new_chunk)

            # Only write to file if content has changed
            if content_changed:
                with open(file_path, 'w', encoding=encoding, buffering=self.buffer_size) as f:
                    output_buffer.seek(0)
                    # Write all content at once
                    f.write(output_buffer.getvalue())
                logger.info(f"Processed file: {file_path}")
                
            # Clean up buffer
            output_buffer.close()
                
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")

    def run(self):
        """Execute replacement operations"""
        text_files = self._collect_text_files()
        logger.info(f"Found {len(text_files)} text files to process")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self._process_file, text_files.items())

def get_current_script_abspath():
    return os.path.abspath(__file__)


def read_config_file(cfg_file_path):
    config_dict = {}
    try:
        with open(cfg_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Remove leading and trailing whitespace from the line
                line = line.strip()
                # Skip empty lines and comment lines
                if not line or line.startswith('#'):
                    continue
                # Split the line by the first space
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    key, value = parts
                    config_dict[key] = value[0].upper() + value[1:]
    except FileNotFoundError:
        logger.error(f"Error: File {cfg_file_path} not found.")
    except Exception as e:
        logger.error(f"An unknown error occurred: {e}")
    return config_dict

if __name__ == "__main__":
    
    # Create a parser
    parser = argparse.ArgumentParser(description='replace words in code')
    parser.add_argument('code_path', type=str, help='Path to the code directory')
    parser.add_argument('--config_file', type=str, help='Config file stored the old and new words')

    args = parser.parse_args()
    logger.info(f"input: {args}")
    
    code_path = os.path.abspath(args.code_path)
    
    if not os.path.exists(code_path):
        logger.error(f"Error: code_path={args.code_path} not exist")
        sys.exit(-1)
    
    if not os.path.isdir(code_path):
        logger.error(f"Error: code_path={args.code_path} not directory")
        sys.exit(-2)
 
    words_dict = {}
    # words_dict['Mentor'] = 'Leda'
    # words_dict['CALIBRE'] = 'LePV'
    # words_dict['calibRE'] = 'lepvRE'
    # words_dict['calibre'] = 'lepv'
    # words_dict['tsmc'] = 'txmc'
    # words_dict['Tsmc'] = 'txmc'
    # words_dict['TSMC'] = 'TXMC' 
    words_dict['symopcmodes_xuv.o'] = 'symopcmodes_euv.o'
    words_dict['cuda_wrap_xuv_sim.o'] = 'cuda_wrap_euv_sim.o'
    if args.config_file and os.path.isfile(args.config_file):
        words_dict = words_dict = read_config_file(args.config_file)


    max_workers = 20     # Use 20 worker threads
    buffer_size = 16384  # 16KB buffer size
    replacer = WordsReplacer(
        code_path=code_path,
        words_dict=words_dict,
        max_workers=max_workers, 
        buffer_size=buffer_size
    )
    replacer.run()
    
    logger.info(f"Execute {get_current_script_abspath()} successfully")
    sys.exit(0) 
                        
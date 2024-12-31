import os
import unicodedata
import blake3
import logging

# Configure logging
logging.basicConfig(filename='file_operations.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def count_files(directory):
    logging.debug(f"Counting files in directory: {directory}")
    file_count = sum([len(files) for r, d, files in os.walk(directory)])
    logging.info(f"Counted {file_count} files in directory: {directory}")
    return file_count

def pause_resume_operations():
    logging.debug("Pause/Resume operation called")
    pass

def restart_operations():
    logging.debug("Restart operation called")
    pass

def hash_file(path):
    logging.debug(f"Hashing file: {path}")
    hasher = blake3.blake3()
    try:
        with open(path, 'rb') as file:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        file_hash = hasher.hexdigest()
        logging.info(f"Hashed file {path}: {file_hash}")
        return file_hash
    except Exception as e:
        logging.error(f"Error hashing file {path}: {e}")
        raise

def normalize_path(file_path):
    logging.debug(f"Normalizing path: {file_path}")
    try:
        normalized_filename = unicodedata.normalize('NFKD', os.path.basename(file_path)).encode('ascii', 'ignore').decode('ascii')
        normalized_filepath = os.path.join(os.path.dirname(file_path), normalized_filename)
        logging.info(f"Normalized path {file_path} to {normalized_filepath}")
        return normalized_filepath
    except Exception as e:
        logging.error(f"Error normalizing path {file_path}: {e}")
        raise

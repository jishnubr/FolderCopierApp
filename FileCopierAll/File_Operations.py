import os
import unicodedata
import blake3

def count_files(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])

def pause_resume_operations():
    pass

def restart_operations():
    pass

def hash_file(path):
    hasher = blake3.blake3()
    with open(path, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def normalize_path(file_path):
    normalized_filename = unicodedata.normalize('NFKD', os.path.basename(file_path)).encode('ascii', 'ignore').decode('ascii')
    normalized_filepath = os.path.join(os.path.dirname(file_path), normalized_filename)
    return normalized_filepath

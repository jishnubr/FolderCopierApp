import os
import unicodedata
import blake3

def hash_file(path):
    """
    Calculates the BLAKE3 hash of a file.
    """
    hasher = blake3.blake3()
    try:
        with open(path, 'rb') as file:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing file {path}: {e}")
        return None

def normalize_path(file_path):
    """
    Normalizes a file path to handle unicode characters consistently.
    """
    normalized_filename = unicodedata.normalize('NFKD', os.path.basename(file_path)).encode('ascii', 'ignore').decode('ascii')
    # Get the path to the file
    normalized_filepath = os.path.join(os.path.dirname(file_path), normalized_filename)
    return normalized_filepath

def count_files(directory):
    """
    Counts the total number of files in a directory recursively.
    """
    return sum([len(files) for r, d, files in os.walk(directory)])

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"

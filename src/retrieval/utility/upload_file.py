import os


def save_file_to_disk(contents, dir_name, filename):
    save_path = f"{dir_name}/PDF/{filename}"
    with open(save_path, "wb") as f:
        f.write(contents)
    

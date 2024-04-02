def process_download(file_name):
    if file_name == "":
        return False

    with open(f"static/LAW/PDF/{file_name}", "rb") as f:
        pdf = f.read()
        return pdf

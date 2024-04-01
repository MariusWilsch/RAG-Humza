def process_download(file_name, CUR_PERSIST_DIR):
    if file_name == "":
        return False

    with open(f"{CUR_PERSIST_DIR}/PDF/{file_name}", "rb") as f:
        pdf = f.read()
        return pdf

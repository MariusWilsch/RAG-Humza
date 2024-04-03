import os, json


def save_file_to_disk(uploaded_file):
    save_path = f"data/RAG_LAW/PDF/{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())
    uploaded_file.seek(0)
    return save_path


def save_as_json(docs, filename):
    os.makedirs("manual_verification/extracted", exist_ok=True)
    doc_dicts = [doc.dict() for doc in docs]
    with open(f"manual_verification/extracted/{filename}.json", "w") as f:
        json.dump(doc_dicts, f, indent=4)

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.schema import Document
import os


def call_pyMu_on_folder(folder_path: str):
    docs: Document = []
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            docs.extend(pyMuPDFLoader(os.path.join(folder_path, file)))
    return docs


def pyMuPDFLoader(path):
    loader = PyMuPDFLoader(path)
    docs = loader.load()
    return docs

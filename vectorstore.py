import os
import shutil

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from config import EMBEDDING_MODEL, OLLAMA_BASE_URL, RAG_FILES_DIR, VECTOR_STORE_PATH


def _embeddings():
    return OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)


def load_documents():
    docs, paths = [], []
    processed_dir = os.path.join(RAG_FILES_DIR, 'processed')
    os.makedirs(processed_dir, exist_ok=True)

    for name in os.listdir(RAG_FILES_DIR):
        path = os.path.join(RAG_FILES_DIR, name)
        if not os.path.isfile(path):
            continue

        if name.lower().endswith('.pdf'):
            loader = PyPDFLoader(path)
        elif name.lower().endswith('.txt'):
            loader = TextLoader(path, autodetect_encoding=True)
        else:
            continue

        docs.extend(loader.load())
        paths.append(path)

    return docs, paths


def get_vectorstore():
    docs, paths = load_documents()

    store = Chroma(
        embedding_function=_embeddings(),
        persist_directory=VECTOR_STORE_PATH,
    )

    if docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        splits = text_splitter.split_documents(docs)
        store.add_documents(splits)

        processed_dir = os.path.join(RAG_FILES_DIR, 'processed')
        for path in paths:
            shutil.move(path, os.path.join(processed_dir, os.path.basename(path)))

    return store

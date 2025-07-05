import os
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_DIR = "./chroma_db"

model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs
)


def load_and_ingest_file(file_path):
    print(f"Loading file: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in [".md", ".markdown"]:
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        loader = TextLoader(file_path)
    docs = loader.load()
    store_embeddings(docs, source_type="file", source_path=file_path)


def load_and_ingest_url(url):
    loader = WebBaseLoader(url)
    docs = loader.load()
    store_embeddings(docs, source_type="url", source_path=url)


def store_embeddings(docs, source_type="file", source_path=""):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    
    # Add metadata to each chunk
    for chunk in chunks:
        chunk.metadata["source_type"] = source_type
        chunk.metadata["source_path"] = source_path

    vectordb = Chroma(
        collection_name="docs_collection",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR,  # Where to save data locally, remove if not necessary
    )
    vectordb.add_documents(chunks)
    print(f"Stored {len(chunks)} chunks in VectorDB.")


def delete_embeddings_by_source(source_path):
    """Delete embeddings for a specific source file or URL"""
    try:
        vectordb = Chroma(
            collection_name="docs_collection",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR,
        )
        # Delete documents where source_path matches
        vectordb._collection.delete(where={"source_path": source_path})
        print(f"Deleted embeddings for source: {source_path}")
        return f"Deleted embeddings for: {source_path}"
    except Exception as e:
        print(f"Error deleting embeddings: {str(e)}")
        return f"Error deleting embeddings: {str(e)}"


def clear_database():
    """Clear all documents from the vector database"""
    try:
        vectordb = Chroma(
            collection_name="docs_collection",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR,
        )
        vectordb._collection.delete(where={})
        print("Database cleared successfully.")
        return "Database cleared successfully."
    except Exception as e:
        print(f"Error clearing database: {str(e)}")
        return f"Error clearing database: {str(e)}"


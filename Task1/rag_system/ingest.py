import os
import glob
import PyPDF2
import markdown
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from langchain.text_splitter import RecursiveCharacterTextSplitter

SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.md']

def extract_metadata(filepath):
    return {
        'filename': os.path.basename(filepath),
        'extension': os.path.splitext(filepath)[1]
    }

def read_pdf(filepath):
    text = ""
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            else:
                print(f"[Warning] Page {i} in {filepath} returned no text.")
    if not text.strip():
        print(f"[Warning] No extractable text found in {filepath}.")
    return text

def read_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def read_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return markdown.markdown(f.read())

def load_document(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        return read_pdf(filepath)
    elif ext == '.txt':
        return read_txt(filepath)
    elif ext == '.md':
        return read_md(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_document(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

def ingest_documents(folder, chroma_collection_name='rag_docs'):
    persist_directory = os.path.join(os.getcwd(), "chroma_db")
    os.makedirs(persist_directory, exist_ok=True)

    client = PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(chroma_collection_name)

    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    for ext in SUPPORTED_EXTENSIONS:
        for filepath in glob.glob(os.path.join(folder, f'*{ext}')):
            print(f"Processing {filepath}")
            text = load_document(filepath)
            if not text or not text.strip():
                print(f"[Warning] Skipping {filepath}: no text extracted.")
                continue
            metadata = extract_metadata(filepath)
            chunks = chunk_document(text)
            if not chunks:
                print(f"[Warning] No chunks created for {filepath}.")
                continue
            print(f"  {len(chunks)} chunks to embed and store.")
            embeddings = embedder.encode(chunks).tolist()
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    print(f"  [Info] Skipping empty chunk {i} in {filepath}.")
                    continue
                doc_id = f"{metadata['filename']}_{i}"
                collection.add(
                    documents=[chunk],
                    metadatas=[metadata],
                    ids=[doc_id],
                    embeddings=[embeddings[i]]
                )

    print("Ingestion complete and data saved to persistent ChromaDB.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RAG Ingestion Script")
    parser.add_argument('--folder', type=str, required=True, help='Folder containing documents')
    args = parser.parse_args()
    ingest_documents(args.folder)

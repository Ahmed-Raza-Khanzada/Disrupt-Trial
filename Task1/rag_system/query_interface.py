import os
import chromadb
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import chainlit as cl
import google.generativeai as genai
from engine import get_engine  

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_chroma_collection(name='rag_docs'):
    persist_directory = os.path.join(os.getcwd(), "chroma_db")
    os.makedirs(persist_directory, exist_ok=True)
    client = PersistentClient(path=persist_directory)
    return client.get_or_create_collection(name)

def get_or_create_whoosh_index(index_dir, schema):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
        return create_in(index_dir, schema)
    return open_dir(index_dir)

def expand_query(query):
    synonyms = {
        'error': ['bug', 'issue', 'fault'],
        'install': ['setup', 'configure', 'deploy']
    }
    expanded = [query]
    for word, syns in synonyms.items():
        if word in query:
            expanded.extend(syns)
    return ' '.join(expanded)

def hybrid_search(query, chroma_collection, whoosh_index, embedder, top_k=5):
    query_emb = embedder.encode([query]).tolist()[0]
    vector_results = chroma_collection.query(query_embeddings=[query_emb], n_results=top_k)
    vector_docs = vector_results.get("documents", [[]])[0]

    qp = QueryParser("content", schema=whoosh_index.schema)
    bm25_query = qp.parse(query)
    with whoosh_index.searcher() as searcher:
        bm25_results = searcher.search(bm25_query, limit=top_k)
        bm25_docs = [hit['content'] for hit in bm25_results]

    combined = list(set(vector_docs + bm25_docs))
    return combined

def confidence_score(results):
    return min(1.0, 0.5 + 0.1 * len(results))

@cl.on_message
async def main(message: cl.Message):
    query = message.content.strip()
    if not query:
        await cl.Message(content="Please enter a question.").send()
        return

    chroma_collection = get_chroma_collection()
    schema = Schema(doc_id=ID(stored=True), content=TEXT(stored=True))
    whoosh_index = get_or_create_whoosh_index('whoosh_index', schema)

    expanded_query = expand_query(query)
    results = hybrid_search(expanded_query, chroma_collection, whoosh_index, embedder)
    score = confidence_score(results)

    model = get_engine(0)

    if results:
        context = "\n\n".join(results)
        prompt = (
            f"You are an expert assistant. Use the following retrieved documents to answer the user's question.\n\n"
            f"Documents:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        )
        response = model.generate_content(prompt)
        answer = response.text if hasattr(response, 'text') else str(response)

        reply = (
            f"**Confidence:** {score:.2f}**\n\n"
            f"**Answer:**\n{answer}\n\n"
            f"---\n\n"
            f"**Context used:**\n{context}"
        )

    else:
        response = model.generate_content(query)
        answer = response.text if hasattr(response, 'text') else str(response)
        reply = f"**Confidence:** {score:.2f}\n\n**Answer:**\n{answer}"

    await cl.Message(content=reply).send()

import os
import re
import docx2txt
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL = "text-embedding-ada-002"

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = "ciberlexdb"

if index_name not in pc.list_indexes().names():
    pc.create_index(index_name, 
                    dimension=1536,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    ))

index = pc.Index(index_name)

def preprocess_text(text):
    return re.sub(r'\s+', ' ', text)

def process_word(file_path):
    text = docx2txt.process(file_path)
    text = preprocess_text(text)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_text(text)
    return documents

def create_embeddings(texts):
    embeddings_list = []
    for text in texts:
        res = client.embeddings.create(model=MODEL, input=text)
        embeddings_list.append(res.data[0].embedding)
    return embeddings_list

def upsert_embeddings_to_pinecone(index, embeddings, ids, texts, filename):
    vectors = []
    for id, embedding, text in zip(ids, embeddings, texts):
        metadata = {
            "filename": filename,
            "chunk_index": id.split('_')[-1],
            "text": text[:1000]  # Store first 1000 chars as metadata
        }
        vectors.append((id, embedding, metadata))
    index.upsert(vectors=vectors)

def process_directory(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".docx"):
            file_path = os.path.join(directory_path, filename)
            print(f"Processing file: {file_path}")
            
            texts = process_word(file_path)
            embeddings = create_embeddings(texts)
            
            ids = [f"{filename}_{i}" for i in range(len(texts))]
            
            upsert_embeddings_to_pinecone(index, embeddings, ids, texts, filename)
            
            print(f"Completed processing {filename}")

if __name__ == "__main__":
    directory_path = "documents3"  # Replace with your actual directory path
    process_directory(directory_path)
    print("All documents processed and embeddings uploaded to Pinecone.")
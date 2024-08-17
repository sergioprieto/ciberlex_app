import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

class PineconeClient:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index_name = os.getenv('PINECONE_INDEX_NAME')
        
        # Check if the index exists, if not, create it
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # Assuming you're using OpenAI's ada-002 model
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        self.index = self.pc.Index(self.index_name)

    def upsert_vector(self, id, vector, metadata=None):
        self.index.upsert(vectors=[(id, vector, metadata)])

    def query_vector(self, vector, top_k=5):
        return self.index.query(vector=vector, top_k=top_k, include_metadata=True)

# Test connection
if __name__ == "__main__":
    client = PineconeClient()
    print(f"Connected to Pinecone index: {os.getenv('PINECONE_INDEX_NAME')}")
from botbuilder.core import TurnContext, ActivityHandler
from pinecone_client import PineconeClient
from openai import OpenAI
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pinecone_client = PineconeClient()

class TeamsRAGBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        try:
            query = turn_context.activity.text
            response = await self.generate_response(query)
            await turn_context.send_activity(response)
        except Exception as e:
            print(f"Error in on_message_activity: {e}")
            traceback.print_exc()
            await turn_context.send_activity("I'm sorry, I encountered an error processing your request.")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("¡Bienvenido a ciberlex!")

    async def generate_response(self, query: str):
        try:
            relevant_docs = self.query_pinecone(query)
            context = self.prepare_context(relevant_docs)
            response = self.generate_openai_response(query, context)
            return response
        except Exception as e:
            print(f"Error in generate_response: {e}")
            traceback.print_exc()
            return "I'm sorry, I couldn't generate a response at this time."

    def query_pinecone(self, query: str):
        try:
            query_embedding = client.embeddings.create(input=[query], model="text-embedding-ada-002").data[0].embedding
            results = pinecone_client.query_vector(query_embedding, top_k=10)
            return results
        except Exception as e:
            print(f"Error in query_pinecone: {e}")
            traceback.print_exc()
            return []

    def prepare_context(self, relevant_docs):
        context = ""
        for doc in relevant_docs['matches']:
            context += f"\n\nDocument: {doc['metadata'].get('filename', 'Unknown')}\n"
            context += f"Chunk {doc['metadata'].get('chunk_index', 'Unknown')}:\n"
            context += f"{doc['metadata'].get('text', 'No text available')}\n"
        return context

    def generate_openai_response(self, query: str, context: str):
        try:
            prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un especialista en educación y tienes a disposición unos sílabos sobre unos cursos técnicos. Debes apoyar al usuario de la mejor manera posible respondiendo a sus preguntas."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in generate_openai_response: {e}")
            traceback.print_exc()
            return "I'm sorry, I couldn't generate a response from OpenAI at this time."
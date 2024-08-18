from fastapi import FastAPI, Request, Response
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from teams_bot import TeamsRAGBot
from azure.identity import ManagedIdentityCredential
import sys
import traceback
import os

# Initialize the Managed Identity credential
credential = ManagedIdentityCredential(client_id=os.getenv("MicrosoftAppId"))

# Create adapter settings
settings = BotFrameworkAdapterSettings(
    app_id=os.getenv("MicrosoftAppId"),
    app_password=None  # No password needed for managed identity
)

# Create adapter
adapter = BotFrameworkAdapter(settings)

# Configure adapter to use managed identity for token acquisition
adapter.credentials = credential

# Catch-all for errors.
async def on_error(context, error):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")

adapter.on_turn_error = on_error

# Create bot
bot = TeamsRAGBot()

# Configure FastAPI app
app = FastAPI()

@app.post("/api/messages")
async def messages(request: Request):
    if request.headers.get("Content-Type") == "application/json":
        body = await request.json()
    else:
        return Response(status_code=415)

    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")

    try:
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        if response:
            return Response(content=response.body, status_code=response.status)
        return Response(status_code=201)
    except Exception as e:
        print(f"Error processing activity: {e}")
        return Response(status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
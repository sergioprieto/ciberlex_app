# app.py
from aiohttp import web
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from teams_bot import TeamsRAGBot
import sys
import traceback
from dotenv import load_dotenv
import os

load_dotenv()

# Create adapter.
# Note: When testing locally, you can use empty strings for app ID and password.
settings = BotFrameworkAdapterSettings(os.getenv("MicrosoftAppId", ""), os.getenv("MicrosoftAppPassword", ""))
adapter = BotFrameworkAdapter(settings)

# Catch-all for errors.
async def on_error(context, error):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")

adapter.on_turn_error = on_error

# Create bot
bot = TeamsRAGBot()

# Listen for incoming requests on /api/messages
async def messages(req: web.Request) -> web.Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    try:
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        if response:
            return web.json_response(data=response.body, status=response.status)
        return web.Response(status=201)
    except Exception as e:
        print(f"Error processing activity: {e}")
        return web.Response(status=500)

# Configure web app
app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(app, host="localhost", port=3978)
    except Exception as error:
        raise error
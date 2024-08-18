from flask import Flask, request, jsonify

app = Flask(__name__)

#create a hello message in the root path
@app.route("/")
def hello():
    return "Hello World!"

@app.route("/api/messages", methods=["POST"])
def messages():
    try:
        data = request.json
        return jsonify({"type": "message", "text": f"You said: {data['text']}"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
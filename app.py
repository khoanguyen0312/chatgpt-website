# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response
import requests
import json

app = Flask(__name__)

# Setting
app.config.from_pyfile("settings.py")


@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    messages = request.form.get("prompts", None)
    apiKey = request.form.get("apiKey", None)
    model = request.form.get("model", "gpt-3.5-turbo")
    if messages is None:
        return jsonify(
            {
                "error": {
                    "message": "prompts！",
                    "type": "invalid_request_error",
                    "code": "",
                }
            }
        )

    if apiKey is None:
        apiKey = app.config["OPENAI_API_KEY"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    # Json load prompt
    prompts = json.loads(messages)

    data = {
        "messages": prompts,
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True,
    }

    try:
        resp = requests.post(
            url=app.config["URL"],
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 10),
        )
    except requests.exceptions.Timeout:
        return jsonify(
            {"error": {"message": "OpenAPI False", "type": "timeout_error", "code": ""}}
        )

    def generate():
        errorStr = ""
        for chunk in resp.iter_lines():
            if chunk:
                streamStr = chunk.decode("utf-8").replace("data: ", "")
                try:
                    streamDict = json.loads(streamStr)
                except:
                    errorStr += streamStr.strip()
                    continue
                delData = streamDict["choices"][0]
                if delData["finish_reason"] != None:
                    break
                else:
                    if "content" in delData["delta"]:
                        respStr = delData["delta"]["content"]
                        # print(respStr)
                        yield respStr

        if errorStr != "":
            with app.app_context():
                yield errorStr

    return Response(generate(), content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

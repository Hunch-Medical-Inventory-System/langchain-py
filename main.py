from llm import get_inventory_information

from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, World!"

@app.route("/assistant", methods=["POST"])
def assistant():
    data = request.get_json()
    question = data["question"]
    return get_inventory_information(question)

if __name__ == "__main__":
    app.run(port=5000)

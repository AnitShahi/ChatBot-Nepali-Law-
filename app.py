from flask import Flask, render_template, request, jsonify
from llama_cpp import Llama

app = Flask(__name__)

# Load the LLaMA model for the chatbot
llm = Llama(model_path="D:/Madan Project VIII/unsloth_Meta-Llama-3-8B-Instruct.Q8_0.gguf", verbose=True)
llm

# Define the Home route
@app.route('/')
def home():
    return render_template('index.html')

# Define the About Us route
@app.route('/about')
def about():
    return render_template('about.html')



def chatbot_response(message):
    response = llm(f"Instruction: {message} Output:", max_tokens=100)
    full_text = response["choices"][0]["text"]

    # Truncate the text at the first occurrence of '।'
    truncated_text = full_text.split('.')[0] + '.'  # Keeps everything before the first '।' and appends the '।'

    return truncated_text

# Define the Virtual Assistance route
@app.route('/chatbot', methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        user_message = request.form["instruction"]
        response = chatbot_response(user_message)
        return render_template("chatbot.html", result=response)
    return render_template("chatbot.html")

# Route to handle AJAX requests for the chatbot
@app.route("/get", methods=["POST"])
def get_bot_response():
    user_message = request.form.get("msg")
    response = chatbot_response(user_message)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
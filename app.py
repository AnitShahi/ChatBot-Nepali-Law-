from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from llama_cpp import Llama
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up Flask-Migrate
migrate = Migrate(app, db)

# Load the LLaMA models for the chatbot
llm_english = Llama(model_path="./unsloth_Meta-Llama-3-8B-Instruct.Q8_0.gguf", verbose=True)
llm_nepali = Llama(model_path="./unsloth_Meta-Llama-3-8B-Instruct.Q8_0.gguf", verbose=True)

# Define the User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

# Define the Chat model for storing chat history
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.String(500), nullable=False)
    bot_response = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Define the Home route
@app.route('/')
def home():
    return render_template('index.html')

# Define the About Us route
@app.route('/about')
def about():
    return render_template('about.html')

def chatbot_response(message, model):
    if model == 'Nepali':
        response = llm_nepali(f"Instruction: {message} Output:", max_tokens=100)
    else:
        response = llm_english(f"Instruction: {message} Output:", max_tokens=100)

    full_text = response["choices"][0]["text"]

    # Extract the text before the word "Instruction"
    truncated_text = full_text.split('Instruction')[0].strip()

    return truncated_text

# Define the Virtual Assistance route
@app.route('/chatbot', methods=["GET", "POST"])
def chatbot():
    if not session.get('logged_in'):
        flash("You need to log in first")
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()
    chat_history = Chat.query.filter_by(user_id=user.id).order_by(Chat.timestamp.desc()).all()

    if request.method == "POST":
        user_message = request.form["instruction"]
        selected_model = request.form.get("model", "English")  # Default to English if no model selected
        response = chatbot_response(user_message, selected_model)
        
        # Save the chat history
        new_chat = Chat(user_id=user.id, user_message=user_message, bot_response=response)
        db.session.add(new_chat)
        db.session.commit()

        return render_template("chatbot.html", result=response, chat_history=chat_history, selected_model=selected_model)
    
    # Handle GET request to render the page with history
    selected_model = request.args.get("model", "English")  # Default to English if no model selected
    return render_template("chatbot.html", chat_history=chat_history, selected_model=selected_model)

# Route to handle AJAX requests for the chatbot
@app.route("/get", methods=["POST"])
def get_bot_response():
    user_message = request.form.get("msg")
    selected_model = request.form.get("model", "English")  # Default to English if no model selected
    response = chatbot_response(user_message, selected_model)
    
    # Save the chat history
    user = User.query.filter_by(id=session['user_id']).first()
    new_chat = Chat(user_id=user.id, user_message=user_message, bot_response=response)
    db.session.add(new_chat)
    db.session.commit()

    return jsonify(response)

# Define the Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            flash('Logged in successfully.')
            return redirect(url_for('chatbot'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

# Define the Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

# Define the Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the database is created
    app.run(debug=True)

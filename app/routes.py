from app import app
from flask import jsonify, request

#testowa baza danych (słowniki)
users = [
    {"id": 1, "name": "John Pork", "email": "john.pork@example.com"},
    {"id": 2, "name": "Jane Smith", "email": "jane.smith@example.com"}
]

#############
@app.route('/')
def home():
    return "Witaj w aplikacji do obliczania śladu węglowego!"

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()  
    new_user = {
        "id": len(users) + 1,
        "name": data['name'],
        "email": data['email']
    }
    users.append(new_user)
    return jsonify(new_user), 201

from flask import Flask, jsonify, request, render_template
from datetime import datetime, timedelta
import jwt  

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  

users = {
    "admin": {"password": "password123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

emissions_data = {
    "daily_activities": []
}

emission_factors = {
    "transport": {
        "car": 0.21,
        "bus": 0.08,
        "bike": 0.0,
        "walk": 0.0,
        "train": 0.04,
        "plane": 0.25
    },
    "food": {
        "vegetarian": 2.0,
        "vegan": 1.5,
        "meat": 5.0
    },
    "energy": {
        "renewable": 0.1,
        "coal": 0.8,
        "gas": 0.6
    }
}

######Create
@app.route('/api/emissions', methods=['POST'])
def add_activity():
    data = request.json
    activity_type = data.get("activity_type")
    choice = data.get("choice")
    value = data.get("value")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    factor = emission_factors.get(activity_type, {}).get(choice, 0)
    emission = factor * value
    activity = {
        "date": date,
        "activity_type": activity_type,
        "choice": choice,
        "value": value,
        "emission": emission
    }
    emissions_data["daily_activities"].append(activity)
    return jsonify({"message": "Activity added successfully!", "activity": activity}), 201

#######Read
@app.route('/api/emissions', methods=['GET'])
def get_activities():
    return jsonify(emissions_data)

#######Update
@app.route('/api/emissions/<int:activity_id>', methods=['PUT'])
def update_activity(activity_id):
    if activity_id < 0 or activity_id >= len(emissions_data["daily_activities"]):
        return jsonify({"error": "Activity not found"}), 404
    
    data = request.json
    activity = emissions_data["daily_activities"][activity_id]
    activity["activity_type"] = data.get("activity_type", activity["activity_type"])
    activity["choice"] = data.get("choice", activity["choice"])
    activity["value"] = data.get("value", activity["value"])
    
    factor = emission_factors.get(activity["activity_type"], {}).get(activity["choice"], 0)
    activity["emission"] = factor * activity["value"]
    return jsonify({"message": "Activity updated successfully!", "activity": activity})

#####Delete
@app.route('/api/emissions/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    if activity_id < 0 or activity_id >= len(emissions_data["daily_activities"]):
        return jsonify({"error": "Activity not found"}), 404
    
    removed_activity = emissions_data["daily_activities"].pop(activity_id)
    return jsonify({"message": "Activity deleted successfully!", "removed_activity": removed_activity})

#############
@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error rendering index.html: {e}", 500

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

####### Wyszukiwanie Restful
@app.route('/api/emissions/search', methods=['GET'])
def search_activities():
    query = request.args.get('q', '').lower()  
    results = [
        activity for activity in emissions_data["daily_activities"]
        if query in activity["choice"].lower() or query in activity["activity_type"].lower()
    ]
    return jsonify(results)

###################################################### Logowanie
######################################################
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users and users[username]["password"] == password:
    #################################### token generowanie
        token = jwt.encode({
            'username': username,
            'role': users[username]["role"],
            'exp': datetime.utcnow() + timedelta(minutes=60 )
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    ######################################################
@app.route('/api/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({"message": f"Hello, {decoded_token['username']}! This is a protected endpoint."})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    ######################################################
    ######################################################
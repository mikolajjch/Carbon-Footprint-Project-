from flask import Flask, jsonify, request, render_template, g
from datetime import datetime, timedelta
import jwt
from functools import wraps
import bcrypt
import sqlite3
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*") 

################ handlery websocket
visit_count = 0  
active_users = 0  

@socketio.on("connect")
def handle_connect():
    global visit_count, active_users
    visit_count += 1
    active_users += 1
    print(f"Client connected! Total visits: {visit_count}, Active users: {active_users}")
    emit("update_visit_count", {"count": visit_count, "active_users": active_users}, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    global active_users
    active_users -= 1
    print(f"Client disconnected! Active users: {active_users}")
    emit("update_visit_count", {"count": visit_count, "active_users": active_users}, broadcast=True)

@socketio.on("visit_count_request")
def handle_visit_count_request():
    emit("update_visit_count", {"count": visit_count, "active_users": active_users})

########################## definijca tokenów i admin ####### NA POCZATKU
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        if token.startswith("Bearer "):
            token = token.split(" ")[1]  

        try:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            g.user = decoded_token
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user or g.user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

###########################################################################
#Łączenie z bazą danych
###########################################################################
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('users.db')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL)''')
        db.commit()
    return db
#############################
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

####################################################################################
############## rejestracja i logowanie użytkowników
###############################################################################################
############## i CRUD dla użytkowników
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    hashed_password = hash_password(password)
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (username, hashed_password, role))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "User already exists"}), 400
    
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    db = get_db()
    cursor = db.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and verify_password(password, user[0]):
        token = jwt.encode({
            'username': username,
            'role': user[1],
            'exp': datetime.utcnow() + timedelta(minutes=60)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({"token": token})
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    db = get_db()
    cursor = db.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    return jsonify([{"id": user[0], "username": user[1], "role": user[2]} for user in users])

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({"message": "User deleted successfully!"})

###############################################################################################
@app.route('/api/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({"message": f"Hello, {g.user['username']}! This is a protected endpoint."})
##############################################################################################
####################################################### emisje i obsluga bez zewnętrznej bazy danych
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
@token_required
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
        "emission": emission,
        "username": g.user["username"]  
    }
    emissions_data["daily_activities"].append(activity)
    socketio.emit("new_activity", {"message": "New activity added!", "activity": activity})
    
    return jsonify({"message": "Activity added successfully!", "activity": activity}), 201

#######Read
@app.route('/api/emissions', methods=['GET'])
@token_required
def get_activities():
    if g.user["role"] == "admin":
        return jsonify(emissions_data)
    else:
        user_activities = [activity for activity in emissions_data["daily_activities"] if activity.get("username") == g.user["username"]]
        return jsonify({"daily_activities": user_activities})

#######Update
@app.route('/api/emissions/<int:activity_id>', methods=['PUT'])
@token_required
def update_activity(activity_id):
    if activity_id < 0 or activity_id >= len(emissions_data["daily_activities"]):
        return jsonify({"error": "Activity not found"}), 404
    
    activity = emissions_data["daily_activities"][activity_id]
    if g.user["role"] != "admin" and activity.get("username") != g.user["username"]:
        return jsonify({"error": "You can only update your own activities"}), 403
    
    data = request.json
    activity["activity_type"] = data.get("activity_type", activity["activity_type"])
    activity["choice"] = data.get("choice", activity["choice"])
    activity["value"] = data.get("value", activity["value"])
    
    factor = emission_factors.get(activity["activity_type"], {}).get(activity["choice"], 0)
    activity["emission"] = factor * activity["value"]
    return jsonify({"message": "Activity updated successfully!", "activity": activity})

#####Delete
@app.route('/api/emissions/<int:activity_id>', methods=['DELETE'])
@token_required
def delete_activity(activity_id):
    if activity_id < 0 or activity_id >= len(emissions_data["daily_activities"]):
        return jsonify({"error": "Activity not found"}), 404
    
    activity = emissions_data["daily_activities"][activity_id]
    if g.user["role"] != "admin" and activity.get("username") != g.user["username"]:
        return jsonify({"error": "You can only delete your own activities"}), 403
    
    removed_activity = emissions_data["daily_activities"].pop(activity_id)
    return jsonify({"message": "Activity deleted successfully!", "removed_activity": removed_activity})

####### Wyszukiwanie Restful
@app.route('/api/emissions/search', methods=['GET'])
def search_activities():
    query = request.args.get('q', '').lower()  
    results = [
        activity for activity in emissions_data["daily_activities"]
        if query in activity["choice"].lower() or query in activity["activity_type"].lower()
    ]
    return jsonify(results)

###################################################### 
######################################################
@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error rendering index.html: {e}", 500
    



#if __name__ == '__main__':
#    socketio.run(app, debug=True)
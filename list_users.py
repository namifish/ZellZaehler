import json

USER_DATA_FILE = 'benutzerdaten.json'

def load_user_data():
    with open(USER_DATA_FILE, 'r') as file:
        return json.load(file)

def list_users():
    users = load_user_data()
    for user in users:
        print(f'Username: {user}, Password Hash: {users[user]["password"]}')

list_users()
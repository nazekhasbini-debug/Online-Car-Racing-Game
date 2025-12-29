import socket
import threading
import sqlite3
import json

class RacingServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.connected_clients = {}  
        self.pending_requests = {}  
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect('racing_game.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            games_won INTEGER DEFAULT 0,
            car_color TEXT DEFAULT 'red'
        )
        ''')
        conn.commit()
        conn.close()
        
    def start(self):
        self.server_socket.listen(5)
        print(f"[SERVER] Started on {self.host}:{self.port}")
        
        while True:
            conn, addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
            
    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        connected = True
        username = None
        
        while connected:
            
            data = conn.recv(1024)
            if not data:
                break
            
            message = json.loads(data.decode('utf-8'))
            action = message.get('action')
            
            if action == 'register':
                response = self.register_user(message.get('username'), message.get('password'), 
                                            message.get('car_color'))
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'login':
                response = self.login_user(message.get('username'), message.get('password'))
                if response.get('status') == 'success':
                    username = message.get('username')
                    client_listening_port = message.get('listening_port')
                    self.connected_clients[username] = (conn, addr, client_listening_port)
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'get_online_users':
                response = self.get_online_users(username)
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'request_race':
                opponent = message.get('opponent')
                response = self.request_race(username, opponent)
                conn.send(json.dumps(response).encode('utf-8'))
                
                if response.get('status') == 'success' and opponent in self.connected_clients:
                    opponent_conn = self.connected_clients[opponent][0]
                    notification = {
                        'action': 'race_request',
                        'from': username
                    }
                    opponent_conn.send(json.dumps(notification).encode('utf-8'))
            
            elif action == 'respond_to_race':
                requester = message.get('requester')
                accept = message.get('accept')
                response = self.respond_to_race(username, requester, accept)
                conn.send(json.dumps(response).encode('utf-8'))
                
                if accept and response.get('status') == 'success':
                    requester_conn = self.connected_clients[requester][0]
                    requester_addr = self.connected_clients[requester][1][0]  
                    requester_listening_port = self.connected_clients[requester][2]
                    
                    responder_addr = self.connected_clients[username][1][0]  
                    responder_listening_port = self.connected_clients[username][2]
                    
                    p2p_info_for_requester = {
                        'action': 'connect_p2p',
                        'opponent': username,
                        'opponent_ip': responder_addr,
                        'opponent_port': responder_listening_port
                    }
                    requester_conn.send(json.dumps(p2p_info_for_requester).encode('utf-8'))
                    
                    p2p_info_for_responder = {
                        'action': 'connect_p2p',
                        'opponent': requester,
                        'opponent_ip': requester_addr,
                        'opponent_port': requester_listening_port
                    }
                    conn.send(json.dumps(p2p_info_for_responder).encode('utf-8'))
            
            elif action == 'get_user_stats':
                target_user = message.get('username')
                response = self.get_user_stats(target_user)
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'update_win':
                response = self.update_win(username)
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif action == 'logout':
                if username and username in self.connected_clients:
                    del self.connected_clients[username]
                response = {'status': 'success', 'message': 'Logged out successfully'}
                conn.send(json.dumps(response).encode('utf-8'))
                connected = False
                    
            
        if username and username in self.connected_clients:
            del self.connected_clients[username]
        conn.close()
    
    def register_user(self, username, password, car_color):
        if not username or not password:
            return {'status': 'error', 'message': 'Username and password are required'}
        
        if car_color not in ["Chili Red", "Ocean Blue", "Cherry Blossom", "Forest Green"]:
            return {'status': 'error', 'message': 'Invalid car color'}
        
        conn = sqlite3.connect('racing_game.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return {'status': 'error', 'message': 'Username already exists'}
        
        cursor.execute("INSERT INTO users (username, password, car_color) VALUES (?, ?, ?)", 
                        (username, password, car_color))
        conn.commit()
        conn.close()
        return {'status': 'success', 'message': 'Registration successful'}
        
    def login_user(self, username, password):
        if not username or not password:
            return {'status': 'error', 'message': 'Username and password are required'}
        
        try:
            conn = sqlite3.connect('racing_game.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                          (username, password))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                if username in self.connected_clients:
                    return {'status': 'error', 'message': 'User already logged in'}
                return {'status': 'success', 'message': 'Login successful', 'car_color': user[3], 'games_won': user[2]}
            else:
                return {'status': 'error', 'message': 'Invalid username or password'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_online_users(self, username):
        if not username or username not in self.connected_clients:
            return {'status': 'error', 'message': 'Not authenticated'}
        
        online_users = [user for user in self.connected_clients.keys() if user != username]
        return {
            'status': 'success', 
            'online_users': online_users
        }
    
    def request_race(self, requester, opponent):
        if not requester or requester not in self.connected_clients:
            return {'status': 'error', 'message': 'Not authenticated'}
        
        if not opponent or opponent not in self.connected_clients:
            return {'status': 'error', 'message': 'Opponent not online'}
        
        if opponent in self.pending_requests and self.pending_requests[opponent] == requester:
            requester_conn = self.connected_clients[requester][0]
            opponent_conn = self.connected_clients[opponent][0]
            
            requester_addr = self.connected_clients[requester][1][0]  
            requester_listening_port = self.connected_clients[requester][2]
            
            opponent_addr = self.connected_clients[opponent][1][0]  
            opponent_listening_port = self.connected_clients[opponent][2]
            
            p2p_info_for_requester = {
                'action': 'connect_p2p',
                'opponent': opponent,
                'opponent_ip': opponent_addr,
                'opponent_port': opponent_listening_port
            }
            requester_conn.send(json.dumps(p2p_info_for_requester).encode('utf-8'))
            
            p2p_info_for_opponent = {
                'action': 'connect_p2p',
                'opponent': requester,
                'opponent_ip': requester_addr,
                'opponent_port': requester_listening_port
            }
            opponent_conn.send(json.dumps(p2p_info_for_opponent).encode('utf-8'))
            
            del self.pending_requests[opponent]
            return {'status': 'success', 'message': 'Auto-matched with opponent'}
        
        self.pending_requests[requester] = opponent
        return {'status': 'success', 'message': 'Race request sent'}
    
    def respond_to_race(self, responder, requester, accept):
        if not responder or responder not in self.connected_clients:
            return {'status': 'error', 'message': 'Not authenticated'}
        
        if not requester or requester not in self.connected_clients:
            return {'status': 'error', 'message': 'Requester not online'}
        
        if requester not in self.pending_requests or self.pending_requests[requester] != responder:
            return {'status': 'error', 'message': 'No pending request from this user'}
        
        del self.pending_requests[requester]
        
        if not accept:
            requester_conn = self.connected_clients[requester][0]
            notification = {
                'action': 'race_declined',
                'by': responder
            }
            requester_conn.send(json.dumps(notification).encode('utf-8'))
            return {'status': 'success', 'message': 'Race declined'}
        
        return {'status': 'success', 'message': 'Race accepted'}
    
    def get_user_stats(self, username):
        try:
            conn = sqlite3.connect('racing_game.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT username, games_won, car_color FROM users WHERE username = ?", 
                          (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'status': 'success',
                    'username': user[0],
                    'games_won': user[1],
                    'car_color': user[2],
                    'is_online': username in self.connected_clients
                }
            else:
                return {'status': 'error', 'message': 'User not found'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def update_win(self, username):
        if not username:
            return {'status': 'error', 'message': 'Username required'}
        
        try:
            conn = sqlite3.connect('racing_game.db')
            cursor = conn.cursor()
            
            cursor.execute("UPDATE users SET games_won = games_won + 1 WHERE username = ?", 
                          (username,))
            conn.commit()
            conn.close()
            return {'status': 'success', 'message': 'Win recorded'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    server = RacingServer()
    server.start()
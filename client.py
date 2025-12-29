import socket
import threading
import json
import random
import sys
import subprocess

class RacingClient:
    def __init__(self, server_host='localhost', server_port=5555):
        self.server_host = server_host
        self.server_port = server_port
        self.server_socket = None
        self.listener_socket = None
        self.p2p_socket = None
        self.username = None
        self.car_color = None
        self.games_won = 0
        self.listening_port = random.randint(10000, 65000)  
        self.opponent = None
        self.opponent_connected = False
        self.gui_callback = None
        self.listening = False
        self.game_started = False
        self.is_host = False  
        self.game_callback = None  
        
    def set_gui_callback(self, callback):
        self.gui_callback = callback
        
    def connect_to_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_host, self.server_port))
            
            server_thread = threading.Thread(target=self.listen_to_server)
            server_thread.daemon = True
            server_thread.start()
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to server: {e}")
            if self.gui_callback:
                self.gui_callback('server_error', {'message': f'Failed to connect to server: {str(e)}'})
            return False
    
    
    def listen_to_server(self):
        while True:
            try:
                data = self.server_socket.recv(1024)
                if not data:
                    if self.gui_callback:
                        self.gui_callback('server_disconnected', {'message': 'Disconnected from server'})
                    break
                
                response = json.loads(data.decode('utf-8'))
                
                if 'action' in response:
                    if response['action'] == 'race_request':
                        if self.gui_callback:
                            self.gui_callback('race_request', {'from': response['from']})
                    
                    elif response['action'] == 'connect_p2p':
                        self.opponent = response['opponent']
                        opponent_ip = response['opponent_ip']
                        opponent_port = response['opponent_port']
                        
                        self.is_host = True  
                
                        self.start_p2p_connection(opponent_ip, opponent_port)
                        
                        if self.gui_callback:
                            self.gui_callback('race_starting', {'opponent': self.opponent})
                    
                    elif response['action'] == 'race_declined':
                        if self.gui_callback:
                            self.gui_callback('race_declined', {'by': response['by']})
                else:
                    if self.gui_callback:
                        self.gui_callback('server_response', response)

            except Exception as e:
                print(f"[ERROR] Server communication error: {e}")
                if self.gui_callback:
                    self.gui_callback('server_error', {'message': f'Connection error: {str(e)}'})
                break
            
            
    
    def register(self, username, password, car_color):
        if not all([username, password, car_color]):
            return {'status': 'error', 'message': 'Missing required registration information'}
            
        if not self.server_socket:
            return {'status': 'error', 'message': 'Not connected to server'}
        
        request = {
            'action': 'register',
            'username': username,
            'password': password,
            'car_color': car_color
        }
        
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def login(self, username, password):
        if not self.server_socket:
            return {'status': 'error', 'message': 'Not connected to server'}
        
        self.username = username
        
        self.start_p2p_listener()
        
        request = {
            'action': 'login',
            'username': username,
            'password': password,
            'listening_port': self.listening_port
        }
        
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def get_online_users(self):
        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = {'action': 'get_online_users'}
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def request_race(self, opponent):
        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = { 'action': 'request_race', 'opponent': opponent}
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def respond_to_race(self, requester, accept):
        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = {'action': 'respond_to_race', 'requester': requester,'accept': accept}
        
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def get_user_stats(self, target_username):
        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = {'action': 'get_user_stats','username': target_username}
        self.server_socket.send(json.dumps(request).encode('utf-8'))
    
    def update_win(self):
        self.games_won += 1

        if self.gui_callback:
            self.gui_callback('win_updated', {
                'games_won': self.games_won
            })

        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = {
            'action': 'update_win'
        }
        
        self.server_socket.send(json.dumps(request).encode('utf-8'))

    def logout(self):
        if not self.server_socket or not self.username:
            return {'status': 'error', 'message': 'Not logged in'}
        
        request = {'action': 'logout'}
        
        self.server_socket.send(json.dumps(request).encode('utf-8'))
        self.username = None
    
    def start_p2p_listener(self):
        """Start a socket listener for incoming P2P connections"""
        if self.listening:
            return
            
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind(('0.0.0.0', self.listening_port))
            self.listener_socket.listen(1)
            
            self.listening = True
            print(f"[P2P] Listening for P2P connections on port {self.listening_port}")
            
            listener_thread = threading.Thread(target=self.accept_p2p_connection)
            listener_thread.daemon = True
            listener_thread.start()
            
        except Exception as e:
            print(f"[ERROR] Failed to start P2P listener: {e}")
            
            self.listening_port = random.randint(10000, 65000)
            self.start_p2p_listener()
       
    def accept_p2p_connection(self):
        while self.listening:
            conn, addr = self.listener_socket.accept()
            print(f"[P2P] Accepted connection from {addr}")
            
            self.p2p_socket = conn
            
            p2p_thread = threading.Thread(target=self.handle_p2p_communication, args=(conn,))
            p2p_thread.daemon = True
            p2p_thread.start()
            
            self.opponent_connected = True
            self.is_host = False  
            
            if self.gui_callback:
                self.gui_callback('p2p_connected', {'message': 'P2P connection established'})
     
    def start_p2p_connection(self, opponent_ip, opponent_port):
        try:
            print(f"[P2P] Connecting to opponent at {opponent_ip}:{opponent_port}")
            self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.p2p_socket.connect((opponent_ip, opponent_port))
            
            p2p_thread = threading.Thread(target=self.handle_p2p_communication, args=(self.p2p_socket,))
            p2p_thread.daemon = True
            p2p_thread.start()
            
            self.send_p2p_message({'action': 'p2p_connected', 'username': self.username})
            self.opponent_connected = True
            self.start_race_game()
        except Exception as e:
            print(f"[ERROR] Failed to connect to opponent: {e}")
            if self.gui_callback:
                self.gui_callback('p2p_error', {'message': f'Failed to connect to opponent: {str(e)}'})
    
    def handle_p2p_communication(self, socket_conn):
        while self.opponent_connected:
            try:
                data = socket_conn.recv(1024)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                print(f"[P2P] Received: {message}")
                
                if message.get('action') == 'p2p_connected':
                    if not self.opponent:
                        self.opponent = message.get('username')
                    
                    if not self.game_started:
                        self.start_race_game()
                
                elif message.get('type') == 'game_data':
                    if self.game_callback:
                        self.game_callback(message.get('data'))
                
                if self.gui_callback:
                    self.gui_callback('p2p_message', message)

            except Exception as e:
                print(f"[ERROR] P2P communication error: {e}")
                break
      
        self.opponent_connected = False
        if self.gui_callback:
            self.gui_callback('p2p_disconnected', {'message': 'Opponent disconnected'})
    
    def send_p2p_message(self, message):
        if not self.opponent_connected or not self.p2p_socket:
            return False
        try:
            self.p2p_socket.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            return False
    
    
    def register_game_callback(self, callback):
        self.game_callback = callback
    
    def start_race_game(self):
        if self.game_started:
            return
                
        if self.gui_callback:
            self.gui_callback('launch_game', {'opponent': self.opponent})
        
        print("[GAME] Launching the race game")
        
        
        opponent_ip = self.p2p_socket.getpeername()[0]
        opponent_port = self.p2p_socket.getpeername()[1]
        is_host_arg = "1" if self.is_host else "0"
        game_path = 'game.py'
        
        self.game_started = True
        
        process = subprocess.Popen([
            sys.executable, 
            game_path,
            "--username", str(self.username),
            "--opponent", str(self.opponent if self.opponent else "Unknown"),
            "--car-color", str(self.car_color if self.car_color else "blue"),
            "--is-host", is_host_arg,
            "--opponent-ip", opponent_ip,
            "--opponent-port", str(opponent_port)
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        def monitor_process():
            while True:
                raw = process.stdout.readline()
                if raw == b'' and process.poll() is not None:
                    break

                if raw:
                    line = raw.decode('utf-8').strip()

                    if line == "GAME_MARKER:YOU_WON":
                        print("[CLIENT] Detected win marker—updating server count")
                        self.update_win()     
                        continue

                    
                    print(f"[GAME OUTPUT] {line}")

            self.game_started = False

            
        monitor_thread = threading.Thread(target=monitor_process)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def close(self):
        
        if self.username:
            self.logout()
        
        if self.server_socket:
            self.server_socket.close()
        
        if self.listener_socket:
            self.listener_socket.close()
            self.listening = False
        
        if self.p2p_socket:
            self.p2p_socket.close()
        
        self.opponent_connected = False
        self.game_started = False

if __name__ == "__main__":
    from game_ui import main
    main()
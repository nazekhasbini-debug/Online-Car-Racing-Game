import pygame
import time
import random
import pickle
import socket
import sys


pygame.init()
pygame.font.init()
coordinate_font = pygame.font.SysFont('Arial', 24)
pygame.mixer.init()

wn_width = 800
wn_height = 600
wn = pygame.display.set_mode((wn_width, wn_height))
pygame.display.set_caption("Multiplayer Car Racing")


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
ChiliRed = (227, 3, 3)
OceanBlue = (0, 102, 204)
CherryBlossom = (255, 183, 197)
ForestGreen = (63, 90, 54)

road_left = 50
road_right = 750
center_divider = 400     

p1_lane_divider = (road_left + center_divider) // 2
p2_lane_divider = (center_divider + road_right) // 2

game_over_sound = pygame.mixer.Sound('game-over-sound-effect-.mp3')
crash_sound = pygame.mixer.Sound('box-crash.mp3')
pygame.mixer.music.load('background.wav')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)


clock = pygame.time.Clock()

SHAPE_RECTANGLE = 0
SHAPE_TRIANGLE = 1
SHAPE_CIRCLE = 2
SHAPE_DIAMOND = 3

class Obstacle:
    def __init__(self, player_side, lane_position):
        self.shape = random.randint(0, 3)
        self.color = random.choice([RED, ORANGE, PURPLE, CYAN, PINK])
        self.width, self.height = self.set_shape(self.shape)
        self.speedy = random.randint(4, 7)
        self.player_side = player_side
        self.lane_position = lane_position
        self.y = -100 - random.randint(0, 300) 
        self.position_in_lane()

    def set_shape(self, shape):
        if shape == SHAPE_CIRCLE:
            return 40, 40
        elif shape == SHAPE_TRIANGLE:
            return 50, 40
        elif shape == SHAPE_DIAMOND:
            return 45, 45
        else:  
            return random.randint(60, 90), random.randint(15, 30)
        
    def position_in_lane(self):
        if self.player_side == 0:  
            if self.lane_position == 0:  
                self.x = random.randrange(road_left + 5, p1_lane_divider - self.width - 5)
            else:  
                self.x = random.randrange(p1_lane_divider + 5, center_divider - self.width - 5)
        else:  
            if self.lane_position == 0: 
                self.x = random.randrange(center_divider + 5, p2_lane_divider - self.width - 5)
            else:  
                self.x = random.randrange(p2_lane_divider + 5, road_right - self.width - 5)

    def get_state(self):
        
        return {
            "x": self.x,
            "y": self.y,
            "shape": self.shape,
            "color": self.color,
            "width": self.width,
            "height": self.height,
            "speedy": self.speedy,
            "player_side": self.player_side,
            "lane_position": self.lane_position
        }

    def set_state(self, state):
        
        self.x = state["x"]
        self.y = state["y"]
        self.shape = state["shape"]
        self.color = state["color"]
        self.width = state["width"]
        self.height = state["height"]
        self.speedy = state["speedy"]
        self.player_side = state["player_side"]
        self.lane_position = state["lane_position"]

    def update(self):
        self.y += self.speedy
        if self.y > wn_height:
            self.reset()
            return 1  
        return 0

    def reset(self):
        
        self.y = -100 - random.randint(0, 200)
        self.shape = random.randint(0, 3)
        self.color = random.choice([RED, ORANGE, PURPLE, CYAN, PINK])
        
        if self.shape == SHAPE_CIRCLE:
            self.width = 40
            self.height = 40
        elif self.shape == SHAPE_TRIANGLE:
            self.width = 50
            self.height = 40
        elif self.shape == SHAPE_DIAMOND:
            self.width = 45
            self.height = 45
        else:  
            self.width = random.randint(60, 90)
            self.height = random.randint(15, 30)
            
        self.speedy = random.randint(4, 7)
        self.position_in_lane()

    def draw(self, wn):
        if self.shape == SHAPE_RECTANGLE:
            pygame.draw.rect(wn, self.color, [self.x, self.y, self.width, self.height])
        
        elif self.shape == SHAPE_TRIANGLE:
            pygame.draw.polygon(wn, self.color, [(self.x + self.width // 2, self.y),(self.x, self.y + self.height),(self.x + self.width, self.y + self.height)])
            
        elif self.shape == SHAPE_CIRCLE:
            pygame.draw.circle(wn, self.color, (self.x + self.width // 2, self.y + self.height // 2), self.width // 2)
            
        elif self.shape == SHAPE_DIAMOND:
            pygame.draw.polygon(wn, self.color, [(self.x + self.width // 2, self.y),(self.x + self.width, self.y + self.height // 2),(self.x + self.width // 2, self.y + self.height),(self.x, self.y + self.height // 2)])
    
    def get_collision_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Player:
    def __init__(self, player_num, color=None):
        self.width = 40
        self.height = 60
        self.player_num = player_num
        self.score = 0
        self.health = 100
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.wins = 0
        self.color=color
        color_map = {
            'red': RED,
            'blue': BLUE,
            'green': GREEN,
            'yellow': YELLOW,
            'cyan': CYAN,
            'orange': ORANGE,
            'purple': PURPLE,
            'pink': PINK
        }
        
        if color and color.lower() in color_map:
            self.color = color_map[color.lower()]
        elif player_num == 1:
            self.color = BLUE
        else:
            self.color = GREEN
            
        if player_num == 1:
            self.rect.x = (road_left + p1_lane_divider) // 2 - self.width // 2
            self.left_key = pygame.K_LEFT
            self.right_key = pygame.K_RIGHT
            self.up_key = pygame.K_UP
            self.down_key = pygame.K_DOWN
            self.boundary_left = road_left
            self.boundary_right = center_divider
            self.lane_divider = p1_lane_divider
        else:
            self.rect.x = (center_divider + p2_lane_divider) // 2 - self.width // 2
            self.left_key = pygame.K_a
            self.right_key = pygame.K_d
            self.up_key = pygame.K_w
            self.down_key = pygame.K_s
            self.boundary_left = center_divider
            self.boundary_right = road_right
            self.lane_divider = p2_lane_divider
            
        self.rect.y = wn_height - self.height - 10
        self.speedx = 0
        self.speedy = 0

    def update(self, keystate):
        self.speedx = 0
        self.speedy = 0
        
        if keystate[self.left_key]:
            self.speedx = -8
        if keystate[self.right_key]:
            self.speedx = 8
            
        if keystate[self.up_key]:
            self.speedy = -5
        if keystate[self.down_key]:
            self.speedy = 5
            
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        if self.rect.left < self.boundary_left:
            self.rect.left = self.boundary_left
        if self.rect.right > self.boundary_right:
            self.rect.right = self.boundary_right
            
        if self.rect.top < wn_height // 2:
            self.rect.top = wn_height // 2
        if self.rect.bottom > wn_height - 10:
            self.rect.bottom = wn_height - 10

    def draw(self, wn):
        
        pygame.draw.rect(wn, self.color, self.rect)
        
        light_color = YELLOW if self.player_num == 1 else WHITE
        
        pygame.draw.rect(wn, light_color,[self.rect.x + 5, self.rect.y, 5, 5])
        pygame.draw.rect(wn, light_color, [self.rect.x + self.width - 10, self.rect.y, 5, 5])

def draw_road():
    pygame.draw.rect(wn, GRAY, [road_left, 0, road_right - road_left, wn_height])
    pygame.draw.rect(wn, YELLOW, [center_divider - 5, 0, 10, wn_height])
    pygame.draw.rect(wn, WHITE, [p1_lane_divider - 2, 0, 4, wn_height])
    pygame.draw.rect(wn, WHITE, [p2_lane_divider - 2, 0, 4, wn_height])
    pygame.draw.rect(wn, WHITE, [road_left - 5, 0, 5, wn_height])
    pygame.draw.rect(wn, WHITE, [road_right, 0, 5, wn_height])
    
    for y in range(0, wn_height, 40):
        pygame.draw.rect(wn, YELLOW, [center_divider - 2, y, 4, 20])
        
        if y % 80 == 0:
            pygame.draw.rect(wn, WHITE, [p1_lane_divider - 1, y, 2, 20])
            pygame.draw.rect(wn, WHITE, [p2_lane_divider - 1, y, 2, 20])

def score_board(player1, player2):
    font = pygame.font.Font(None, 30)
    
    text1 = font.render(f'P1 Score: {player1.score}  Health: {player1.health}', True, WHITE)
    wn.blit(text1, (10, 10))
    text2 = font.render(f'P2 Score: {player2.score}  Health: {player2.health}', True, WHITE)
    wn.blit(text2, (wn_width - 250, 10))

def game_over(player1, player2, client=None):
    pygame.mixer.music.stop()
    game_over_sound.play()
    font = pygame.font.Font(None, 70)
    small_font = pygame.font.Font(None, 40)
    
    text = font.render('Game Over!', True, RED)
    wn.blit(text, (wn_width // 2 - 150, wn_height // 2 - 50))
    
    winner = None
    
    if player1.health <= 0 and player2.health <= 0:
        if player1.score > player2.score:
            winner_text = small_font.render("Player 1 Wins by score!", True, BLACK)
            winner = "player1"
        elif player2.score > player1.score:
            winner_text = small_font.render("Player 2 Wins by score!", True, BLACK)
            winner = "player2"
        else:
            winner_text = small_font.render("It's a tie!", True, BLACK)
    elif player1.health <= 0:
        winner_text = small_font.render("Player 2 Wins!", True, BLACK)
        winner = "player2"
    else:
        winner_text = small_font.render("Player 1 Wins!", True, BLACK)
        winner = "player1"
        
    wn.blit(winner_text, (wn_width // 2 - 100, wn_height // 2 + 30))
    pygame.display.update()
    
    if winner == "player1":
        player1.wins += 1
    elif winner == "player2":
        player2.wins += 1
    if client and winner:
        is_local = (client.is_host and winner == "player1") or (not client.is_host and winner == "player2")
        if is_local:
            print("GAME_MARKER:YOU_WON")

    time.sleep(3)
    pygame.quit()
    sys.exit()

def display_controls():
    font = pygame.font.Font(None, 24)
    p1_text = font.render("P1: Arrow Keys", True, WHITE)
    p2_text = font.render("P2: WASD Keys", True, WHITE)
    
    wn.blit(p1_text, (10, 40))
    wn.blit(p2_text, (wn_width - 150, 40))

def display_coordinates(player1, player2):
    font = pygame.font.Font(None, 24)
    
    p1_coords_text = font.render(f"Player1 Car: ({player1.rect.x}, {player1.rect.y})", True, WHITE)
    wn.blit(p1_coords_text, (10, 70))
    
    p2_coords_text = font.render(f"Player2 Car: ({player2.rect.x}, {player2.rect.y})", True, WHITE)
    wn.blit(p2_coords_text, (10, 100))

class NetworkHandler:
    def __init__(self, is_host, opponent_ip=None, opponent_port=None):
        self.is_host = is_host
        self.opponent_ip = opponent_ip
        self.opponent_port = opponent_port
        self.socket = None
        self.connected = False
        self.connection_timeout = 10  
        
    def setup_connection(self):
        print(f"[NETWORK] Setting up {'host' if self.is_host else 'client'} connection")
        
        if self.is_host:
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(self.connection_timeout)
            
            self.socket.bind(('', 12345))  
            self.socket.listen(1)
            
            print(f"[NETWORK] Waiting for opponent to connect on port 12345...")
            
            conn, addr = self.socket.accept()
            print(f"[NETWORK] Opponent connected from {addr}")
            
            self.socket = conn
            self.socket.setblocking(0)
            
            self.socket.sendall(pickle.dumps({"handshake": "host"}))
            
            start_time = time.time()
            while time.time() - start_time < 5:  
                try:
                    data = self.socket.recv(1024)
                    if data:
                        response = pickle.loads(data)
                        if "handshake" in response and response["handshake"] == "client":
                            print("[NETWORK] Handshake successful")
                            break
                except BlockingIOError:
                    time.sleep(0.1)
                
            
        else:
           
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.connection_timeout)
            
            print(f"[NETWORK] Connecting to host at {self.opponent_ip}:12345")
            self.socket.connect((self.opponent_ip, 12345))
            
            self.socket.setblocking(0)
            
            start_time = time.time()
            while time.time() - start_time < 5:  
                try:
                    data = self.socket.recv(1024)
                    if data:
                        message = pickle.loads(data)
                        if "handshake" in message and message["handshake"] == "host":
                            
                            self.socket.sendall(pickle.dumps({"handshake": "client"}))
                            print("[NETWORK] Handshake successful")
                            break
                except BlockingIOError:
                    
                    time.sleep(0.1)
            print(f"[NETWORK] Connected to host")
                
        self.connected = True
        print("[NETWORK] Connection established successfully")
        return True
        
    def send_data(self, data):
        if not self.connected:
            return False
        try:
            self.socket.sendall(pickle.dumps(data))
            return True
        except BlockingIOError:
            return False
        except Exception as e:
            print(f"[NETWORK] Send error: {e}")
            return False
            
    def receive_data(self):
        if not self.connected:
            return None
            
        try:
            data = self.socket.recv(4096)
            if data:
                return pickle.loads(data)
        except BlockingIOError:
            pass  
        except ConnectionResetError:
            print("[NETWORK] Connection reset by peer")
            self.connected = False
        
            
        return None
        
    def close(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"[NETWORK] Error closing socket: {e}")
        self.connected = False
        print("[NETWORK] Connection closed")
        


def game_loop(is_host=True, opponent_ip=None, opponent_port=None, client=None):
    print(f"[GAME] Starting game as {'host' if is_host else 'client'}")
    print(f"[GAME] Opponent IP: {opponent_ip}, Port: {opponent_port}")
    
    network = NetworkHandler(is_host, opponent_ip, opponent_port)
    
    print("[GAME] Setting up network connection...")
    connection_success = network.setup_connection()
    
    if not connection_success:
        print("[GAME] Failed to establish network connection")
        print("[GAME] Game will run in standalone mode for testing")
    else:
        print("[GAME] Network connection established")
    
    player1 = Player(1)
    player2 = Player(2)
    
    if client and hasattr(client, 'car_color') and client.car_color:
        color_map = {
            'red': RED,
            'blue': BLUE,
            'green': GREEN,
            'yellow': YELLOW,
            'cyan': CYAN,
            'orange': ORANGE,
            'purple': PURPLE,
            'pink': PINK,
            'Cherry Blossom' : CherryBlossom,
            'Ocean Blue': OceanBlue,
            'Chili Red': ChiliRed,
            'Forest Green':ForestGreen
        }
        
        player_color = color_map.get(client.car_color, OceanBlue)
        
        if is_host:
            player1.color = player_color
        else:
            player2.color = player_color
    
    obstacles = [Obstacle(0, 0), Obstacle(0, 1), Obstacle(1, 0), Obstacle(1, 1)]
    
    if is_host:
        controlled_player = player1
        opponent_player = player2
    else:
        controlled_player = player2
        opponent_player = player1
    
    running = True
    last_send_time = time.time()
    last_network_check = time.time()
    
    print("[GAME] Game initialized, starting main loop")
    
    game_start_time = time.time()
    game_duration = 30  
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        current_time = time.time()
        elapsed_time = current_time - game_start_time
        remaining_time = max(0, game_duration - elapsed_time)
        
        if elapsed_time >= game_duration:
            print("[GAME] Time's up! Game ending...")
            if player1.score > player2.score:
                player2.health = 0  
            elif player2.score > player1.score:
                player1.health = 0 
            else:
                if player1.health < player2.health:
                    player1.health = 0
                else:
                    player2.health = 0
            
            game_over(player1, player2, client)
            break
        
        wn.fill(DARK_GRAY)
        draw_road()
        
        keystate = pygame.key.get_pressed()
        controlled_player.update(keystate)
        
        
        if network.connected:
            if current_time - last_network_check > 2.0:
                try:
                    network.send_data({"ping": current_time})
                except Exception as e:
                    print(f"[NETWORK] Ping error: {e}")
                last_network_check = current_time
                
            if current_time - last_send_time > 0.05:
                try:
                    player_data = {
                        "rect_x": controlled_player.rect.x,
                        "rect_y": controlled_player.rect.y,
                        "score": controlled_player.score,
                        "health": controlled_player.health,
                        "color": controlled_player.color,
                        "player_num": controlled_player.player_num,
                        "wins": controlled_player.wins
                    }
                    
                    obstacles_state = []
                    for obstacle in obstacles:
                        if (is_host and obstacle.player_side == 0) or (not is_host and obstacle.player_side == 1):
                            obstacles_state.append(obstacle.get_state())
                        else:
                            obstacles_state.append(None)
                    
                    combined_data = {
                        "player": player_data,
                        "obstacles": obstacles_state,
                        "remaining_time": remaining_time  
                    }
                    
                    network.send_data(combined_data)
                    last_send_time = current_time
                except Exception as e:
                    print(f"[GAME] Send error: {e}")
            
            try:
                received_data = network.receive_data()
                if received_data:
                    if "ping" in received_data:
                        pass
                    else:
                        opponent_data = received_data.get("player", {})
                        player_num = opponent_data.get("player_num")
                        
                        if player_num == 1:
                            player1.rect.x = opponent_data.get("rect_x", player1.rect.x)
                            player1.rect.y = opponent_data.get("rect_y", player1.rect.y)
                            player1.score = opponent_data.get("score", player1.score)
                            player1.health = opponent_data.get("health", player1.health)
                            player1.color = opponent_data.get("color", player1.color) 
                            player1.wins = opponent_data.get("wins", player1.wins)
                        elif player_num == 2:
                            player2.rect.x = opponent_data.get("rect_x", player2.rect.x)
                            player2.rect.y = opponent_data.get("rect_y", player2.rect.y)
                            player2.score = opponent_data.get("score", player2.score)
                            player2.health = opponent_data.get("health", player2.health)
                            player2.color = opponent_data.get("color", player2.color)
                            player2.wins = opponent_data.get("wins", player2.wins)
                        
                        received_obstacles = received_data.get("obstacles", [])
                        for i, state in enumerate(received_obstacles):
                            if i < len(obstacles) and state is not None:
                                if (is_host and obstacles[i].player_side == 1) or (not is_host and obstacles[i].player_side == 0):
                                    obstacles[i].set_state(state)
            except Exception as e:
                print(f"[NETWORK] Receive error: {e}")

       
        
        for obstacle in obstacles:
            points = obstacle.update()
            
            if points > 0:
                if obstacle.player_side == 0:
                    player1.score += points
                else:
                    player2.score += points
            
            if obstacle.player_side == 0:  
                player = player1
            else:  
                player = player2
                
            obstacle_rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
            if player.rect.colliderect(obstacle_rect):
                try:
                    crash_sound.play()
                except:
                    pass
                player.health -= 10
                obstacle.reset()
        
        for obstacle in obstacles:
            obstacle.draw(wn)
            
        player1.draw(wn)
        player2.draw(wn)
        
        score_board(player1, player2)
        display_controls()
        
        display_coordinates(player1, player2)
        
        font = pygame.font.Font(None, 24)
        network_status = "Connected" if network.connected else "Disconnected"
        status_text = font.render(f"Network: {network_status}", True, WHITE)
        wn.blit(status_text, (10, 130))
        
        time_color = WHITE
        if remaining_time < 10:  
            time_color = RED
        time_text = font.render(f"Time remaining: {int(remaining_time)} seconds", True, time_color)
        wn.blit(time_text, (10, 160))

        if player1.health <= 0 or player2.health <= 0:
            game_over(player1, player2, client)

        pygame.display.update()
        
        clock.tick(60)
    
    network.close()
    pygame.quit()

if __name__ == "__main__":
    try:
        args = {}
        i = 1
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                param = sys.argv[i][2:]  
                if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith("--"):
                    args[param] = sys.argv[i+1]
                    i += 2
                else:
                    args[param] = True
                    i += 1
            else:
                i += 1
        
        print(f"Game started with arguments: {args}")
        
        if "is-host" in args and "opponent-ip" in args and "opponent-port" in args:
            is_host = args["is-host"] == '1'
            opponent_ip = args["opponent-ip"]
            opponent_port = int(args["opponent-port"]) if args["opponent-port"].isdigit() else None
            
            print(f"Running in multiplayer mode. Is host: {is_host}, Opponent IP: {opponent_ip}, Port: {opponent_port}")
            
            try:
                from client import RacingClient
                
                client = RacingClient()
                client.username = args.get("username")
                client.car_color = args.get("car-color")
                client.is_host = is_host
                
                print("Connecting to server...")
                client.connect_to_server()
                
                print("Starting game loop...")
                game_loop(is_host, opponent_ip, opponent_port, client)
            except ImportError as e:
                print(f"[GAME] Client module not available: {e}")
                print("[GAME] Running standalone")
                game_loop(is_host, opponent_ip, opponent_port)
            except Exception as e:
                print(f"[GAME] Error: {e}")
                
                print("[GAME] An error occurred. Press Enter to exit...")
                input()
        else:
            print("[GAME] Running in standalone mode")
            game_loop()
    except Exception as e:
        print(f"[GAME] Critical error: {e}")
        
        print("[GAME] An error occurred. Press Enter to exit...")
        input()
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, 
                            QMessageBox, QTabWidget, QComboBox, QGroupBox, 
                            QRadioButton, QButtonGroup, QFormLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                            QGridLayout, QDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QIntValidator

from client import RacingClient

class SignalHandler(QObject):
    update_signal = pyqtSignal(str, dict)

class LoginWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.signal_handler = SignalHandler()
        self.signal_handler.update_signal.connect(self.handle_client_signal)
        self.client.set_gui_callback(self.receive_client_signal)
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Racing Game - Login")
        self.setMinimumSize(400, 300)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
      
        login_group = QGroupBox("Login")
        login_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        login_layout.addRow("Username:", self.username_input)
        login_layout.addRow("Password:", self.password_input)
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        login_layout.addRow("", login_btn)
        
        login_group.setLayout(login_layout)
        
        register_group = QGroupBox("Register")
        register_layout = QFormLayout()
        
        self.reg_username_input = QLineEdit()
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        
        self.car_color_combo = QComboBox()
        self.car_color_combo.addItems(["Chili Red", "Ocean Blue", "Cherry Blossom", "Forest Green"])
        
        register_layout.addRow("Username:", self.reg_username_input)
        register_layout.addRow("Password:", self.reg_password_input)
        register_layout.addRow("Car Color:", self.car_color_combo)
        
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register)
        register_layout.addRow("", register_btn)
        
        register_group.setLayout(register_layout)
        
        server_group = QGroupBox("Server Connection")
        server_layout = QFormLayout()
        
        self.server_host_input = QLineEdit("localhost")
        self.server_port_input = QLineEdit("5555")
        self.server_port_input.setValidator(QIntValidator(1, 65535))
        
        connect_btn = QPushButton("Connect to Server")
        connect_btn.clicked.connect(self.connect_to_server)
        
        server_layout.addRow("Server Host:", self.server_host_input)
        server_layout.addRow("Server Port:", self.server_port_input)
        server_layout.addRow("", connect_btn)
        
        server_group.setLayout(server_layout)
       
        main_layout.addWidget(server_group)
        main_layout.addWidget(login_group)
        main_layout.addWidget(register_group)
       
        self.statusBar().showMessage("Not connected to server")
    
    def connect_to_server(self):
        host = self.server_host_input.text()
        port = int(self.server_port_input.text())
        
        self.client.server_host = host
        self.client.server_port = port
        
        if self.client.connect_to_server():
            self.statusBar().showMessage(f"Connected to server at {host}:{port}")
        else:
            QMessageBox.critical(self, "Connection Error", "Failed to connect to server")
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required")
            return
        
        self.client.login(username, password)
        self.statusBar().showMessage("Logging in...")
    
    def register(self):
        username = self.reg_username_input.text()
        password = self.reg_password_input.text()
        car_color = self.car_color_combo.currentText()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required")
            return
        
        self.client.register(username, password, car_color)
        self.statusBar().showMessage("Registering...")
    
    def receive_client_signal(self, signal_type, data):
        self.signal_handler.update_signal.emit(signal_type, data)
    
    def handle_client_signal(self, signal_type, data):
        if signal_type == 'server_response':
            status = data.get('status')
            message = data.get('message', '')
            
            if status == 'success':
                if 'car_color' in data and 'games_won' in data:
                    self.client.car_color = data.get('car_color')
                    self.client.games_won = data.get('games_won')
                    
                    self.lobby_window = LobbyWindow(self.client)
                    self.lobby_window.show()
                    self.lobby_window.handle_client_signal(
                        'server_response', 
                        { 'online_users': [], }
                    )

                    self.close()
                else:
                    QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Error", message)
            
            self.statusBar().showMessage(message)
        
        elif signal_type == 'server_disconnected':
            QMessageBox.critical(self, "Connection Lost", "Disconnected from server")
            self.statusBar().showMessage("Disconnected from server")
        
        elif signal_type == 'server_error':
            QMessageBox.critical(self, "Server Error", data.get('message', 'Unknown error'))
            self.statusBar().showMessage("Server error")

class RaceRequestDialog(QDialog):
    def __init__(self, requester, parent=None):
        super().__init__(parent)
        self.requester = requester
        self.result = False
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Race Request")
        layout = QVBoxLayout()
        
        message = QLabel(f"{self.requester} has requested a race with you!")
        layout.addWidget(message)
        
        btn_layout = QHBoxLayout()
        accept_btn = QPushButton("Accept")
        decline_btn = QPushButton("Decline")
        
        accept_btn.clicked.connect(self.accept_race)
        decline_btn.clicked.connect(self.reject_race)
        
        btn_layout.addWidget(accept_btn)
        btn_layout.addWidget(decline_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def accept_race(self):
        self.result = True
        self.accept()
    
    def reject_race(self):
        self.result = False
        self.reject()

class UserStatsDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("User Statistics")
        layout = QFormLayout()
        
        layout.addRow("Username:", QLabel(self.user_data.get('username', 'Unknown')))
        layout.addRow("Games Won:", QLabel(str(self.user_data.get('games_won', 0))))
        layout.addRow("Car Color:", QLabel(self.user_data.get('car_color', 'Unknown')))
        
        status = "Online" if self.user_data.get('is_online', False) else "Offline"
        layout.addRow("Status:", QLabel(status))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addRow("", close_btn)
        
        self.setLayout(layout)

class LobbyWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.signal_handler = SignalHandler()
        self.signal_handler.update_signal.connect(self.handle_client_signal)
        self.client.set_gui_callback(self.receive_client_signal)
        
        self.online_users = []
        self.init_ui()
        
        self.update_online_users()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_online_users)
        self.update_timer.start(5000)  
    
    def init_ui(self):
        self.setWindowTitle(f"Racing Game Lobby - {self.client.username}")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        user_info_layout = QHBoxLayout()
        self.username_label = QLabel(f"Username: {self.client.username}")
        self.car_label = QLabel(f"Car Color: {self.client.car_color}")
        self.wins_label = QLabel(f"Games Won: {self.client.games_won}")
        
        user_info_layout.addWidget(self.username_label)
        user_info_layout.addWidget(self.car_label)
        user_info_layout.addWidget(self.wins_label)
        user_info_layout.addStretch()
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        user_info_layout.addWidget(logout_btn)
        
        main_layout.addLayout(user_info_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        
        users_group = QGroupBox("Online Users")
        users_layout = QVBoxLayout()
        
        self.users_list = QListWidget()
        self.users_list.itemDoubleClicked.connect(self.user_selected)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_online_users)
        
        users_layout.addWidget(self.users_list)
        users_layout.addWidget(refresh_btn)
        
        users_group.setLayout(users_layout)
        splitter.addWidget(users_group)
        
        actions_group = QGroupBox("User Actions")
        actions_layout = QVBoxLayout()
        
        self.selected_user_label = QLabel("No user selected")
        actions_layout.addWidget(self.selected_user_label)
        
        btn_layout = QGridLayout()
        
        view_stats_btn = QPushButton("View Stats")
        view_stats_btn.clicked.connect(self.view_user_stats)
        btn_layout.addWidget(view_stats_btn, 0, 0)
        
        request_race_btn = QPushButton("Request Race")
        request_race_btn.clicked.connect(self.request_race)
        btn_layout.addWidget(request_race_btn, 0, 1)
        
        actions_layout.addLayout(btn_layout)
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        splitter.addWidget(actions_group)
        
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)
        
        self.statusBar().showMessage("Connected to server")
    
    def update_online_users(self):
        self.client.get_online_users()
        
    def user_selected(self, item):
        selected_username = item.text()
        self.selected_user_label.setText(f"Selected: {selected_username}")
        
        self.client.get_user_stats(selected_username)
    
    def view_user_stats(self):
        selected_items = self.users_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a user first")
            return
        
        selected_username = selected_items[0].text()
        self.client.get_user_stats(selected_username)
    
    def request_race(self):
        selected_items = self.users_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a user first")
            return
        
        selected_username = selected_items[0].text()
        self.client.request_race(selected_username)
        self.statusBar().showMessage(f"Race request sent to {selected_username}")
    
    def logout(self):
        self.client.logout()
        self.close()
        
        login_window = LoginWindow(self.client)
        login_window.show()
    
    def receive_client_signal(self, signal_type, data):
        self.signal_handler.update_signal.emit(signal_type, data)
    
    def handle_client_signal(self, signal_type, data):
        if signal_type == 'server_response':
            if 'online_users' in data:
                self.online_users = data.get('online_users', [])
                self.users_list.clear()
                for user in self.online_users:
                    self.users_list.addItem(user)
            elif 'username' in data and 'games_won' in data:
                stats_dialog = UserStatsDialog(data, self)
                stats_dialog.exec_()
            elif signal_type == 'win_updated':
                self.client.games_won = data['games_won']
                self.statusBar().showMessage("You just won! Total wins updated.")
            
            else:
                status = data.get('status')
                message = data.get('message', '')
                if status == 'success':
                    self.statusBar().showMessage(message)
                else:
                    QMessageBox.warning(self, "Error", message)
                    self.statusBar().showMessage(message)
        
        elif signal_type == 'race_request':
            requester = data.get('from')
            dialog = RaceRequestDialog(requester, self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.client.respond_to_race(requester, dialog.result)
                
                if dialog.result:
                    self.statusBar().showMessage(f"Accepted race with {requester}")
                else:
                    self.statusBar().showMessage(f"Declined race with {requester}")
        
        elif signal_type == 'race_starting':
            opponent = data.get('opponent')
            QMessageBox.information(self, "Race Starting", f"Get ready to race against {opponent}!")
            self.statusBar().showMessage(f"Starting race with {opponent}")
        
        elif signal_type == 'race_declined':
            by_user = data.get('by')
            QMessageBox.information(self, "Race Declined", f"{by_user} declined your race request")
            self.statusBar().showMessage(f"Race request declined by {by_user}")
        
        elif signal_type == 'launch_game':
            opponent = data.get('opponent')
            QMessageBox.information(self, "Race Starting", f"Launching race game against {opponent}!")
            print(f"[GUI] Launching race game against {opponent}")
        
        elif signal_type == 'server_disconnected':
            QMessageBox.critical(self, "Connection Lost", "Disconnected from server")
            self.close()
            login_window = LoginWindow(self.client)
            login_window.show()
        
        elif signal_type == 'server_error':
            QMessageBox.critical(self, "Server Error", data.get('message', 'Unknown error'))

def main():
    app = QApplication(sys.argv)
    client = RacingClient()
    login_window = LoginWindow(client)
    login_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
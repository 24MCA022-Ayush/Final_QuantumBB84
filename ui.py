import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
                           QTextEdit, QLabel, QMessageBox, QInputDialog, 
                           QWidget, QTextBrowser, QFrame, QStyle)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QFont, QPalette, QColor, QIcon
from network_discovery import BB84NetworkNode
import socket
import time
import os
from datetime import datetime

def log_message(sender, receiver, message, is_secure):
    log_file = "messages_log.txt"
    timestamp = datetime.now().isoformat()
    
    if is_secure:
        log_entry = f"Encrypted|{sender}|{receiver}|{message}|{timestamp}\n"
    else:
        log_entry = f"Normal|{sender}|{receiver}|{message}|{timestamp}\n"
    
    with open(log_file, "a") as file:
        file.write(log_entry)
    

class MessageHandler(QObject):
    message_received = pyqtSignal(str, str)

class UserListItem(QWidget):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.selected = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Container for user info
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #353535;
                border-radius: 6px;
            }
        """)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(10, 8, 10, 8)
        
        # User icon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #C8C8CC;
                border-radius: 12px;
                padding: 2px;
                color: white;
            }
        """)
        icon_label.setText("👤")
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Username
        self.name_label = QLabel(username)
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-family: 'Nunito';
                font-size: 14px;
                padding-left: 10px;
                font-weight: 800;
            }
        """)
        
        # Menu button
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(24, 24)
        menu_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: #404060;
                border-radius: 4px;
            }
        """)
        
        container_layout.addWidget(icon_label)
        container_layout.addWidget(self.name_label, 1)
        container_layout.addWidget(menu_btn)
        
        layout.addWidget(self.container)
        
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            list_widget = self.parent().parent()
            if isinstance(list_widget, QListWidget):
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    widget = list_widget.itemWidget(item)
                    if widget == self:
                        list_widget.setCurrentItem(item)
                        self.setSelected(True)
                    else:
                        widget.setSelected(False)

    def setSelected(self, selected):
        self.selected = selected
        if selected:
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #5A5A5A;
                    border-radius: 6px;
                }
            """)
        else:
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #5A5A5A;
                    border-radius: 6px;
                }
            """)

    def enterEvent(self, event):
        if not self.selected:
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #383838;
                    border-radius: 6px;
                }
            """)
    
    def leaveEvent(self, event):
        if not self.selected:
            self.container.setStyleSheet("""
                QWidget {
                    background-color: #6A6A6D;
                    border-radius: 6px;
                }
            """)



class BB84NetworkUI(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.node = BB84NetworkNode(username)
        self.message_handler = MessageHandler()
        self.toggle_switch = QPushButton()
        self.is_secure_mode = True  # Add this variable to track secure mode state

        self.message_handler.message_received.connect(self.update_message_display)

        self.node.message_received_callback = self.handle_received_message
        
        self.messages_html = []
        self.initUI()
        self.node.start()

    def send_normal_message(self, target_ip, message, port):
        """Send a message using normal TCP/IP without quantum encryption."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.settimeout(10)
                tcp_socket.connect((target_ip, port))
                send_time = time.time()
                message_with_timestamp = f"{self.username}|{message}|{send_time}"
                tcp_socket.sendall(message_with_timestamp.encode())
                return True
            
        except Exception as e:
            print(f"Failed to send normal message: {e}")
            return False
        
    def initUI(self):
        self.setWindowTitle('Quantum Secured Communication')
        self.setGeometry(100, 100, 900, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #212121;
            }
            QWidget {
                color: #FFFFFF;
                font-family: 'Nunito';
                font-weight: bold;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Main Title
        title_label = QLabel("Quantum Secured Communication")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
            padding: 10px 0;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Content Container
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Users section
        users_container = QWidget()
        users_container.setStyleSheet("""
            QWidget {
                background-color: #3B3B3B;
                border-color: 10px solid #31C6EF;
                border-radius: 12px;
            }
        """)
        users_layout = QVBoxLayout(users_container)
        users_layout.setContentsMargins(10, 10, 10, 10)
        users_layout.setSpacing(8)
        
        # Header with count
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(5, 0, 5, 0)
        
        users_label = QLabel('Available Users')
        users_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: white;
        """)
        
        self.count_label = QLabel('0')
        self.count_label.setObjectName('user_count')
        self.count_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            margin-right: 5px;
        """)
        
        count_icon = QLabel("👥")
        count_icon.setStyleSheet("font-size: 14px;")
        
        header_layout.addWidget(users_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        header_layout.addWidget(count_icon)
        
        # Users List
        self.users_list = QListWidget()
        self.users_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: transparent;
            }
        """)
        
        users_layout.addWidget(header_container)
        users_layout.addWidget(self.users_list)
        
        # Secure Communication Toggle
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_label = QLabel("Secure Communication")
        toggle_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.toggle_switch = QPushButton()  # Make it an instance variable
        self.toggle_switch.setCheckable(True)
        self.toggle_switch.setChecked(self.is_secure_mode)  # Set initial state
        self.toggle_switch.setFixedSize(50, 25)
        self.toggle_switch.setStyleSheet("""
            QPushButton {
                background-color: #404041;
                border-radius: 12px;
                border: 2px solid #2B5AFE;
            }
            QPushButton:checked {
                background-color: #2B5AFE;
            }
        """)
        
        self.toggle_switch.clicked.connect(self.toggle_secure_mode)  # Connect the signal
        toggle_layout.addWidget(toggle_label)
        toggle_layout.addWidget(self.toggle_switch)
        users_layout.addWidget(toggle_container)

        # Chat Area
        chat_container = QWidget()
        chat_container.setStyleSheet("""
            QWidget {
                background-color: #2F2F2F;
                border-radius: 12px;
            }
        """)
        
        # Using QVBoxLayout for proper bottom alignment
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(10, 10, 10, 10)

        # Chat Header
        chat_header = QLabel('Messages')
        chat_header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: white;
            padding: 10px 5px;
        """)
        chat_layout.addWidget(chat_header)
        
        # Messages Display with Stretch
        messages_container = QWidget()
        messages_layout = QVBoxLayout(messages_container)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        
        self.messages_display = QTextBrowser()
        self.messages_display.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                padding: 15px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #515151;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: transparent;
            }
        """)
        messages_layout.addWidget(self.messages_display)
        chat_layout.addWidget(messages_container, 1)  # Add stretch

        # Bottom Section
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setSpacing(10)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Encryption Status
        encryption_status = QWidget()
        status_layout = QVBoxLayout(encryption_status)
        status_layout.setContentsMargins(0, 5, 0, 5)
        status_layout.setSpacing(2)
        
        self.encryption_status_label = QLabel('END to END Message is Quantum Encrypted')
        self.encryption_status_label.setStyleSheet("""
            color: #00C2FF;
            font-size: 12px;
            font-family: 'Nunito';
        """)
        self.encryption_status_label.setAlignment(Qt.AlignCenter)
        
        self.encryption_status_line = QFrame()
        self.encryption_status_line.setFrameShape(QFrame.HLine)
        self.encryption_status_line.setFixedHeight(1)
        self.encryption_status_line.setStyleSheet("background-color: #00C2FF;")
        
        status_layout.addWidget(self.encryption_status_label)
        status_layout.addWidget(self.encryption_status_line)
        bottom_layout.addWidget(encryption_status)
        
        # Message Input
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFixedHeight(60)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #404041;
                border: 1px solid #00C2FF;    /* Added blue border */
                border-radius: 15px;
                padding: 12px 15px;
                color: white;
                font-family: 'Nunito';
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        send_btn = QPushButton('Send')
        send_btn.setFixedSize(70, 35)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B5AFE;
                border-radius: 17px;
                color: white;
                font-family: 'Nunito';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3365FF;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)
        bottom_layout.addWidget(input_container)
        
        # Add bottom container to chat layout
        chat_layout.addWidget(bottom_container)
        
        # Add panels to content layout
        content_layout.addWidget(users_container, 1)
        content_layout.addWidget(chat_container, 3)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        
        # Initialize timer
        self.users_timer = QTimer()
        self.users_timer.timeout.connect(self.update_online_users)
        self.users_timer.start(1000)
        
        self.update_online_users()

    def toggle_secure_mode(self):
        """Handle toggle switch state changes"""
        self.is_secure_mode = self.toggle_switch.isChecked()
        if self.is_secure_mode:
            self.show_security_status("Quantum Encryption Enabled", True)
        else:
            self.show_security_status("Non-Encrypted", False)

    def show_security_status(self, message, is_secure):
        """Update the security status display"""
        color = "#00C2FF" if is_secure else "#FFA500"
        self.encryption_status_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-family: 'Nunito';
        """)
        self.encryption_status_label.setText(message)
        self.encryption_status_line.setStyleSheet(f"background-color: {color};")
   
    def format_message(self, sender, message):
        is_sent = (sender == self.username)
        
        base_style = """
            background-color: %s;
            padding: 10px 15px;
            border-radius: 16px;
            display: inline-block;
            max-width: fit-content;
            word-wrap: break-word;
            margin: %s;
            color: white;
            font-size: 14px;
            font-family: 'Nunito';
            font-weight: bold;
        """
        
        if is_sent:
            bubble_style = base_style % ("transparent", "5px 0 5px auto")  # Right aligned
            container_align = "right"
            name_align = "right"
            border_radius = "16px 16px 0 16px"
        else:
            bubble_style = base_style % ("transparent", "5px auto 5px 0")  # Left aligned
            container_align = "left"
            name_align = "left"
            border_radius = "16px 16px 16px 0"
            
        return f'''
            <div style="margin: 10px 0;">
                <div style="text-align: {container_align};">
                    <div style="{bubble_style} border-radius: {border_radius};">
                        {message}
                    </div>
                    <div style="color: #808080; font-family: 'Nunito'; font-weight: extra-bold; font-size: 12px; margin-top: 4px; text-align: {name_align};">
                        {sender}
                    </div>
                </div>
            </div>
        '''

    def update_message_display(self, sender, message):
        self.messages_html.append(self.format_message(sender, message))
        full_html = ''.join(self.messages_html)
        self.messages_display.setHtml(full_html)
        
        scrollbar = self.messages_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        current_item = self.users_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Error', 'Please select a user')
            return
            
        widget = self.users_list.itemWidget(current_item)
        if not widget:
            return
            
        target_user = widget.username
        message = self.message_input.toPlainText().strip()
        
        if not message:
            return
            
        try:
            if self.toggle_switch.isChecked():
                # Send using BB84
                if self.node.send_message(target_user, message):
                    self.update_message_display(self.username, message)
                    self.message_input.clear()
                else:
                    QMessageBox.warning(self, 'Error', 'Failed to send message using BB84')
            else:
                # Send using normal method
                devices = self.node.listener.devices
                print(devices)
                target_device = None
                
                # Find the target device in the devices dictionary
                for device_info in devices.values():
                    if device_info.get('username') == target_user:
                        target_device = device_info
                        break
                
                if target_device and 'address' in target_device and 'port' in target_device:
                    target_ip = target_device['address']
                    target_port = target_device['port']
                    
                    if self.send_normal_message(target_ip, message, target_port):

                        log_message(self.username, target_user, message, False)
                        
                        self.update_message_display(self.username, message)
                        self.message_input.clear()
                    else:
                        QMessageBox.warning(self, 'Error', 'Failed to send normal message')
                else:
                    QMessageBox.warning(self, 'Error', 'Target user device information not found')
                
                    
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Send failed: {str(e)}')

    def update_online_users(self):
        try:
            current_selected = self.users_list.currentItem()
            selected_username = None
            if current_selected:
                widget = self.users_list.itemWidget(current_selected)
                if widget:
                    selected_username = widget.username
                
            online_users = self.node.get_online_users()
            if not isinstance(online_users, list):
                return
                
            self.count_label.setText(str(len(online_users)))
            
            self.users_list.clear()
            
            for username in online_users:
                if username == self.username:  # Skip current user
                    continue
                    
                item = QListWidgetItem(self.users_list)
                user_widget = UserListItem(username)
                item.setSizeHint(user_widget.sizeHint())
                
                self.users_list.addItem(item)
                self.users_list.setItemWidget(item, user_widget)
                
                if selected_username and selected_username == username:
                    self.users_list.setCurrentItem(item)
                    user_widget.setSelected(True)
                    
        except Exception as e:
            print(f"Error updating users: {str(e)}")

    def handle_received_message(self, sender, message):
        self.message_handler.message_received.emit(sender, message)
            
    def closeEvent(self, event):
        self.users_timer.stop()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    
    font = QFont('Nunito')
    app.setFont(font)
    
    username_dialog = QInputDialog()
    username_dialog.setWindowTitle('Username')
    username_dialog.setLabelText('Enter your username:')
    username_dialog.setStyleSheet("""
        QInputDialog {
            background-color: #262626;
            color: white;
        }
        QLineEdit {
            background-color: #2A2A3C;
            border: 1px solid #3A3A4C;
            border-radius: 4px;
            padding: 5px;
            color: white;
            font-family: 'Nunito';
        }
        QPushButton {
            background-color: #2B5AFE;
            border: none;
            border-radius: 4px;
            padding: 5px 15px;
            color: white;
            font-family: 'Nunito';
        }
        QPushButton:hover {
            background-color: #3365FF;
        }
    """)
    
    ok = username_dialog.exec_()
    username = username_dialog.textValue()
    
    if ok and username:
        ui = BB84NetworkUI(username)
        ui.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
# network_discovery.py
import socket
import json
import threading
import time
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import netifaces
from bb84_utils import *
import random
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


class BB84NetworkSender:
    
    def __init__(self):
        self.sender_bits = None
        self.sender_bases = None
        self.sender_sifted_key = None
        self.sender_final_key = None
    
    def prepare_message(self, message):
        """Prepare message data for BB84 protocol"""
        # Calculate required number of qubits
        len_key = len(message) * 8 * 2
        #print(f"[INFO] Required key length: {len_key}")

        # Generate sender's bits and bases
        self.sender_bits = [random.randint(0, 1) for _ in range(len_key)]
        
        self.sender_bases = [random.choice(['+', 'x']) for _ in range(len_key)]
        """
        print(f"[INFO] Generated Sender's Bits and Bases.")
        print()
        print(f"[INFO] Sender Bits : {self.sender_bits}")
        print()
        print(f"[INFO] Sender Bases : {self.sender_bases}")
        """
        return {
            'len_key': len_key,
            'sender_bits': self.sender_bits,
            'sender_bases': self.sender_bases,
            'original_message': message
        }
    

    def verify_key_exchange(self, client,receiver_bases):
        
        try:
            self.sender_sifted_key = reconcile_key(self.sender_bits, self.sender_bases, receiver_bases)    
            
            # Select check bits and their indices
            check_bits, check_bit_indices = select_check_bits(self.sender_sifted_key)
            
            # Prepare check bit data to send
            check_data = {
                'type': 'check_bits',
                'check_bits': check_bits,
                'check_bit_indices': check_bit_indices
            }
            client.send(json.dumps(check_data).encode())
            
            # Receive Bob's response
            response = json.loads(client.recv(4096).decode())
            
            if response['type'] == 'check_bits_response':
                if response['status'] == 'error':
                    print("Key verification failed due to mismatched check bits!")
                    print(f"Reason: {response.get('reason', 'Unknown')}")
                    return False
                else:
                    print("Key verification successful.")
                    return True
        
        except Exception as e:
            print(f"Error in key verification: {e}")
            return False

    def encrypt_message(self,message):
        
        final_key = privacy_amplification(self.sender_sifted_key)

        # Add the quantum bit sequence for entropy calculation
        self.sender_final_key = final_key
        
        # Encrypt message using the sifted key
        encrypted_bits = encrypt_message(final_key, message)
        
        return encrypted_bits
    
    def return_finalkey(self):
        
        return self.sender_final_key
    
    

    



class BB84NetworkReceiver:
    def __init__(self):
        self.final_key = None
        self.receiver_bases = None
        self.sifted_key = None
        self.encrypted_bits = None  # Add this line

    def generate_bases(self, len_key):
        """Generate receiver's bases"""
        self.receiver_bases = [random.choice(['+', 'x']) for _ in range(len_key)]
        #print()
        #print(f"[INFO] Receiver bases: {self.receiver_bases}")
        return self.receiver_bases

    def process_received_bits(self, sender_bits, sender_bases):
        """Process received bits and prepare sifted key"""
        self.sifted_key = []
        for i, (s_base, r_base) in enumerate(zip(sender_bases, self.receiver_bases)):
            if s_base == r_base:
                self.sifted_key.append(sender_bits[i])
        
        #print()
        #print(f"[INFO] Sifted key: {self.sifted_key}")
        return self.sifted_key
    
    def process_check_bits(self, client):
        """
        Process check bits from sender
        
        Args:
        - client: Socket connection
        
        Returns:
        - Boolean indicating successful verification
        """
        try:
            # Receive Alice's check bit data
            data = json.loads(client.recv(4096).decode())
            
            if data['type'] == 'check_bits':
                # Get sender's check bit indices
                sender_check_indices = data['check_bit_indices']

                # Validate indices are within sifted key range
                valid_indices = [
                    index for index in sender_check_indices 
                    if index < len(self.sifted_key)
                ]
                
                if not valid_indices:
                    print("[ERROR] No valid check bit indices found!")
                    response = {
                        'type': 'check_bits_response',
                        'status': 'error',
                        'reason': 'No valid check bit indices'
                    }
                    client.send(json.dumps(response).encode())
                    return False
                
                # Select our check bits using SENDER'S indices
                bob_check_bits = [self.sifted_key[index] for index in sender_check_indices]

                # Get sender's check bits for the valid indices
                sender_check_bits = [
                    data['check_bits'][data['check_bit_indices'].index(index)] 
                    for index in valid_indices
                ]
                
                # Verify check bits
                verification_result = perform_error_check(
                    sender_check_bits, 
                    bob_check_bits
                )
                
                # Prepare response
                response = {
                    'type': 'check_bits_response',
                    'status': 'success' if verification_result else 'error',
                    'bob_check_bits': bob_check_bits,
                    'check_bit_indices': sender_check_indices
                }
                client.send(json.dumps(response).encode())
                
                # If verification passes, generate final key
                if verification_result:
                    self.final_key = privacy_amplification(self.sifted_key)
                    #print()
                    #print(f"[INFO] Final key after privacy amplification: {self.final_key}")
                
                return verification_result
        
        except Exception as e:
            print(f"Error processing check bits: {e}")
            return False
        
    def decrypt_message(self, encrypted_bits):
        """Decrypt received message using final key"""
        if not self.final_key:
            raise Exception("No key available for decryption")
        self.encrypted_bits = encrypted_bits  # Store encrypted bits
        decrypted_message = decrypt_message(self.final_key, encrypted_bits)
        #print()
        #print(f"[INFO] Decrypted message: {decrypted_message}")
        return decrypted_message


class BB84ServiceListener(ServiceListener):
    def __init__(self):
        self.devices = {}

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.remove_service(zc, type_, name)
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.devices:
            del self.devices[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            address = socket.inet_ntoa(info.addresses[0])
            port = info.port
            username = info.properties.get(b'username', b'').decode('utf-8')
            self.devices[name] = {
                'address': address,
                'port': port,
                'username': username
            }
            #print(f"[INFO] Service added: {self.devices[name]}")


class BB84NetworkNode:
    def __init__(self, username):
        self.username = username
        self.port = self.get_available_port()
        self.zeroconf = Zeroconf()
        self.listener = BB84ServiceListener()
        self.browser = None
        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connections = {}
        self.bb84_sender = BB84NetworkSender()
        self.bb84_receiver = BB84NetworkReceiver()
        self.error_rates = []
        self.message_received_callback = None
        self.encrypted_message_callback = None

    def get_user_ip(self, username):
        for device in self.listener.devices.values():
            if device['username'] == username:
                return device['address']
        return None

    def get_available_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def start(self):
        self.running = True
        self.browser = ServiceBrowser(self.zeroconf, "_bb84._tcp.local.", self.listener)
        self.socket.bind(('', self.port))
        self.socket.listen(5)
        threading.Thread(target=self.accept_connections).start()
        self.register_service()

    def register_service(self):
        from zeroconf import ServiceInfo
        local_ip = self.get_local_ip()
        #print(f"[INFO] Local IP: {local_ip}")
        service_info = ServiceInfo(
            "_bb84._tcp.local.",
            f"{self.username}._bb84._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties={b'username': self.username.encode()}
        )
        self.zeroconf.register_service(service_info)

    def get_local_ip(self):
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        return ip
        return '127.0.0.1'

    def accept_connections(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                print(f"\n[INFO] Connection accepted from {addr}")
                threading.Thread(target=self.handle_connection, args=(client, addr)).start()
            except Exception as e:
                if self.running:
                    print(f"\n[ERROR] Error accepting connection: {e}")

    def handle_connection(self, client_socket, address):
        client_socket.settimeout(10)  # Add timeout to prevent hanging

        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break

                # Try to parse as JSON (for BB84 messages)
                try:

                    message = json.loads(data.decode())
                    #print(f"[INFO] Received message: {message}")

                    if message['type'] == 'bb84_init':
                        receiver_bases = self.bb84_receiver.generate_bases(message['len_key'])
                        response = {
                            'type': 'bb84_bases',
                            'receiver_bases': receiver_bases
                        }
                        client_socket.send(json.dumps(response).encode())

                    elif message['type'] == 'bb84_key_exchange':
                        sifted_key = self.bb84_receiver.process_received_bits(
                            message['sender_bits'],
                            message['sender_bases']
                        )

                        # Verify check bits
                        if not self.bb84_receiver.process_check_bits(client_socket):
                            print("[ERROR] Key verification failed!")
                            continue

                        response = {'type': 'bb84_key_confirmed', 'status': 'success'}
                        client_socket.send(json.dumps(response).encode())

                    elif message['type'] == 'encrypted_message':
                        try:
                            decrypted = self.bb84_receiver.decrypt_message(message['content'])
                            print(f"Message from {message['sender']}: {decrypted}")
                            
                            if self.message_received_callback:
                                # Call the callback with sender and decrypted message
                                self.message_received_callback(message['sender'], decrypted)
                            
                            response = {'type': 'message_received', 'status': 'success'}
                        except Exception as e:
                            print(f"[ERROR] Error decrypting message: {e}")
                            response = {'type': 'message_received', 'status': 'error'}
                        client_socket.send(json.dumps(response).encode())

                # If not JSON, treat as normal message
                except json.JSONDecodeError:
                    try:
                        normal_message = data.decode()
                        if '|' in normal_message:
                            sender_username,message, timestamp = normal_message.split('|')
                            print(f"\nNormal message received from {sender_username}: {message}")

                            # Call the message received callback if it exists
                            if hasattr(self, 'message_received_callback') and self.message_received_callback:
                                self.message_received_callback(sender_username, message)

                            # Send acknowledgment
                            client_socket.send("ACK".encode())
                    except Exception as e:
                        print(f"[ERROR] Error processing normal message: {e}")

        except socket.timeout:
            print("[WARNING] Connection timed out")
        except ConnectionResetError:
            print("[WARNING] Connection was reset by peer")
        except ConnectionAbortedError:
            print("[WARNING] Connection was aborted")
        except Exception as e:
            print(f"[ERROR] Error handling connection: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    
    def send_message(self, target_username, message):
        target_device = next((device for device in self.listener.devices.values() if device['username'] == target_username), None)

        if not target_device:
            raise Exception(f"User {target_username} not found")

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_device['address'], target_device['port']))
            print(f"\n[INFO] Connected to {target_username} at {target_device['address']}:{target_device['port']}")

            message_data = self.bb84_sender.prepare_message(message)
            
            # Initial key exchange negotiation
            init_data = {'type': 'bb84_init', 'len_key': message_data['len_key']}
            client.send(json.dumps(init_data).encode())

            # Receive receiver's bases
            response = json.loads(client.recv(4096).decode())
            receiver_bases = response['receiver_bases']
            #print()
            #print(f"[INFO] Received receiver bases: {receiver_bases}")

            # Send sender's bits and bases
            key_exchange_data = {
                'type': 'bb84_key_exchange',
                'sender_bits': message_data['sender_bits'],
                'sender_bases': message_data['sender_bases']
            }
            client.send(json.dumps(key_exchange_data).encode())

            # Verify key exchange
            if not self.bb84_sender.verify_key_exchange(client,receiver_bases):
                print("[ERROR] Key verification failed!")
                client.close()
                return {'status' : False , 'quantum_bits' : None , 'len_key' : 0 , 'len_finalkey' : 0}
                return False

            # Encrypt message using verified key
            encrypted_bits = self.bb84_sender.encrypt_message(message)

            # For Eve Window UI
            log_message(self.username, target_username, encrypted_bits, True)

            # Prepare final encrypted message
            final_message = {
                'type': 'encrypted_message',
                'sender': self.username,
                'content': encrypted_bits
            }
            client.send(json.dumps(final_message).encode())
            #print(f"[INFO] Sent encrypted message: {encrypted_bits}")
            print(f"[INFO] Message Send !!!")

            # Wait for receiver's response
            response = json.loads(client.recv(4096).decode())
            print(f"[INFO] Message Send !!!")

            # Testing Entropy Calculation
            return {'status' : response['status'] == 'success' , 
                    'quantum_bits' : self.bb84_sender.return_finalkey() ,
                    'len_key' : message_data['len_key'] ,
                    'len_finalkey' : len(self.bb84_sender.return_finalkey())
                }
        
            # Normal Return Statement
            # return response['status'] == 'success'

        except Exception as e:
            print(f"[ERROR] Error sending message: {e}")
            return {'status' : False , 'quantum_bits' : None , 'len_key' : 0 , 'len_finalkey' : 0}
            return False
        finally:
            client.close()

    def calculate_error_rate(self, sent_bits, receiver_bases):
        matching_bases = sum(1 for s, r in zip(sent_bits, receiver_bases) if s == r)
        error_rate = 1 - (matching_bases / len(sent_bits)) if sent_bits else 0
        #print(f"[INFO] Calculated error rate: {error_rate}")
        return error_rate

    def get_average_error_rate(self):
        avg_error_rate = sum(self.error_rates) / len(self.error_rates) if self.error_rates else 0
        #print(f"[INFO] Average error rate: {avg_error_rate}")
        return avg_error_rate

    def get_online_users(self):
        online_users = [device['username'] for device in self.listener.devices.values() if device['username'] != self.username]
        #print(f"[INFO] Online users: {online_users}")
        return online_users

    def stop(self):
        self.running = False
        self.zeroconf.close()
        self.socket.close()
        print("[INFO] Service stopped")

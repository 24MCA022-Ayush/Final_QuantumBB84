import time
import socket
import threading
from network_discovery import BB84NetworkNode
import numpy as np

def measure_bb84_message_sending_time(node, target_username, message, num_iterations=1000):

    # List to store transmission times
    transmission_times = []
    
    print(f"Measuring BB84 message transmission time for {num_iterations} iterations...")
    
    for i in range(num_iterations):
        # Start time measurement
        start_time = time.time()
        
        # Attempt to send message
        try:
            success = node.send_message(target_username, message)
            
            # End time measurement
            end_time = time.time()
            
            # Calculate transmission time
            transmission_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if success:
                transmission_times.append(transmission_time)
                print(f"Iteration {i+1}: Transmission time = {transmission_time:.2f} ms")
            else:
                print(f"Iteration {i+1}: Message sending failed")
        
        except Exception as e:
            print(f"Iteration {i+1}: Error - {e}")
        
        # Optional: Add a small delay between iterations to prevent overwhelming the network
        #time.sleep(1)
    
    # Calculate statistics if we have successful transmissions
    if transmission_times:
        # Convert to numpy array for easy calculations
        times_array = np.array(transmission_times)
        
        # Calculate statistics
        stats = {
            'mean_time': np.mean(times_array),
            'median_time': np.median(times_array),
            'std_time': np.std(times_array),
            'min_time': np.min(times_array),
            'max_time': np.max(times_array),
            'cv_time': (np.std(times_array) / np.mean(times_array)) * 100
        }
        
        # Print detailed statistics
        print("\nTransmission Time Statistics:")
        print(f"Mean Time: {stats['mean_time']:.2f} ms")
        print(f"Median Time: {stats['median_time']:.2f} ms")
        print(f"Standard Deviation: {stats['std_time']:.2f} ms")
        print(f"Minimum Time: {stats['min_time']:.2f} ms")
        print(f"Maximum Time: {stats['max_time']:.2f} ms")
        print(f"Coefficient of Variation: {stats['cv_time']:.2f}%")
        
        return stats
    else:
        print("No successful transmissions to analyze.")
        return None

def send_normal_message(target_ip, message, port, sender_username):
    """Send a message using normal TCP/IP without quantum encryption."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.settimeout(10)  # Add timeout
            tcp_socket.connect((target_ip, port))
            send_time = time.time()
            message_with_timestamp = f"{sender_username}|{message}|{send_time}"
            tcp_socket.sendall(message_with_timestamp.encode())
            return True
    except ConnectionRefusedError:
        print("Connection refused - make sure the recipient is online")
        return False
    except socket.timeout:
        print("Connection timed out")
        return False
    except Exception as e:
        print(f"Failed to send normal message: {e}")
        return False
    finally:
        if tcp_socket:
            try:
                tcp_socket.close()
            except:
                pass

def main():
    print("BB84 Quantum Key Distribution Network")
    print("====================================")

    username = input("Enter your username: ")
    node = BB84NetworkNode(username)
    node.start()

    print(f"\nStarted BB84 node with username: {username}")
    print("Discovering other nodes on the network...")
    time.sleep(2)  # Give some time for device discovery

    try:
        while True:
            print("\nAvailable commands:")
            print("1. List online users")
            print("2. Send message (BB84)")
            print("3. Send message (Normal)")
            print("4. View error rates")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ")

            if choice == '1':
                online_users = node.get_online_users()
                if online_users:
                    print("\nOnline users:")
                    for i, user in enumerate(online_users, 1):
                        print(f"{i}. {user}")
                else:
                    print("\nNo other users online")

            elif choice in ['2', '3']:
                online_users = node.get_online_users()
                if not online_users:
                    print("\nNo other users online")
                    continue

                print("\nAvailable users:")
                for i, user in enumerate(online_users, 1):
                    print(f"{i}. {user}")

                try:
                    user_index = int(input("\nEnter user number: ")) - 1
                    target_user = online_users[user_index]
                    message = input("Enter your message: ")
                    
                    if choice == '2':
                        print("\nSending message using BB84 protocol...")
                        """
                        i=1
                        while i<=1000:
                            if node.send_message(target_user, message):
                                print("Message sent successfully!")
                            else:
                                print("Failed to send message")
                            print("Process No : ",i)
                            i=i+1
                        
                        if node.send_message(target_user, message):
                            print("Message sent successfully!")
                        else:
                            print("Failed to send message")
                        """
                        # Measure transmission time
                        transmission_stats = measure_bb84_message_sending_time(node, target_user, message)
                        print(transmission_stats)

                            
                    else:  # choice == '3'
                        print("\nSending message using normal protocol...")
                        target_ip = node.get_user_ip(target_user)  # You'll need to implement this method
                        target_device = next((device for device in node.listener.devices.values() 
                                            if device['username'] == target_user), None)
                        
                        if target_device:
                            target_port = target_device['port']  # Use the same port that's already registered
                            if send_normal_message(target_ip, message, target_port, node.username):
                                print("Normal message sent successfully!")
                            else:
                                print("Failed to send normal message")
                    
                except (ValueError, IndexError):
                    print("Invalid selection")

            elif choice == '4':
                error_rate = node.get_average_error_rate()
                print(f"\nAverage error rate: {error_rate:.2%}")
                if node.error_rates:
                    print("Error rates for all transmissions:")
                    for i, rate in enumerate(node.error_rates, 1):
                        print(f"Transmission {i}: {rate:.2%}")
                else:
                    print("No transmissions yet")

            elif choice == '5':
                break

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        node.stop()

if __name__ == "__main__":
    main()
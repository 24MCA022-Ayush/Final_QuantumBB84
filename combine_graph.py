import numpy as np
import matplotlib.pyplot as plt
import os

class NetworkMetricsVisualizer:
    def __init__(self, data_dir='network_data'):
        self.data_dir = data_dir
        
    def load_data(self, filename):
        try:
            with open(filename, 'r') as f:
                return [float(line.strip()) for line in f]
        except FileNotFoundError:
            print(f"File {filename} not found!")
            return []
        
    def load_int_data(self, filename): #function for integer data loading
        try:
            with open(filename, 'r') as f:
                return [int(line.strip()) for line in f]
        except FileNotFoundError:
            print(f"File {filename} not found!") 
            return []
        
    def plot_key_length_vs_message_length(self):
        key_lengths = self.load_int_data('len_key.txt')
        message_lengths = self.load_int_data('len_message.txt')

        if not key_lengths or not message_lengths:
            return

        if len(key_lengths) != len(message_lengths):
            print("Error: Key lengths and message lengths arrays must have the same size.")
            return

        plt.figure(figsize=(10, 6))
        plt.plot(message_lengths, key_lengths, color='green', marker='o', label='Key Length')
        plt.title('Key Length vs. Message Length')
        plt.xlabel('Message Length')
        plt.ylabel('Key Length')
        plt.grid(True)
        plt.legend()
    
    
    def plot_entropy_bar(self):
        entropy_data = self.load_data('entropy_data.txt')
        if not entropy_data:
            return
        iterations = range(1, len(entropy_data) + 1)
        plt.figure(figsize=(12, 6))  # Increased figure size for better readability
        plt.bar(iterations, entropy_data, label='Entropy', color='purple')
        plt.title('Entropy per Iteration (Bar Graph)')
        plt.xlabel('Iterations')
        plt.ylabel('Entropy (bits)')
        plt.ylim(0, 1.1)
        plt.legend()
        plt.grid(True, axis='y')
        plt.xticks(np.arange(1, len(entropy_data) + 1, step=max(1, len(entropy_data) // 10)))
        avg_entropy = np.mean(entropy_data)
        plt.axhline(y=avg_entropy, color='red', linestyle='--', label=f'Average Entropy: {avg_entropy:.2f}')
        plt.show(block=False)

    def plot_entropy_line(self):
        entropy_data = self.load_data('entropy_data.txt')
        if not entropy_data:
            return
        iterations = range(1, len(entropy_data) + 1)
        
        # Calculate moving average (adjust window size as needed)
        window_size = 20  
        moving_average = np.convolve(entropy_data, np.ones(window_size), 'valid') / window_size
        moving_average_iterations = range(window_size, len(entropy_data) + 1)


        plt.figure(figsize=(12, 6))
        plt.plot(iterations, entropy_data, label='Entropy', color='purple', alpha=0.5) #alpha to make line less dominant
        plt.plot(moving_average_iterations, moving_average, label=f'{window_size}-Iteration Moving Average', color='red', linewidth=2) #highlight the moving average
        plt.title('Entropy per Iteration (Line Graph)')
        plt.xlabel('Iterations')
        plt.ylabel('Entropy (bits)')
        plt.ylim(0, 1.1)
        plt.legend()
        plt.grid(True)
        plt.show(block=False)

    


    def plot_average_time(self):
        
        file1 = 'transmission_times_bb84.txt'
        file2 = 'transmission_times_e91.txt'

        transmission_times1 = self.load_data(file1)
        transmission_times2 = self.load_data(file2)

        if not transmission_times1 or not transmission_times2:
            return
        
        # Handle potentially different lengths gracefully
        max_len = max(len(transmission_times1), len(transmission_times2))
        iterations = range(1, max_len + 1)

        avg_times1 = [np.mean(transmission_times1[:i]) for i in range(1, len(transmission_times1) + 1)]
        avg_times2 = [np.mean(transmission_times2[:i]) for i in range(1, len(transmission_times2) + 1)]


        plt.figure(figsize=(10, 6))

        plt.plot(range(1, len(avg_times1) + 1), avg_times1, label=f'Average Time (BB84)', color='blue', marker='o')
        plt.plot(range(1, len(avg_times2) + 1), avg_times2, label=f'Average Time (E91)', color='red', marker='x')

        plt.title('Average Transmission Time')
        plt.xlabel('Iterations')
        plt.ylabel('Time (ms)')
        plt.legend()
        plt.grid(True)
        plt.show(block=False)  # Open in a non-blocking way


    def plot_throughput(self):
        file1 = 'throughput_data_bb84.txt'
        file2 = 'throughput_data_e91.txt'

        throughput_data1 = self.load_data(file1)
        throughput_data2 = self.load_data(file2)

        if not throughput_data1 or not throughput_data2:
            return
        
        # Handle potentially different lengths gracefully
        max_len = max(len(throughput_data1), len(throughput_data2))
        iterations = range(1, max_len + 1)

        avg_throughput1 = [np.mean(throughput_data1[:i]) for i in range(1, len(throughput_data1) + 1)]
        avg_throughput2 = [np.mean(throughput_data2[:i]) for i in range(1, len(throughput_data2) + 1)]


        plt.figure(figsize=(10, 6))

        plt.plot(range(1, len(avg_throughput1) + 1), avg_throughput1, label=f'Throughput (msgs/sec) (BB84)', color='blue', marker='o')
        plt.plot(range(1, len(avg_throughput2) + 1), avg_throughput2, label=f'Throughput (msgs/sec) (E91)', color='red', marker='x')

        plt.title('Throughput')
        plt.xlabel('Iterations')
        plt.ylabel('Throughput (msgs/sec)')
        plt.legend()
        plt.grid(True)
        plt.show(block=False)  # Open in a non-blocking way

    def plot_error_rate(self):
        file1 = 'error_data_bb84.txt'
        file2 = 'error_data_e91.txt'

        error_data1 = self.load_data(file1)
        error_data2 = self.load_data(file2)

        if not error_data1 or not error_data2:
            return
        
        # Handle potentially different lengths gracefully
        max_len = max(len(error_data1), len(error_data2))
        iterations = range(1, max_len + 1)

        avg_error_times1 = [np.mean(error_data1[:i]) for i in range(1, len(error_data1) + 1)]
        avg_error_times2 = [np.mean(error_data2[:i]) for i in range(1, len(error_data2) + 1)]


        plt.figure(figsize=(10, 6))

        plt.plot(range(1, len(avg_error_times1) + 1), avg_error_times1, label=f'Error Rate (%) (BB84)', color='blue', marker='o')
        plt.plot(range(1, len(avg_error_times2) + 1), avg_error_times2, label=f'Error Rate (%) (E91)', color='red', marker='x')

        plt.title('Error Rate')
        plt.xlabel('Iterations')
        plt.ylabel('Error Rate (%)')
        plt.legend()
        plt.grid(True)
        plt.show(block=False)  # Open in a non-blocking way


    def plot_all_metrics(self):
        self.plot_average_time()
        self.plot_throughput()
        self.plot_error_rate()
        #self.plot_entropy_bar()
        #self.plot_entropy_line()
        #self.plot_key_length_vs_message_length()
        
        # Keep the plots open until closed by the user
        plt.show()


def main():
    visualizer = NetworkMetricsVisualizer()
    visualizer.plot_all_metrics()


if __name__ == "__main__":
    main()
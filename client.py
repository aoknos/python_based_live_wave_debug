import socket
import struct
import time
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import os
import json
from filters import lowpass_filter
from fft import compute_fft

# Set up UDP socket
UDP_IP = "0.0.0.0"
UDP_PORT = 6000

BROADCAST_IP = '224.1.1.1'
UDP_ADVERT_PORT = 5007
ADVERT_INTERVAL = 1000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
#fixed-size packet (8 bytes header + 1024 bytes payload)
PACKET_HEADER_SIZE = 8
PACKET_PAYLOAD_SIZE = 1024
PACKET_SIZE = PACKET_HEADER_SIZE + PACKET_PAYLOAD_SIZE

# Buffer for data storage (store the last 10,000 points)
BUFFER_SIZE = 10000
data_buffer = deque(maxlen=BUFFER_SIZE)
TIME_FOR_NEW_FILE = 30
SIZEOF_INT = 4;
SIZEOF_FLOAT = 4;

# Filter parameters
SAMPLING_FREQ = 2000  # Hz
CUTOFF_FREQ = 10     # Hz
FFT_POINTS = 256     # FFT resolution

# Plotting data
y_data = np.zeros(BUFFER_SIZE)
y_filtered = np.zeros(BUFFER_SIZE)

# Create matplotlib figure and subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

#last_received_time = time.time()
last_received_time = 0
file_start_time = last_received_time
data_dir = 'data_files'
os.makedirs(data_dir, exist_ok=True)

Vadc = 3.3 #Volts

def advertise_service(service_info):
    global UDP_ADVERT_PORT
    global BROADCAST_IP
    global ADVERT_INTERVAL
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    while True:
        # Convert service info to JSON and send
        message = json.dumps(service_info).encode('utf-8')
        sock.sendto(message, (BROADCAST_IP, UDP_ADVERT_PORT))
        time.sleep(ADVERT_INTERVAL)

def start_advertising(service_info):
    # Start advertising in background thread
    thread = threading.Thread(target=advertise_service, args=(service_info,))
    thread.daemon = True
    thread.start()
    return thread

def tuple2Str(bytes_tuple):
    parsedStr = ''
    for byte in bytes_tuple:
        if byte == b'\x00':
            break
        parsedStr += byte.decode('utf-8')

    return parsedStr

def create_new_file(payload):
    global current_file, last_received_time, file_start_time
    DACDevices = ["DAC8532", "PWM_ARDUINO2040"]
    ADCDevices = ["ADS1256", "ADC_ARDUINO2040"]
    DACWaveForms = ["Saw Tooth", "Sine Wave", "Ramp Wave", "Square Wave", "FM Saw Tooth", "FM Sine Wave", "FM Ramp Wave", "FM Square Wave"]
    current_time = time.time()
    # Close current file and open a new one if data stopped for 5 minutes
    try:
        current_file
    except NameError:
        print("current_file not open. So nothing to close. Opening new one\n")
    else:
        current_file.close()

    file_start_time = current_time
    current_file = open(os.path.join(data_dir, f"data_{int(file_start_time)}.dat"), 'wb')
    current_descdatfile = open(os.path.join(data_dir, f"data_{int(file_start_time)}_desc.json"), 'w')
    #Session Info

    json_str = payload.rstrip(b'\x00').decode('utf-8')
    json_obj = json.loads(json_str)
    print(json_obj)

    current_descdatfile.write(json_str)
    current_descdatfile.close()

    last_received_time = current_time

def save_data_to_file(values):
    global current_file, last_received_time, file_start_time
    current_time = time.time()

    if current_time - last_received_time > TIME_FOR_NEW_FILE:
        # Close current file and open a new one if data stopped for 5 minutes
        try:
            current_file
        except NameError:
            print("current_file not open. So nothing to close. Opening new one\n")
        else:
            current_file.close()

        file_start_time = current_time
        current_file = open(os.path.join(data_dir, f"data_{int(file_start_time)}.dat"), 'wb')

    current_file.write(values);
    # Ensure data is written immediately
    current_file.flush()
    # for value in values:
    #     current_file.write(f"{value}\n")

    last_received_time = current_time


def update_plot(frame):
    """Update matplotlib display with raw and filtered signals and FFTs."""
    global y_data, y_filtered

    buffer_copy = list(data_buffer)
    buffer_length = len(buffer_copy)

    if buffer_length > 0:
        y_data[-buffer_length:] = np.array(buffer_copy)

        # Apply low-pass filter if enough data points
        if buffer_length > 10:
            try:
                y_filtered[-buffer_length:] = lowpass_filter(
                    y_data[-buffer_length:], CUTOFF_FREQ, SAMPLING_FREQ
                )
            except:
                y_filtered[-buffer_length:] = y_data[-buffer_length:]

    # Compute FFTs
    fft_raw = compute_fft(y_data, FFT_POINTS)
    fft_filtered = compute_fft(y_filtered, FFT_POINTS)

    # Clear subplots
    ax1.clear()
    ax2.clear()

    # Time domain plot
    x_time = np.arange(BUFFER_SIZE)
    ax1.plot(x_time, y_data, label='Raw', color='blue', linewidth=1)
    ax1.plot(x_time, y_filtered, label='Filtered', color='green', linewidth=1)
    ax1.set_title('Signal - Real Time')
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_ylim(0, Vadc)
    ax1.legend()
    ax1.grid(True)

    # FFT plot
    x_freq = np.linspace(0, SAMPLING_FREQ / 2, FFT_POINTS // 2 + 1)
    ax2.plot(x_freq, fft_raw, label='Raw FFT', color='blue', linewidth=1)
    ax2.plot(x_freq, fft_filtered, label='Filtered FFT', color='green', linewidth=1)
    ax2.set_title('FFT Spectrum')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Magnitude')
    ax2.legend()
    ax2.grid(True)

    return ax1, ax2

def unpack_and_swap_values(payload, value_size):
    """Unpack data values from payload with byte-swapping based on specified byte size (1, 2, or 4)."""
    values = []
    offset = 0
    for _ in range(1024 // value_size):
        if value_size == 1:
            # Directly assign the 1-byte value without swapping
            swapped_value = struct.unpack('b', payload[offset:offset + 1])[0]
            swapped_value = Vadc*swapped_value/(2 ** (8) - 1)
        elif value_size == 2:
            # Swap two bytes: AB -> BA
            swapped_value = struct.unpack('!h', payload[offset + 1:offset + 2] + payload[offset:offset + 1])[0]
            swapped_value = Vadc*swapped_value/(2 ** (16) - 1)
        elif value_size == 4:
            # Swap four bytes: ABCD -> DCBA
            swapped_value = struct.unpack('!i', payload[offset + 3:offset + 4] + payload[offset + 2:offset + 3] + payload[offset + 1:offset + 2] + payload[offset:offset + 1])[0]
            swapped_value = Vadc*swapped_value/(2 ** (23) - 1)
        values.append(swapped_value)
        offset += value_size
    return values

def receive_data():
    """Receive and process data from UDP socket."""
    global PACKET_SIZE
    while True:
    # Read the fixed-size packet
        data, _ = sock.recvfrom(PACKET_SIZE)
        # print(data)

        # Unpack header fields and payload
        packet_type, ack_flag, packet_id = struct.unpack('!HHI', data[:PACKET_HEADER_SIZE])
        packet_type = struct.unpack('!H', struct.pack('!H', packet_type)[::-1])[0]
        ack_flag = struct.unpack('!H', struct.pack('!H', ack_flag)[::-1])[0]
        packet_id = struct.unpack('!I', struct.pack('!I', packet_id)[::-1])[0]

        payload = data[PACKET_HEADER_SIZE:]

        # print(packet_type)
        # Determine value size based on packet_type
        if packet_type == 5:
            value_size = 1
        elif packet_type == 6:
            value_size = 2
        elif packet_type == 7:
            value_size = 4
        elif packet_type == 102:
            create_new_file(payload)
            continue  # Start New Session, skip data processing
        else:
            continue  # Invalid packet_type, skip processing

        # Extract and interpret values with byte-swapping based on the dynamic value size
        values = unpack_and_swap_values(payload, value_size)

        # Append the values to the buffer
        data_buffer.extend(values)
        save_data_to_file(payload)

# Start Adv. Service
service_info = {
    "message": "Aoknos Data Capture Service",
    "timeDuration": 300,
    "httpProgressPort": 4000,
    "dataUDPPort": 6000,
    "fsamp": 2000,
    "DAC1waveform": 1,
    "DAC1amplitude": 0.24242424242424243,
    "DAC1frequency": 30.0,
    "DAC2waveform": 1,
    "DAC2amplitude": 0.24242424242424243,
    "DAC2frequency": 30.0,
    "stages": 3,
    "delayBetweenStages": 10,
    "DAC1fmod": 30,
    "DAC2fmod": 50,
    "DAC1maxFreqDev": 30,
    "DAC2maxFreqDev": 50,
    "metaStr": "Low Freq ChannerAr"
}
advertise_thread = start_advertising(service_info)

# Start data reception in a separate thread
threading.Thread(target=receive_data, daemon=True).start()

# Set up animation to update the plot every second
ani = animation.FuncAnimation(fig, update_plot, interval=1000, blit=False)
plt.tight_layout()
plt.show()

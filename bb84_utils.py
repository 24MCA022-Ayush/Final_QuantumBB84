import random
import cirq
import json

def format_binary(bits):
    binary_str = ''.join(str(bit) for bit in bits)
    return ' '.join(binary_str[i:i + 8] for i in range(0, len(binary_str), 8))


def message_to_bits(message):
    bits = []
    for char in message:
        char_bits = format(ord(char), '08b')
        bits.extend(int(bit) for bit in char_bits)
    return bits


def reconcile_key(alice_bits, alice_bases, bob_bases):
    sifted_key = []

    for i, (a_base, b_base) in enumerate(zip(alice_bases, bob_bases)):
        
        if a_base == b_base:
            sifted_key.append(alice_bits[i])
    
    return sifted_key



def select_check_bits(key, sender_indices=None):
    """
    Select check bits either by sender's indices or randomly
    
    Args:
    - key: Full sifted key
    - sender_indices: Indices provided by sender (optional)
    
    Returns:
    - Check bits
    - Indices used
    """

    if sender_indices is None:
        # If no indices provided, randomly select
        num_check_bits = int(len(key) * 0.2)  # 20% of bits
        sender_indices = random.sample(range(len(key)), num_check_bits)
    
    check_bits = [key[index] for index in sender_indices]
    return check_bits, sender_indices




def perform_error_check(alice_check_bits, bob_check_bits, threshold=0.11):
    """
    Perform error checking between Alice and Bob's check bits
    
    Args:
    - alice_check_bits: Check bits from Alice
    - bob_check_bits: Check bits from Bob
    - threshold: Maximum acceptable error rate
    
    Returns:
    - Boolean indicating if key is safe
    """
    if len(alice_check_bits) != len(bob_check_bits):
        print("Unequal check bit lengths!")
        return False
    
    mismatched_bits = sum(a != b for a, b in zip(alice_check_bits, bob_check_bits))
    error_rate = mismatched_bits / len(alice_check_bits)
    
    if error_rate > threshold:
        print(f"Potential eavesdropping detected! Error rate: {error_rate:.2%}")
        return False
    
    print(f"Error check passed. Error rate: {error_rate:.2%}")
    return True





def privacy_amplification(key):
    if len(key) < 2:
        return key

    amplified = []
    for i in range(0, len(key) - 1, 2):
        amplified.append(key[i] ^ key[i + 1])

    return amplified


def bits_to_bytes(bits):
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) == 8:
            byte = 0
            for bit in byte_bits:
                byte = (byte << 1) | bit
            bytes_list.append(byte)
    return bytes_list


def encrypt_message(key, message):
    message_bits = message_to_bits(message)
    encrypted_bits = []

    for i, bit in enumerate(message_bits):
        key_bit = key[i % len(key)]
        encrypted_bits.append(bit ^ key_bit)

    return encrypted_bits


def decrypt_message(key, encrypted_bits):
    decrypted_bits = []

    for i, bit in enumerate(encrypted_bits):
        key_bit = key[i % len(key)]
        decrypted_bits.append(bit ^ key_bit)

    decrypted_bytes = bits_to_bytes(decrypted_bits)
    decrypted_message = ''.join(chr(byte) for byte in decrypted_bytes)

    return decrypted_message

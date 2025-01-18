import random
from ecdsa import SECP256k1, SigningKey
import hashlib
import base58
from multiprocessing import Pool, Value, Lock

# Target Bitcoin address
target_address = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

# Range of private keys
start_value = 40000000000000000
end_value = 0x7ffffffffffffffff

# Random search flag
random_search = True

# Shared variables for process-safe counters
total_keys = Value('i', 0)
lock = Lock()

def pubkey_to_address(pubkey):
    sha256 = hashlib.sha256(pubkey).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()
    prefix = b'\x00'  # Mainnet prefix
    address = prefix + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    address += checksum
    return base58.b58encode(address).decode('utf-8')

def check_private_key(private_key_int):
    private_key = SigningKey.from_secret_exponent(private_key_int, curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    public_key_bytes = public_key.to_string()
    address = pubkey_to_address(public_key_bytes)
    return address == target_address

def worker_process():
    global total_keys
    while True:
        if random_search:
            private_key_int = random.randint(start_value, end_value)
        else:
            # Implement incremental search logic here if needed
            continue
        with lock:
            total_keys.value += 1
            if total_keys.value % 1000 == 0:
                progress = (total_keys.value / (end_value - start_value)) * 100
                print(f"Keys searched: {total_keys.value}, Progress: {progress:.8f}%", end="\r")
        if check_private_key(private_key_int):
            return private_key_int

def main():
    with Pool(processes=4) as pool:  # Adjust number of processes
        result_objects = [pool.apply_async(worker_process) for _ in range(4)]
        
        for result in result_objects:
            private_key = result.get()  # Waits for process completion
            if private_key:
                print(f"\nFound private key: {private_key}")
                pool.terminate()  # Stop other processes
                break

if __name__ == "__main__":
    main()

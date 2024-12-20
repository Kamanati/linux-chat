import socket
import json
import hashlib
import struct
import time
import threading
import argparse

class Miner:
    def __init__(self, pool_url, pool_port, username, password, debug=False):
        self.pool_url = pool_url
        self.pool_port = pool_port
        self.username = username
        self.password = password
        self.socket = None
        self.total_hashes = 0
        self.hashes_per_second = 0
        self.found_hashes = 0
        self.lock = threading.Lock()  # Thread-safe lock for shared variables
        self.debug = debug  # Enable debug mode if specified

    def connect(self):
        """Establishes a socket connection to the mining pool."""
        print(f"Connecting to {self.pool_url}:{self.pool_port}")
        self.socket = socket.create_connection((self.pool_url, self.pool_port))
        #self.socket.settimeout(10)  # Set a timeout of 10 seconds
        self.socket_file = self.socket.makefile('r', encoding='utf-8')

    def send_message(self, message):
        """Sends a message to the pool."""
        self.socket.sendall(json.dumps(message).encode('utf-8') + b'\n')

    def receive_message(self):
        """Receives a message from the pool."""
        try:
            message = self.socket_file.readline().strip()
            if message:
                if self.debug:  # Print raw message in debug mode
                    print(f"Received message: {message}")
                return json.loads(message)
        except socket.timeout:
            if self.debug:  # Print timeout message in debug mode
                print("Socket timed out waiting for a message.")
            return None  # No message received within the timeout period
        return None

    def authenticate(self):
        """Authenticate to the mining pool with username and password."""
        self.send_message({
            'id': 1,
            'method': 'mining.subscribe',
            'params': []
        })
        response = self.receive_message()

        if self.debug:  # Print subscription result in debug mode
            print("Subscribed:", response)

        self.send_message({
            'id': 2,
            'method': 'mining.authorize',
            'params': [self.username, self.password]
        })
        response = self.receive_message()

        if response and response['result']:
            print("Authenticated successfully.")
        else:
            print("Authentication failed.")
            exit()

    def mine(self):
     """Main mining loop that receives work and attempts to find valid shares."""
     while True:
        # Get new work
        work = self.receive_message()

        if work and 'method' in work and work['method'] == 'mining.notify':
            if self.debug:  # Print new work message in debug mode
                print("Received new work.")

            job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs = work['params']

            # Calculate the difficulty target from nbits
            target = int(nbits, 16)

            # Craft the block header
            coinbase = coinb1 + self.username.encode('utf-8').hex() + coinb2
            coinbase_hash_bin = hashlib.sha256(hashlib.sha256(bytes.fromhex(coinbase)).digest()).digest()

            merkle_root_bin = coinbase_hash_bin
            for branch in merkle_branch:
                merkle_root_bin = hashlib.sha256(hashlib.sha256(merkle_root_bin + bytes.fromhex(branch)).digest()).digest()

            # Prepare the block header
            header_hex = version + prevhash + merkle_root_bin.hex() + ntime + nbits + "00000000"

            nonce = 0
            nonce_limit = 1000000  # Set an initial limit for nonces

            # You can set a dynamic nonce limit based on the target difficulty
            while nonce < nonce_limit:
                nonce_bin = struct.pack("<I", nonce)
                block_header_bin = bytes.fromhex(header_hex) + nonce_bin
                block_hash = hashlib.sha256(hashlib.sha256(block_header_bin).digest()).digest()[::-1].hex()

                # Increment total hashes count
                with self.lock:
                    self.total_hashes += 1

                # Check if the hash is valid
                if int(block_hash, 16) < target:
                    print(f"Valid share found! Nonce: {nonce}, Hash: {block_hash}")
                    with self.lock:
                        self.found_hashes += 1  # Increment found hash count
                    self.submit_share(job_id, nonce, block_hash)
                    break

                nonce += 1

    '''
    def mine(self):
        """Main mining loop that receives work and attempts to find valid shares."""
        while True:
            # Get new work
            work = self.receive_message()

            if work and 'method' in work and work['method'] == 'mining.notify':
                if self.debug:  # Print new work message in debug mode
                    print("Received new work.")

                job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs = work['params']

                # Craft the block header
                coinbase = coinb1 + self.username.encode('utf-8').hex() + coinb2
                coinbase_hash_bin = hashlib.sha256(hashlib.sha256(bytes.fromhex(coinbase)).digest()).digest()

                merkle_root_bin = coinbase_hash_bin
                for branch in merkle_branch:
                    merkle_root_bin = hashlib.sha256(hashlib.sha256(merkle_root_bin + bytes.fromhex(branch)).digest()).digest()

                # Prepare the block header
                header_hex = version + prevhash + merkle_root_bin.hex() + ntime + nbits + "00000000"
                target = int(nbits, 16)

                nonce = 0
                nonce_limit = 1000000  # Let's limit nonce for debugging to 1 million
                while nonce < nonce_limit:
                    nonce_bin = struct.pack("<I", nonce)
                    block_header_bin = bytes.fromhex(header_hex) + nonce_bin
                    block_hash = hashlib.sha256(hashlib.sha256(block_header_bin).digest()).digest()[::-1].hex()

                    # Increment total hashes count
                    with self.lock:
                        self.total_hashes += 1

                    # Print hashes every 100,000 attempts for debugging
                    if self.debug and nonce % 100000 == 0:
                        print(f"Nonce: {nonce}, Hash: {block_hash}")

                    # Check if the hash is valid
                    if int(block_hash, 16) < target:
                        print(f"Valid share found! Nonce: {nonce}, Hash: {block_hash}")
                        with self.lock:
                            self.found_hashes += 1  # Increment found hash count
                        self.submit_share(job_id, nonce, block_hash)
                        break

                    nonce += 1
    '''
    def update_hash_rate(self):
        #Update and print hash rate every second.
        tot = self.total_hashes
        while True:
            time.sleep(1)  # Update every second
            with self.lock:
                elapsed_time = 1.0  # Since this is called every second
                if elapsed_time >= 1.0:
                    self.hashes_per_second = self.total_hashes / elapsed_time
                    tot += self.total_hashes
                    print(f"\rHash Rate: {self.hashes_per_second:.2f} H/s | Total: {tot} | Found: {self.found_hashes}", end='', flush=True)
                    self.total_hashes = 0  # Reset total hashes for the next interval

    def submit_share(self, job_id, nonce, hash_hex):
        """Submit a valid share to the pool."""
        self.send_message({
            'id': 3,
            'method': 'mining.submit',
            'params': [self.username, job_id, nonce, hash_hex]
        })
        response = self.receive_message()
        #if self.debug:  # Print share submission result in debug mode
        print("Share submission result:", response)


if __name__ == '__main__':
    # Parse command line arguments for debug mode
    parser = argparse.ArgumentParser(description='Simple Mining Client')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    # Replace with actual pool details and your worker info
    pool_url = 'btc.1pool.org'
    pool_port = 1111
    username = 'bc1qzw7s79eea5ywnmmr4m5c0as2yjtnz8htk0fm5v'
    password = "r1"

    miner = Miner(pool_url, pool_port, username, password, debug=args.debug)
    miner.connect()
    miner.authenticate()

    # Start a thread to update the hash rate every second
    hash_rate_thread = threading.Thread(target=miner.update_hash_rate)
    hash_rate_thread.daemon = True  # Daemonize thread so it exits with the program
    hash_rate_thread.start()

    # Start mining
    miner.mine()

import socket
import json
import hashlib
import struct
import time
import threading
import argparse

class Miner:
    def __init__(self, pool_url, pool_port, username, password, num_threads, debug=False):
        self.pool_url = pool_url
        self.pool_port = pool_port
        self.username = username
        self.password = password
        self.num_threads = num_threads
        self.socket = None
        self.total_hashes = 0
        self.hashes_per_second = 0
        self.found_hashes = 0
        self.lock = threading.Lock()
        self.debug = debug
        self.difficulty = 0  # Initialize difficulty

    def connect(self):
        print(f"Connecting to {self.pool_url}:{self.pool_port}")
        self.socket = socket.create_connection((self.pool_url, self.pool_port))
        self.socket_file = self.socket.makefile('r', encoding='utf-8')

    def send_message(self, message):
        self.socket.sendall(json.dumps(message).encode('utf-8') + b'\n')

    def receive_message(self):
        try:
            message = self.socket_file.readline().strip()
            if message:
                if self.debug:
                    print(f"Received message: {message}")
                return json.loads(message)
        except socket.timeout:
            if self.debug:
                print("Socket timed out waiting for a message.")
            return None
        return None

    def authenticate(self):
        auth_message = {
            "jsonrpc": "2.0",
            "method": "mining.authorize",
            "params": [self.username, self.password],
            "id": 1
        }
        self.send_message(auth_message)
        response = self.receive_message()

        if response is not None:
            if 'result' in response:
                print("Authenticated successfully." if response['result'] else "Authentication failed.")
            else:
                print("Authentication response received, but 'result' key is missing. Response: ", response)
        else:
            print("No response received during authentication.")

    def mine(self):
        while True:
            work = self.receive_message()
            if work:
                if 'method' in work:
                    if work['method'] == 'mining.notify':
                        self.handle_mining_notify(work['params'])
                    elif work['method'] == 'mining.set_difficulty':
                        self.handle_difficulty_set(work['params'])

    def handle_difficulty_set(self, params):
        self.difficulty = params[0]  # Update difficulty
        if self.debug:
            print(f"Difficulty set to: {self.difficulty}")

    def handle_mining_notify(self, params):
        if self.debug:
            print("Received new work.")
        
        job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime, clean_jobs = params
        threads = []

        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.threaded_mining, args=(job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()  # Wait for all threads to finish

    def threaded_mining(self, job_id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime):
        target = int(nbits, 16)
        coinbase = coinb1 + self.username.encode('utf-8').hex() + coinb2
        coinbase_hash_bin = hashlib.sha256(hashlib.sha256(bytes.fromhex(coinbase)).digest()).digest()
        merkle_root_bin = coinbase_hash_bin

        for branch in merkle_branch:
            merkle_root_bin = hashlib.sha256(hashlib.sha256(merkle_root_bin + bytes.fromhex(branch)).digest()).digest()

        header_hex = version + prevhash + merkle_root_bin.hex() + ntime + nbits + "00000000"

        nonce_limit = 4294967295  # Limit for debugging
        nonce_range = nonce_limit // self.num_threads
        start_nonce = nonce_range * (threading.current_thread().ident % self.num_threads)
        end_nonce = start_nonce + nonce_range

        for nonce in range(start_nonce, end_nonce):
            nonce_bin = struct.pack("<I", nonce)
            block_header_bin = bytes.fromhex(header_hex) + nonce_bin
            block_hash = hashlib.sha256(hashlib.sha256(block_header_bin).digest()).digest()[::-1].hex()

            with self.lock:
                self.total_hashes += 1

            if int(block_hash, 16) < target:
                print(f"Valid share found! Nonce: {nonce}, Hash: {block_hash}")
                with self.lock:
                    self.found_hashes += 1
                self.submit_share(job_id, nonce, block_hash)
                break

    def update_hash_rate(self):
        while True:
            time.sleep(1)
            with self.lock:
                self.hashes_per_second = self.total_hashes
                print(f"\rHash Rate: {self.hashes_per_second:.2f} H/s | Total: {self.total_hashes} | Found: {self.found_hashes}", end='', flush=True)
                self.total_hashes = 0  # Reset total hashes for the next interval

    def submit_share(self, job_id, nonce, hash_hex):
        self.send_message({
            'id': 3,
            'method': 'mining.submit',
            'params': [self.username, job_id, nonce, hash_hex]
        })
        response = self.receive_message()
        print("Share submission result:", response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Mining Client')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('-t', '--threads', type=int, default=1, help='Number of threads to use for mining')
    args = parser.parse_args()

    pool_url = 'btc.luckymonster.pro'
    pool_port = 7112
    username = 'bc1qzw7s79eea5ywnmmr4m5c0as2yjtnz8htk0fm5v'
    password = "r1"

    miner = Miner(pool_url, pool_port, username, password, args.threads, debug=args.debug)
    miner.connect()
    miner.authenticate()

    hash_rate_thread = threading.Thread(target=miner.update_hash_rate)
    hash_rate_thread.daemon = True
    hash_rate_thread.start()

    miner.mine()

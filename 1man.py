import random
import hashlib

# SECP256k1 Parameters (simplified)
SECP256k1_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
SECP256k1_n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256k1_g = (0x79BE667EF9DCBBAC55A62ED6FBFBF3A2D1C8C81B7A2C04B5A35C2127E4B3B3F09, 0x48528F1FDE6A1B4B81E5B383B915B858FCF7DCE015A57BCE0363707D15E372E6)

# Base58 Alphabet
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def mod_mul(a, b, p):
    """Modular multiplication (a * b) % p"""
    return (a * b) % p


def mod_exp(base, exp, p):
    """Modular exponentiation base^exp % p"""
    result = 1
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % p
        base = (base * base) % p
        exp = exp // 2
    return result


def generate_keys():
    """Generate ECDSA private and public keys for SECP256k1"""
    priv_key = random.randint(1, SECP256k1_n - 1)
    pub_key_x = mod_mul(SECP256k1_g[0], priv_key, SECP256k1_p)
    pub_key_y = mod_mul(SECP256k1_g[1], priv_key, SECP256k1_p)
    return priv_key, (pub_key_x, pub_key_y)


def sha256(data):
    """SHA-256 hash function"""
    return hashlib.new('sha256', data).digest()


def ripemd160(data):
    """RIPEMD-160 hash function"""
    return hashlib.new('ripemd160', data).digest()


def base58_encode(num):
    """Base58 encoding"""
    encoded = ""
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded
    return encoded


def bytes_to_int(b):
    """Convert bytes to an integer"""
    return int.from_bytes(b, byteorder='big')


def pubkey_to_address(pubkey):
    """Convert public key to Bitcoin address"""
    sha256_hash = sha256(pubkey)
    ripemd160_hash = ripemd160(sha256_hash)
    address = b'\x00' + ripemd160_hash  # Add version byte (0x00 for mainnet)
    checksum = sha256(sha256(address)).digest()[:4]  # First 4 bytes of double SHA-256
    address_with_checksum = address + checksum
    return base58_encode(bytes_to_int(address_with_checksum))


def check_private_key(private_key_int, target_address):
    """Check if the private key matches the target Bitcoin address"""
    pub_key_x, pub_key_y = generate_keys()  # Generate public key from private key
    pubkey_bytes = pub_key_x.to_bytes(32, byteorder='big') + pub_key_y.to_bytes(32, byteorder='big')
    address = pubkey_to_address(pubkey_bytes)
    return address == target_address


def main():
    target_address = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"
    start_value = 40000000000000000
    end_value = 0x7ffffffffffffffff
    print(f"Searching between: {hex(start_value)} - {hex(end_value)}")
    
    while True:
        private_key_int = random.randint(start_value, end_value)
        pub_key_x, pub_key_y = generate_keys()  # Generate public key from private key
        pubkey_bytes = pub_key_x.to_bytes(32, byteorder='big') + pub_key_y.to_bytes(32, byteorder='big')
        address = pubkey_to_address(pubkey_bytes)
        
        if address == target_address:
            print(f"Found target private key: {private_key_int:064x}")
            break


if __name__ == "__main__":
    main()

from cryptography.fernet import Fernet
import os 
from dotenv import load_dotenv

load_dotenv()

key=os.getenv("FERNET_KEY")


key_bytes=key.encode()

fernet=Fernet(key_bytes)


def encrypt_token(token_str: str) -> bytes:
    return fernet.encrypt(token_str.encode())

def decrypt_token(token_bytes: bytes) -> str:
    return fernet.decrypt(token_bytes).decode()









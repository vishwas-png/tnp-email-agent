from sqlmodel import Session, select
from backend.db.database import engine
from backend.db.models import User
from backend.auth.encrypt import encrypt_token, decrypt_token

with Session(engine) as session:
    users = session.exec(select(User)).all()

    for user in users:
        original = user.token_json
        encrypted = encrypt_token(original)
        decrypted = decrypt_token(encrypted)

        print(f"{user.email}: match = {decrypted == original}")
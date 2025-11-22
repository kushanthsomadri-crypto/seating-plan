# create_hash.py
import bcrypt
pw = input("Enter a new admin password (will not be shown): ")
h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())
print("\nCopy this EXACT string and paste it into app.py as ADMIN_PASSWORD_HASH (including the leading b' and trailing '):\n")
print(repr(h))

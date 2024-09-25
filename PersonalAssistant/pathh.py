import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GOOGLE_OAUTH_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'users/credentials.py')
print(GOOGLE_OAUTH_CLIENT_SECRETS_FILE)
import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow

def send_email_via_gmail(subject, body, to):
    token_file = 'token.json'
    credentials_file = 'credentials.json'

    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/gmail.send'])
        except ValueError as e:
            print(f"Error loading credentials: {e}")
            return False
    else:
        print("Token file not found.")
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {'raw': raw_message}
        service.users().messages().send(userId='me', body=message).execute()
        print(f"Email sent to {to}.")
        return True
    except HttpError as error:
        print(f'An error occurred: {error}')
        return False



# def authenticate_and_save_token():
#     scopes = ['https://www.googleapis.com/auth/gmail.send']
#     credentials_file = 'credentials.json'
#     token_file = 'token.json'

#     if not os.path.exists(credentials_file):
#         print(f"Credentials file '{credentials_file}' not found.")
#         return

#     flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes=scopes)

#     try:
#         creds = flow.run_local_server(port=8080, access_type='offline')
#         with open(token_file, 'w') as token:
#             token.write(creds.to_json())
#         print(f'Token saved to {token_file}')
#     except Exception as e:
#         print(f"Error during OAuth flow: {e}")

# if __name__ == '__main__':
#     authenticate_and_save_token()

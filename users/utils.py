from django.conf import settings
from twilio.rest import Client


def send_sms_via_twilio(body, to):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to
        )
        print(f"SMS sent to {to}: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False
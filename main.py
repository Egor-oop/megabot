import os.path
from base64 import urlsafe_b64decode

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authorize():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def get_messages(service):
    msgs = []
    try:
        # Call the Gmail API
        result = service.users().messages().list(userId="me", q='').execute()
        messages = []
        if 'messages' in result:
            messages.extend(result['messages'])

        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId="me", q='', pageToken=page_token).execute()
            messages.extend(result['messages'])
            print(f'Recieved page {page_token}')
        if messages:
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                msgs.append(msg)
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
    print(f'Total messages: {len(msgs)}')
    return msgs


def parse_message_part(part, file):
    mime_type = part.get('mimeType')
    if mime_type in ('text/plain', 'text/html'):
        body = part.get('body')
        data = body.get('data')
        if data:
            text = urlsafe_b64decode(data).decode()
            file.write(text + '\n')
    elif mime_type == 'multipart/alternative':
        parse_parts(part.get('parts'), file)


def parse_parts(parts, file):
    for part in parts:
        parse_message_part(part, file)


def read_message(message, file):
    payload = message.get('payload')
    headers = payload.get('headers')
    if headers:
        for header in headers:
            value = header['value']
            match header['name'].lower():
                case 'from':
                    file.write(f'From:    {value}\n')
                case 'to':
                    file.write(f'To:      {value}\n')
                case 'subject':
                    file.write(f'Subject: {value}\n')
    parse_message_part(payload, file)


def main():
    service = authorize()
    messages = get_messages(service)
    with open('res.txt', 'w') as file:
        for message in messages:
            read_message(message, file)


if __name__ == "__main__":
    main()

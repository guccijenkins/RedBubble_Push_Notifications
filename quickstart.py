import os.path
import base64
from dotenv import load_dotenv

load_dotenv('.env')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import smtplib

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
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

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    RedBubble = os.getenv("RedBubble")
    query = f"-is:starred from: {RedBubble}"
    results = service.users().messages().list(userId="me", q=f"{query}", maxResults=5).execute()
    messages = results.get("messages", [])

    msg_id = messages[0]["id"]
    msg = service.users().messages().get(userId="me", id=msg_id).execute()

    # Extract email content
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    date = next((h["value"] for h in headers if h["name"] == "Date"), "No Date")

    body = ""
    if "parts" in payload:
      for part in payload["parts"]:
        if part["mimeType"] == "text/plain":
          body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
    else:
      body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")


    try:
      parsed_date = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
      formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S %Z")

    except ValueError:
      formatted_date = date  # In case the format is different

    print(f"Subject: {subject}")
    print(f"Received Date: {formatted_date}")
    print(body[0:640])

    email = f"Subject: {subject}\n\nReceived Date: {formatted_date}\n\n{body[0:640]}"

    # send an email to user for latest price updates and trending NFTs
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=os.getenv('user'), password=os.getenv('password'))
        connection.sendmail(from_addr=os.getenv('user'), to_addrs=os.getenv('to_addrs'),
                            msg=email)

  except :
    # TODO(developer) - Handle errors from gmail API.
    print("No new sales")

if __name__ == "__main__":
  main()
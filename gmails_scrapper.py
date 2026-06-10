from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import time
import dbdriver
from os import path
from google_auth_oauthlib.flow import InstalledAppFlow


def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S')

def second_to_millisec(seconds):
    return str(int(seconds * 1000)) + " ms"

def run(
    
        BEFORE = "2048/01/01",
        AFTER = "1970/01/01",
        BATCHES_COUNT = 999999,
        BATCHES_SIZE = 100,
    ):

    dbdriver.create_emails_db()

    # if token json doesnt exists, authenticate using google oauth 
    CREDS = None
    if not path.exists("token.json"):

        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            ["https://www.googleapis.com/auth/gmail.modify"]
        )
        CREDS = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(CREDS.to_json())
        
        
        
    else:
        CREDS = Credentials.from_authorized_user_file(
            "token.json",
            ["https://www.googleapis.com/auth/gmail.modify"]
        )
        
    gmail = build("gmail", "v1", credentials=CREDS)



    def extract_text(payload):
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        return base64.urlsafe_b64decode(
                            data.encode()
                        ).decode(errors="ignore")

        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(
                data.encode()
            ).decode(errors="ignore")

        return ""


    def make_callback(batch_data):

        def callback(request_id, msg, exception):
            if exception:
                print(f"Error for {request_id}: {exception}")
                return

            payload = msg["payload"]
            headers = payload.get("headers", [])

            sender = ""
            subject = ""

            for header in headers:
                if header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Subject":
                    subject = header["value"]

            body = extract_text(payload)

            batch_data.append(
                (
                    msg["id"],
                    sender,
                    subject,
                    msg.get("snippet", ""),
                    body,
                    "",
                    0.0,
                    msg.get("sizeEstimate", 0),
                    timestamp_to_date(msg.get("internalDate", "")),
                    False
                )
            )

        return callback

    page_token = None
    batch_num = 1

    while batch_num <= BATCHES_COUNT:

        print("--" * 20)
        batch_data = []
        t0 = time.time()
        
        results = gmail.users().messages().list(
            userId="me",
            maxResults=BATCHES_SIZE,
            pageToken=page_token,
            q='after:'+ AFTER +' before:' + BEFORE
        ).execute()

        print("Listing took:", second_to_millisec(time.time() - t0))
        t0 = time.time()
        messages = results.get("messages", [])

        print(
            f"Batch {batch_num}: "
            f"{len(messages)} emails"
        )

        batch = gmail.new_batch_http_request(
            callback=make_callback(batch_data)
        )

        for msg in messages:
            batch.add(
                gmail.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="full"
                )
            )
        batch.execute()
        
        
        print("Processing batch took:", second_to_millisec(time.time() - t0))
        t0 = time.time()
        page_token = results.get("nextPageToken")

        if not page_token:
            break
        

        dbdriver.upsert_emails(batch_data)
        
        last_email_date = batch_data[-1][8] if batch_data else "N/A"
        
        print("DB update took:", second_to_millisec(time.time() - t0))
        t0 = time.time()
        
        print(f"Batch {batch_num} completed. Last email date: {last_email_date}")
        print(f"Total emails processed: {len(batch_data * batch_num)}")
        
        batch_num += 1



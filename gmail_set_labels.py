from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pprint
import dbdriver
from os import path
from google_auth_oauthlib.flow import InstalledAppFlow

def run():


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



    # get all gmail existing labels and their ids
    existing_labels = []
    labels_response = gmail.users().labels().list(userId='me').execute()
    for label in labels_response.get('labels', []):
        existing_labels.append((label["name"], label["id"]))

    emails = dbdriver.get_emails(-1)
    processed_count = 0
    for email in emails:
        gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete = email
        processed_count += 1
        label = classification
        if label is None \
            or label.strip() == "" \
            or label.strip() == "0" \
            or label.strip().lower() == "unknown" \
                : continue
                
        label = label.replace("*", "").strip()
        label = "__" + label
        print(f"{processed_count}/{len(emails)} > Applying label <<{label}>> to email with id {gmail_id}...")
        
        # call google api to create label if not exists and get label id
        label_id = None
        
        if label in [el[0] for el in existing_labels]:
            label_id = [el[1] for el in existing_labels if el[0] == label][0]
            
        else:
            new_label = gmail.users().labels().create(userId='me', body={
                "name": label,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }).execute()
            label_id = new_label["id"]
            existing_labels.append((label, label_id))
            
        # call google api to apply label to email
        gmail.users().messages().modify(userId='me', id=gmail_id, body={
            "addLabelIds": [label_id]
        }).execute()
        
        
        
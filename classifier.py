import ollama
import dbdriver
import json
import time
import re
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize

CATEGORIES = [
    # High value

    "personal conversation",
    "projects discussion",
    "financial statement",
    "receipt and invoice",
    "travel tickets",
    "booking confirmation",
    "purchase confirmation",
    "appointment confirmation",
    "shipping update",
    "security alert and verification",

    # Medium value

    "service status notification",
    "subscription renewal",
    "account notification",
    "job alert",
    "event invitation",
    "reminders",
    "password reset",

    # Usually low value

    "social notification",
    "newsletter",
    "advertising",
    "product announcement",
    "promotional offer",
    "survey and feedback request",
    "junk",

    # Legal / compliance

    "privacy policy update",
    "terms of service update",
    "legal notice",

    # Machine generated

    "system notification",
    "automated report",
    "build & deployment notification",
    "monitoring alert",

    # Uncategorized

    "other"
]



def gen_clusters(embeddings):
    
    # Compute similarity between emails embeddings
    # --
    
    # get embeddings from db
    ids = []
    vectors = []
    embedding_rows = dbdriver.get_all_embeddings()
    for gmail_id, embedding_json in embedding_rows:
        ids.append(gmail_id)
        vectors.append(json.loads(embedding_json))

    X = np.array(vectors)
    X = normalize(X)
            
    clustering = DBSCAN(
        eps=0.1,
        min_samples=15,
        metric="cosine"
    )
    labels = clustering.fit_predict(X)
    
    
    clusters = []
    for target_label in sorted(set(labels)):

        cluster = {
            "label": None,
            "size": 0,
            "email_samples": [],
            "emails_ids": []
        }

        cluster_emails = [
            gmail_id
            for gmail_id, label in zip(ids, labels)
            if label == target_label
        ]

        print()
        print("--" * 20)
        print(f"Cluster {target_label}")
        print(f"Size: {len(cluster_emails)}")
        cluster["label"] = int(target_label)
        cluster["size"] = len(cluster_emails)
        cluster["emails_ids"] = cluster_emails
        cluster_emails_random_sample = np.random.choice(cluster_emails, min(len(cluster_emails), 5), replace=False)
        for gmail_id in cluster_emails_random_sample:
            row = dbdriver.get_email_by_id(gmail_id)
            cluster["email_samples"].append(
                {
                    "sender": row[1],
                    "subject": row[2],
                    "snippet": row[3],
                }
            )
      # The code snippet `print(row[0], row[1], row[2])` is printing out specific information related
      # to an email. Here's what each element represents:
            print(
                row[0],
                row[1],
                row[2],
            )
        clusters.append(cluster)
                
            
    # Statistics about clusters
    # --
    clusters_email_counts = {}
    for label in sorted(set(labels)):
        count = np.sum(labels == label)
        clusters_email_counts[label] = count
    print("--" * 20)
    for label, count in clusters_email_counts.items():
        print(f"Cluster {label}: {count} emails")
    print("--" * 20)
    print("Total Clusters:", len(clusters_email_counts))
    print("Median Cluster size:", np.median(list(clusters_email_counts.values())))
    print("--" * 20)
    
    return clusters



def get_embeddings():
    offset = 0
    dbdriver.create_embeddings_db()
    total_emails = dbdriver.get_total_emails_count()

    def get_embedding(gmail_id, sender, subject, snippet):

        text = f"""
                {subject}
                """

        response = ollama.embed(
            model="nomic-embed-text",
            input=text
        )
        
        embedding = json.dumps(response["embeddings"][0])
        dbdriver.upsert_embedding(gmail_id, embedding)


    while True:
        emails = dbdriver.get_emails(limit=1, offset=offset)
        if not emails:
            break
        
        print(f"{offset}/{total_emails} Generating embedding...")
        
        for email in emails:
            gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete = email
            get_embedding(gmail_id, sender, subject, snippet)

        offset += 1
        
        

def gen_label_for_email(email):
    t0 = time.time()

    content = f"""
        Classify this email into one of the categories.

        Sender: {email[1]}
        Subject: {email[2]}
        Snippet: {email[3]}
    """

    response = ollama.chat(
        model="qwen3:8b",
        messages=  [  
            {
                "role":"system",
                 "content": "You are an email classifier"
            },
            {
                "role":"user",
                 "content": content
            }
        ],
        think=False,
        format={
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "enum": CATEGORIES
                }
            },
            "required": ["label"]
        },
        options={
            "temperature": 0,
            "seed": 42
        },
        keep_alive="30m"
    )

    label = json.loads(response.message.content)["label"]
    print(f"       -------- {email[0]} > Generated label: {label} in {time.time() - t0:.2f} seconds")
    return label
    
    
    
def gen_label_for_cluster(cluster):
    t0 = time.time()

    content = f"""
        Classify this email into one of the categories.

        {json.dumps(cluster['email_samples'][0], indent=4)}
    """

    print("--" * 20)
    print(f"Generating label for cluster {cluster['label']} with size {cluster['size']}...")


    response = ollama.chat(
        model="qwen3:8b",
        messages=  [  
            {
                "role":"system",
                 "content": "You are an email classifier"
            },
            {
                "role":"user",
                 "content": content
            }
        ],
        think=False,
        format={
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "enum": CATEGORIES
                }
            },
            "required": ["label"]
        },
        options={
            "temperature": 0,
            "seed": 42
        },
        keep_alive="30m"
    )

    label = json.loads(response.message.content)["label"]
    print(f"       -------- {cluster['label']} > Generated label: {label} in {time.time() - t0:.2f} seconds")
    return label




def run(
        DROP_EXISTING=False,
        SKIP_CLUSTERS=False
    ):
    dbdriver.drop_clusters_db_if_exists()
    if DROP_EXISTING: dbdriver.drop_classification_from_emails()

    # cluster emails based on embeddings similarity
    #--
    if not SKIP_CLUSTERS:
        print("")
        print("")
        print("--" * 20)
        print("Clustering emails based on embeddings similarity")
        print("processing...")
        dbdriver.create_clusters_db()
        clusters = gen_clusters(dbdriver.get_all_embeddings())
        clusters_count = len(clusters)
        cluster_index = 0
        for cluster in clusters:
            if cluster['label'] == -1: continue # misc category, skip
            cluster_index += 1
            print("--" * 20)
            print(f"{cluster_index}/{clusters_count} > Cluster {cluster['label']} | Size: {cluster['size']}")
            for email in cluster["email_samples"][:3]:
                print(f"{email['sender']} | {email['subject']}")
            label = gen_label_for_cluster(cluster)
            dbdriver.upsert_cluster(cluster)
            print(f"Cluster {cluster['label']} labeled as <<{label}>>")
            print("--" * 20)
            print()
            
            for gmail_id in cluster["emails_ids"]:
                dbdriver.update_email_classification(gmail_id, label)



    # for remainings emails, classification request to LLM
    # --
    print("")
    print("")
    print("--" * 20)
    print("Classifying remaining emails with LLM...")
    print("processing...")
    emails = dbdriver.get_unclassified_emails()
    total_emails = len(emails)
    processed_count = 0
    for email in emails:
        gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete = email
        processed_count += 1
        pct_done = (processed_count / total_emails) * 100
        pct_done_str = f"{pct_done:.2f}%"
        print("")
        print(f"{pct_done_str} %  ({processed_count}/{total_emails})")
        label = gen_label_for_email(email)
        dbdriver.update_email_classification(gmail_id, label)
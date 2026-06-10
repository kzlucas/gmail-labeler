import ollama
import dbdriver
import json
import time
import re
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
import hdbscan

CATEGORIES = [
    # High value - almost never delete

    "personal conversation",
    "project discussion and work communication",
    "financial statement",
    "receipt and invoice",
    "tax document",
    "travel tickets",
    "booking confirmation",
    "purchase confirmation",
    "shipping update",
    "appointment confirmation",
    "security alert and verification",
    "password reset",

    # Medium value

    "service status notification",
    "subscription renewal",
    "account notification",
    "job alert",
    "event invitation",
    "appointment reminder",

    # Usually low value

    "social notification",
    "newsletter",
    "advertising",
    "product announcement",
    "promotional offer",
    "survey and feedback request",

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

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )



def compare_embedding_single(target_gmail_id, embeddings):
    target_mail = dbdriver.get_email_by_id(target_gmail_id)
    target_embedding = embeddings[target_gmail_id]
    scores = []
    
    # find nearest emails by cosine similarity
    for gmail_id, other_embedding in embeddings.items():

        if gmail_id == target_gmail_id:
            continue

        score = cosine_similarity(
            target_embedding,
            other_embedding
        )

        scores.append(
            (score, gmail_id)
        )
    scores.sort(reverse=True)

    # print top X similar emails
    print("For email:")
    print("--" * 20)
    print(f"{target_gmail_id} | {target_mail[1]} | {target_mail[2]}") 
    print("--" * 20)
    print("Similar emails:")
    
    for score, gmail_id in scores[:10]:

        row = dbdriver.get_email_by_id(gmail_id)
        print(
            f"{score:.3f}",
            row[0],
            row[1],
            row[2],
        )
    


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
            
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=10,
        metric='euclidean'
    )
    labels = clusterer.fit_predict(X)
    
    
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
                Sender: {sender}
                Subject: {subject}
                Snippet: {snippet[:500]}
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
    prompt = f"""
        Return ONLY ONE category from the following list.
        Output only the label without any explanation, comment or text decoration. The label must be picked from the list.
        
        {json.dumps(CATEGORIES, indent=4)}  

        Here is the email to classify:

        Sender: {email[1]}
        Subject: {email[2]}
        Snippet: {email[3]}
    """
    
    response = ollama.chat(
        model="qwen3:4b",
        messages=[{"role": "user","content": prompt}],
        think=False
    )
    label = response.message.content.strip()
    print(f"       -------- {email[0]} > Generated label: {label} in {time.time() - t0:.2f} seconds")
    return label
    
    
    
def gen_label_for_cluster(cluster):
    t0 = time.time()
    prompt = f"""
        Return ONLY ONE category from the following list.
        Output only the label without any explanation, comment or text decoration. The label must be picked from the list.

        {json.dumps(CATEGORIES, indent=4)}

        Here is the data for this email cluster:

        - Content: {json.dumps(cluster['email_samples'], indent=4)}
        
    """
    
    print("--" * 20)
    print(f"Generating label for cluster {cluster['label']} with size {cluster['size']}...")
    response = ollama.chat(
        model="qwen3:4b",
        messages=[{"role": "user","content": prompt}],
        think=False
    )
    label = response.message.content.strip()
    print(f"<<{label}>> ----- Label generated in {time.time() - t0:.2f} seconds")
    return label





def run(DROP_EXISTING=False):
    dbdriver.drop_clusters_db_if_exists()
    if DROP_EXISTING: dbdriver.drop_classification_from_emails()

    # cluster emails based on embeddings similarity
    #--
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
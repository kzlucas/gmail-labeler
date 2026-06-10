import sqlite3
import json


def create_emails_db():

    db = sqlite3.connect("emails.db")

    db.execute("""
    CREATE TABLE IF NOT EXISTS emails(
        gmail_id TEXT PRIMARY KEY,
        sender TEXT,
        subject TEXT,
        snippet TEXT,
        body TEXT,
        classification TEXT,
        confidence REAL,
        size INTEGER,
        date TEXT,
        safe_delete BOOLEAN
    )
    """)

    db.commit()
    
    
    
def upsert_email(gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete):
    db = sqlite3.connect("emails.db")

    db.execute("""
    INSERT OR REPLACE INTO emails
    (
        gmail_id,
        sender,
        subject,
        snippet,
        body,
        classification,
        confidence,
        size,
        date,
        safe_delete
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        gmail_id,
        sender,
        subject,
        snippet,
        body,
        classification,
        confidence,
        size,
        date,
        safe_delete
    ))

    db.commit()


def upsert_emails(emails):
    db = sqlite3.connect("emails.db")

    db.executemany("""
    INSERT OR REPLACE INTO emails
    (
        gmail_id,
        sender,
        subject,
        snippet,
        body,
        classification,
        confidence,
        size,
        date,
        safe_delete
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, emails)

    db.commit()
    
    
def update_email_classification(gmail_id, classification):
    db = sqlite3.connect("emails.db")

    db.execute("""
    UPDATE emails
    SET classification = ?
    WHERE gmail_id = ?
    """, (classification, gmail_id))

    db.commit()
    
    
def get_email_by_id(gmail_id):
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete
    FROM emails
    WHERE gmail_id = ?
    """, (gmail_id,))
    
    return cursor.fetchone()
    
def get_emails(limit=100, offset=0):
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete
    FROM emails
    LIMIT ? OFFSET ?
    """, (limit, offset))
    
    return cursor.fetchall()

    
def drop_classification_from_emails():
    db = sqlite3.connect("emails.db")

    db.execute("""
    UPDATE emails
    SET classification = NULL, confidence = NULL
    """)
    db.commit()
    
def get_unclassified_emails():
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT gmail_id, sender, subject, snippet, body, classification, confidence, size, date, safe_delete
    FROM emails
    WHERE classification IS NULL
    """)
    
    return cursor.fetchall()


def get_total_emails_count():
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT COUNT(*)
    FROM emails
    """)
    
    return cursor.fetchone()[0]


def create_embeddings_db():
    db = sqlite3.connect("emails.db")

    db.execute("""
            CREATE TABLE IF NOT EXISTS email_embeddings (
                gmail_id TEXT PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (gmail_id) REFERENCES emails(gmail_id)
            );
    """)
    db.commit()
    
def upsert_embedding(gmail_id, embedding):
    db = sqlite3.connect("emails.db")

    db.execute("""
    INSERT OR REPLACE INTO email_embeddings
    (
        gmail_id,
        embedding
    )
    VALUES (?, ?)
    """,
    (
        gmail_id,
        embedding
    ))

    db.commit()
    
    
def get_all_embeddings():
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT gmail_id, embedding
    FROM email_embeddings
    """)
    
    return cursor.fetchall()


def drop_clusters_db_if_exists():
    db = sqlite3.connect("emails.db")

    db.execute("""
    DROP TABLE IF EXISTS clusters
    """)
    db.commit()


def create_clusters_db():
    db = sqlite3.connect("emails.db")

    db.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                label INTEGER PRIMARY KEY,
                size INTEGER,
                email_samples TEXT,
                emails_ids TEXT
            );
    """)
    db.commit()


def upsert_cluster(cluster):
    db = sqlite3.connect("emails.db")

    db.execute("""
    INSERT OR REPLACE INTO clusters
    (
        label,
        size,
        email_samples,
        emails_ids
    )
    VALUES (?, ?, ?, ?)
    """,
    (
        cluster["label"],
        cluster["size"],
        json.dumps(cluster["email_samples"]),
        json.dumps(cluster["emails_ids"])
    ))

    db.commit()
    
    
def get_all_clusters():
    db = sqlite3.connect("emails.db")

    cursor = db.execute("""
    SELECT label, size, email_samples, emails_ids
    FROM clusters
    """)
    
    return cursor.fetchall()
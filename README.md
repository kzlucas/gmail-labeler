

# Gmail Automatic Labeler

**This project is designed to automatically classify and label emails in a Gmail account based on their content. It uses the Gmail API to fetch emails, extract features, generate embeddings using Ollama's language models, and then applies clustering algorithms to group similar emails together.**

**Then, it will ask Ollama's language model to classify each cluster into predefined categories such as "receipt and invoice", "service status notification", "appointment and event reminders"...**

**All un-clustered emails will be labeled individually as well.**

**Finally, it applies labels to the emails in Gmail based on the generated classifications.**

Note that it's not intended to live classify emails as they arrive, but rather to be run periodically to organize and label existing emails in the account.

### Approach

1. **Email Fetching**: The script connects to the Gmail API and retrieves emails from the user's account. It can fetch emails in batches and supports filtering by date range.

2. **Feature Extraction**: For each email, it extracts relevant features such as sender, subject, snippet, body, size, and date. These features are stored in a local SQLite database for further processing.

3. **Embedding Generation**: The script uses Ollama's language models to generate embeddings for the email content. These embeddings capture the semantic meaning of the emails and are stored in the database.

4. **Clustering and Classification**: The script applies clustering algorithms to group similar emails together based on their embeddings. It then classifies each cluster into predefined categories such as "receipt and invoice", "service status notification", "appointment and event reminders", "social notification", "newsletter", "advertising", "security alert and verification", "project discussion", "personal conversation", "travel tickets", and "other".

5. **Label Application**: Finally, the script applies the generated labels to the corresponding emails in the user's Gmail account using the Gmail API.


## Prerequisites

- Obtain Gmail API credentials by creating a project in the Google Cloud Console, enabling the Gmail API, and downloading the `credentials.json` file. Place this file in the same directory as `main.py` for authentication purposes.

- At least 2GB of free disk space for the SQLite database, model and embeddings (more if your Email Box is huge).

- 2GB of VRAM.

## Install

#### Install Python dependencies

Crearte a virtual environment and install the required Python packages using the following commands:

`pip install -r requirements.txt`

#### Install Ollama and pull the models

`curl -fsSL https://ollama.com/install.sh | sh`

`ollama pull nomic-embed-text`

`ollama pull qwen3:4b`

You can also use bigger models available in the Ollama library to get more accurate results, but make sure to update the model names in the code accordingly.


## Usage


- **Step 1**: Run `python main.py build-db` 
    This command will fetch emails from your Gmail account within the specified date range, extract their features, and store them in a local SQLite database. If no arguments are provided, it will fetch all emails. Use `python main.py build-db --help` for more options. The processing rate is about 1200 emails per minutes.


- **Step 2**: Run `python main.py get-embeddings` 
     This command will generate embeddings ("vectors") for the emails stored in the database using the Ollama model and update the database with these embeddings.

- **Step 3**: Run `python main.py classify`
    This command will classify the emails into clusters based on their embeddings and update the database with the cluster labels.

- **Step 4**: Verify the generated labels and clusters in the database are suitable for your needs. You can use tools like DB Browser for SQLite to inspect the `emails.db` file and see the classifications.

- **Step 5**: Run `python main.py apply-labels`
    This command will apply the generated labels to the corresponding emails in your Gmail account based on the classifications stored in the database.


Here is the list of default categories. 
You can modify this list in `classifier.py` to better fit your needs.

``` python
CATEGORIES = [

    # High value

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
```

## Available commands and their arguments

- `build-db`: Fetch emails from Gmail and build the local database.
  - `--before`: Optional start date for fetching emails (format: YYYY/MM/DD).
  - `--after`: Optional end date for fetching emails (format: YYYY/MM/DD).
  - `--batches-count`: Optional maximum number of batches to fetch. Means the script will stop after fetching this number of batches, even if there are more emails to fetch.
  - `--batches-size`: Number of emails to fetch in each batch (default: 20). Adjust this based on your needs and Gmail API limits.

- `get-embeddings`: Generate embeddings for all emails in the database. This process can take some time depending on the number of emails and the model used for generating embeddings.
- `classify`: Classify emails into clusters based on their embeddings.
  - `--drop-existing`: Optional flag to drop existing classifications and clusters before classifying.


## Credits

- **Ollama** - for providing the language models used for generating embeddings and classifications. 
*@see https://ollama.com/*

- **Nomic** - for their work on embedding models and clustering algorithms that inspired the approach taken in this project. 
*@see https://ollama.com/library/nomic-embed-text*

- **Google** - for providing the Gmail API that allows access to email data for processing and classification. 
*@see https://developers.google.com/gmail/api*

## License

Please refer to the licenses of Ollama and Gmail API 

**Creative Commons Free License (CC0)** - These scripts are released into the public domain, allowing anyone to use, modify, and distribute it without any restrictions.

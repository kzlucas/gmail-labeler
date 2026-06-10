

# Gmail Automatic Labeler

**This project is designed to automatically classify and label emails in a Gmail account based on their content. It uses the Gmail API to fetch emails, extract features, generate embeddings using Ollama's language models, and then applies clustering algorithms to group similar emails together. Finally, it applies labels to the emails in Gmail based on the generated classifications.**

Note that it's not intended to live classify emails as they arrive, but rather to be run periodically to organize and label existing emails in the account.

## Prerequisites

- Obtain Gmail API credentials by creating a project in the Google Cloud Console, enabling the Gmail API, and downloading the `credentials.json` file. Place this file in the same directory as `main.py` for authentication purposes.

## Install

### Install Python dependencies

`pip install -r requirements.txt`

#### Install Ollama and pull the models

`curl -fsSL https://ollama.com/install.sh | sh`
`ollama pull nomic-embed-text`
`ollama pull qwen3:8b`


## Usage

- **Step 1**: Run `python main.py build-db` - This command will fetch emails from your Gmail account within the specified date range, extract their features, and store them in a local SQLite database. If no arguments are provided, it will fetch all emails. Use `python main.py build-db --help` for more options. The processing rate is about 1200 emails per minutes. 

- **Step 2**: Run `python main.py get-embeddings` - This command will generate embeddings for the emails stored in the database using the Ollama model and update the database with these embeddings.

- **Step 3**: Run `python main.py classify` - This command will classify the emails into clusters based on their embeddings and update the database with the cluster labels.

- **Step 4**: Verify the generated labels and clusters in the database are suitable for your needs. You can use tools like DB Browser for SQLite to inspect the `emails.db` file and see the classifications.

- **Step 5**: Run `python main.py apply-labels` - This command will apply the generated labels to the corresponding emails in your Gmail account based on the classifications stored in the database.


## Credits

- **Ollama** - for providing the language models used for generating embeddings and classifications. *@see https://ollama.com/*
- **Nomic** - for their work on embedding models and clustering algorithms that inspired the approach taken in this project. *@see https://ollama.com/library/nomic-embed-text*
- **Google** - for providing the Gmail API that allows access to email data for processing and classification. *@see https://developers.google.com/gmail/api*

## License

**Creative Commons Free License (CC0)** - This project is released into the public domain, allowing anyone to use, modify, and distribute it without any restrictions.
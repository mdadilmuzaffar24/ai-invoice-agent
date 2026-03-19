# 🤖 Automated AI Financial Agent (Two-Way Sync)

An AI-powered agent that automates financial data extraction from PDF invoices in Google Drive and synchronizes it with Google Sheets.

This project goes beyond simple data appending by implementing a **Continuous Two-Way Synchronization** architecture, ensuring the database remains a perfect mirror of the source file system.

## 🧠 System Architecture & Key Features

* **Two-Way State Synchronization:** The agent performs a differential check ("diff") between the Google Drive source folder and the Google Sheets database. If a source PDF is deleted, the agent intelligently identifies and drops the corresponding row from the database to maintain data integrity.
* **LLM-Powered Structured Extraction:** Utilizes **Llama 3.1 (8B)** via the Groq Cloud API. It implements `langchain` and `pydantic` schemas to strictly enforce structured JSON outputs (Date, Vendor, Amount, Items) from highly variable, unstructured PDF text.
* **Idempotency & Duplicate Prevention:** Built-in validation ensures that re-running the synchronization process will never result in duplicate database entries, even if the source files remain in the inbox.
* **Enterprise-Grade Security:** Cryptographic keys, Google Cloud Service Account credentials, and LLM API tokens are entirely decoupled from the codebase using Streamlit's native encrypted secrets management.
* **Dynamic UI/UX:** Features a custom-styled, interactive frontend with real-time processing logs, progress tracking, and dynamic success metrics.

## 🛠️ Technology Stack

* **Language:** Python 3.11+
* **AI / Inference:** Meta Llama 3.1 8B (via Groq Cloud), LangChain
* **Data Parsing:** PyPDF2, Pydantic (Data Validation)
* **Cloud Infrastructure:** Google Drive API (v3), Google Sheets API (v4)
* **Frontend & Deployment:** Streamlit Community Cloud
* **Authentication:** OAuth2 Service Accounts (`oauth2client`)

## 💡 Processing Pipeline Workflow

1.  **Ingestion:** Scans the designated Google Drive "Inbox" folder for `application/pdf` MIME types.
2.  **Reconciliation (Diff Check):** Loops backward through the Google Sheet to safely delete records of files that no longer exist in the Drive folder.
3.  **Extraction:** Downloads new PDFs into an in-memory byte stream (avoiding local disk storage), extracts raw text, and passes it to the LLM with a strict extraction prompt.
4.  **Database Commit:** Appends the structured payload to the Google Sheet and updates the local state to prevent redundant processing.

## 👨‍💻 Developer
**MD Adil Muzaffar**
*MTech in Data Science*

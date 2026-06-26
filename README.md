# 🤖 Automated AI Financial Agent (Two-Way Sync)

<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/f96a78a9-d084-4c4a-b956-4bc7793956dd" />


An AI-powered agent that automates financial data extraction from PDF invoices in Google Drive and synchronizes it with Google Sheets.

This project goes beyond simple data appending by implementing a **Continuous Two-Way Synchronization** architecture, ensuring the database remains a perfect mirror of the source file system.

## 🧠 System Architecture & Key Features

* **Two-Way State Synchronization:** The agent performs a differential check ("diff") between the Google Drive source folder and the Google Sheets database. If a source PDF is deleted, the agent intelligently identifies and drops the corresponding row from the database to maintain data integrity.
* **LLM-Powered Structured Extraction:** Utilizes **Llama 3.1 (8B)** via the Groq Cloud API. It implements `langchain` and `pydantic` schemas to strictly enforce structured JSON outputs (Date, Vendor, Amount, Items) from highly variable, unstructured PDF text.
* **Idempotency & Duplicate Prevention:** Built-in validation ensures that re-running the synchronization process will never result in duplicate database entries, even if the source files remain in the inbox.
* **Enterprise-Grade Security:** Cryptographic keys, Google Cloud Service Account credentials, and LLM API tokens are entirely decoupled from the codebase using Streamlit's native encrypted secrets management.
* **Dynamic UI/UX:** Features a custom-styled, interactive frontend with real-time processing logs, progress tracking, and dynamic success metrics.

## 🏗️ Advanced ADK Graph Architecture
To scale beyond a simple script, this agent has been re-engineered using a deterministic linear state graph. This decouples the frontend execution from the heavy background processes, guaranteeing system stability:
* **`node_ingest_batch`**: Automatically runs live differential checks against the cloud ledger to drop duplicates and maintain data idempotency.
* **`node_process_queue`**: Implements a native 8-second backoff pacing loop to cleanly handle Google Cloud and LLM API rate limits (`429` and `503`).
* **`node_extract_invoice`**: Leverages structured schema output to guarantee exact type mapping.
* **`node_export_ledger`**: Securely syncs authenticated records directly to the cloud database via a headless GCP Service Account.

## 🛠️ Technology Stack

* **Language:** Python 3.11+
* **AI / Inference:** Meta Llama 3.1 8B (via Groq Cloud), LangChain
* **Data Parsing:** PyPDF2, Pydantic (Data Validation)
* **Cloud Infrastructure:** Google Drive API (v3), Google Sheets API (v4)
* **Frontend & Deployment:** Streamlit Community Cloud
* **Authentication:** OAuth2 Service Accounts (`oauth2client`)

## 🛠️ Core Concepts Demonstrated (Kaggle Intensive)
1. **Agent / Multi-Agent Workflow (ADK):** Native tracking of an explicit `AgentState` queue across isolated nodes.
2. **Security & Validation:** Fully protected environment variables (`.env`) paired with strict Pydantic cryptographic-style data validation schemas.
3. **Antigravity Environment:** Built, tested, and fully optimized within the native Antigravity IDE ecosystem.

## 💡 Processing Pipeline Workflow

1.  **Ingestion:** Scans the designated Google Drive "Inbox" folder for `application/pdf` MIME types.
2.  **Reconciliation (Diff Check):** Loops backward through the Google Sheet to safely delete records of files that no longer exist in the Drive folder.
3.  **Extraction:** Downloads new PDFs into an in-memory byte stream (avoiding local disk storage), extracts raw text, and passes it to the LLM with a strict extraction prompt.
4.  **Database Commit:** Appends the structured payload to the Google Sheet and updates the local state to prevent redundant processing.

## 👨‍💻 Developer
**MD Adil Muzaffar**
*MTech in Data Science*

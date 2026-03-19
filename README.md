# 🤖 Automated AI Financial Agent (Two-Way Sync)

An AI-powered agent that automates financial data extraction from PDF invoices in Google Drive and synchronizes it with Google Sheets.

## 🚀 Key Features
* **Two-Way Synchronization:** Detects new PDFs in Google Drive for extraction and automatically removes rows from the Sheet if the source file is deleted.
* **LLM Extraction:** Uses **Llama 3.1 (8B)** via Groq for structured data extraction.
* **Duplicate Prevention:** Ensures each invoice is processed only once.
* **Secure Architecture:** Uses Streamlit secrets and `.gitignore` to protect API keys and Service Account credentials.

## 🛠️ Tech Stack
* **Language:** Python
* **AI Model:** Llama 3.1 8B (Groq Cloud)
* **APIs:** Google Drive API, Google Sheets API
* **Libraries:** Streamlit, LangChain, Pydantic, PyPDF2, gspread

## 💡 How it Works
1. **Scan:** The agent checks a specific Google Drive folder for new PDFs.
2. **Extract:** Text is parsed and sent to Llama 3.1 to extract Date, Vendor, Amount, and Items.
3. **Sync:** Data is written to Google Sheets.
4. **Cleanup:** The agent compares the Sheet against Drive and removes entries for deleted files.
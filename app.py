import streamlit as st
import PyPDF2
import gspread
import io
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
# Pull secrets from Streamlit's secure storage (secrets.toml)
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]
GOOGLE_SHEET_NAME = "Invoice Agent Output"

class InvoiceData(BaseModel):
    date: str = Field(description="The date of the invoice (e.g., YYYY-MM-DD or DD/MM/YYYY)")
    vendor: str = Field(description="The name of the company or vendor")
    amount: str = Field(description="The final total amount charged")
    items: str = Field(description="A short, comma-separated list of the main items purchased")

# Authenticate Google Services using the secrets dictionary
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

drive_service = build('drive', 'v3', credentials=creds)
gclient = gspread.authorize(creds)

# ==========================================
# 2. STREAMLIT USER INTERFACE
# ==========================================
st.set_page_config(page_title="Automated Financial Agent", layout="centered")
st.title("🤖 Automated Financial AI Agent")
st.markdown("This agent provides a **Two-Way Sync** between your Google Drive 'Invoice Inbox' and Google Sheets.")

if st.button("🔄 Sync with Google Drive"):
    with st.spinner("Synchronizing database..."):
        
        sheet = gclient.open(GOOGLE_SHEET_NAME).sheet1
        existing_records = sheet.col_values(1) # Gets everything in Column A (Filenames)
        
        # Search the Drive folder for PDF files
        query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf'"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        # Create a simple list of just the filenames currently in the Drive
        drive_filenames = [file['name'] for file in files]
        
        # ==========================================
        # STEP 1: DELETION (Two-Way Sync)
        # ==========================================
        # Loop backwards through the sheet to safely delete rows of removed files
        deleted_count = 0
        # Start from the last row, stop before index 0 (the header)
        for i in range(len(existing_records) - 1, 0, -1):
            sheet_filename = existing_records[i]
            if sheet_filename not in drive_filenames:
                sheet.delete_rows(i + 1) # +1 because gspread rows are 1-indexed, lists are 0-indexed
                st.warning(f"🗑️ Deleted '{sheet_filename}' from database (File removed from Drive).")
                deleted_count += 1
                
        # Update our records list after deletions
        existing_records = sheet.col_values(1)

        # ==========================================
        # STEP 2: EXTRACTION (Add New Files)
        # ==========================================
        processed_count = 0
        
        if not files:
            st.info("No PDF invoices found in the Drive folder.")
        else:
            llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=GROQ_API_KEY)
            structured_llm = llm.with_structured_output(InvoiceData)
            
            for file in files:
                file_name = file['name']
                file_id = file['id']
                
                if file_name in existing_records:
                    continue # Silently skip files we already have
                
                st.write(f"📄 Processing new invoice: **{file_name}**...")
                
                # Download the PDF into memory
                request = drive_service.files().get_media(fileId=file_id)
                file_memory = io.BytesIO()
                downloader = MediaIoBaseDownload(file_memory, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                # Extract Text using PyPDF2
                file_memory.seek(0)
                pdf_reader = PyPDF2.PdfReader(file_memory)
                raw_text = ""
                for page in pdf_reader.pages:
                    raw_text += page.extract_text()
                    
                # Run the AI Extraction
                extracted_data = structured_llm.invoke(
                    f"You are a financial data extraction AI. Extract the required fields from this invoice text:\n\n{raw_text}"
                )
                
                # Append to Google Sheet
                new_row = [
                    file_name, 
                    extracted_data.date, 
                    extracted_data.vendor, 
                    extracted_data.amount, 
                    extracted_data.items
                ]
                sheet.append_row(new_row)
                existing_records.append(file_name) # Prevents duplicates within the same run
                processed_count += 1
                
        # Final Status Message
        if processed_count > 0 or deleted_count > 0:
            st.success(f"✅ Sync Complete! Added {processed_count} new records and removed {deleted_count} old records.")
        else:
            st.success("✅ Database is entirely up to date. No changes needed.")
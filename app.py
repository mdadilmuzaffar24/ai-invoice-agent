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
# PAGE CONFIGURATION & STYLING
# ==========================================
# Sets the page to use the full width of the screen and adds a custom browser tab icon
st.set_page_config(page_title="AI Financial Agent", page_icon="🧾", layout="centered")

# Custom CSS to make the button pop and smooth out the interface
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 55px;
        font-size: 20px;
        font-weight: 600;
        background-color: #2e66ff;
        color: white;
        transition: all 0.3s ease-in-out;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1b4bcf;
        box-shadow: 0 6px 15px rgba(46, 102, 255, 0.3);
        transform: translateY(-2px);
    }
    .metric-container {
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]
GOOGLE_SHEET_NAME = "Invoice Agent Output"

class InvoiceData(BaseModel):
    date: str = Field(description="The date of the invoice (e.g., YYYY-MM-DD or DD/MM/YYYY)")
    vendor: str = Field(description="The name of the company or vendor")
    amount: str = Field(description="The final total amount charged")
    items: str = Field(description="A short, comma-separated list of the main items purchased")

# Authenticate Google Services
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

drive_service = build('drive', 'v3', credentials=creds)
gclient = gspread.authorize(creds)

# ==========================================
# 2. STREAMLIT UI - DASHBOARD
# ==========================================
# Hero Section
st.markdown("<h1 style='text-align: center;'>🤖 Automated Financial AI Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 18px; margin-bottom: 30px;'>This agent provides a Two-Way Sync between your Google Drive and Google Sheets.</p>", unsafe_allow_html=True)

# Main Interaction Area
if st.button("🚀 Synchronize Database"):
    # Initialize metric counters
    processed_count = 0
    deleted_count = 0
    
    # Create placeholders for dynamic UI updates before the expander
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Wrap the technical logs in an expander so it looks clean
    with st.expander("⚙️ System Processing Logs", expanded=True):
        status_text.info("Connecting to Google Cloud & Drive...")
        
        sheet = gclient.open(GOOGLE_SHEET_NAME).sheet1
        existing_records = sheet.col_values(1)
        
        query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf'"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        drive_filenames = [file['name'] for file in files]
        
        # STEP 1: DELETION
        status_text.warning("Running Diff Check (Scanning for removed files)...")
        for i in range(len(existing_records) - 1, 0, -1):
            sheet_filename = existing_records[i]
            if sheet_filename not in drive_filenames:
                sheet.delete_rows(i + 1)
                st.write(f"🗑️ **Removed:** `{sheet_filename}` (File no longer in Drive)")
                deleted_count += 1
                
        existing_records = sheet.col_values(1)

        # STEP 2: EXTRACTION
        if not files:
            st.write("📂 No PDF invoices found in Drive.")
        else:
            status_text.info("Initializing Llama 3.1 AI Extraction Engine...")
            llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=GROQ_API_KEY)
            structured_llm = llm.with_structured_output(InvoiceData)
            
            total_files = len(files)
            
            for index, file in enumerate(files):
                file_name = file['name']
                file_id = file['id']
                
                # Smooth progress bar update
                progress_bar.progress((index + 1) / total_files)
                
                if file_name in existing_records:
                    continue 
                
                st.write(f"📄 **Extracting data from:** `{file_name}`...")
                
                request = drive_service.files().get_media(fileId=file_id)
                file_memory = io.BytesIO()
                downloader = MediaIoBaseDownload(file_memory, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                file_memory.seek(0)
                pdf_reader = PyPDF2.PdfReader(file_memory)
                raw_text = ""
                for page in pdf_reader.pages:
                    raw_text += page.extract_text()
                    
                extracted_data = structured_llm.invoke(
                    f"You are a financial data extraction AI. Extract the required fields from this invoice text:\n\n{raw_text}"
                )
                
                new_row = [file_name, extracted_data.date, extracted_data.vendor, extracted_data.amount, extracted_data.items]
                sheet.append_row(new_row)
                existing_records.append(file_name)
                processed_count += 1
                
                st.write(f"✅ **Logged:** {extracted_data.vendor} - {extracted_data.amount}")

    # Clear the loading text/bar
    status_text.empty()
    progress_bar.empty()
    
    # Display beautiful success metrics
    st.success("✨ Synchronization Completed Successfully!")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("New Invoices Processed", f"+{processed_count}", delta_color="normal")
    with col_m2:
        st.metric("Old Records Removed", f"-{deleted_count}", delta_color="inverse")

# Footer
st.markdown("<br><hr><center><small>Powered by Llama 3.1 & Streamlit • Built by MD Adil Muzaffar</small></center>", unsafe_allow_html=True)
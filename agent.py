import os
import json
import time  # <-- NEW: Add this here
from typing import List, Dict, Any
from dotenv import load_dotenv # <-- NEW: Import the tool
from pydantic import BaseModel, Field
import pandas as pd
from google import genai
from google.genai import types
import gspread

# ---------------------------------------------------------
# 1. SECURITY & CONFIGURATION LAYER
# ---------------------------------------------------------
# Load the variables from the .env file
load_dotenv() # <-- NEW: Tell Python to read the .env file

# Pulling keys safely from environment variables (Zero-Credential Rule)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SHEETS_CREDENTIALS = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")

if not GEMINI_API_KEY:
    raise ValueError("CRITICAL SECURITY ERROR: GEMINI_API_KEY not found in environment variables.")

# Initialize the Gemini client natively
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------
# 2. DATA VALIDATION SCHEMA (Security Guardrails)
# ---------------------------------------------------------
class InvoiceData(BaseModel):
    """Strict schema definition for financial ledger compliance."""
    vendor_name: str = Field(description="The name of the company or merchant issuing the invoice.")
    invoice_date: str = Field(description="The date of the invoice, formatted as YYYY-MM-DD if possible.")
    invoice_number: str = Field(description="The unique invoice number or identifier string.")
    total_amount: float = Field(description="The total final balance amount including taxes.")
    confidence_score: float = Field(description="Confidence rating of the extraction from 0.0 to 1.0.")

class AgentState(BaseModel):
    """Maintains the internal state across graph execution nodes."""
    queue: List[str] = []
    processed_records: List[Dict[str, Any]] = []
    current_file: str = ""
    errors: List[Dict[str, str]] = []

# ---------------------------------------------------------
# 3. GRAPH WORKFLOW NODES
# ---------------------------------------------------------
def node_ingest_batch(state: AgentState) -> AgentState:
    """Discovers pending assets and filters out files already in the ledger."""
    target_dir = "data/mock_invoices"
    if not os.path.exists(target_dir):
        return state

    # 1. Get all local files in the folder
    all_local_files = [f for f in os.listdir(target_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
    
    # 2. Fetch existing records from Google Sheets to cross-reference
    existing_files = []
    print("🔍 Checking cloud database for duplicates...")
    try:
        gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS)
        sheet = gc.open("AI_Ledger_Database").sheet1
        records = sheet.get_all_records()
        # Extract just the 'file_source' column
        existing_files = [row.get('file_source', '') for row in records]
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch cloud records for deduplication: {e}")

    # 3. Filter the queue: Only add files that ARE NOT in the database yet
    for f in all_local_files:
        if f not in existing_files:
            state.queue.append(os.path.join(target_dir, f))
        else:
            print(f"⏭️ Skipping: {f} (Already synced to ledger)")

    state.queue = sorted(state.queue)
    return state

def node_extract_invoice(state: AgentState) -> AgentState:
    """Processes the current file in the queue using structured schemas."""
    if not state.queue:
        return state
        
    state.current_file = state.queue.pop(0)
    print(f"🤖 Processing file: {state.current_file}...")

    try:
        # Load visual or textual asset
        with open(state.current_file, "rb") as f:
            file_bytes = f.read()

        # Dynamically determine the correct MIME type
        if state.current_file.lower().endswith('.pdf'):
            file_mime_type = 'application/pdf'
        elif state.current_file.lower().endswith(('.jpg', '.jpeg')):
            file_mime_type = 'image/jpeg'
        else:
            file_mime_type = 'image/png'

        # Execute extraction using structured output schemas to enforce type safety
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=file_mime_type),
                "Extract the following core business metrics from this invoice document with strict accuracy."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InvoiceData,
                temperature=0.1
            ),
        )

        # Parse and append to state storage
        parsed_json = json.loads(response.text)
        # Validate data integrity via Pydantic instantiation
        validated_invoice = InvoiceData(**parsed_json)
        
        record = validated_invoice.model_dump()
        record['file_source'] = os.path.basename(state.current_file)
        state.processed_records.append(record)
        print(f"✅ Successfully extracted data from {record['vendor_name']}")

    except Exception as e:
        print(f"❌ Failed to parse data from {state.current_file}: {str(e)}")
        state.errors.append({"file": state.current_file, "error": str(e)})

    # NEW: Pause for 4 seconds to respect API rate limits and avoid 503 errors
    time.sleep(8)
    
    return state

def node_export_ledger(state: AgentState) -> AgentState:
    """Consolidates valid extractions and syncs them to Google Sheets."""
    if not state.processed_records:
        print("⚠️ No valid records were compiled during this run.")
        return state

    df = pd.DataFrame(state.processed_records)
    print("\n--- Current Compiled Local Ledger Balance Sheet ---")
    print(df.to_string(index=False))
    print("----------------------------------------------------\n")

    print("☁️ Syncing data to Google Sheets...")
    try:
        # Authenticate using your secure local JSON file
        gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS)
        
        # Connect to your specific sheet
        spreadsheet = gc.open("AI_Ledger_Database") 
        worksheet = spreadsheet.sheet1
        
        # Convert the DataFrame into a list of lists (excluding the header row)
        data_to_upload = df.values.tolist()
        
        # Append the rows directly to the cloud sheet
        worksheet.append_rows(data_to_upload)
        print("✅ Cloud sync complete! Check your Google Sheet.")
        
    except Exception as e:
        print(f"❌ Cloud sync failed: {str(e)}")

    return state

# ---------------------------------------------------------
# 4. EXECUTION CONTROL GRAPH ENGINE
# ---------------------------------------------------------
def run_agent_workflow():
    """Compiles execution logic following deterministic ADK graph loops."""
    # Initialize running state
    current_state = AgentState()
    
    # 1. Execute Ingestion Node
    current_state = node_ingest_batch(current_state)
    print(f"📦 Staged {len(current_state.queue)} invoice files into execution queue.")

    # 2. Loop through execution queue nodes until empty
    while len(current_state.queue) > 0:
        current_state = node_extract_invoice(current_state)

    # 3. Compile data through export node
    current_state = node_export_ledger(current_state)
    print("🎯 Iterative processing workflow completed successfully.")

if __name__ == "__main__":
    run_agent_workflow()
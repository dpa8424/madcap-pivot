import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import datetime
import uuid
import re # For email validation
from streamlit_javascript import st_javascript

# --- CONFIGURATION ---
st.set_page_config(page_title="Madcap Pivot", page_icon="🚀", layout="centered")

# --- HELPER FUNCTIONS ---
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    # Simple check: remove non-digits, check if length is 10 or more
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 10

def get_browser_data():
    try:
        ua = st_javascript("navigator.userAgent")
        ip = st_javascript("await fetch('https://api.ipify.org').then(r => r.text())")
        return ua, ip
    except:
        return "Unknown", "Unknown"

# --- GOOGLE SHEETS CONNECTION ---
def get_sheet_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Madcap Pivot Leads").sheet1

def check_if_user_exists(email):
    try:
        sheet = get_sheet_connection()
        # Get all emails in column 2 (B)
        emails = sheet.col_values(2)
        if email in emails:
            return True
        return False
    except:
        return False

def save_lead_to_sheets(name, email, phone, vision, session_id, ip, device):
    try:
        sheet = get_sheet_connection()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Added empty string for Password column (Column I) initially
        sheet.append_row([str(name), str(email), str(phone), str(vision), str(timestamp), str(session_id), str(ip), str(device), ""])
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def update_password_in_sheet(email, password):
    try:
        sheet = get_sheet_connection()
        cell = sheet.find(email)
        # Update Column 9 (I) which is Password
        sheet.update_cell(cell.row, 9, password) 
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- SESSION STATE ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "blueprint_stage" not in st.session_state:
    st.session_state.blueprint_stage = 0 

# --- THE ARCHITECT SYSTEM PROMPT ---
system_prompt_content = """
You are the "Madcap Architect." You are helping a founder build a 50,000-foot Strategic Outline.

YOUR PROCESS:
1. **Validation Strategy:** Who is the customer and what is the MVP?
2. **Brand Strategy:** What is the "Hunk Factor"? (Differentiation).
3. **Systems Strategy:** How does this run without the founder? (Automation/Madcap Stack).
4. **Scale Strategy:** What is the franchise/exit vision?

BEHAVIOR:
- Ask ONE clear, high-level question to define the current phase.
- When the user answers, validate it briefly, then IMMEDIATEY move to the next phase.
- If Phase 4 is done, generate "THE MADCAP BLUEPRINT" summary.
"""

# --- THE LANDING PAGE ---
def lead_gen_form():
    st.title("Madcap Pivot // Founder's Launchpad")
    st.markdown("### Architect Your Vision.")
    
    device_info, ip_address = get_browser_data()
    
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
        with col2:
            phone = st.text_input("Phone Number")
        vision = st.text_area("What is your Business Vision?", placeholder="e.g. Uber for Pet Waste...")
        
        submitted = st.form_submit_button("Start Blueprint Session 🚀", type="primary")
        
        if submitted:
            # 1. Validate Inputs
            if not name or not email or not phone or not vision:
                st.error("Please fill in all fields.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            elif not is_valid_phone(phone):
                st.error("Please enter a valid phone number (10+ digits).")
            
            # 2. Check Duplicates
            elif check_if_user_exists(email):
                st.warning("It looks like you've been here before, partner. We already have that email in the Madcap Vault.")
                st.info("Since this is a Beta, please use a different email or ping Admin.")
            
            # 3. Success
            else:
                with st.spinner("Initializing Architect..."):
                    save_lead_to_sheets(name, email, phone, vision, st.session_state.session_id, ip_address, device_info)
                    st.session_state.user_info = {"name": name, "vision": vision, "email": email}
                    st.session_state.blueprint_stage = 1 
                    
                    first_msg = (
                        f"Hello {name}. Let's draft the Blueprint for *'{vision}'*.\n\n"
                        "**Phase 1: Validation Strategy**\n"
                        "We need to prove this works. In one sentence: **Who is your ideal first client, and what is the 'MVP' (Minimum Viable Product) you will sell them?**"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first_msg})
                    st.rerun()

# --- STATUS LIGHTS COMPONENT ---
def render_status_lights():
    st.markdown("### Blueprint Status")
    cols = st.columns(4)
    phases = ["1. Validation", "2. Brand", "3. Systems", "4. Scale"]
    
    for i, phase_name in enumerate(phases):
        # Logic: 
        # If stage > (i+1): Green (Completed)
        # If stage == (i+1): Yellow (In Progress)
        # If stage < (i+1): Red (Not Started)
        
        phase_num = i + 1
        if st.session_state.blueprint_stage > phase_num:
            color = "🟢" # Done
        elif st.session_state.blueprint_stage == phase_num:
            color = "🟡" # Active
        else:
            color = "🔴" # Pending
            
        cols[i].markdown(f"**{color} {phase_name}**")
    st.markdown("---")

# --- THE MAIN INTERFACE ---
def main_app():
    st.title("Madcap Pivot")
    
    # Render Traffic Lights at the top
    render_status_lights()

    # API Key Check
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    else:
        st.error("System Error: OpenAI Key Missing.")
        return

    # Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Account Conversion (End of Flow)
    if st.session_state.blueprint_stage == 5:
        st.success("Blueprint Generated.")
        with st.container(border=True):
            st.markdown("### 🔒 Save Your Blueprint")
            st.markdown("Create a password to convert this Guest Session into a **Madcap Founder Account**.")
            
            with st.form("account_convert"):
                new_password = st.text_input("Create Password", type="password")
                convert_btn = st.form_submit_button("Create Account")
                
                if convert_btn and new_password:
                    update_password_in_sheet(st.session_state.user_info['email'], new_password)
                    st.balloons()
                    st.success("Account Created! You are officially in the ecosystem.")
                    st.stop() # Stops the chat input from showing

    # Input (Only show if not complete)
    if st.session_state.blueprint_stage < 5:
        if prompt := st.chat_input("Your strategy..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Advance Stage Logic
            st.session_state.blueprint_stage += 1

            # Context Injection
            full_system_prompt = f"""
            {system_prompt_content}
            CONTEXT:
            User: {st.session_state.user_info['name']}
            Vision: {st.session_state.user_info['vision']}
            Current Blueprint Phase: {st.session_state.blueprint_stage} / 4
            
            INSTRUCTION:
            If Phase is 1-4: Acknowledge briefly, then ask the key strategic question for the NEW Phase.
            If Phase is 5: Generate the full "THE MADCAP BLUEPRINT" summary.
            """
            
            conversation_history = [{"role": "system", "content": full_system_prompt}]
            conversation_history.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])

            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation_history,
                    stream=True,
                )
                response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun() # Force refresh to update Status Lights immediately

# --- ROUTING ---
if st.session_state.user_info is None:
    lead_gen_form()
else:
    main_app()

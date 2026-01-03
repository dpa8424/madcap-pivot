import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import datetime
import uuid
import re
from streamlit_javascript import st_javascript

# --- CONFIGURATION ---
st.set_page_config(page_title="Madcap Launch Pad", page_icon="🚀", layout="centered")

# --- HELPER FUNCTIONS ---
def get_browser_data():
    try:
        ua = st_javascript("navigator.userAgent")
        ip = st_javascript("await fetch('https://api.ipify.org').then(r => r.text())")
        return ua, ip
    except:
        return "Unknown", "Unknown"

# --- GOOGLE SHEETS DATABASE ---
def get_sheet_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Madcap Pivot Leads").sheet1

def save_new_lead(name, email, phone, vision, session_id, ip, device):
    try:
        sheet = get_sheet_connection()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Columns: Name, Email, Phone, Vision, Timestamp, Session, IP, Device, Pass, Blueprint
        sheet.append_row([str(name), str(email), str(phone), str(vision), str(timestamp), str(session_id), str(ip), str(device), "", ""])
        return True
    except Exception as e:
        st.error(f"DB Error: {e}")
        return False

def login_user(email, password):
    try:
        sheet = get_sheet_connection()
        records = sheet.get_all_records() # Gets data as list of dicts
        for row in records:
            # Check if email matches and password matches (and password isn't empty)
            if str(row['Email']).strip().lower() == email.strip().lower() and str(row['Password']) == password and str(row['Password']) != "":
                return row # Return the user data
        return None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

def reset_password(email, phone, new_password):
    try:
        sheet = get_sheet_connection()
        # Find row where Email AND Phone match
        cell = sheet.find(email)
        if cell:
            row_num = cell.row
            stored_phone = sheet.cell(row_num, 3).value # Column 3 is Phone
            if str(stored_phone).strip() == str(phone).strip():
                sheet.update_cell(row_num, 9, new_password) # Column 9 is Password
                return True
        return False
    except:
        return False

def update_account_data(email, password=None, blueprint=None):
    try:
        sheet = get_sheet_connection()
        cell = sheet.find(email)
        if cell:
            if password:
                sheet.update_cell(cell.row, 9, password) # Col 9
            if blueprint:
                sheet.update_cell(cell.row, 10, blueprint) # Col 10
            return True
        return False
    except:
        return False

# --- SESSION STATE ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None # Holds data if logged in
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "blueprint_stage" not in st.session_state:
    st.session_state.blueprint_stage = 0 
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "Guest" # Options: Guest, Login, Dashboard, Reset

# --- SYSTEM PROMPTS ---
system_prompt_content = """
You are the "Madcap Architect." 
PROCESS:
1. Validation Strategy (Customer/MVP)
2. Brand Strategy (Hunk Factor)
3. Systems Strategy (Automation)
4. Scale Strategy (Exit)
BEHAVIOR:
- Ask ONE clear strategic question per phase.
- Move immediately to the next phase after an answer.
- If Phase 4 is done, generate "THE MADCAP BLUEPRINT" summary.
"""

# --- COMPONENT: STATUS LIGHTS ---
def render_status_lights():
    if st.session_state.blueprint_stage == 5:
        st.success("Blueprint Complete 🟢")
        return
        
    cols = st.columns(4)
    phases = ["Validation", "Brand", "Systems", "Scale"]
    for i, phase_name in enumerate(phases):
        phase_num = i + 1
        color = "🟢" if st.session_state.blueprint_stage > phase_num else ("🟡" if st.session_state.blueprint_stage == phase_num else "🔴")
        cols[i].markdown(f"**{color} {phase_name}**")
    st.markdown("---")

# --- VIEW: DASHBOARD (Logged In) ---
def dashboard_view():
    user = st.session_state.user_info
    st.title(f"Madcap HQ // {user['Name']}")
    
    # Vision Card
    with st.container(border=True):
        st.subheader("Your Vision")
        st.info(user['Vision'])
    
    # Blueprint Card
    with st.container(border=True):
        st.subheader("Your Blueprint")
        if user['Blueprint_Text']:
            st.markdown(user['Blueprint_Text'])
        else:
            st.warning("No Blueprint generated yet. Please restart a session.")
            
    if st.button("Log Out"):
        st.session_state.user_info = None
        st.session_state.page_mode = "Guest"
        st.session_state.messages = []
        st.session_state.blueprint_stage = 0
        st.rerun()

# --- VIEW: LOGIN / RESET ---
def auth_sidebar():
    with st.sidebar:
        st.title("Madcap Access")
        
        # Navigation Buttons
        if st.button("🏠 New Session"):
            st.session_state.page_mode = "Guest"
            st.rerun()
            
        if st.session_state.user_info is None:
            if st.button("🔑 Member Login"):
                st.session_state.page_mode = "Login"
                st.rerun()
            if st.button("❓ Forgot Password"):
                st.session_state.page_mode = "Reset"
                st.rerun()

def login_page():
    st.title("Member Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Access Dashboard")
        
        if submitted:
            user_data = login_user(email, password)
            if user_data:
                st.session_state.user_info = user_data
                st.session_state.page_mode = "Dashboard"
                st.success("Welcome back.")
                st.rerun()
            else:
                st.error("Invalid credentials.")

def reset_page():
    st.title("Reset Password")
    st.caption("Verify your identity to set a new password.")
    with st.form("reset_form"):
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number (Must match records)")
        new_pass = st.text_input("New Password", type="password")
        submitted = st.form_submit_button("Update Password")
        
        if submitted:
            if reset_password(email, phone, new_pass):
                st.success("Password updated! Please log in.")
            else:
                st.error("Identity verification failed. Email or Phone does not match records.")

# --- VIEW: THE CHAT APP (Guest) ---
def guest_app():
    # Only show Landing Page if stage is 0
    if st.session_state.blueprint_stage == 0:
        st.title("Madcap Pivot // Founder's Launchpad")
        st.markdown("### Architect Your Vision.")
        device_info, ip_address = get_browser_data()
        
        with st.form("entry_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name")
            email = col1.text_input("Email Address")
            phone = col2.text_input("Phone Number")
            vision = st.text_area("Business Vision")
            
            if st.form_submit_button("Start Blueprint Session 🚀", type="primary"):
                if name and email and vision:
                    # Save Initial Lead
                    save_new_lead(name, email, phone, vision, st.session_state.session_id, ip_address, device_info)
                    
                    # Set Session
                    st.session_state.user_info = {"Name": name, "Email": email, "Vision": vision}
                    st.session_state.blueprint_stage = 1
                    
                    # First Message
                    first_msg = f"Hello {name}. Let's draft the Blueprint for *'{vision}'*.\n\n**Phase 1: Validation Strategy**\nWho is your ideal first client, and what is the 'MVP' you will sell them?"
                    st.session_state.messages.append({"role": "assistant", "content": first_msg})
                    st.rerun()
                else:
                    st.error("Please fill all fields.")
    
    # If Stage > 0, Show Chat
    else:
        st.title("Madcap Pivot")
        render_status_lights()
        
        # API Key
        if "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        else:
            st.error("API Key Missing.")
            return

        # Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Account Conversion (Stage 5)
        if st.session_state.blueprint_stage == 5:
            # Capture the last AI message (The Blueprint)
            last_msg = st.session_state.messages[-1]['content']
            
            with st.container(border=True):
                st.markdown("### 🔒 Save Your Blueprint")
                st.markdown("Create a password to save this to your account.")
                password = st.text_input("Create Password", type="password", key="new_acct_pass")
                
                if st.button("Create Account"):
                    if password:
                        # Save Password AND Blueprint to Sheet
                        update_account_data(st.session_state.user_info['Email'], password, last_msg)
                        st.balloons()
                        st.success("Account Created! Go to 'Member Login' to see your dashboard.")
        
        # Chat Input (Only if not done)
        elif prompt := st.chat_input("Your strategy..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.blueprint_stage += 1
            
            # Context
            full_prompt = f"{system_prompt_content}\nCONTEXT: User: {st.session_state.user_info['Name']} Vision: {st.session_state.user_info['Vision']} Phase: {st.session_state.blueprint_stage}/4"
            
            # AI Response
            conversation_history = [{"role": "system", "content": full_prompt}]
            conversation_history.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
            
            with st.chat_message("assistant"):
                stream = client.chat.completions.create(model="gpt-4o", messages=conversation_history, stream=True)
                response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# --- MAIN CONTROLLER ---
auth_sidebar()

if st.session_state.page_mode == "Login":
    login_page()
elif st.session_state.page_mode == "Reset":
    reset_page()
elif st.session_state.page_mode == "Dashboard":
    dashboard_view()
else:
    guest_app()

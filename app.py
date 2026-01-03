import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import datetime
import uuid
from streamlit_javascript import st_javascript

# --- CONFIGURATION ---
st.set_page_config(page_title="Madcap Pivot", page_icon="🚀", layout="centered")

# --- BROWSER FINGERPRINTING ---
def get_browser_data():
    try:
        ua = st_javascript("navigator.userAgent")
        ip = st_javascript("await fetch('https://api.ipify.org').then(r => r.text())")
        return ua, ip
    except:
        return "Unknown", "Unknown"

# --- GOOGLE SHEETS CONNECTION ---
def save_lead_to_sheets(name, email, phone, vision, session_id, ip, device):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Madcap Pivot Leads").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Ensure we write strings to avoid JSON errors
        sheet.append_row([str(name), str(email), str(phone), str(vision), str(timestamp), str(session_id), str(ip), str(device)])
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

# --- SESSION STATE ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "Validation" # Tracks where the user is in the roadmap

# --- THE EFFORTLESS ENTREPRENEUR SYSTEM PROMPT ---
system_prompt_content = """
You are the "Madcap Pivot" Coach. You are not a generic AI. You are a disciplined Business Builder following the 'Effortless Entrepreneur' methodology (Schwartz, Friedman, Soliman).

YOUR ROADMAP (Do not skip steps):
1. **PHASE 1: THE CARGO VAN TEST (Validation)**
   - Goal: Force the user to validate the idea NOW.
   - Key Questions: "Who pays you today?", "Can you do this with a rented van (MVP)?", "Stop planning, start selling."
   - DO NOT let them move to Phase 2 until they prove someone wants this.

2. **PHASE 2: THE HUNK FACTOR (Branding)**
   - Goal: Differentiation. How is this not just a commodity?
   - Key Questions: "What is the 'Experience'?", "Why would they remember your name?", "What is your 'Uniform' (Brand Identity)?"

3. **PHASE 3: THE PLAYBOOK (Systematization)**
   - Goal: Remove the founder from the daily work.
   - Key Questions: "Write the manual.", "If you get sick, does the business stop?", "Automate or Delegate."

4. **PHASE 4: SCALE (Franchise Mindset)**
   - Goal: 10x Growth.
   - Key Questions: "Can this be franchised?", "How do we replicate you?", "What is the exit strategy?"

YOUR BEHAVIOR:
- Check `current_stage` in context. Stick to that stage.
- Be Direct. Use the "Ready, Fire, Aim" philosophy.
- TONE: Encouraging but tough. "Madcap Style."
- OUTPUT: Short paragraphs. End with ONE specific question to move them through the current phase.
"""

# --- THE LANDING PAGE (The Gate) ---
def lead_gen_form():
    # Header Section
    st.title("Madcap Pivot // Founder's Launchpad")
    
    st.markdown("""
    ### Stop Dreaming. Start Building.
    Most "ideas" stay in your head because you lack a roadmap. 
    **Madcap Pivot** is your 24/7 AI Co-Founder designed to take you from **"Napkin Sketch"** to **"Scalable Business."**
    
    **Why use this?**
    * **Validate Fast:** We use the *"Effortless Entrepreneur"* method to test your idea before you waste money.
    * **Build Your Board:** Get instant feedback from an AI trained on the minds of top Venture Capitalists.
    * **Create Your Deck:** Every conversation here builds the data you need for your future Pitch Deck.
    
    **Enter the Lab below to begin.**
    ---
    """)
    
    # Spy Data
    device_info, ip_address = get_browser_data()
    
    # The Form
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
        with col2:
            phone = st.text_input("Phone Number")
            
        vision = st.text_area("What is your Business Vision?", placeholder="e.g. I want to start a premium mobile car wash service...")
        
        st.caption("By entering, you agree to the Madcap Labs Beta Protocol.")
        submitted = st.form_submit_button("Launch Session 🚀", type="primary")
        
        if submitted:
            if name and email and vision:
                with st.spinner("Initializing Launchpad..."):
                    save_lead_to_sheets(name, email, phone, vision, st.session_state.session_id, ip_address, device_info)
                    
                    st.session_state.user_info = {"name": name, "vision": vision}
                    
                    # THE FIRST PROMPT (Kicks off Phase 1)
                    first_msg = (
                        f"Welcome to the Lab, {name}. I've reviewed your vision for *'{vision}'*.\n\n"
                        "We are starting at **Phase 1: The Cargo Van Test** (Validation).\n\n"
                        "Forget the logo. Forget the website. **Who is the very first person who will pay you real money for this, and have you asked them yet?**"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first_msg})
                    st.rerun()
            else:
                st.error("Please fill in all fields to access the Launchpad.")

# --- THE MAIN INTERFACE ---
def main_app():
    st.title("Madcap Pivot")
    st.progress(25, text="Phase 1: Validation") # Visual progress bar (Static for now, dynamic later)
    st.caption("Methodology: Effortless Entrepreneur // Ready. Fire. Aim.")

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

    # Input
    if prompt := st.chat_input("Your response..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Inject Context
        full_system_prompt = f"{system_prompt_content}\n\nUSER CONTEXT: Name: {st.session_state.user_info['name']}. Vision: {st.session_state.user_info['vision']}."
        
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

# --- ROUTING ---
if st.session_state.user_info is None:
    lead_gen_form()
else:
    main_app()

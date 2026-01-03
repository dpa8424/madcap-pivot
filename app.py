import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import datetime
import uuid
from streamlit_javascript import st_javascript

# --- CONFIGURATION ---
st.set_page_config(page_title="Madcap Pivot", page_icon="🚀", layout="centered")

# --- BROWSER FINGERPRINTING (The Spy Logic) ---
# We use JS to ask the browser "Who are you?" and "Where are you?"
def get_browser_data():
    try:
        # Get User Agent (Device Type)
        ua = st_javascript("navigator.userAgent")
        # Get IP Address (by pinging an external API from the client side)
        ip = st_javascript("await fetch('https://api.ipify.org').then(r => r.text())")
        return ua, ip
    except:
        return "Unknown", "Unknown"

# --- CONNECT TO GOOGLE SHEETS ---
def save_lead_to_sheets(name, email, phone, vision, session_id, ip, device):
    try:
        # Load credentials from Streamlit Secrets
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the Sheet
        sheet = client.open("Madcap Pivot Leads").sheet1
        
        # Append the row
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, email, phone, vision, timestamp, session_id, ip, device])
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

# --- INITIALIZE SESSION STATE ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) # Generate a unique ID for this visit

# --- THE COLLECTIVE PERSONA ---
system_prompt_content = """
You are the Madcap Founder's Agent. You are a "Board of Directors" in one AI.
You combine the wisdom of:
1. Steve Blank (The Lean Startup): Obsessed with customer discovery.
2. Gary Vaynerchuk (Hustle/Brand): Obsessed with attention and speed.
3. Donald Kuratko (Feasibility): Obsessed with financial viability.
4. Robert Hisrich (Scale): Obsessed with international structure.

BEHAVIOR:
- Synthesize their advice.
- TONE: Direct, strategic, encouraging but realistic.
- FORMAT: Short paragraphs. End with ONE provocative question.
"""

# --- THE GATEKEEPER (Lead Gen) ---
def lead_gen_form():
    st.title("Madcap Pivot // The Founder's Launchpad")
    st.markdown("To access the Madcap Brainstorming Agent, please introduce yourself.")
    
    # Run the "Spy" code in the background while they look at the form
    device_info, ip_address = get_browser_data()
    
    with st.form("entry_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        vision = st.text_area("What is your rough Business Vision?", placeholder="e.g. I want to build an Uber for Dog Walkers...")
        
        submitted = st.form_submit_button("Enter the Lab")
        
        if submitted:
            if name and email and vision:
                with st.spinner("Securing your session..."):
                    success = save_lead_to_sheets(
                        name, email, phone, vision, 
                        st.session_state.session_id, 
                        str(ip_address), 
                        str(device_info)
                    )
                    
                    if success:
                        st.session_state.user_info = {"name": name, "vision": vision}
                        # Inject the first AI message based on their vision
                        first_msg = f"Hello {name}. I see you want to build: *'{vision}'*. Let's pressure test this. Who is the FIRST person who will pay you for this?"
                        st.session_state.messages.append({"role": "assistant", "content": first_msg})
                        st.rerun()
            else:
                st.error("Please provide Name, Email, and Vision.")

# --- THE MAIN APP ---
def main_app():
    st.title("Madcap Pivot")
    st.caption(f"Session ID: {st.session_state.session_id} | User: {st.session_state.user_info['name']}")

    # API Key Handling
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    else:
        st.error("System Error: OpenAI API Key missing.")
        return

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # The User Input
    if prompt := st.chat_input("Reply to the Board..."):
        
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Prepare History
        conversation_history = [{"role": "system", "content": system_prompt_content}]
        conversation_history.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history,
                stream=True,
            )
            response = st.write_stream(stream)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- CONTROL FLOW ---
if st.session_state.user_info is None:
    lead_gen_form()
else:
    main_app()

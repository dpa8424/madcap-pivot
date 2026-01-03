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
if "blueprint_stage" not in st.session_state:
    st.session_state.blueprint_stage = 0 
    # Stages: 0=Intro, 1=Validation, 2=Brand, 3=Systems, 4=Scale, 5=Complete

# --- THE ARCHITECT SYSTEM PROMPT ---
system_prompt_content = """
You are the "Madcap Architect." You are helping a founder build a 50,000-foot Strategic Outline (The Madcap Blueprint).

YOUR GOAL:
Interview the user to fill out the 4 Phases of the 'Effortless Entrepreneur' Framework.
Do not get stuck in the weeds. Do not ask for task lists. Ask for *Strategy*.

YOUR PROCESS (Track the user's progress):
1. **Validation Strategy:** Who is the customer and what is the MVP? (Get the high-level concept).
2. **Brand Strategy:** What is the "Hunk Factor"? (Differentiation/Vibe).
3. **Systems Strategy:** How does this run without the founder? (Automation/Team).
4. **Scale Strategy:** What is the franchise/exit vision?

BEHAVIOR:
- Ask ONE clear, high-level question to define the current phase.
- When the user answers, validate it briefly, then IMMEDIATEY move to the next phase.
- Do not nag. If their answer is vague, accept it as a "Draft" and move on.
- Your goal is to finish the Outline, not to coach them on daily tasks.

FINAL OUTPUT (When Phase 4 is done):
Generate "THE MADCAP BLUEPRINT" in a code block.
Structure it like a One-Page Business Plan:
- **Executive Summary**
- **Phase 1: Validation Plan**
- **Phase 2: Brand Identity**
- **Phase 3: Operational Systems**
- **Phase 4: Scale & Exit**
Then ask: "Does this outline match your vision? If so, we are ready to build."
"""

# --- THE LANDING PAGE ---
def lead_gen_form():
    st.title("Madcap Pivot // Founder's Launchpad")
    st.markdown("""
    ### Architect Your Vision.
    You have the idea. Now you need the **Blueprint**.
    
    This agent helps you design the **50,000-foot Strategic Outline** for your business.
    We will walk through the 4 Phases of the *Madcap Methodology* to build your roadmap.
    
    *Output: A One-Page Strategic Blueprint you can use to start building.*
    ---
    """)
    
    device_info, ip_address = get_browser_data()
    
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
        with col2:
            phone = st.text_input("Phone Number")
        vision = st.text_area("What is your Business Vision?", placeholder="e.g. AI Agent for Waste Management...")
        
        submitted = st.form_submit_button("Start Blueprint Session 🚀", type="primary")
        
        if submitted:
            if name and email and vision:
                with st.spinner("Initializing Architect..."):
                    save_lead_to_sheets(name, email, phone, vision, st.session_state.session_id, ip_address, device_info)
                    st.session_state.user_info = {"name": name, "vision": vision}
                    st.session_state.blueprint_stage = 1 # Start Phase 1
                    
                    first_msg = (
                        f"Hello {name}. Let's draft the Blueprint for *'{vision}'*.\n\n"
                        "**Phase 1: Validation Strategy**\n"
                        "We need to prove this works. In one sentence: **Who is your ideal first client, and what is the 'MVP' (Minimum Viable Product) you will sell them?**"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": first_msg})
                    st.rerun()
            else:
                st.error("Please fill in all fields.")

# --- THE MAIN INTERFACE ---
def main_app():
    st.title("Madcap Pivot")
    
    # Progress Bar Logic
    stage_map = {1: 25, 2: 50, 3: 75, 4: 90, 5: 100}
    current_progress = stage_map.get(st.session_state.blueprint_stage, 100)
    
    stage_names = {
        1: "Phase 1: Validation Strategy",
        2: "Phase 2: Brand Differentiation",
        3: "Phase 3: Systems & Ops",
        4: "Phase 4: Scale Vision",
        5: "Blueprint Complete"
    }
    current_label = stage_names.get(st.session_state.blueprint_stage, "Complete")
    
    st.progress(current_progress, text=current_label)

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
    if prompt := st.chat_input("Your strategy..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Advance Stage Logic (Simple Incrementer)
        if st.session_state.blueprint_stage < 5:
            st.session_state.blueprint_stage += 1

        # Context Injection
        full_system_prompt = f"""
        {system_prompt_content}
        CONTEXT:
        User: {st.session_state.user_info['name']}
        Vision: {st.session_state.user_info['vision']}
        Current Blueprint Phase: {st.session_state.blueprint_stage} / 4
        
        INSTRUCTION:
        If Phase is 1-4: Acknowledge the user's last answer briefly, then ask the key strategic question for the NEW Phase.
        If Phase is 5: Generate the full "Madcap Blueprint" Summary based on the chat history.
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

# --- ROUTING ---
if st.session_state.user_info is None:
    lead_gen_form()
else:
    main_app()

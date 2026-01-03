import streamlit as st
from openai import OpenAI

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Madcap Pivot",
    page_icon="🚀",
    layout="centered"
)

# --- HEADER ---
st.title("Madcap Pivot // The CSO Agent")
st.markdown("""
**Transform your past into your future.** This agent takes your "Old Resume" and rewrites your narrative to fit your "Dream Role," 
using the MadcapVC methodology: *Data over fluff. Strategy over tactics.*
""")

# --- MAIN INPUTS ---
col1, col2 = st.columns(2)

with col1:
    target_role = st.text_input("Target Role", placeholder="e.g. Managing Partner, VC")

with col2:
    target_industry = st.text_input("Target Industry", placeholder="e.g. Venture Capital, AI")

old_resume = st.text_area("Paste your Old Resume / LinkedIn Bio", height=300)

# --- THE AGENT BRAIN ---
def generate_pivot(resume, role, industry):
    # LOOK FOR THE KEY IN SECRETS
    if "OPENAI_API_KEY" in st.secrets:
        secret_key = st.secrets["OPENAI_API_KEY"]
    else:
        st.error("Missing API Key in Secrets")
        return None
        
    client = OpenAI(api_key=secret_key)
    
    system_instruction = f"""
    You are the Chief Storytelling Officer (CSO) for MadCapVC. You are an expert in executive career pivots.
    
    YOUR GOAL:
    Rewrite the user's resume summary to position them perfectly for the role of '{role}' in the '{industry}' industry.
    
    THE RULES:
    1. NO FLUFF: Ban words like "passionate," "visionary," "synergy," or "guru."
    2. DATA FIRST: Find every metric ($ saved, % growth, team size) in the resume and prioritize them.
    3. THE BRIDGE: Explain how their OLD skills (e.g., Sales) make them dangerous in the NEW role (e.g., VC).
    4. TONE: Confident, terse, executive. "Madcap Style."
    
    OUTPUT FORMAT:
    1. A bold 6-10 word Headline.
    2. A "Pivot Bio" (2 paragraphs max).
    3. "The Transferable Edge" (3 bullet points linking past wins to future value).
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Here is my resume data:\n{resume}"}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

# --- THE ACTION BUTTON ---
if st.button("Generate My Narrative", type="primary"):
    if not old_resume or not target_role:
        st.warning("Please provide both a resume and a target role.")
    else:
        with st.spinner("Analyzing your career data..."):
            try:
                result = generate_pivot(old_resume, target_role, target_industry)
                if result:
                    st.success("Pivot Successful.")
                    st.markdown("### Your New Narrative")
                    st.markdown("---")
                    st.markdown(result)
            except Exception as e:
                st.error(f"An error occurred: {e}")

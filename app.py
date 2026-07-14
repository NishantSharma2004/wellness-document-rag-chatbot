import streamlit as st
import os
from pathlib import Path
from config.settings import settings
from src.indexing.index_manager import IndexManager
from src.generation.answer_generator import AnswerGenerator
from src.utils.exceptions import ChatbotException
from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()

# Page config
st.set_page_config(
    page_title="Document Intelligence Chatbot",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Restrained custom CSS for a premium dark/light mode friendly layout)
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Outfit', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .disclaimer-box {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #F59E0B;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .privacy-notice {
        font-size: 12px;
        color: #6B7280;
        margin-bottom: 20px;
    }
    .evidence-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
        margin-top: 5px;
    }
    .badge-high { background-color: #D1FAE5; color: #065F46; }
    .badge-medium { background-color: #DBEAFE; color: #1E40AF; }
    .badge-low { background-color: #FEF3C7; color: #92400E; }
    .badge-insufficient { background-color: #FEE2E2; color: #991B1B; }
    .badge-conflicting { background-color: #F3E8FF; color: #6B21A8; }
    .badge-safety { background-color: #FEE2E2; color: #991B1B; }
</style>
""", unsafe_allow_html=True)

# Singleton Resource caching to load index once
@st.cache_resource
def get_index_manager():
    return IndexManager()

@st.cache_resource
def get_answer_generator():
    return AnswerGenerator(get_index_manager())

try:
    index_manager = get_index_manager()
    generator = get_answer_generator()
except Exception as e:
    st.error(f"Failed to load application modules: {str(e)}")
    st.stop()

# Title
st.markdown("<h1 class='main-header'>🩺 Document Intelligence Chatbot</h1>", unsafe_allow_html=True)
st.markdown("##### Grounded Healthcare & Wellness Policy Assistant")

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Settings & Controls")
        
    # Get index status
    stats = index_manager.get_stats()
    indexed_docs = stats.get("documents", [])
    
    st.markdown(f"**Indexed Documents:** {len(indexed_docs)}")
    
    # Filter selection
    if indexed_docs:
        doc_sources = [d["source"] for d in indexed_docs]
        filter_option = st.radio("Search Scope", ["All Documents", "Filter by Document"])
        
        selected_sources = None
        if filter_option == "Filter by Document":
            selected_sources = st.multiselect("Select Documents", doc_sources, default=doc_sources)
    else:
        st.info("No documents indexed. Ingest sample documents using: `python ingest.py --sample`")
        selected_sources = None

    st.markdown("---")
    # Reset/clear chat history
    if st.button("🔄 Clear Chat Conversation"):
        st.session_state.messages = []
        st.rerun()

# Healthcare Disclaimer & Privacy Notice
st.markdown("""
<div class="disclaimer-box">
    <strong>Healthcare Disclaimer:</strong> This assistant retrieves information from the supplied company documents. 
    It does not provide independent medical diagnosis, emergency guidance, medication advice, or personalized treatment. 
    Please consult a qualified healthcare professional.
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='privacy-notice'>🔒 <strong>Privacy Notice:</strong> All searches and queries remain local and secure. Real policy documents are never committed to version control.</div>", unsafe_allow_html=True)

# Examples section
st.markdown("### 💡 Example Questions")
examples = [
    "What is the therapeutic alliance in digital mental health apps?",
    "What are the main findings regarding conversational agents?",
    "Summarize the barriers to using online mental health apps.",
    "What is the role of trust in digital interventions?"
]
cols = st.columns(len(examples))
selected_example = None
for i, ex in enumerate(examples):
    if cols[i].button(ex, key=f"ex_{i}"):
        selected_example = ex

def format_response_as_markdown(response_obj) -> str:
    lines = []
    
    # 1. Answer Summary
    lines.append("### Answer Summary")
    lines.append(response_obj.answer_summary)
    lines.append("")
    
    # 2. Key Details (only if present)
    if response_obj.key_details:
        lines.append("### Key Details")
        for detail in response_obj.key_details:
            lines.append(f"- {detail}")
        lines.append("")
        
    # 3. Source Document, Page Number, Section, Exact Supporting Text (only if citations present)
    if response_obj.citations:
        docs = list(set([cit.source for cit in response_obj.citations]))
        pages = [str(cit.page_start) for cit in response_obj.citations]
        sections = [cit.section if cit.section else "General" for cit in response_obj.citations]
        quotes = [f"“{cit.quote}”" for cit in response_obj.citations]
        
        lines.append("### Source Document")
        lines.append(", ".join(docs))
        lines.append("")
        
        lines.append("### Page Number")
        lines.append(", ".join(pages))
        lines.append("")
        
        lines.append("### Section")
        lines.append(", ".join(sections))
        lines.append("")
        
        lines.append("### Exact Supporting Text")
        for q in quotes:
            lines.append(q)
        lines.append("")
    
    # 4. Evidence Strength
    lines.append("### Evidence Strength")
    lines.append(response_obj.confidence.capitalize())
    
    return "\n".join(lines)

# Chat Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input field
user_query = st.chat_input("Ask a wellness or benefit policy question...")

# Trigger run on either user input or example click
query_to_run = user_query or selected_example

if query_to_run:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": query_to_run})
    with st.chat_message("user"):
        st.markdown(query_to_run)
        
    with st.chat_message("assistant"):
        response_obj = None
        error_to_show = None
        
        with st.spinner("🔍 Processing query..."):
            try:
                # Execute answer generation
                response_obj = generator.generate_response(
                    query=query_to_run,
                    filter_sources=selected_sources
                )
            except ChatbotException as ce:
                error_to_show = f"Error processing question: {str(ce)}"
            except Exception as e:
                error_to_show = "An unexpected error occurred. Please contact the administrator."
                logger.error(f"Unhandled app exception: {str(e)}", exc_info=True)
                
        if response_obj:
            # Generate full formatted markdown
            formatted_markdown = format_response_as_markdown(response_obj)
            # Show Response directly on page
            st.markdown(formatted_markdown)
            # Append response to session history
            st.session_state.messages.append({
                "role": "assistant",
                "content": formatted_markdown
            })
        elif error_to_show:
            st.error(error_to_show)

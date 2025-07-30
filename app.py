# app.py
import streamlit as st
import requests
import json
from io import BytesIO
import uuid

# Configure Streamlit page
st.set_page_config(
    page_title="Document Analysis Tool",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def check_api_health():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def analyze_documents_and_setup_chat(original_file, modified_file):
    """Send documents to backend for analysis and setup chat context"""
    files = {
        'original_file': ('original.pdf', original_file, 'application/pdf'),
        'modified_file': ('modified.pdf', modified_file, 'application/pdf')
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-and-chat/",
            files=files,
            data={'session_id': st.session_state.session_id}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def send_chat_message(message):
    """Send a chat message to the bot"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/",
            json={
                'message': message,
                'session_id': st.session_state.session_id
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Chat request failed: {str(e)}")
        return None

def clear_chat_session():
    """Clear the current chat session"""
    try:
        response = requests.post(f"{API_BASE_URL}/chat/clear/{st.session_state.session_id}")
        response.raise_for_status()
        st.session_state.chat_history = []
        st.session_state.analysis_complete = False
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to clear chat: {str(e)}")
        return False

def main():
    st.title("📄 Legal Document Analysis Tool")
    st.markdown("Compare two PDF documents and chat with AI about the changes")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Health Check
        if check_api_health():
            st.success("✅ Backend API is running")
        else:
            st.error("❌ Backend API is not available")
            st.warning("Please make sure the FastAPI backend is running on http://localhost:8000")
            return
        
        st.markdown("---")
        
        # Session info
        st.info(f"Session ID: {st.session_state.session_id[:8]}...")
        
        if st.button("🔄 New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.analysis_complete = False
            st.rerun()
        
        if st.button("🗑️ Clear Chat"):
            if clear_chat_session():
                st.success("Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        
        # Instructions
        st.markdown("""
        ### 📋 Instructions
        1. Upload the original PDF document
        2. Upload the modified PDF document
        3. Click 'Analyze Documents'
        4. Chat with AI about the changes
        """)
    
    # Main content area
    if not st.session_state.analysis_complete:
        # Document upload section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Original Document")
            original_file = st.file_uploader(
                "Choose the original PDF file",
                type=['pdf'],
                key="original",
                help="Upload the original version of your legal document"
            )
            
            if original_file is not None:
                st.success(f"✅ Loaded: {original_file.name}")
        
        with col2:
            st.subheader("📄 Modified Document")
            modified_file = st.file_uploader(
                "Choose the modified PDF file",
                type=['pdf'],
                key="modified",
                help="Upload the modified version of your legal document"
            )
            
            if modified_file is not None:
                st.success(f"✅ Loaded: {modified_file.name}")
        
        # Analysis button
        st.markdown("---")
        
        if st.button("🔍 Analyze Documents", type="primary", use_container_width=True):
            if original_file is None or modified_file is None:
                st.error("❌ Please upload both original and modified documents")
                return
            
            # Reset file pointers
            original_file.seek(0)
            modified_file.seek(0)
            
            with st.spinner("🔄 Analyzing documents and setting up chat... This may take a few minutes."):
                result = analyze_documents_and_setup_chat(original_file, modified_file)
            
            if result and result.get('status') == 'success':
                st.success("✅ Analysis completed! You can now chat about the document changes.")
                
                # Store the analysis result in session state so it persists
                st.session_state.analysis_result = result
                st.session_state.analysis_complete = True
                
                # Add initial message to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"I've analyzed your documents ({result.get('original_filename')} vs {result.get('modified_filename')}). The analysis is complete! Ask me anything about the changes, their legal implications, or what you should consider next."
                })
                
                st.rerun()
            else:
                st.error("❌ Analysis failed. Please check your files and try again.")
    
    else:
        # Section 2: Document Analysis Results (always visible)
        st.markdown("---")
        st.subheader("📊 Document Analysis Results")
        
        if 'analysis_result' in st.session_state:
            result = st.session_state.analysis_result
            
            # File information
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Original:** {result.get('original_filename', 'Unknown')}")
            with col2:
                st.info(f"**Modified:** {result.get('modified_filename', 'Unknown')}")
            
            # Analysis content
            with st.container():
                analysis_text = result.get('analysis', 'No analysis available')
                st.markdown(analysis_text)
            
            # Download option
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Download Report"):
                    report_data = {
                        "files": {
                            "original": result.get('original_filename'),
                            "modified": result.get('modified_filename')
                        },
                        "analysis": result.get('analysis'),
                        "session_id": st.session_state.session_id
                    }
                    
                    report_json = json.dumps(report_data, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=report_json,
                        file_name="document_analysis_report.json",
                        mime="application/json",
                        key="download_report"
                    )
            
            with col2:
                if st.button("📄 Analyze New Documents"):
                    st.session_state.analysis_complete = False
                    st.session_state.chat_history = []
                    if 'analysis_result' in st.session_state:
                        del st.session_state.analysis_result
                    st.rerun()
        
        # Section 3: Chat Interface
        st.markdown("---")
        st.subheader("💬 Chat About Document Changes")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about the document changes..."):
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Get bot response
            with st.spinner("Thinking..."):
                response = send_chat_message(prompt)
            
            if response and response.get('response'):
                bot_message = response['response']
                
                # Add bot response to history
                st.session_state.chat_history.append({"role": "assistant", "content": bot_message})
                
                # Rerun to update the chat display
                st.rerun()
            else:
                st.error("Failed to get response from the chatbot.")

if __name__ == "__main__":
    main()
import streamlit as st
import requests
import json
from io import BytesIO

# Configure Streamlit page
st.set_page_config(
    page_title="Document Analysis Tool",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def analyze_documents(original_file, modified_file):
    """Send documents to backend for analysis"""
    files = {
        'original_file': ('original.pdf', original_file, 'application/pdf'),
        'modified_file': ('modified.pdf', modified_file, 'application/pdf')
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/analyze-documents/", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def extract_text_only(original_file, modified_file):
    """Extract text and differences without LLM analysis"""
    files = {
        'original_file': ('original.pdf', original_file, 'application/pdf'),
        'modified_file': ('modified.pdf', modified_file, 'application/pdf')
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/extract-text/", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def main():
    st.title("📄 Legal Document Analysis Tool")
    st.markdown("Compare two PDF documents and analyze changes with AI-powered legal expertise")
    
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
        
        # Instructions
        st.markdown("""
        ### 📋 Instructions
        1. Upload the original PDF document
        2. Upload the modified PDF document
        3. Choose your analysis type
        4. Click 'Analyze Documents'
        """)
    
    # Main content area
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
        
        with st.spinner("🔄 Analyzing documents... This may take a few minutes."):
            result = analyze_documents(original_file, modified_file)
        
        if result and result.get('status') == 'success':
            st.success("✅ Analysis completed successfully!")
            
            # Display results
            st.markdown("---")
            st.header("📊 Analysis Results")
            
            # File information
            with st.expander("📁 File Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Original:** {result.get('original_filename', 'Unknown')}")
                with col2:
                    st.write(f"**Modified:** {result.get('modified_filename', 'Unknown')}")
            
            with st.expander("🤖 AI Legal Analysis", expanded=True):
                st.markdown(result.get('analysis', 'No analysis available'))
        
            # Download results
            st.markdown("---")
            if st.button("💾 Download Analysis Report"):
                report_data = {
                    "files": {
                        "original": result.get('original_filename'),
                        "modified": result.get('modified_filename')
                    },
                    "results": result
                }
                
                report_json = json.dumps(report_data, indent=2)
                st.download_button(
                    label="📥 Download JSON Report",
                    data=report_json,
                    file_name="document_analysis_report.json",
                    mime="application/json"
                )
        
        else:
            st.error("❌ Analysis failed. Please check your files and try again.")

if __name__ == "__main__":
    main()
import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="Document Differences Viewer",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Visual Document Differences")

st.markdown("This page shows a visual diff between the original and modified legal documents.")

# Path to the generated HTML diff file
html_diff_path = "html_files/differences.html"  # since Streamlit is running in project root

if os.path.exists(html_diff_path):
    with open(html_diff_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Render HTML diff
    components.html(html_content, height=1000, scrolling=True)
else:
    st.warning("⚠️ No visual diff file found yet. Run an analysis on the main page first.")

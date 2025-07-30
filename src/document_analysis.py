#src/document_analysis.py

from src.custom_exception import CustomException
import fitz
from difflib import SequenceMatcher
import requests
from difflib import HtmlDiff
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(BASE_DIR, "html_files")

class DocumentAnalysis:
    def __init__(self, original_file_path, modified_file_path):
        self.original_file_path=original_file_path
        self.modified_file_path=modified_file_path

    def extract_text(self, pdf_path):
        """
        Extract text from pdf at given path
        """
        doc=fitz.open(pdf_path)
        complete_text=""
        for page in doc:
            text=page.get_text()
            complete_text+=text+"\n"
        doc.close()
        return complete_text

    def extract_text_from_documents(self):
        """
        Extract text from original and updated pdfs
        """
        try:
            original_text=self.extract_text(self.original_file_path)
            modified_text=self.extract_text(self.modified_file_path)
            return original_text, modified_text

        except Exception as e:
            raise CustomException("Failed to extract data", e)

    def extract_text_diffs(self, a: str, b: str):
        """
        Extract changes made in the provided documents using difflib

        Args:
            a: Original document text
            b: Altered document text

        Returns:
            Tuple of changes
        """
        try:
            a_lines = a.splitlines()
            b_lines = b.splitlines()

            matcher = SequenceMatcher(None, a_lines, b_lines)
            diffs = []

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    continue  # skip unchanged sections

                diffs.append({
                    'type': tag,  # 'replace', 'delete', or 'insert'
                    'original_lines': a_lines[i1:i2],
                    'new_lines': b_lines[j1:j2],
                    'original_line_numbers': (i1 + 1, i2),  # line numbers are 1-indexed
                    'new_line_numbers': (j1 + 1, j2),
                })

            return diffs
        
        except Exception as e:
            raise CustomException("Failed to extract textual differences")
        
    def format_text_differences(self, diffs: str):
        """
        Formats differences to be utilised by LLM
        
        Args:
            diffs: Tuple consisting of differences between documents
        
        Returns:
            string: LLM friendly Natural language string explaining differences
        """
        try:
            formatted = []
            for change in diffs:
                if change['type'] == 'replace':
                    formatted.append(
                        f"Lines {change['original_line_numbers'][0]}–{change['original_line_numbers'][1]} were modified:\n"
                        f"Before: {' '.join(change['original_lines'])}\n"
                        f"After: {' '.join(change['new_lines'])}\n"
                    )
                elif change['type'] == 'delete':
                    formatted.append(
                        f"Lines {change['original_line_numbers'][0]}–{change['original_line_numbers'][1]} were deleted:\n"
                        f"Content: {' '.join(change['original_lines'])}\n"
                    )
                elif change['type'] == 'insert':
                    formatted.append(
                        f"Lines {change['new_line_numbers'][0]}–{change['new_line_numbers'][1]} were added:\n"
                        f"Content: {' '.join(change['new_lines'])}\n"
                    )

            llm_input = "\n".join(formatted)
            return llm_input

        except Exception as e:
            raise CustomException("Failed to format text")
        
    def analyze_document_changes(self, diff_text):
        """
        Analyzes changes using llama 3.1
        
        Args:
            diff_text: String consisting of changes between documents
        
        Output:
            string: Analysis of differences
        """
        prompt = f"""
        Act as a legal expert specialising in legal agreements.
        Explain it like to someone who is an affected stakeholder by the legal agreement.
        You are provided a list of changes in a legal agreement.
        Analyse and elaborate on it.
        The output should be a structured response involving all necessary details.
        Be precise and analytical in your responses, and only concern yourself with the relevant legal aspects.   
        {diff_text}
        """
        
        response = requests.post('http://localhost:11434/api/generate',
                                json={
                                    'model': 'llama3.1:8b-instruct-q4_K_M',
                                    'prompt': prompt,
                                    'stream': False
                                })
        
        return response.json()['response']
    
    def create_html_representation(self, original_text, new_text, output_path):
        """
        Creates visual representation of differences in the documents

        Args:
            original_text: text contained in original agreement
            new_text: text contained in altered agreement
            output_path: path to HTML file for observing visual differences
        """
        try:
            os.makedirs(output_path, exist_ok=True)

            d = HtmlDiff()
            html_table = d.make_table(
                original_text.splitlines(),
                new_text.splitlines(),
                context=True,
                numlines=3,
                fromdesc="Original Document",
                todesc="Modified Document"
            )

            html_template = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Document Differences Analysis</title>
                <style>
                    * {{
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                    }}
                    
                    .header {{
                        background: rgba(255, 255, 255, 0.95);
                        backdrop-filter: blur(10px);
                        padding: 20px;
                        box-shadow: 0 2px 20px rgba(0,0,0,0.1);
                        position: sticky;
                        top: 0;
                        z-index: 100;
                    }}
                    
                    .header h1 {{
                        margin: 0;
                        color: #2c3e50;
                        font-size: 2.2em;
                        font-weight: 600;
                        text-align: center;
                    }}
                    
                    .header p {{
                        margin: 10px 0 0 0;
                        color: #7f8c8d;
                        text-align: center;
                        font-size: 1.1em;
                    }}
                    
                    .container {{
                        max-width: 100%;
                        margin: 0;
                        padding: 20px;
                        background: rgba(255, 255, 255, 0.95);
                        backdrop-filter: blur(10px);
                        border-radius: 15px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                        margin: 20px;
                    }}
                    
                    .diff-wrapper {{
                        overflow-x: auto;
                        border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    }}
                    
                    table.diff {{
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 13px;
                        line-height: 1.4;
                        background: white;
                        min-width: 1200px; /* Ensures proper column width */
                    }}
                    
                    .diff_header {{
                        background: linear-gradient(135deg, #3498db, #2980b9);
                        color: white;
                        font-weight: bold;
                        text-align: center;
                        padding: 15px 10px;
                        font-size: 14px;
                        position: sticky;
                        top: 0;
                        z-index: 10;
                    }}
                    
                    .diff_next {{
                        background: linear-gradient(135deg, #34495e, #2c3e50);
                        color: white;
                        text-align: center;
                        font-weight: bold;
                        padding: 8px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }}
                    
                    .diff_next:hover {{
                        background: linear-gradient(135deg, #2c3e50, #34495e);
                        transform: translateY(-1px);
                    }}
                    
                    td, th {{
                        padding: 10px 12px;
                        border: 1px solid #e0e0e0;
                        vertical-align: top;
                        word-wrap: break-word;
                        max-width: 500px; /* Prevents columns from being too wide */
                    }}
                    
                    /* Line numbers styling */
                    td:first-child, td:nth-child(3) {{
                        background: #f8f9fa;
                        font-family: 'Courier New', monospace;
                        text-align: right;
                        padding: 10px 8px;
                        color: #6c757d;
                        font-size: 12px;
                        width: 60px;
                        min-width: 60px;
                        border-right: 2px solid #dee2e6;
                    }}
                    
                    /* Content columns */
                    td:nth-child(2), td:nth-child(4) {{
                        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                        white-space: pre-wrap;
                        width: calc(50% - 60px);
                    }}
                    
                    /* Diff highlighting with better colors */
                    .diff_add {{
                        background: linear-gradient(135deg, #d4edda, #c3e6cb);
                        border-left: 4px solid #28a745;
                        animation: fadeIn 0.5s ease-in;
                    }}
                    
                    .diff_sub {{
                        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                        border-left: 4px solid #dc3545;
                        animation: fadeIn 0.5s ease-in;
                    }}
                    
                    .diff_chg {{
                        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                        border-left: 4px solid #ffc107;
                        animation: fadeIn 0.5s ease-in;
                    }}
                    
                    /* Enhanced change highlighting within text */
                    .diff_add span.highlight {{
                        background: #28a745;
                        color: white;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-weight: bold;
                    }}
                    
                    .diff_sub span.highlight {{
                        background: #dc3545;
                        color: white;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-weight: bold;
                        text-decoration: line-through;
                    }}
                    
                    .diff_chg span.highlight {{
                        background: #fd7e14;
                        color: white;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-weight: bold;
                    }}
                    
                    /* Alternating row colors for better readability */
                    tr:nth-child(even) {{
                        background: rgba(248, 249, 250, 0.5);
                    }}
                    
                    /* Legend */
                    .legend {{
                        display: flex;
                        justify-content: center;
                        gap: 30px;
                        margin: 20px 0;
                        padding: 15px;
                        background: rgba(255, 255, 255, 0.8);
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    
                    .legend-item {{
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-weight: 500;
                    }}
                    
                    .legend-color {{
                        width: 20px;
                        height: 20px;
                        border-radius: 4px;
                        border: 2px solid rgba(0,0,0,0.1);
                    }}
                    
                    .legend-added {{ background: linear-gradient(135deg, #d4edda, #c3e6cb); }}
                    .legend-removed {{ background: linear-gradient(135deg, #f8d7da, #f5c6cb); }}
                    .legend-modified {{ background: linear-gradient(135deg, #fff3cd, #ffeaa7); }}
                    
                    /* Animations */
                    @keyframes fadeIn {{
                        from {{ opacity: 0; transform: translateY(10px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    
                    /* Responsive design */
                    @media (max-width: 768px) {{
                        .container {{
                            margin: 10px;
                            padding: 15px;
                        }}
                        
                        .legend {{
                            flex-direction: column;
                            gap: 15px;
                        }}
                        
                        table.diff {{
                            font-size: 12px;
                            min-width: 800px;
                        }}
                        
                        .header h1 {{
                            font-size: 1.8em;
                        }}
                    }}
                    
                    /* Scrollbar styling */
                    .diff-wrapper::-webkit-scrollbar {{
                        height: 12px;
                    }}
                    
                    .diff-wrapper::-webkit-scrollbar-track {{
                        background: #f1f1f1;
                        border-radius: 6px;
                    }}
                    
                    .diff-wrapper::-webkit-scrollbar-thumb {{
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        border-radius: 6px;
                    }}
                    
                    .diff-wrapper::-webkit-scrollbar-thumb:hover {{
                        background: linear-gradient(135deg, #764ba2, #667eea);
                    }}
                </style>
                <script>
                    // Add smooth scrolling to diff navigation
                    document.addEventListener('DOMContentLoaded', function() {{
                        const diffButtons = document.querySelectorAll('.diff_next');
                        diffButtons.forEach(button => {{
                            button.addEventListener('click', function() {{
                                this.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            }});
                        }});
                    }});
                </script>
            </head>
            <body>
                <div class="header">
                    <h1>📄 Document Differences Analysis</h1>
                    <p>Compare changes between original and modified legal documents</p>
                </div>
                
                <div class="container">
                    <div class="legend">
                        <div class="legend-item">
                            <div class="legend-color legend-added"></div>
                            <span>Added Content</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color legend-removed"></div>
                            <span>Removed Content</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color legend-modified"></div>
                            <span>Modified Content</span>
                        </div>
                    </div>
                    
                    <div class="diff-wrapper">
                        {html_table}
                    </div>
                </div>
            </body>
            </html>
            """

            output_file = os.path.join(output_path, "differences.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_template)

            print(f"Enhanced HTML diff saved to: {output_file}")

        except Exception as e:
            raise CustomException(f"Error in creating enhanced html: {e}")
   
    def run(self):
        a, b=self.extract_text_from_documents()
        differences=self.extract_text_diffs(a, b)
        llm_input=self.format_text_differences(differences)
        llm_response=self.analyze_document_changes(llm_input)
        self.create_html_representation(a, b, HTML_PATH)
        return llm_response

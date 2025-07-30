from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pathlib import Path
import shutil
import uvicorn
from src.document_analysis import DocumentAnalysis
from src.custom_exception import CustomException

app = FastAPI(title="Document Analysis API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document Analysis API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze-documents/")
async def analyze_documents(
    original_file: UploadFile = File(...),
    modified_file: UploadFile = File(...)
):
    """
    Analyze differences between two PDF documents
    
    Args:
        original_file: The original PDF file
        modified_file: The modified PDF file
        
    Returns:
        JSON response with analysis results
    """
    
    # Validate file types
    if not original_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Original file must be a PDF")
    
    if not modified_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Modified file must be a PDF")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files to temporary directory
        original_path = os.path.join(temp_dir, "original.pdf")
        modified_path = os.path.join(temp_dir, "modified.pdf")
        
        # Write files
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(original_file.file, buffer)
            
        with open(modified_path, "wb") as buffer:
            shutil.copyfileobj(modified_file.file, buffer)
        
        # Perform analysis
        document_analyzer = DocumentAnalysis(original_path, modified_path)
        analysis = document_analyzer.run()
        
        return {
            "status": "success",
            "analysis": analysis,
            "original_filename": original_file.filename,
            "modified_filename": modified_file.filename
        }
        
    except CustomException as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    finally:
        # Clean up temporary files
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
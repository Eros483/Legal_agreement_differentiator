#backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pathlib import Path
import shutil
import uvicorn
from src.document_analysis import DocumentAnalysis
from src.custom_exception import CustomException
from src.chatbot import ChatBot
from models.models import ChatRequest, ChatResponse
from prompt_templates.templates import default_chat_template

app = FastAPI(title="Document Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot_sessions={}
analysis=""

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
    Analyze differences between original file and updated file
    
    Args:
        original_file: The original PDF file
        modified_file: The modified PDF file
        
    Returns:
        JSON: response with analysis
    """

    if not original_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Original file must be a PDF")
    
    if not modified_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Modified file must be a PDF")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        original_path = os.path.join(temp_dir, "original.pdf")
        modified_path = os.path.join(temp_dir, "modified.pdf")

        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(original_file.file, buffer)
            
        with open(modified_path, "wb") as buffer:
            shutil.copyfileobj(modified_file.file, buffer)

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
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")

@app.post("/chat/", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Chat with the AI assistant

    Args:
        request: ChatRequest pydantic model containing message, message_id and system_prompt if needed

    Output:
        ChatResponse pydantic model containing bot reply
    """
    try:
        if request.session_id not in chatbot_sessions:
            print(f"Analysis for default system prompt: {analysis}")
            default_system_prompt=default_chat_template(analysis)

            system_prompt = request.system_prompt or default_system_prompt

            if not system_prompt:
                print("NO SYSTEM PROMPT")
                raise ValueError("No system prompt found in chat with bot route")
            else:
                print(system_prompt)
            chatbot_sessions[request.session_id] = ChatBot(system_prompt=system_prompt)
        
        chatbot = chatbot_sessions[request.session_id]
        
        # Update system prompt if provided
        if request.system_prompt:
            chatbot.set_system_prompt(request.system_prompt)
        
        # Get response
        response_text = chatbot.chat(request.message)
        if not response_text:
            raise HTTPException(status_code=500, detail="Empty response from chatbot")
        
        return ChatResponse(response=response_text, session_id=request.session_id)
        
    except Exception as e:
        raise CustomException(f"error in chat route", e)

@app.post("/chat/clear/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a specific chat session"""
    if session_id in chatbot_sessions:
        chatbot_sessions[session_id].clear_conversation()
        return {"status": "success", "message": f"Cleared session {session_id}"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    if session_id in chatbot_sessions:
        history = chatbot_sessions[session_id].get_conversation_history()
        return {"session_id": session_id, "history": history}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/analyze-and-chat/")
async def analyze_documents_and_start_chat(
    original_file: UploadFile = File(...),
    modified_file: UploadFile = File(...),
    session_id: str = "default"
):
    """
    Analyze documents and set up a chat session with the analysis context
    """
    if not original_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Original file must be a PDF")
    
    if not modified_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Modified file must be a PDF")
    
    temp_dir = tempfile.mkdtemp()
    global analysis
    try:
        original_path = os.path.join(temp_dir, "original.pdf")
        modified_path = os.path.join(temp_dir, "modified.pdf")
        
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(original_file.file, buffer)
            
        with open(modified_path, "wb") as buffer:
            shutil.copyfileobj(modified_file.file, buffer)
        
        document_analyzer = DocumentAnalysis(original_path, modified_path)
        analysis = document_analyzer.run()

        template=default_chat_template(analysis)

        if not template:
            print("NO INITIAL CHAT TEMPLATE")
            raise ValueError("No template set in analyze documents and start chat route")
        else:
            print(template)
        chatbot_sessions[session_id] = ChatBot(system_prompt=template)
        
        return {
            "status": "success",
            "analysis": analysis,
            "session_id": session_id,
            "message": "Analysis complete. You can now chat about the document changes.",
            "original_filename": original_file.filename,
            "modified_filename": modified_file.filename
        }
        
    except CustomException as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
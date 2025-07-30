#src/chatbot.py
import ollama
from typing import List, Dict, Optional
from src.custom_exception import CustomException

class ChatBot:
    def __init__(self, system_prompt: str="", model: str="llama3.1:8b-instruct-q4_K_M"):
        self.model=model
        self.messages=[]

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        else:
            raise ValueError("No system prompt received in chatbot class")

    def chat(self, user_input: str)-> str:
        """
        Send a message to the chatbot, and get response, and append to chat history

        Args:
            user_input: user's question

        Output:
            string: LLM Response
        """
        self.messages.append({"role": "user", "content": user_input})

        if len(self.messages)>10:
            system_msgs=[msg for msg in self.messages if msg["role"]=="system"]
            recent_messages=self.messages[-10:]
            self.messages=system_msgs+recent_messages

        try:
            response=ollama.chat(
                model=self.model,
                messages=self.messages
            )

            assistant_message=response['message']['content']

            if not assistant_message:
                raise ValueError(f"Failed to receive assistant message in chatbot class")
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message
        
        except Exception as e:
            self.messages.pop()
            raise CustomException(f"Failed to query llm for chat", e)
            
    def clear_conversation(self):
        """
        clear conversation memory without removing system prompt
        """
        self.messages=[msg for msg in self.messages if msg["role"]=="system"]

    def get_conversation_history(self, system_prompt: str):
        """
        Get current conversation history
        """
        return self.messages.copy()
    
    def set_system_prompt(self, system_prompt: str):
        """
        Update system prompt and clear conversation history
        """
        self.clear_conversation()
        if system_prompt:
            self.messages.insert(0, {"role": "system", "content": system_prompt})

            
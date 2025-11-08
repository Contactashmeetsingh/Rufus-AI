# Command to run this program
# GEMINI_API_KEY=AIzaSyCaedega5CfHeWDkd1yQKeR7SHEdFHZKHY python geminiTest.py
# python -m pip install google-genai
# This will install package needed, might be different based on how environment is setup
import os
import json
from google import genai
from google.genai import types

# --- Configuration ---
# Your API key will be read from the GEMINI_API_KEY environment variable.
# Get a key from the Google AI Studio: https://aistudio.google.com/apikey
MODEL_NAME = "gemini-2.5-flash"
MEMORY_FILE = 'results7.json'
#Results7.json is a local file, will push a proper updated file to github in a few days

import os
import json
from google import genai
from google.genai import types

# ... (Configuration variables remain the same) ...

def load_knowledge(file_path):
    """Loads knowledge from the JSON file and formats it into a system instruction."""
    if os.path.exists(file_path):
        # Use UTF-8 encoding for broad compatibility
        with open(file_path, 'r', encoding='utf-8') as f: 
            try:
                data = json.load(f)
                
                # Convert the loaded data into a string format the LLM can easily consume
                knowledge_string = json.dumps(data, indent=2)
                
                system_instruction = (
                    "You are a helpful assistant. Your knowledge is based *only* on the "
                    "following data provided in JSON format. Do not use outside knowledge. "
                    "When answering, reference this data if relevant:\n\n"
                    f"--- KNOWLEDGE DATA START ---\n{knowledge_string}\n--- KNOWLEDGE DATA END ---"
                )
                print(f"✅ Loaded knowledge from {file_path} and set system instructions.")
                return system_instruction
            
            except json.JSONDecodeError:
                print(f"⚠️ Error reading JSON file '{file_path}'. Using default instructions.")
                return "You are a helpful assistant."
            except UnicodeDecodeError as e:
                print(f"⚠️ UnicodeDecodeError when reading '{file_path}': {e}. Using default instructions.")
                return "You are a helpful assistant."
    
    print(f"⏳ Knowledge file '{file_path}' not found. Using default instructions.")
    return "You are a helpful assistant."

def save_history(history):
    """Saves the conversation history to the JSON file."""
    # Convert parts from Part objects to the required dictionary format for JSON saving
    serializable_history = []
    for message in history:
        # A message is a types.Content object with 'role' and 'parts'
        parts_list = []
        for part in message.parts:
            # part is a types.Part object; we only care about text for this example
            if part.text:
                parts_list.append({"text": part.text})
        
        # We need the 'role' and the converted 'parts' list for saving
        serializable_history.append({
            "role": message.role,
            "parts": parts_list
        })
        
    with open(MEMORY_FILE, 'w') as f:
        # Use simple dictionary structure for saving to JSON file
        json.dump(serializable_history, f, indent=4)
    # print(f"💾 History saved to {MEMORY_FILE}.")

def run_chatbot():
    """Initializes the chat, runs the main loop, and uses file for context."""
    
    # Check for API Key
    if 'GEMINI_API_KEY' not in os.environ:
        print("🚨 Error: Please set the GEMINI_API_KEY environment variable.")
        return

    # Initialize the client
    client = genai.Client()

    # 1. Load the data from the file to use as knowledge/system instruction
    system_instruction = load_knowledge(MEMORY_FILE)
    
    # 2. CREATE THE CONFIG OBJECT WITH THE SYSTEM INSTRUCTION
    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )
    
    # 3. Start the chat session, passing the config object
    chat = client.chats.create(
        model=MODEL_NAME, 
        config=config # Correct way to pass system instruction for chats.create()
    )

    print("\n🤖 Chatbot initialized. Type 'quit' or 'exit' to end the session.")
    
    # Main Chat Loop
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower() in ["quit", "exit"]:
                print("👋 Goodbye!")
                break
            
            # Send message
            response = chat.send_message(user_input)
            
            print(f"Bot: {response.text}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":

    run_chatbot()

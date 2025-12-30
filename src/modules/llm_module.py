import os
from groq import Groq
from dotenv import load_dotenv
from typing import Optional, List, Dict
import re

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("[WARNING] GROQ_API_KEY not found in environment. LLM features will not work.")
    print("Please set GROQ_API_KEY in your .env file.")

try:
    # Initialize the Groq client
    client = Groq(api_key=GROQ_API_KEY)
    GROQ_API_AVAILABLE = True
except Exception as e:
    print(f"[ERROR] Failed to initialize Groq client: {e}")
    GROQ_API_AVAILABLE = False

# Conversation history to maintain context
conversation_history: List[Dict[str, str]] = []
MAX_HISTORY = 6  # Keep last 3 exchanges (user + assistant pairs)


def is_likely_garbled(text: str) -> bool:
    """
    Detect if text is likely garbled from poor voice recognition.
    
    Returns True if the text shows signs of being unclear/garbled.
    """
    text = text.lower().strip()
    
    # Very short queries that are just filler words
    filler_only = ["okay", "ok", "um", "uh", "yeah", "yes", "no"]
    if text in filler_only:
        return False  # These are fine
    
    # Check for extremely fragmented sentences (lots of short words)
    words = text.split()
    if len(words) > 5:
        avg_word_length = sum(len(w) for w in words) / len(words)
        if avg_word_length < 3:  # Average word is very short - might be garbled
            return True
    
    # Check for repetitive words ("vintage vintage")
    word_counts = {}
    for word in words:
        if len(word) > 3:  # Only count non-trivial words
            word_counts[word] = word_counts.get(word, 0) + 1
            if word_counts[word] > 2:  # Same word repeated 3+ times
                return True
    
    # Check for incomplete/broken sentences
    broken_patterns = [
        r'^(and|but|or|so|because)\s',  # Starts with conjunction
        r'^(the|a|an)\s+$',  # Just an article
        r'\b(what|where|when|who|how)\s+in\s+the\s+\w+$',  # Incomplete question pattern
    ]
    for pattern in broken_patterns:
        if re.search(pattern, text):
            return True
    
    return False


def clear_conversation_history():
    """Clear the conversation history."""
    global conversation_history
    conversation_history = []


def generate_response(query: str, context: Optional[str] = None, use_history: bool = True) -> str:
    """
    Generates a response from the LLM based on a query and optional context.

    Args:
        query (str): The user's original query.
        context (Optional[str]): Optional context from a web search (e.g., dynamic_info_module).
        use_history (bool): Whether to use conversation history for context.

    Returns:
        A string containing the LLM's generated response.
    """
    global conversation_history
    
    if not GROQ_API_AVAILABLE:
        return "Sorry, the LLM service is not available. Please check your GROQ_API_KEY."

    # Define the persona and instructions for the model
    system_prompt = (
        "You are Lumen, a helpful voice assistant. Your responses should be brief, conversational, and suitable for being spoken aloud. "
        "Do not use markdown or special formatting. "
        "IMPORTANT: If the user's input seems unclear, garbled, or doesn't make sense (possibly due to poor voice recognition), "
        "politely ask them to repeat or rephrase their question. For example: 'I didn't quite catch that. Could you please repeat?' or "
        "'I'm not sure I understood correctly. Could you rephrase that?'. "
        "Use conversation context when available to better understand what the user is asking about. "
        "Keep responses under 3 sentences unless more detail is specifically requested."
    )

    # Check if input might be garbled
    if is_likely_garbled(query) and not context:
        # Ask for clarification instead of trying to interpret garbled input
        return "I didn't quite catch that. Could you please repeat or rephrase your question?"
    
    # Build messages list with history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if enabled
    if use_history and conversation_history:
        messages.extend(conversation_history[-MAX_HISTORY:])
    
    # Construct the user's message, including context if available
    if context:
        user_prompt = f"Based on this information:\n---\n{context}\n---\n\nPlease answer: {query}"
    else:
        user_prompt = query
    
    messages.append({"role": "user", "content": user_prompt})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
            top_p=1,
        )
        response = chat_completion.choices[0].message.content
        
        # Update conversation history
        if use_history:
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": response})
            # Trim history if too long
            if len(conversation_history) > MAX_HISTORY:
                conversation_history = conversation_history[-MAX_HISTORY:]
        
        return response
    except Exception as e:
        return f"Sorry, I encountered an error with the LLM service: {e}"


# Example usage for testing
if __name__ == "__main__":
    print("--- Testing LLM Chat (no context) ---")
    chat_query = "Tell me a fun fact about the Roman Empire."
    print(f"Query: {chat_query}\nResponse: {generate_response(chat_query)}\n")

    print("--- Testing Dynamic Info (with context) ---")
    info_query = "What's the latest news on space exploration?"
    search_context = "Top Search Results:\n\n🔹 SpaceX successfully launched its Starship rocket on its fourth test flight.\n🔹 NASA's Artemis program is preparing for a manned mission to the moon.\n"
    print(f"Query: {info_query}\nContext: {search_context}Response: {generate_response(info_query, context=search_context)}")
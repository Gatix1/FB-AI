import os
from groq import Groq
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

try:
    # Initialize the Groq client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    GROQ_API_AVAILABLE = True
except Exception:
    GROQ_API_AVAILABLE = False


def generate_response(query: str, context: Optional[str] = None) -> str:
    """
    Generates a response from the LLM based on a query and optional context.

    Args:
        query (str): The user's original query.
        context (Optional[str]): Optional context from a web search (e.g., dynamic_info_module).

    Returns:
        A string containing the LLM's generated response.
    """
    if not GROQ_API_AVAILABLE:
        return "Sorry, the LLM service is not available. Please check your GROQ_API_KEY."

    # Define the persona and instructions for the model
    system_prompt = (
        "You are a helpful and concise voice assistant named Lumen. "
        "Your responses should be brief, conversational, and suitable for being spoken aloud. "
        "Do not use markdown or special formatting."
    )

    # Construct the user's message, including context if available
    if context:
        user_prompt = f"Based on this information:\n---\n{context}\n---\n\nPlease answer the following user query: '{query}'"
    else:
        user_prompt = query

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=150,
            top_p=1,
        )
        return chat_completion.choices[0].message.content
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
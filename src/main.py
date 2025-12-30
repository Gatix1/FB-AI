# --- Import all the necessary modules ---
from modules import voice_module
from modules import intent_module
from modules import media_control_module
from modules import information_module
from modules import dynamic_info_module
from modules import llm_module


def process_command(command_text: str) -> tuple[str, bool]:
    """
    Processes the transcribed command text, routes it to the correct module,
    and returns the response.
    
    Args:
        command_text (str): The user's voice command transcribed to text.

    Returns:
        A tuple containing (response string, should_continue_conversation bool)
    """
    if not command_text:
        return "I didn't catch that. Could you please repeat?", True

    # 1. Parse the intent from the command
    parsed_data = intent_module.parse_intent(command_text)
    intent = parsed_data.get("intent")
    parameters = parsed_data.get("parameters", {})

    print(f"[DEBUG] Intent: {intent}, Parameters: {parameters}")

    response = ""
    # Media playback commands should exit conversation mode
    media_playback_intents = ["media_play_pause", "media_stop", "media_next", "media_previous", "play_song"]
    should_continue = intent not in media_playback_intents

    # 2. Route the intent to the appropriate module/function
    try:
        if intent == "set_volume":
            response = media_control_module.set_volume(**parameters)
        elif intent == "media_play_pause":
            response = media_control_module.media_play_pause()
        elif intent == "media_stop":
            response = media_control_module.media_stop()
        elif intent == "media_next":
            response = media_control_module.media_next()
        elif intent == "media_previous":
            response = media_control_module.media_previous()
        elif intent == "play_song":
            response = media_control_module.play_song(**parameters)
        elif intent == "get_time":
            response = information_module.get_current_time()
        elif intent == "get_date":
            response = information_module.get_current_date()
        elif intent == "get_weather":
            response = information_module.get_weather(**parameters)
        elif intent == "dynamic_info":
            query = parameters.get("query")
            print(f"Performing web search for: '{query}'")
            context = dynamic_info_module.fetch_dynamic_info(query)
            print(f"Context from web search:\n{context}")
            response = llm_module.generate_response(query, context=context)
        elif intent == "llm_chat":
            query = parameters.get("query")
            response = llm_module.generate_response(query)
        else:
            response = "I'm not sure how to handle that command."

    except Exception as e:
        print(f"[ERROR] An error occurred while executing the command for intent '{intent}': {e}")
        response = "Sorry, I ran into a problem trying to do that."

    return response, should_continue


def main():
    """
    The main function that runs the voice assistant loop.
    """
    # Initialize all modules (especially the voice module)
    voice_module.initialize()
    print("--- FB-AI Assistant is now running ---")

    in_conversation = False

    try:
        while True:
            command = ""
            if not in_conversation:
                # Standard mode: wait for the wake word
                if voice_module.listen_for_wake_word():
                    voice_module.speak_with_gtts("Yes?")
                    command = voice_module.listen_for_command()
                    in_conversation = True
            else:
                # Follow-up mode: listen for an immediate command
                command = voice_module.listen_for_follow_up(timeout=5)
                if not command:
                    in_conversation = False # Timeout, go back to wake word mode
                    # Clear LLM conversation history when exiting conversation mode
                    llm_module.clear_conversation_history()

            if command:
                response, should_continue = process_command(command)
                print(f"AI Response: {response}")
                voice_module.speak_with_gtts(response)
                # Continue conversation only if the command type allows it
                in_conversation = should_continue
                if not should_continue:
                    # Clear conversation history when exiting
                    llm_module.clear_conversation_history()

    except KeyboardInterrupt:
        print("\nExiting assistant...")
    finally:
        voice_module.cleanup()
        print("System shut down gracefully.")

if __name__ == "__main__":
    main()

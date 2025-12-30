from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from typing import Dict, Any, List, Tuple
import re

# Mapping of number words to their numeric values
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24, "twenty-five": 25,
    "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29, "thirty": 30,
    "thirty-five": 35, "forty": 40, "forty-five": 45, "fifty": 50,
    "fifty-five": 55, "sixty": 60, "sixty-five": 65, "seventy": 70,
    "seventy-five": 75, "eighty": 80, "eighty-five": 85, "ninety": 90,
    "ninety-five": 95, "hundred": 100, "one hundred": 100
}

# Define the known intents and the keywords/phrases that trigger them.
# This structure allows for multiple phrases to map to a single intent.
INTENT_MAP = {
    "set_volume": ["volume", "sound"],
    "media_play_pause": ["play", "pause", "unpause", "pose"],
    "media_stop": ["stop"],
    "media_next": ["next song", "next track", "skip", "next"],
    "play_song": ["play the song", "play song", "music", "song"],
    "media_previous": ["previous song", "previous track", "go back"],
    "get_time": ["time", "what time is it"],
    "get_date": ["date", "what is today's date"],
    "get_weather": ["weather", "what's the weather"],
}

# A list of all possible phrases to match against.
ALL_PHRASES = [phrase for phrases in INTENT_MAP.values() for phrase in phrases]

# Keywords to identify a query that requires a web search for dynamic information.
# If a query is not a predefined command and does not contain these triggers,
# it will be treated as a general conversational query for the LLM.
DYNAMIC_INFO_TRIGGERS = [
    "what are", "who are", "where are", "when are",
    "who is", "who's",
    "where is", "where's",
    "when is", "when's",
    "how to",
    "define",
    "price of", "cost of",
    "latest news", "headlines",
]

def _extract_parameters(command_text: str, intent: str) -> Dict[str, Any]:
    """
    Extracts parameters from the command text based on the identified intent.
    
    Args:
        command_text (str): The user's full command.
        intent (str): The identified intent.
        
    Returns:
        A dictionary of extracted parameters.
    """
    parameters = {}
    words = command_text.lower().split()

    if intent == "set_volume":
        direction = None
        
        # Keywords that indicate increasing volume
        increase_keywords = ["up", "increase", "raise", "higher", "louder"]
        # Keywords that indicate decreasing volume
        decrease_keywords = ["down", "decrease", "reduce", "lower", "quieter", "softer"]
        
        # Check for direction keywords
        if any(keyword in words for keyword in increase_keywords):
            direction = "up"
        elif any(keyword in words for keyword in decrease_keywords):
            direction = "down"

        # Find the first number in the command (check both digits and number words)
        value = None
        # First try to find numeric digits
        for word in words:
            cleaned_word = word.replace('%', '')
            try:
                value = int(cleaned_word)
                break
            except ValueError:
                continue # Not a number
        
        # If no digit found, check for number words
        if value is None:
            for word in words:
                if word in NUMBER_WORDS:
                    value = NUMBER_WORDS[word]
                    break
        
        if direction:
            # If a direction is specified, the number is the adjustment amount.
            parameters["direction"] = direction
            if value is not None:
                parameters["value"] = value
        elif value is not None:
            # If no direction, the number is the absolute target value.
            parameters["value"] = value

    if intent == "get_weather":
        # Extract time period (tomorrow, this week, etc.)
        time_period = "current"  # default
        if "tomorrow" in words:
            time_period = "tomorrow"
        elif "week" in words or "7 days" in command_text.lower():
            time_period = "week"
        elif "today" in words or "now" in words or "currently" in words:
            time_period = "current"
        
        parameters["when"] = time_period
        
        # Example for extracting location (e.g., "what's the weather in London")
        if "in" in words:
            try:
                loc_index = words.index("in") + 1
                if loc_index < len(words):
                    # Join all words after "in" to form the location
                    location = " ".join(words[loc_index:])
                    # A simple way to remove trailing punctuation and filter out time-related words
                    location = re.sub(r'[^\w\s]$', '', location).strip()
                    # Remove time-related words like "tomorrow", "today", "tonight"
                    time_words = ["tomorrow", "today", "tonight", "now", "currently", "week"]
                    location_words = [word for word in location.split() if word not in time_words]
                    if location_words:
                        parameters["city"] = " ".join(location_words)
            except (ValueError, IndexError):
                pass # Ignore if "in" is at the end of the sentence

    elif intent == "play_song":
        # Find the trigger phrase and extract what comes after it.
        # e.g., "play the song [Bohemian Rhapsody]"
        trigger_phrases = INTENT_MAP["play_song"]
        lower_command = command_text.lower()
        
        for phrase in trigger_phrases:
            if phrase in lower_command:
                # Find the position after the trigger phrase
                start_index = lower_command.find(phrase) + len(phrase)
                song_name = command_text[start_index:].strip()
                if song_name:
                    parameters["song_name"] = song_name
                break

    return parameters


def _find_best_intent(command_text: str, confidence_threshold: int) -> Tuple[str, Dict[str, Any]]:
    """
    Finds the best intent by checking all keywords, prioritizing longer matches.
    """
    # Use extract instead of extractOne to get multiple good matches
    # The 'token_set_ratio' scorer is better for finding a phrase within a larger string
    # without being penalized for the extra words. This prevents false positives on
    # dynamic queries that happen to contain words like "what is the...".
    top_matches = process.extract(
        command_text.lower(), ALL_PHRASES, limit=3, scorer=fuzz.token_set_ratio
    )

    # Filter matches below the confidence threshold
    valid_matches = [m for m in top_matches if m[1] >= confidence_threshold]

    if not valid_matches:
        return None, None

    # Sort by score (desc), then by length of the matched keyword (desc)
    # This prioritizes more specific commands like "next song" over "play"
    best_match = sorted(valid_matches, key=lambda m: (m[1], len(m[0])), reverse=True)[0]
    
    # Find which intent this matched phrase belongs to
    for intent, phrases in INTENT_MAP.items():
        if best_match[0] in phrases:
            parameters = _extract_parameters(command_text, intent)
            return intent, parameters
            
    return None, None


def parse_intent(command_text: str, confidence_threshold: int = 80) -> Dict[str, Any]:
    """
    Analyzes the user's transcribed command to determine the intent.

    It uses fuzzy string matching to find the best match for the command
    against a list of predefined command phrases.

    Args:
        command_text (str): The user's transcribed command.
        confidence_threshold (int): The minimum confidence score (0-100) to consider a match valid.

    Returns:
        A dictionary containing the identified `intent` and any extracted `parameters`.
        If no predefined command is matched above the threshold, it returns a
        dictionary for either a `dynamic_info` query (needs web search) or an
        `llm_chat` query (direct to LLM).
    """
    parsed_intent, parsed_parameters = _find_best_intent(command_text, confidence_threshold)
    lower_command = command_text.lower()

    # --- Intent Correction Logic ---
    # If the intent is 'media_play_pause' but the command is structured like
    # "play [song name]", we should correct the intent to 'play_song'.
    if parsed_intent == "media_play_pause" and lower_command.startswith("play "):
        # Check if there's more than just "play"
        potential_song_name = lower_command.split(" ", 1)[1].strip()
        if potential_song_name:
            # It's a command to play a specific song.
            return {"intent": "play_song", "parameters": {"song_name": potential_song_name}}
    
    # If the intent is 'play_song' but it also contains a 'next' or 'previous' keyword,
    # it's more likely a navigation command.
    if parsed_intent == "play_song":
        next_keywords = INTENT_MAP["media_next"]
        if any(keyword in lower_command for keyword in next_keywords):
            return {"intent": "media_next", "parameters": {}}

    if parsed_intent:
        return {"intent": parsed_intent, "parameters": parsed_parameters}

    # If no predefined intent is found, check if it requires a web search.
    for trigger in DYNAMIC_INFO_TRIGGERS:
        if trigger in lower_command:
            return {"intent": "dynamic_info", "parameters": {"query": command_text}}

    # If it's not a known command and not a search query, treat as general chat.
    return {"intent": "llm_chat", "parameters": {"query": command_text}}


# Example usage for testing
if __name__ == "__main__":
    test_commands = [
        "hey computer, can you turn the volume up",
        "set the sound to 50 percent",
        "set volume 75",
        "lower 20 percent of the volume",
        "what time is it right now?",
        "how's the weather in Paris",
        "what is the weather in New York City?",
        "play the next song",
        "what is the latest news on space exploration?",
        "tell me a fun fact about giraffes",
        "what is today's date",
        "what is the price of ethereum",
        "play some music",
        "Who is Elon Musk?",
        "play the song Bohemian Rhapsody",
        "what are 5 most rich people?",
        "Hey, how are you doing?",
        "What have you done?",
        "Play Mozzart"
    ]

    for command in test_commands:
        result = parse_intent(command)
        print(f"Command: '{command}'\nParsed: {result}\n")
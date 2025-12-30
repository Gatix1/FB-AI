# FB-AI Voice Assistant

A voice-controlled AI assistant built with Python that can handle various tasks through voice commands and leverage a Large Language Model for dynamic queries.

## Features

- 🎤 **Wake Word Detection** - Activate the assistant with "Alex" or "Alexa"
- 🗣️ **Speech Recognition** - Using Vosk for accurate offline speech-to-text
- 🔊 **Text-to-Speech** - Natural voice responses using Google TTS
- 🎵 **Media Control** - Control system-wide media playback (play, pause, next, previous)
- 🔉 **Volume Control** - Adjust system volume with voice commands
- ⏰ **Time & Date** - Get current time and date information
- 🌤️ **Weather** - Check weather for any location
- 🔍 **Web Search** - Dynamic information retrieval from the web
- 🤖 **LLM Chat** - Powered by Groq's LLaMA model for intelligent conversations

## Prerequisites

- Python 3.8 or higher
- Microphone for voice input
- Internet connection (for TTS, weather, web search, and LLM features)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd c:\Dev\FB-AI
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download the Vosk speech recognition model**:
   - The project uses `vosk-model-en-us-0.42-gigaspeech`
   - The model should already be in the project directory
   - If not, download from: https://alphacephei.com/vosk/models

4. **Set up environment variables**:
   ```bash
   copy .env.example .env
   ```
   Then edit `.env` and add your API keys:
   - `GROQ_API_KEY` - Get from https://console.groq.com/keys
   - `GOOGLE_CUSTOM_SEARCH_API_KEY` - Get from https://console.cloud.google.com/apis/credentials
   - `SEARCH_ENGINE_ID` - Get from https://programmablesearchengine.google.com/

## Usage

Run the main application:

```bash
python src/main.py
```

### Voice Commands Examples

**Media Control:**
- "Play" / "Pause"
- "Next song"
- "Previous track"
- "Stop"
- "Play Bohemian Rhapsody" (plays on YouTube)

**Volume Control:**
- "Turn volume up"
- "Turn volume down"
- "Set volume to 50"
- "Increase volume by 20"

**Information:**
- "What time is it?"
- "What's today's date?"
- "What's the weather in London?"

**Dynamic Queries (requires API keys):**
- "What's the latest news?"
- "Who is Elon Musk?"
- "What are the 5 richest people?"

**General Chat:**
- "Tell me a fun fact"
- "How are you doing?"

## Project Structure

```
FB-AI/
├── src/
│   ├── main.py                 # Main application entry point
│   └── modules/
│       ├── __init__.py
│       ├── voice_module.py     # Wake word, STT, and TTS
│       ├── intent_module.py    # Command parsing and routing
│       ├── media_control_module.py  # Media and volume control
│       ├── information_module.py    # Time, date, weather
│       ├── dynamic_info_module.py   # Web search integration
│       └── llm_module.py       # LLM integration (Groq)
├── docs/
│   └── architecture.md         # Detailed architecture documentation
├── vosk-model-en-us-0.42-gigaspeech/  # Speech recognition model
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration
└── LICENSE

```

## Platform-Specific Notes

### Windows
- Uses `pycaw` for volume control
- Uses `pyautogui` for media key simulation
- All features should work out of the box

### Linux
- Requires `amixer` for volume control
- Requires `playerctl` for media control
- Install: `sudo apt-get install alsa-utils playerctl`

### macOS
- Uses `osascript` (AppleScript) for system control
- All features should work natively

## Troubleshooting

**"Import could not be resolved" errors:**
- Make sure you're running from the `src` directory or the project root
- Ensure `__init__.py` exists in the `modules` folder

**No audio input:**
- Check microphone permissions
- Test microphone with `python -m pyaudio` or other audio tools

**API features not working:**
- Verify your `.env` file has the correct API keys
- Check console output for warning messages about missing credentials

**Wake word not detected:**
- Speak clearly and ensure low background noise
- Try saying "Hey Alex" or "Alexa" more distinctly
- Adjust `SILENCE_THRESHOLD` in `voice_module.py` if needed

## Contributing

This is a university project. Feel free to fork and modify for your own use.

## License

See the LICENSE file for details.

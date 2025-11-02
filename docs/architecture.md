# FB-AI: Architectural Design Document

## 1. Project Overview and Goals

### Project Overview

This document outlines the architectural design for the "FB-AI," a voice-controlled application. The system is designed to understand and respond to user voice commands. It handles a set of predefined tasks directly and leverages a Large Language Model (LLM) for more dynamic or complex queries. The architecture is tailored for a university project, emphasizing a clear and functional implementation of core features over long-term extensibility.

### Core Goals

*   **Voice Interaction:** To provide a hands-free user interface through voice, including wake-word detection, speech-to-text, and text-to-speech capabilities.
*   **Defined Task Execution:** To reliably execute a specific set of commands, such as controlling media playback (e.g., KODI), managing system volume, and answering queries about time and weather.
*   **Dynamic Query Handling:** To use an external LLM to process and generate responses for queries that fall outside the scope of predefined tasks, such as requests for news or general information.
*   **Simplicity and Focus:** To implement a streamlined and self-contained system that meets the specific requirements of a university-level project, prioritizing core functionality and successful demonstration.

## 2. System Context and High-Level Architecture

The FB-AI operates as a standalone system that listens for user input and orchestrates various internal modules to produce a response. The high-level architecture is centered around a Python-based backend that acts as the main controller.

The system's logic is divided into two primary paths:

1.  **Direct Command Path:** For simple, known commands (e.g., "turn up the volume"), the backend processes the intent and directly triggers a corresponding task module.
2.  **LLM-Assisted Path:** For complex or unidentified queries (e.g., "what's the latest news?"), the backend routes the request to an LLM for processing and response generation.

All user interactions begin with voice input and end with a synthesized voice output, creating a seamless conversational experience.

## 3. Detailed Component Breakdown and Data Flow

The system is composed of three primary functional groups: the voice pipeline, task execution modules, and the LLM integration layer.

### Table 1: Voice Processing Pipeline

This pipeline manages the conversion of human speech into system-readable text and back into audible speech.

| Component          | Description                                                                                             | Data Flow                               |
| ------------------ | ------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **WWD**            | **Wake-Word Detection:** Continuously listens for a specific phrase (the "wake word") to activate the assistant. | Ambient Audio -> "Wake Word" Trigger    |
| **Voice Recognition**| Captures the user's voice command immediately after the wake word is detected.                           | User Speech -> Raw Audio Data           |
| **STT**            | **Speech-to-Text:** Transcribes the captured raw audio data into a plain text string.                     | Raw Audio Data -> "User Command" Text   |
| **TTS**            | **Text-to-Speech:** Converts a final text response (from a task module or the LLM) into synthesized speech. | "Final Response" Text -> Spoken Audio |

### Table 2: Intent Parsing and Routing

This component acts as the brain of the system, deciding where to route the user's transcribed command.

| Component       | Description                                                                                                                                                             | Data Flow                                                              |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Intent Parser** | Analyzes the text from the STT to determine the user's intent. It uses a combination of techniques to match the command against a list of predefined tasks, even if the phrasing differs slightly. This often involves **keyword spotting** (looking for words like "volume" or "weather") and **fuzzy string matching** to calculate a similarity score against known command patterns. If a match is found above a confidence threshold, the corresponding task is triggered. If no match is found, the input is treated as a dynamic query for the LLM. | "User Command" Text -> "Intent" (e.g., Volume, News) + [Parameters] |

### Table 3: Command/Task Execution Modules

These modules are responsible for handling specific, predefined user commands.

| Component         | Description                                                                                             | Data Flow                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Media/Volume**  | Manages media playback and system volume. Includes integration with external players like **KODI**.       | "Play/Pause/Volume" Command -> System Action    |
| **Time/Weather**  | Fetches and formats the current time, date, or weather information from a reliable source.              | "What time is it?" Command -> Formatted Response |
| **Custom Tasks**  | A module for other simple, user-defined commands that have a direct, predictable outcome.                | "Custom Command" -> Pre-scripted Action         |

### Table 4: LLM Integration and Data Flow

This flow is activated for queries that are not recognized as direct commands.

| Component        | Description                                                                                             | Data Flow                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Dynamic Info** | For certain queries (e.g., "news"), the system may first fetch dynamic data (e.g., via Google Search).   | Unidentified Query -> External API Call (e.g., Google) -> Fetched Data |
| **LLM**          | The **Large Language Model** receives the user's query (and any fetched data) to generate a natural language response. | Query + [Optional Data] -> "Generated Response" Text                   |

## 4. Technology Stack and Rationale

The technology stack is intentionally lean to maintain focus and simplicity, aligning with the project's goals.

*   **Primary Language: Python**
    *   **Rationale:** Python was chosen as the sole programming language for this project. Its extensive ecosystem of libraries for audio processing, web requests, and AI/ML model integration makes it ideal for rapid development and prototyping. Libraries for STT/TTS, API clients (for weather, search), and interacting with LLMs are readily available and well-documented. This simplifies the development process by allowing all components—from wake-word detection to command processing—to be built within a single, unified language environment.

*   **Media Control: KODI Integration**
    *   **Rationale:** KODI is specified for media control due to its robust JSON-RPC API, which allows for easy and reliable control over playback, library management, and volume via simple network requests. This avoids the complexity of writing low-level media player integrations.

## 5. Architectural Flow Examples

The following scenarios illustrate the end-to-end data flow for two distinct types of user requests.

### Scenario A: Executing a "News" Query

This flow demonstrates how the system handles a complex query requiring the LLM.

1.  **STT:** The user says, "What's the latest news?" The STT engine transcribes this into the text string: `"What's the latest news?"`.
2.  **Backend:** The backend receives the text, determines it is not a simple, predefined command (like volume control), and flags it as a dynamic query.
3.  **Google Search:** The backend initiates a search query to Google to fetch current news headlines or summaries.
4.  **Pass result to LLM:** The search results are passed as context along with the original user query to the LLM.
5.  **LLM Generates Response:** The LLM processes the query and the provided context, generating a concise, natural language summary of the news.
6.  **TTS:** The generated text response is sent to the TTS engine, which speaks the news summary back to the user.

### Scenario B: Executing a "Volume Control" Command

This flow demonstrates the direct path for a simple, predefined command.

1.  **STT:** The user says, "Turn the volume up." The STT engine transcribes this into the text string: `"Turn the volume up"`.
2.  **Backend:** The backend receives the text and parses it, identifying the intent ("increase volume") and the target ("volume").
3.  **Command Processing:** The backend recognizes this as a direct command and bypasses the LLM entirely.
4.  **Volume Control Module:** The backend invokes the Volume Control module, which executes the system-level action to increase the master volume. A simple confirmation response (e.g., "Done") may be generated.
5.  **TTS:** The confirmation text "Done" is sent to the TTS engine, which provides audible feedback to the user.

## 6. Team Roles and Work Distribution

To facilitate parallel development for a team of six, the project can be broken down into the following distinct roles and responsibilities. Each part corresponds to a set of related components from the architecture.

### Part 1: Voice I/O Developer
*   **Focus:** Capturing and transcribing user voice commands.
*   **Components:** Wake-Word Detection (WWD), Voice Recognition (Audio Capture), Speech-to-Text (STT), Text-to-Speech (TTS).
*   **Primary Deliverable:** A consolidated module for all voice interactions: one part that listens and returns text, and another part that accepts text and produces audio.

### Part 2: Intent Parsing Developer
*   **Focus:** Understanding the user's intent from the transcribed text.
*   **Components:** Intent Parser.
*   **Primary Deliverable:** A module that takes a text string and either identifies a predefined command (with parameters) or flags it as a dynamic query for the LLM.

### Part 3: System & Media Control Developer
*   **Focus:** Executing commands related to media playback and system functions.
*   **Components:** Media/Volume Module, KODI Integration.
*   **Primary Deliverable:** A module with functions to control system volume and interact with the KODI API for media playback.

### Part 4: Information Task Developer
*   **Focus:** Handling predefined commands that provide users with specific information.
*   **Components:** Time/Weather Module, Custom Tasks.
*   **Primary Deliverable:** A module with functions that fetch and format data for time, weather, and other simple, user-defined queries.

### Part 5: Dynamic Information Developer
*   **Focus:** Fetching and preparing data from external sources for dynamic queries.
*   **Components:** Dynamic Info (Google Search).
*   **Primary Deliverable:** A module with a function that takes a query (e.g., "latest news") and returns structured data fetched from an external API like Google Search.

### Part 6: Backend Orchestrator & LLM Developer
*   **Focus:** Managing the main application flow and interfacing with the Large Language Model.
*   **Components:** Main application logic, LLM Integration.
*   **Primary Deliverable:** The main executable script that runs the application and a module to handle LLM communication. This role is responsible for receiving input from the Intent Parser and routing it to the correct Task Developer or the LLM.

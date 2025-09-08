# Motive Human-in-the-Loop Proxy

A standalone, stateful proxy server that emulates the OpenAI Chat Completions API to allow a human to act as a "model" for any application that can connect to an OpenAI-compatible endpoint.

This is useful for projects like AI-driven games, simulations, or agent frameworks where you want to seamlessly swap an LLM for a human player/participant without changing the core application logic.

## How It Works

The proxy pairs two clients based on a shared **session ID**, which is passed as the `model` name in the API request.

1.  **The Human Client** (e.g., a generic chat UI like Ollama Web UI, Chatbot UI) connects to the proxy. It sends its first message, which acts as a "ping" to establish the connection. The proxy holds this connection open.
2.  **The Controller Client** (e.g., your Game Master application) connects to the proxy using the *same session ID*. It sends the first real prompt (e.g., "You see a troll. What do you do?").
3.  **The Proxy** receives the controller's prompt and immediately sends it back as the response to the human's waiting "ping" request.
4.  **The Human** sees the controller's prompt in their chat UI. They type their response ("I attack the troll!").
5.  **The Proxy** receives the human's response and sends it back to the controller, completing the controller's original request.
6.  This cycle continues for the duration of the session.



## Features

-   **OpenAI API Compatible:** Exposes a `/v1/chat/completions` endpoint.
-   **Concurrent Sessions:** Manages multiple independent human/controller pairs simultaneously based on the session ID (`model` name).
-   **Asynchronous:** Built with FastAPI and asyncio for efficient handling of long-polling requests.
-   **Standalone:** No dependencies on any specific game or application.  Motive Proxy was designed to work with the Motive game engine, but it is a generic chat proxy so it can be used for other projects easily.

## Setup
(TODO)

## Usage
(TODO)

## Recommended chat client
(TODO)
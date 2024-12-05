# Langchain based Chatbot

This repository presents a flexible and intelligent chatbot system that uses data fetched from APIs to answer user queries. The chatbot dynamically evaluates and utilizes API responses to provide accurate answers while maintaining conversation context.

This project implements a command-line chatbot interface designed to process user queries based on data fetched from APIs. The system allows users to configure multiple APIs, run them in isolated Docker containers, cache their responses for future use, and interact with the chatbot to receive intelligent, context-aware answers derived from the API data.
Key Feature: Users can easily add new APIs to the system by updating the db.json configuration file, enabling seamless integration of additional data sources.

## Steps to Run the Project

1. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt

2. **Create a .env File**
  ```bash
  echo "OPENAI_API_KEY=your_key_here" > .env
  ```
3. **Start the Docker Containers**
  ```bash
  python containers.py
  ```
4.**Launch the Chatbot Interface**
  ```bash
  python chatbot.py
```

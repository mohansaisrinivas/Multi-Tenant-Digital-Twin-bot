# 🤖 Multi-Tenant Digital Twin Telegram Bot

A scalable, stateful Telegram bot that creates a "Digital Twin" for users using Retrieval-Augmented Generation (RAG). By uploading a Resume and a Personal Bio (PDFs), users build a persistent, isolated vector memory. They can then chat with the bot, which answers questions about them in the first person ("I", "me", "my").

## 🌟 About the Project

This project demonstrates how to build a multi-tenant AI application without needing separate databases for every user. It uses a single local vector database (ChromaDB) but strictly isolates user data by attaching Telegram User IDs as metadata to every vector chunk. When a user queries the bot, the retriever applies a hard filter to ensure the LLM can only "see" documents belonging to that specific user.

## ✨ Key Features

* **Multi-Tenant Data Isolation:** Users share a single ChromaDB instance, but metadata filtering guarantees complete privacy and data separation.
* **Strict Document Constraints:** Validates uploads at the Telegram level, exclusively accepting `.pdf` files.
* **Persistent Upload Limits:** Users are limited to 2 files (Resume and Bio). This state is tracked locally via JSON, preventing the "unlimited upload" loophole even if the server restarts.
* **Self-Serve Memory Wiping:** Users can type `/reset` to instantly purge their specific vector chunks from ChromaDB and reset their upload counters to start fresh.
* **First-Person Persona:** Prompt-engineered to speak strictly as the user based *only* on the provided context, refusing to hallucinate facts outside the PDFs.

---

## 🚧 Challenges Faced & Solutions

### 1. API Rate Limiting During Development
* **The Problem:** Using standard tier models like Gemini 1.5 and 2.0 Flash led to `RESOURCE_EXHAUSTED` (429) errors very quickly during testing, breaking the bot's responsiveness.
* **The Solution:** Pivoted the LLM to `gemini-3.1-flash-lite`, which is highly optimized for fast, repetitive RAG tasks. Additionally, environments were isolated using newly created Google AI Studio projects to access fresh daily quota buckets.

### 2. The "Unlimited Upload" RAM Loophole
* **The Problem:** In a multi-user environment, upload limits were initially tracked using a Python dictionary in temporary RAM. When the bot script was restarted, the RAM cleared, resetting user counts to 0. However, ChromaDB data persisted on the hard drive. This allowed users to bypass the 2-file limit and infinitely stack duplicate PDFs into their memory.
* **The Solution:** Engineered a persistent state-tracking system using Python's built-in `json` library. The bot now immediately reads/writes `upload_counts.json` to the hard drive on every interaction, keeping the application state perfectly synced with the ChromaDB persistence layer.

---

## 🛠️ Technologies & Libraries Used

This project relies on a carefully selected stack to manage Telegram polling, document processing, embedding, and LLM orchestration.

### Core Stack
* **Language:** Python 3.x
* **Orchestration:** LangChain
* **LLM & Embeddings:** Google Gemini API
* **Vector Database:** ChromaDB
* **Interface:** Telegram Bot API
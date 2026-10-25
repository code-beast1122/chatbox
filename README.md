# 🤖 Multi-Chat AI Assistant

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-6366F1?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

An interactive, multi-session conversational AI assistant built with **Streamlit**, **LangChain**, and **SQLite**. It features persistent multi-chat conversation history, flexible session switching, and multimodal document/image comprehension powered by **OpenRouter**.

---

## ✨ Features

- **💬 Persistent Multi-Session Chats**: Create multiple conversation threads, switch between them anytime, rename titles, or delete past chats. All conversations and message histories are saved locally in SQLite (`chat_history.db`).
- **🖼️ Multimodal Vision Support**: Upload images (`PNG`, `JPG`, `JPEG`) and ask questions about diagrams, charts, photos, or screenshots using vision-capable LLMs.
- **📄 Document Understanding**: Attach and analyze documents on the fly:
  - **PDF documents** (`.pdf`) via `pypdf`
  - **Word documents** (`.docx`) via `python-docx`
  - **Plain text** (`.txt`)
- **⚡ OpenRouter Integration**: Easily plug into top-tier models (such as `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, Cohere, Anthropic, or OpenAI models) via OpenRouter API.
- **🧹 Session Management**: "Start Fresh" reset capability, dynamic titles based on the first prompt, and clean sidebar navigation.

---

## 🏗️ Architecture & Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **LLM Orchestration**: [LangChain](https://python.langchain.com/) (`langchain-core`, `langchain-openrouter`)
- **Database**: SQLite3 (`chat_history.db`)
- **Document Extractors**: `pypdf`, `python-docx`
- **Model Provider**: [OpenRouter](https://openrouter.ai/)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- An API key from [OpenRouter](https://openrouter.ai/)

### 2. Clone the Repository
```bash
git clone https://github.com/code-beast1122/chatbox.git
cd chatbox
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install streamlit langchain-core langchain-openrouter pypdf python-docx
```

### 4. Configure API Key
Set your OpenRouter API key using either:
- **Environment Variable**:
  ```bash
  # Windows PowerShell
  $env:OPENROUTER_API_KEY="your-openrouter-api-key"

  # Linux / macOS
  export OPENROUTER_API_KEY="your-openrouter-api-key"
  ```
- **Local File**: Create an `api.txt` file in the root directory and paste your API key inside.

### 5. Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🗄️ Database Schema

The SQLite database (`chat_history.db`) contains two tables:
- `conversations`: Stores `id`, `title`, and `created_at` timestamp.
- `chat_messages`: Stores `id`, `conversation_id`, `role` (`user` or `assistant`), `content`, and `created_at`.

---

## 🤝 Contributing
Contributions, issues, and feature suggestions are welcome! Feel free to open an issue or pull request.

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

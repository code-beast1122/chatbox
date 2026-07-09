import os
import sqlite3
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openrouter import ChatOpenRouter

# --- 1. PAGE SETUP & CREDENTIALS ---
st.set_page_config(page_title="Multi-Chat AI", page_icon="🤖")
st.title("🤖 Multi-Chat Assistant")
st.caption("Each conversation is saved locally in SQLite so you can switch between chats easily.")

DB_FILE = "chat_history.db"


def get_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key
    try:
        with open("api.txt", "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return ""


# --- 2. SQLITE DATABASE HELPERS ---
def init_db():
    """Creates the database tables needed for conversations and messages."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute(
            """
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = [row[1] for row in cursor.fetchall()]
        if "conversation_id" not in columns:
            cursor.execute("ALTER TABLE chat_messages RENAME TO chat_messages_old")
            cursor.execute(
                """
                CREATE TABLE chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "INSERT INTO chat_messages (conversation_id, role, content) SELECT session_id, role, content FROM chat_messages_old"
            )
            cursor.execute("DROP TABLE chat_messages_old")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
    if cursor.fetchone() is None:
        cursor.execute(
            """
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    cursor.execute("SELECT DISTINCT conversation_id FROM chat_messages")
    conversation_ids = [row[0] for row in cursor.fetchall()]
    for conversation_id in conversation_ids:
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE id = ?", (conversation_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "SELECT content FROM chat_messages WHERE conversation_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
                (conversation_id,),
            )
            first_message = cursor.fetchone()
            title = (first_message[0][:30] + "...") if first_message and first_message[0] else "New Chat"
            cursor.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (conversation_id, title))

    conn.commit()
    conn.close()


def load_conversations():
    """Loads all saved conversation ids and titles."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM conversations ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def create_conversation(title: str = "New Chat") -> str:
    """Creates a new conversation and returns its id."""
    conversation_id = uuid.uuid4().hex
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (conversation_id, title))
    conn.commit()
    conn.close()
    return conversation_id


def load_history_from_db(conversation_id: str):
    """Retrieves past messages from SQLite and formats them for LangChain."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    history = []
    for role, content in rows:
        if role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))
    return history


def save_message_to_db(conversation_id: str, role: str, content: str):
    """Saves a single message row into SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content),
    )
    conn.commit()
    conn.close()


def update_conversation_title(conversation_id: str, title: str):
    """Updates the title shown in the sidebar."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
    conn.commit()
    conn.close()


def clear_conversation_history(conversation_id: str):
    """Deletes all messages from a conversation and resets its title."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", ("New Chat", conversation_id))
    conn.commit()
    conn.close()


def delete_conversation(conversation_id: str):
    """Deletes an entire conversation and its messages from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


# Initialize the database file upon script run
init_db()

# section 2.1
import base64
from pypdf import PdfReader
from docx import Document
def extract_text_from_pdf(file) -> str:
    """Extracts all text from a PDF file."""
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(file) -> str:
    """Extracts all text from a Word document."""
    doc = Document(file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


# --- 3. MODEL & SESSION INITIALIZATION ---
@st.cache_resource
def load_llm():
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Add OPENROUTER_API_KEY to your environment or api.txt")
    os.environ["OPENROUTER_API_KEY"] = api_key
    return ChatOpenRouter(model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free") #cohere/north-mini-code:free


try:
    llm = load_llm()
except Exception as exc:
    st.error(f"Could not initialize the model: {exc}")
    st.stop()


if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

conversations = load_conversations()
if not conversations:
    new_conversation_id = create_conversation("New Chat")
    conversations = [(new_conversation_id, "New Chat")]

if (
    st.session_state.current_conversation_id is None
    or st.session_state.current_conversation_id not in {conversation_id for conversation_id, _ in conversations}
):
    st.session_state.current_conversation_id = conversations[0][0]

current_conversation_id = st.session_state.current_conversation_id
if current_conversation_id not in st.session_state.chat_histories:
    st.session_state.chat_histories[current_conversation_id] = load_history_from_db(current_conversation_id)

# --- 4. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("💬 Chats")
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_conversation_id = create_conversation("New Chat")
        st.session_state.current_conversation_id = new_conversation_id
        st.session_state.chat_histories[new_conversation_id] = []
        st.rerun()

    st.divider()

    for conversation_id, title in conversations:
        button_label = title if len(title) <= 24 else title[:21] + "..."
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(button_label, key=f"conv_{conversation_id}", use_container_width=True):
                st.session_state.current_conversation_id = conversation_id
                if conversation_id not in st.session_state.chat_histories:
                    st.session_state.chat_histories[conversation_id] = load_history_from_db(conversation_id)
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{conversation_id}", help="Delete chat", use_container_width=True):
                st.session_state.chat_histories.pop(conversation_id, None)
                if st.session_state.current_conversation_id == conversation_id:
                    st.session_state.current_conversation_id = None
                delete_conversation(conversation_id)
                st.rerun()

    st.divider()
    if st.button("🧹 Start Fresh", use_container_width=True):
        clear_conversation_history(current_conversation_id)
        st.session_state.chat_histories[current_conversation_id] = []
        st.rerun()

# --- 5. RENDER CHAT INTERFACE ---
current_history = st.session_state.chat_histories[current_conversation_id]
if not current_history:
    with st.chat_message("assistant"):
        st.write("Hello! I am your custom AI. How can I assist you today?")

for message in current_history:
    role = "assistant" if isinstance(message, AIMessage) else "user"
    with st.chat_message(role):
        # Look inside LangChain multimodal structures to safely display old text
        if isinstance(message.content, list):
            for item in message.content:
                if item.get("type") == "text":
                    st.write(item.get("text"))
        else:
            st.write(message.content)


# --- 6. CHAT INPUT & FILE UPLOADER LOGIC ---
# This widget places the uploader directly above the chat bar
uploaded_file = st.file_uploader(
    "📎 Attach a file (Image, PDF, Word, or TXT)", 
    type=["png", "jpg", "jpeg", "pdf", "docx", "txt"]
)

if user_query := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.write(user_query)
        if uploaded_file:
            st.caption(f"📎 Attached: {uploaded_file.name}")
            if uploaded_file.name.split(".")[-1].lower() in ["png", "jpg", "jpeg"]:
                st.image(uploaded_file, width=300)

    file_context = ""
    is_image = False
    
    # 1. Parse file if one is uploaded
    if uploaded_file:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        
        if file_ext in ["png", "jpg", "jpeg"]:
            is_image = True
            base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        elif file_ext == "pdf":
            file_context = extract_text_from_pdf(uploaded_file)
        elif file_ext == "docx":
            file_context = extract_text_from_docx(uploaded_file)
        elif file_ext == "txt":
            file_context = uploaded_file.getvalue().decode("utf-8")

    # 2. Construct the message payload based on file type
    if is_image:
        message_content = [
            {"type": "text", "text": user_query},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        ]
        new_message = HumanMessage(content=message_content)
    elif file_context:
        full_prompt = (
            f"The user has attached a document named '{uploaded_file.name}'.\n"
            f"--- DOCUMENT CONTENT START ---\n{file_context}\n--- DOCUMENT CONTENT END ---\n\n"
            f"User Question: {user_query}"
        )
        new_message = HumanMessage(content=full_prompt)
    else:
        new_message = HumanMessage(content=user_query)

    # 3. State lifecycle execution
    current_history.append(new_message)
    save_message_to_db(current_conversation_id, "user", user_query)

    with st.chat_message("assistant"):
        with st.spinner("Processing context and thinking..."):
            response = llm.invoke(current_history)
            st.write(response.content)

    current_history.append(AIMessage(content=response.content))
    save_message_to_db(current_conversation_id, "assistant", response.content)
    st.rerun()
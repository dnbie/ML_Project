import os
import streamlit as st
from typing import List
from PyPDF2 import PdfReader
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from prompts import get_rag_prompt

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("Please set THE OPENAI_API_KEY in .env")
    st.stop()

st.set_page_config(page_title="CHATBOT — Document Intelligence", layout="wide")
st.title("CHATBOT — Document Intelligence Assistant")

st.markdown(
    """
Advanced document analysis system using Retrieval Augmented Generation:
1. Load PDF documents → extract content  
2. Split text into optimized chunks  
3. Generate embeddings and build vector index  
4. Retrieve relevant information for queries  
5. Generate accurate responses using contextual AI
"""
)

def load_pdf(file) -> str:
    reader = PdfReader(file)
    text = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
        else:
            text.append("")
    return "\n\n".join(text)


def load_pdf_from_path(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return load_pdf(f)


def load_excel(file) -> str:
    try:
        df = pd.read_excel(file, sheet_name=None)
        text = []
        for sheet_name, sheet_df in df.items():
            text.append(f"\n=== Sheet: {sheet_name} ===\n")
            text.append(sheet_df.to_string())
        return "\n\n".join(text)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return ""


def load_excel_from_path(file_path: str) -> str:
    return load_excel(file_path)


def create_text_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


@st.cache_resource(show_spinner=False)
def embeddings_and_vectorstore(chunks: List[str], model: str = "text-embedding-3-small"):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=model)
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store


def llm(model_name: str = "gpt-4o-mini", temperature: float = 0.2, max_tokens: int = 1000):
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        model_name=model_name,
    )


with st.sidebar:
    st.header("Settings")
    chunk_size = st.number_input("Chunk size (chars)", value=1000, step=100)
    chunk_overlap = st.number_input("Chunk overlap (chars)", value=200, step=50)
    embedding_model = st.selectbox(
        "Embedding model",
        options=["text-embedding-3-small", "text-embedding-3-large"],
        index=0,
    )
    llm_model = st.selectbox(
        "LLM model",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4o-mini-instruct"],
        index=0,
    )
    top_k = st.slider("Top-k retrieved chunks", min_value=1, max_value=8, value=4)
    st.write("---")
    st.markdown(
        "Upload files or enter a path. Multiple files are supported."
    )
    uploads = st.file_uploader("Upload PDF or Excel files", type=["pdf", "xlsx", "xls"], accept_multiple_files=True)
    file_path_input = st.text_input("Or enter file path", value="")


text = ""
source_labels = []

if uploads:
    all_texts = []
    for upload in uploads:
        try:
            if upload.name.endswith('.pdf'):
                file_text = load_pdf(upload)
            elif upload.name.endswith(('.xlsx', '.xls')):
                file_text = load_excel(upload)
            else:
                continue
            
            if file_text:
                all_texts.append(f"\n\n=== File: {upload.name} ===\n\n{file_text}")
                source_labels.append(upload.name)
        except Exception as e:
            st.error(f"Failed to read {upload.name}: {e}")
    
    text = "\n\n".join(all_texts)

elif file_path_input.strip():
    try:
        file_path = file_path_input.strip()
        if file_path.endswith('.pdf'):
            text = load_pdf_from_path(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            text = load_excel_from_path(file_path)
        else:
            st.error("Unsupported file type. Please use PDF or Excel files.")
            st.stop()
        source_labels.append(os.path.basename(file_path))
    except FileNotFoundError:
        st.error("Local file not found. Please verify the path.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

if not text:
    st.info("Please upload files (PDF/Excel) or provide a valid file path to build the knowledge base.")
    st.stop()

if source_labels:
    st.success(f"Loaded {len(source_labels)} file(s): **{', '.join(source_labels)}**")
st.write(f"Total document length: **{len(text)}** characters")

with st.spinner("Splitting text into chunks..."):
    chunks = create_text_chunks(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
st.write(f"Created **{len(chunks)}** chunks (chunk_size={chunk_size}, overlap={chunk_overlap}).")

with st.spinner("Creating embeddings and building FAISS vector store (cached)..."):
    vector_store = embeddings_and_vectorstore(chunks, model=embedding_model)
st.success("Vector store ready.")

st.markdown("---")
st.subheader("Query Interface")
user_question = st.text_input("Enter your question:")

if user_question:
    import random
    
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    help_keywords = ["what can you do", "how can you help", "what are you", "who are you", "what is this", "help"]
    
    user_lower = user_question.lower().strip()
    
    if user_lower in greetings:
        greeting_responses = [
            "Hello! I am a Document Intelligence Assistant. I can help you analyze and extract information from your uploaded PDF documents. Please ask me any questions about the content of your document.",
            "Hi there! I'm here to help you understand your document better. Feel free to ask me anything about the content you've uploaded.",
            "Hey! I'm your Document Intelligence Assistant. I can answer questions based on the PDF you've provided. What would you like to know?",
            "Greetings! Ready to assist you with your document analysis. Ask me anything about the uploaded content!",
            "Hello! I specialize in analyzing PDF documents. How can I help you explore the content today?"
        ]
        st.subheader("Answer")
        st.write(random.choice(greeting_responses))
        st.stop()
    
    if any(keyword in user_lower for keyword in help_keywords):
        help_responses = [
            "I am a RAG-based Document Intelligence Assistant. I can help you by:\n\n- Answering questions based on your uploaded PDF document\n- Extracting specific information from the document\n- Providing summaries and explanations\n- Finding relevant sections related to your queries\n\nPlease ask me anything about the content of your uploaded document!",
            "I'm designed to help you understand your documents better! I can:\n\n- Answer specific questions about the PDF content\n- Find and extract relevant information\n- Provide context-based explanations\n- Locate specific sections in your document\n\nJust ask me about anything in your uploaded file!",
            "My capabilities include:\n\n- Intelligent document analysis using AI\n- Quick information retrieval from your PDFs\n- Context-aware responses based on document content\n- Finding relevant passages for your queries\n\nWhat would you like to know from your document?",
            "I'm here to make document analysis easy! I can:\n\n- Search through your PDF and find answers\n- Provide accurate information based on the content\n- Help you understand complex sections\n- Point you to relevant parts of the document\n\nFeel free to ask any question about your uploaded file!"
        ]
        st.subheader("Answer")
        st.write(random.choice(help_responses))
        st.stop()
    
    try:
        matches = vector_store.similarity_search(user_question, k=top_k)
        if not matches:
            st.warning("No relevant chunks found in the document.")
        else:
            context = "\n\n---\n\n".join(doc.page_content for doc in matches)

            prompt_text = get_rag_prompt(context, user_question)

            with st.expander("Show prompt sent to LLM"):
                st.code(prompt_text[:1000] + ("\n\n... (truncated)" if len(prompt_text) > 1000 else ""), language="text")

            llm_instance = llm(model_name=llm_model, temperature=0.2, max_tokens=1000)
            with st.spinner("Generating answer from LLM..."):
                llm_response = llm_instance.invoke(prompt_text)

            st.subheader("Answer")
            st.write(llm_response.content)

            st.subheader("Retrieved chunks (evidence)")
            for i, doc in enumerate(matches, start=1):
                with st.expander(f"Chunk {i}"):
                    st.write(doc.page_content)

    except Exception as err:
        st.error(f"An error occurred during retrieval or generation: {err}")



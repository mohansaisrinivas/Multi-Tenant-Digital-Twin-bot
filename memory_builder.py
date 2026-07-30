import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

class MemoryBuilder:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )

    def add_document(self, file_path: str, user_id: str):
        print(f"Processing file for user: {user_id}")
        
        # 1. Strictly enforce PDF only
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Only PDF files are allowed for your resume and bio.")

        # 2. Load the PDF
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        # 3. Chunk it
        splits = self.text_splitter.split_documents(docs)
        
        # 4. Tag it with the user ID so it merges with their existing memory
        for chunk in splits:
            chunk.metadata["user_id"] = str(user_id) 

        # 5. Save it to the shared database
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        vector_store.add_documents(splits)
        print(f"Successfully added {len(splits)} chunks to memory for user {user_id}!")
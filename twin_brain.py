import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class DigitalTwinAgent:
    def __init__(self, model_name="gemini-3.1-flash-lite"):
        print("Booting up Twin's memory connections...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
        )
        self.vectorstore = Chroma(
            persist_directory="./chroma_db", 
            embedding_function=self.embeddings
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=0.3, 
            api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
        )
        
        system_prompt = (
            "You are my digital twin. Answer the user's question in the first person ('I', 'my', 'me') "
            "using ONLY the provided context. Match a helpful and friendly tone.\n\n"
            "If the context doesn't contain the answer, say 'I haven't shared that about myself yet.' "
            "Do not invent facts or guess.\n\n"
            "Context: {context}"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        self.answer_chain = create_stuff_documents_chain(self.llm, self.prompt)

    def ask(self, user_id: str, query: str):
        retriever = self.vectorstore.as_retriever(
            search_kwargs={
                "k": 3, 
                "filter": {"user_id": str(user_id)} 
            }
        )
        
        twin_chain = create_retrieval_chain(retriever, self.answer_chain)
        response = twin_chain.invoke({"input": query})
        return response['answer']
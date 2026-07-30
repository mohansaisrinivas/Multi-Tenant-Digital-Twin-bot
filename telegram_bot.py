import os
import json
import telebot
from dotenv import load_dotenv

from twin_brain import DigitalTwinAgent
from memory_builder import MemoryBuilder

load_dotenv()

class TelegramTwinBot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.getenv("telegram_api_key"))
        self.twin_agent = DigitalTwinAgent()
        self.memory_builder = MemoryBuilder()
        
        self.tracker_file = "upload_counts.json"
        self.user_upload_counts = self.load_counts() 
        
        os.makedirs("temp_data", exist_ok=True)
        self.register_handlers()

    def load_counts(self):
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as file:
                return json.load(file)
        return {}

    def save_counts(self):
        with open(self.tracker_file, 'w') as file:
            json.dump(self.user_upload_counts, file)

    def register_handlers(self):
        
        # --- NEW: RESET COMMAND ---
        @self.bot.message_handler(commands=['reset'])
        def reset_memory(message):
            user_id = str(message.from_user.id)
            
            # 1. Reset their upload counter in the JSON file
            self.user_upload_counts[user_id] = 0
            self.save_counts()
            
            # 2. Delete their specific chunks from ChromaDB
            try:
                from langchain_chroma import Chroma
                
                print(f"\n🗑️ Attempting memory wipe for user: {user_id}")
                
                # Create a fresh, direct connection to the database
                temp_db = Chroma(
                    persist_directory="./chroma_db",
                    embedding_function=self.twin_agent.embeddings
                )
                
                collection = temp_db._collection
                
                # Check exactly how many chunks exist for this user
                results = collection.get(where={"user_id": user_id})
                chunk_count = len(results['ids']) if results and results['ids'] else 0
                
                print(f"🔍 Found {chunk_count} chunks in ChromaDB.")
                
                if chunk_count > 0:
                    # Force delete directly from the collection using the filter
                    collection.delete(where={"user_id": user_id})
                    print(f"✅ Successfully deleted {chunk_count} chunks!")
                else:
                    print("⚠️ No chunks found to delete.")
                    
                self.bot.reply_to(message, "🗑️ **Memory Wiped!**\n\nYour digital brain has been completely erased, and your upload limit is reset to 2. You can upload a new Resume and Bio now.")
                
            except Exception as e:
                self.bot.reply_to(message, "Oops, something went wrong while trying to wipe your memory.")
                print(f"Reset Error: {e}")
        # ---------------------------

        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = (
                "Hi! To build your perfect digital twin, I need two things:\n\n"
                "1️⃣ Upload your **Resume** (PDF)\n"
                "2️⃣ Upload your **Personal Bio** (PDF)\n\n"
                "Send them one by one, and I will combine them into your digital brain!\n\n"
                "*(If you ever need to start over, just type /reset)*"
            )
            self.bot.reply_to(message, welcome_text, parse_mode='Markdown')

        @self.bot.message_handler(content_types=['document'])
        def handle_docs(message):
            try:
                user_id = str(message.from_user.id)
                current_count = self.user_upload_counts.get(user_id, 0)
                
                if current_count >= 2:
                    self.bot.reply_to(message, "❌ **Upload Limit Reached!**\n\nYou are only allowed a maximum of 2 files (Resume and Bio). If you need to update them, type /reset to wipe your memory and start over.")
                    return

                file_name = message.document.file_name.lower()
                if not file_name.endswith('.pdf'):
                    self.bot.reply_to(message, "❌ Please upload a PDF file. I cannot read other formats.")
                    return

                self.bot.reply_to(message, "Downloading your PDF...")
                
                file_info = self.bot.get_file(message.document.file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                
                temp_file_path = f"temp_data/{user_id}_{file_name}"
                
                with open(temp_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                    
                self.bot.reply_to(message, "Reading and merging into your digital brain...")
                self.memory_builder.add_document(temp_file_path, user_id)
                
                self.user_upload_counts[user_id] = current_count + 1
                self.save_counts()  
                
                files_remaining = 2 - self.user_upload_counts[user_id]
                os.remove(temp_file_path)
                self.bot.reply_to(message, f"Memory updated with {file_name}! ✅\n\nYou have {files_remaining} upload(s) remaining.")
                
            except Exception as e:
                self.bot.reply_to(message, "Oops, something went wrong saving that file.")
                print(f"File Error: {e}")

        @self.bot.message_handler(func=lambda message: True)
        def chat_with_twin(message):
            self.bot.send_chat_action(message.chat.id, 'typing')
            
            try:
                user_id = str(message.from_user.id)
                
                # Prevent querying if they haven't uploaded anything yet
                if self.user_upload_counts.get(user_id, 0) == 0:
                    self.bot.reply_to(message, "I couldn't find any memory for you yet! Please upload your PDF first.")
                    return

                user_query = message.text
                answer = self.twin_agent.ask(user_id, user_query)
                self.bot.reply_to(message, answer, parse_mode='Markdown')
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    self.bot.reply_to(message, "I'm thinking a little too fast! ⏱️ Google's limit reached. Please wait 30 seconds.")
                else:
                    self.bot.reply_to(message, "An error occurred while thinking. Please try again.")
                    print(f"Chat Error: {e}")

    def run(self):
        print("🤖 V2 Multi-User Telegram Bot is online! (With Reset & Persistent Limits)")
        self.bot.infinity_polling()

if __name__ == "__main__":
    app = TelegramTwinBot()
    app.run()
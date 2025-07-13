# rag_system.py
import os
import time
import traceback
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, Docx2txtLoader, 
    JSONLoader, CSVLoader, UnstructuredMarkdownLoader,
    UnstructuredExcelLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from config import Config
from file_manager import FileManager
import requests
import json

file_manager = FileManager()

class RAGSystem:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=Config.OLLAMA_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.vectorstore = None
        self.last_user = None
        self.last_access_level = None
    
    def load_documents(self, file_paths):
        documents = []
        print(f"Loading {len(file_paths)} documents...")
        for file_path in file_paths:
            # 确保文件存在
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            ext = os.path.splitext(file_path)[1].lower()
            try:
                print(f"Loading document: {file_path}")
                if ext == '.pdf':
                    loader = PyPDFLoader(file_path)
                elif ext in ['.docx', '.doc']:
                    loader = Docx2txtLoader(file_path)
                elif ext == '.json':
                    loader = JSONLoader(file_path, jq_schema='.', text_content=False)
                elif ext == '.csv':
                    loader = CSVLoader(file_path)
                elif ext in ['.xlsx', '.xls']:
                    loader = UnstructuredExcelLoader(file_path)
                elif ext == '.md':
                    loader = UnstructuredMarkdownLoader(file_path)
                else:  # txt and others
                    loader = TextLoader(file_path)
                
                docs = loader.load()
                print(f"Loaded {len(docs)} chunks from {file_path}")
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                continue
        
        print(f"Total loaded chunks: {len(documents)}")
        return documents
    
    def create_vectorstore(self, documents):
        if not documents:
            print("No documents to create vector store")
            return None
        
        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)
        print(f"Documents split into {len(split_docs)} chunks")
        
        # 确保 ChromaDB 目录存在
        os.makedirs(Config.CHROMA_DB_DIR, exist_ok=True)
        
        try:
            # 创建向量存储 - 使用外部存储路径
            vectorstore = Chroma.from_documents(
                documents=split_docs, 
                embedding=self.embeddings,
                persist_directory=Config.CHROMA_DB_DIR
            )
            print(f"Vector store created successfully at {Config.CHROMA_DB_DIR}")
            return vectorstore
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            return None
    
    def update_knowledge_base(self, user):
        """Update knowledge base (vector store)"""
        # 检查用户和权限是否变化
        if user.id == self.last_user and user.get_access_level() == self.last_access_level:
            print("User and access level unchanged, skipping update")
            return
        
        print(f"Updating knowledge base for {user.id} ({user.get_access_level()} access)")
        accessible_files = file_manager.get_accessible_files(user)
        print(f"Accessible files: {len(accessible_files)}")
        
        if not accessible_files:
            print("No accessible files")
            self.vectorstore = None
            return
        
        documents = self.load_documents(accessible_files)
        self.vectorstore = self.create_vectorstore(documents)
        
        # 更新最后状态
        self.last_user = user.id
        self.last_access_level = user.get_access_level()
    
    def get_relevant_context(self, query, user):
        """Retrieve context relevant to the query"""
        # 确保知识库是最新的
        self.update_knowledge_base(user)
        
        if not self.vectorstore:
            print("Vector store not available, cannot retrieve context")
            return ""
        
        # 从向量库中检索相关内容
        print(f"Query: {query}")
        try:
            results = self.vectorstore.similarity_search(query, k=3)
            context = "\n\n".join([doc.page_content for doc in results])
            print(f"Retrieved context: {context[:200]}...")
            return context
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
            return ""
    
    def query_ollama(self, query, context, history):
        try:
            llm = ChatOllama(model=Config.OLLAMA_MODEL, temperature=0.7)
            
            template = """
            <s>[INST] <<SYS>>
            You are an AI assistant that answers questions based on the provided context.
            If the context is insufficient, answer based on your knowledge.
            Respond in English.
            <</SYS>>
            
            Context:
            {context}
            
            Conversation History:
            {history}
            
            Question: {question} [/INST]
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm
            
            history_str = "\n".join([f"User: {h[0]}\nAI: {h[1]}" for h in history]) if history else "No history"
            
            response = chain.invoke({
                "context": context,
                "history": history_str,
                "question": query
            })
            
            return response.content
        except Exception as e:
            print(f"Error querying Ollama: {str(e)}")
            return "An error occurred while querying the local model"
    
    def query_deepseek(self, query, context, history):
        if not Config.DEEPSEEK_API_KEY:
            return "DeepSeek API key not configured"
        
        headers = {
            "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that answers questions based on the provided context. Respond in English."
            }
        ]
        
        # 添加上下文
        if context:
            messages.append({
                "role": "system",
                "content": f"Context information:\n{context}"
            })
        
        # 添加历史对话
        for user_msg, ai_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_msg})
        
        # 添加当前问题
        messages.append({"role": "user", "content": query})
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(Config.DEEPSEEK_API_URL, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"DeepSeek API error: {response.text}"
        except Exception as e:
            return f"API request failed: {str(e)}"
    
    def query(self, query, user, history, use_deepseek=False):
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 获取相关上下文
            context = self.get_relevant_context(query, user)
            
            if use_deepseek and Config.DEEPSEEK_API_KEY:
                print("Using DeepSeek API")
                response = self.query_deepseek(query, context, history)
            else:
                print("Using local Ollama model")
                response = self.query_ollama(query, context, history)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            formatted_time = f"{elapsed_time:.2f} seconds"
            print(f"Response generated in {formatted_time}")
            
            # 返回两个值：响应内容和响应时间
            return response, formatted_time
            
        except Exception as e:
            # 错误处理
            elapsed_time = time.time() - start_time
            formatted_time = f"{elapsed_time:.2f} seconds"
            print(f"Error during query: {str(e)}")
            
            # 返回错误信息和响应时间
            return f"An error occurred: {str(e)}", formatted_time
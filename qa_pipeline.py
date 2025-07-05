import os
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.callbacks import StdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_DIR = "./chroma_db"

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
OPENAI_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_BASE = os.getenv("GROQ_API_BASE")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
if not OPENAI_API_BASE:
    raise ValueError("OPENAI_API_BASE not found in environment variables. Please check your .env file.")

model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)


def get_qa_chain():
    vectordb = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="docs_collection",
    )

    print(f"Number of embedded documents: {vectordb._collection.count()}")
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})


    llm = ChatOpenAI(
        model_name="llama-3.1-8b-instant",
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0.2,
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever, 
        memory=memory, 
        callbacks=[StdOutCallbackHandler()]
    )

    return conversation_chain


def answer_question(question):
    qa_chain = get_qa_chain()
    result = qa_chain.invoke({"question": question})

    answer = result["answer"]

    return answer

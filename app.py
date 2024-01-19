import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
import os
from dotenv import find_dotenv, load_dotenv
import debugpy
from pathlib import Path
import yaml

# TODO:
# Simple graph store
# Modulize


if False: # Set to False to disable debugging
    # 5678 is the default attach port in the VS Code debug configurations
    if not debugpy.is_client_connected():
        debugpy.listen(5678)
        debugpy.wait_for_client()


load_dotenv(find_dotenv())

PAGE_NAME = "lovdata"


# Load the YAML file
with open(Path().cwd() / "configs" / f'{PAGE_NAME}_config.yaml', 'r') as file:
    config = yaml.safe_load(file)


st.set_page_config(
    page_title=f"Chat med {config['company']}.{config['domain']}",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
openai.api_key = os.environ.get("OPENAI_API_KEY")
st.title(f"Chat med {config['company']}.{config['domain']}")

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Still meg et spørsmål om {config['company']}.{config['domain']}!",
        }
    ]


@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(
        text="Loading and indexing the web page – hang tight! This should take less than a minute."
    ):
        reader = SimpleDirectoryReader(input_files=[Path().cwd() / "data" / f"{PAGE_NAME}.txt"], recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(
            llm=OpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                system_prompt=f"Aldri hallusiner. Skriv svar basert på konteksten du får. Du snakker med en advokat og kan alt svare på spørsmål om hvitvaskingsforskriften, energimerkeforskriften og byggteknisk forskrift som funnet på {config['company']}. Du skal svare på spørsmål om paragrafer i tre ulike forskrifter. Skriv alltid svaret i to paragrafer. Først et lengre svar på spørsmålet, før du sier at det går an å finne mer informasjon i den forskriften du skriver om, samt lenken til forskriften.",
            )
        )
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index


index = load_data()

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question",
        verbose=True,
        streaming=True,
    )

# Prompt for user input and save to chat history
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display the prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)  # Add response to message history

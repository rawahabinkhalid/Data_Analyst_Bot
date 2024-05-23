from langchain.agents import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
import streamlit as st
import pandas as pd
import os
from langchain.callbacks.tracers import ConsoleCallbackHandler
from utils import *
from langchain_community.utilities import SQLDatabase

from langchain.chat_models import AzureChatOpenAI
import openai


def clear_submit():
    """
    Clear the Submit Button State
    Returns:

    """
    st.session_state["submit"] = False

#Importing database
db_uri = "sqlite:///sales.db"
db = SQLDatabase.from_uri(db_uri)


st.set_page_config(page_title="LangChain: Chat with Data Analyst", page_icon="🦜")
st.title("🦜 LangChain: Chat with Data Analyst")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="What is this data about?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    openai.api_type = "azure"
    os.environ["OPENAI_API_TYPE"] = "azure"
    #os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["OPENAI_API_KEY"] = st.secrets.openai["openai_api_key"]
    os.environ["OPENAI_API_BASE"] = st.secrets.openai["azure_endpoint"]
    os.environ["OPENAI_API_VERSION"] = "2024-02-01"

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        temperature = 0,
        deployment_name=st.secrets.openai["deployment_name"], 
        model_name=st.secrets.openai["model_name"])

    
    DDL = get_tables_ddl(db_uri)  

    

    with st.chat_message("assistant"):

        #Fetching the latest question asked by user
        question = (st.session_state.messages[len(st.session_state.messages) - 1]["content"])

        #Generating KPIs from DDL
        kpi_list = generate_kpi(question, DDL, llm)

        #Fetching aggregated KPIs
        response = generate_results(kpi_list, db_uri, DDL, llm)

        if response == "Please try again and provide proper analysis metric":
             st.write(response)

        else:
            #Generating final report
            report = generate_report(question, response, llm)

            if "database is missing" in report.lower():
                st.write(response)
                
            else:
                st.write(report)
                st.session_state.messages.append({"role": "assistant", "content": report})

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


# Load the data from Excel file
@st.cache_data
def load_data():
    df = pd.read_excel('KPI_List.xlsx')
    return df

# Define the function `xyz` which processes a list of values and returns some output
def xyz(column_data):
    # Example function implementation (you can customize this function)
    return f"Processed data: {column_data}"

# Main app function
def main(db_uri,db,DDL,llm):
    st.sidebar.title("Analysis Navigation")
    option = st.sidebar.selectbox("Select Option", ["Predefined KPIs", "Data Analysis Chat Bot"])

    if option == "Data Analysis Chat Bot":

        st.title("Chat with Data Analysis Expert")
        st.sidebar.write("Chat bot is selected")
        st.sidebar.selectbox("Select Column", options=[], disabled=True)
        
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input(placeholder="What is this data about?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            
            with st.chat_message("assistant"):
                
                #Fetching the latest question asked by user
                question = (st.session_state.messages[len(st.session_state.messages) - 1]["content"])


                #Generating KPIs from DDL
                kpi_list = generate_kpi(question, DDL, llm)
                #st.write(DDL)

                #Fetching aggregated KPIs
                response, df_results, individual_kpi_list = generate_results(question, kpi_list, db_uri, DDL, llm)

                if response == "Please try again and provide proper analysis metric":
                    st.write(response)

                else:
                    #Generating final report
                    report = generate_report(question, response, llm)

                    if "database is missing" in report.lower():
                        st.write("Please try again and provide proper analysis metric")
                        
                    else:
                        st.write(report)
                        st.session_state.messages.append({"role": "assistant", "content": report})

    
    elif option == "Predefined KPIs":
        st.sidebar.write("Predefined KPIs is selected")
        
        # Load the dataframe
        kpi_df = load_data()
        
        # Second dropdown menu with column names
        columns = kpi_df.columns.tolist()
        selected_domain = st.sidebar.selectbox("Select Column", columns)
        
        # Collected listed kpis for the selected domain and removing any null values
        kpis_list = kpi_df[selected_domain].dropna().tolist()  # Drop NaN values first

        kpis_list = [kpi for kpi in kpis_list if kpi != '']
        
        #Fetching aggregated KPIs
        response, df_results = generate_results_predefind_kpis(selected_domain, kpis_list, db_uri, DDL, llm)

        if response == "Please try again and provide proper analysis metric in KPI list":
            st.write(response)

        else:
            #Generating final report
            report = generate_report(selected_domain, response, llm)

            if "database is missing" in report.lower():
                st.write("Please try again and provide proper analysis metric in KPI list")
                
            else:
                st.write(report)



# Run the main function
if __name__ == "__main__":
    st.set_page_config(page_title="Data Analysis Expert")

    logo_url = "https://i.brecorder.com/primary/2022/04/626b6c9fc04c7.jpg"
 
    col1, col2, col3 = st.columns([2, 2, 2])
    # Display the logo using st.image
    with col2:  
        st.image(logo_url, width=200)
    

    #Importing database
    db_uri = "sqlite:///sales_dataset.db"
    db = SQLDatabase.from_uri(db_uri)
    
    openai.api_type = "azure"
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["OPENAI_API_KEY"] = st.secrets.openai["openai_api_key"]
    os.environ["OPENAI_API_BASE"] = st.secrets.openai["azure_endpoint"]
    os.environ["OPENAI_API_VERSION"] = "2024-02-01"

    llm = AzureChatOpenAI(
        openai_api_type="azure",
        temperature = 0,
        deployment_name=st.secrets.openai["deployment_name"], 
        model_name=st.secrets.openai["model_name"])

    DDL = get_tables_ddl(db_uri)  

    main(db_uri,db,DDL, llm)

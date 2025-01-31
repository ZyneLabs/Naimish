import streamlit as st
from BestBuy_keyword_crawler_Global import bestbuy_keyword_crawler
import pandas as pd

st.set_page_config(page_title="BestBuy Keyword Crawler",
    layout="wide")

st.title("# BestBuy Keyword Crawler")
# take input from the user

keyword = st.text_input("Enter the keyword")
max_results = st.number_input("Enter the number of results", min_value=1, max_value=100, value=10, step=1)
detailed_records = st.checkbox("Get detailed records")
queue_name = st.text_input("Enter the queue name", value="bestbuy")

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")
if st.button("Crawl"):
    if not keyword:
        st.error("Please enter a keyword")
    else:
        with st.spinner('Wait Data is under process'):
            data = bestbuy_keyword_crawler(url='https://www.bestbuy.com/site/searchpage.jsp?st='+keyword,detailed_records=detailed_records,max_results=max_results,queue_name=queue_name)
            st.session_state.df = pd.DataFrame(data)
        st.success("Done!")
    

if 'df' in st.session_state:
    st.write(st.session_state.df)
    # select columns to export 
    columns = st.multiselect("Select columns to export", st.session_state.df.columns, default=st.session_state.df.columns)
    record_range = st.slider("Select record range", 0, len(st.session_state.df), (0, len(st.session_state.df)))
    df = st.session_state.df[columns][record_range[0]:record_range[1]]
    # st.write(df.shape)
    csv = convert_df(df)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        help='Visible data will be downloaded',
        file_name=f"bestbuy_{keyword}.csv",
        mime="text/csv",
    )
    

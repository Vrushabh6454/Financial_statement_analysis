import streamlit as st

st.set_page_config(layout="wide")
st.title("📊 NPN Financial Dashboard")

# Your Power BI Report URL
powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=b90fcfbc-d5c7-4f99-bbf4-13bc62800297&autoAuth=true&ctid=58cf0878-8e3c-4ef8-b07b-4910aec8f052"

# Embed the report in an iframe
st.markdown(
    f"""
    <iframe title="NPN_Dashboard" width="1140" height="541.25" src="{powerbi_url}" frameborder="0" allowFullScreen="true"></iframe>
    """,
    unsafe_allow_html=True
)
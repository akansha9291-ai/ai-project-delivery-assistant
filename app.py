import streamlit as st
import pandas as pd
from datetime import datetime

st.title("AI Project Delivery Assistant")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is None:
    st.warning("No file uploaded. Showing sample data.")

    df = pd.DataFrame({
        "Task_ID": ["T1", "T2"],
        "Task_Name": ["API Build", "DB Setup"],
        "Start_Date": ["2026-04-01", "2026-04-02"],
        "End_Date": ["2026-04-05", "2026-04-04"],
        "Status": ["In Progress", "Completed"],
        "%_Complete": [60, 100]
    })
else:
    df = pd.read_excel(uploaded_file)

st.subheader("Data")
st.dataframe(df)

# Convert dates
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

today = datetime.today()

# Delay logic
df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")

# Metrics
st.subheader("Metrics")
st.write("Total Tasks:", len(df))
st.write("Delayed Tasks:", df["Is_Delayed"].sum())
st.write("Average Completion:", df["%_Complete"].mean())
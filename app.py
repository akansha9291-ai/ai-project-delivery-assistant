import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI Project Intelligence Dashboard", layout="wide")

st.title("🚀 AI Project Intelligence Dashboard")

# Sidebar
st.sidebar.title("📂 Controls")
uploaded_file = st.sidebar.file_uploader("Upload File", type=["xlsx", "csv"])
show_delayed = st.sidebar.checkbox("Show Only Delayed Tasks")
show_high_risk = st.sidebar.checkbox("Show Only High Risk Tasks")

if uploaded_file is None:
    st.warning("Upload a project file (Excel or CSV) to begin")
    st.stop()

# File handling
file_type = uploaded_file.name.split(".")[-1]

if file_type == "csv":
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

required_cols = ["Task_ID", "Task_Name", "Start_Date", "End_Date", "Status", "%_Complete"]

if not all(col in df.columns for col in required_cols):
    st.error("Missing required columns")
    st.stop()

# Data processing
df = df.dropna(subset=required_cols)

df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

today = datetime.today()

df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")

df["Days_Remaining"] = (df["End_Date"] - today).dt.days

def risk(row):
    if row["Is_Delayed"]:
        return "High"
    elif row["%_Complete"] < 50:
        return "Medium"
    return "Low"

df["Risk"] = df.apply(risk, axis=1)
df["Risk_Score"] = df["Risk"].map({"High": 3, "Medium": 2, "Low": 1})

# Filters
if show_delayed:
    df = df[df["Is_Delayed"]]

if show_high_risk:
    df = df[df["Risk"] == "High"]

# Metrics
total_tasks = len(df)
delayed_tasks = df["Is_Delayed"].sum()
completion = df["%_Complete"].mean()

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📁 Data", "🤖 AI Chat"])

# ---------------- DASHBOARD ----------------
with tab1:
    st.subheader("📊 Project Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Delayed Tasks", int(delayed_tasks))
    col3.metric("Completion %", round(completion, 2))
    col4.metric("Avg Days Remaining", int(df["Days_Remaining"].mean()))

    st.divider()

    st.subheader("📈 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Completion Distribution")
        st.bar_chart(df["%_Complete"])

    with col2:
        st.write("Status Breakdown")
        st.bar_chart(df["Status"].value_counts())

    st.subheader("🚨 Top Risk Tasks")
    st.dataframe(df.sort_values(by="Risk_Score", ascending=False).head(5))

    st.subheader("⏱ SLA Risk")
    if delayed_tasks > 0:
        st.error(f"{delayed_tasks} tasks at risk")
    else:
        st.success("No SLA risks")

    st.subheader("💡 Insights")

    if delayed_tasks > total_tasks * 0.3:
        st.error("High project risk")
    elif completion > 70:
        st.success("Project is healthy")
    else:
        st.warning("Moderate risk")

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Report", csv, "project_report.csv", "text/csv")

# ---------------- DATA ----------------
with tab2:
    st.subheader("📁 Project Data")
    st.dataframe(df)

# ---------------- AI CHAT ----------------
with tab3:
    st.subheader("🤖 AI Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    user_input = st.text_input("Ask something (risk, delay, summary, recommend)")

    if user_input:
        st.session_state.chat.append(("User", user_input))

        q = user_input.lower()

        if "risk" in q:
            response = f"{len(df[df['Risk']=='High'])} high-risk tasks detected."

        elif "delay" in q:
            response = f"{len(df[df['Is_Delayed']])} tasks are delayed."

        elif "summary" in q:
            response = f"""
            Total Tasks: {total_tasks}
            Delayed Tasks: {delayed_tasks}
            Completion: {round(completion,2)}%
            """

        elif "recommend" in q:
            response = "Focus on delayed tasks and improve completion rate."

        else:
            response = "Try asking about risk, delay, summary or recommendations."

        st.session_state.chat.append(("Bot", response))

    for role, msg in st.session_state.chat:
        if role == "User":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Bot:** {msg}")
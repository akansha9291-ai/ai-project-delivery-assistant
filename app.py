import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="AI Project Intelligence Dashboard", layout="wide")

st.title("🚀 AI Project Intelligence Dashboard")

# Sidebar
st.sidebar.title("📂 Controls")
uploaded_file = st.sidebar.file_uploader("Upload File", type=["xlsx", "csv"])

if uploaded_file is None:
    st.warning("Upload a project file to begin")
    st.stop()

# File loading
file_type = uploaded_file.name.split(".")[-1]
df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

required_cols = ["Task_ID", "Task_Name", "Start_Date", "End_Date", "Status", "%_Complete"]

if not all(col in df.columns for col in required_cols):
    st.error("Missing required columns")
    st.stop()

# Data prep
df = df.dropna(subset=required_cols)

df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

today = datetime.today()

df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")
df["Days_Remaining"] = (df["End_Date"] - today).dt.days

# Risk
def risk(row):
    if row["Is_Delayed"]:
        return "High"
    elif row["%_Complete"] < 50:
        return "Medium"
    return "Low"

df["Risk"] = df.apply(risk, axis=1)

# Scrum detection
is_scrum = "Sprint" in df.columns and "Story_Points" in df.columns

if is_scrum:
    st.success("Scrum project detected 🟢")
else:
    st.info("Traditional project detected 🔵")

# Metrics
total_tasks = len(df)
delayed_tasks = df["Is_Delayed"].sum()
completion = df["%_Complete"].mean()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Timeline", "🤖 AI Chat", "📁 Data"])

# ---------------- DASHBOARD ----------------
with tab1:
    st.subheader("📊 Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Delayed Tasks", int(delayed_tasks))
    col3.metric("Completion %", round(completion, 2))
    col4.metric("Avg Days Remaining", int(df["Days_Remaining"].mean()))

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(df["%_Complete"])

    with col2:
        st.bar_chart(df["Status"].value_counts())

    # Scrum dashboard
    if is_scrum:
        st.subheader("🏃 Scrum Dashboard")

        velocity = df.groupby("Sprint")["Story_Points"].sum()
        st.bar_chart(velocity)

        sprint_filter = st.selectbox("Select Sprint", df["Sprint"].unique())
        sprint_df = df[df["Sprint"] == sprint_filter]

        total_points = sprint_df["Story_Points"].sum()
        completed_points = sprint_df[sprint_df["Status"] == "Completed"]["Story_Points"].sum()

        progress = (completed_points / total_points) * 100 if total_points > 0 else 0
        st.metric("Sprint Completion %", round(progress, 2))

# ---------------- GANTT CHART ----------------
with tab2:
    st.subheader("📅 Project Timeline")

    fig = px.timeline(
        df,
        x_start="Start_Date",
        x_end="End_Date",
        y="Task_Name",
        color="Risk"
    )

    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AI CHAT + SMART FEATURES ----------------
with tab3:
    st.subheader("🤖 AI Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    user_input = st.text_input("Ask something (risk, delay, sprint, recommend)")

    if user_input:
        st.session_state.chat.append(("User", user_input))
        q = user_input.lower()

        # Basic responses
        if "risk" in q:
            response = f"{len(df[df['Risk']=='High'])} high-risk tasks."

        elif "delay" in q:
            response = f"{len(df[df['Is_Delayed']])} tasks are delayed."

        elif "summary" in q:
            response = f"""
            Total Tasks: {total_tasks}
            Delayed Tasks: {delayed_tasks}
            Completion: {round(completion,2)}%
            """

        # Scrum-specific
        elif "velocity" in q and is_scrum:
            avg_velocity = df.groupby("Sprint")["Story_Points"].sum().mean()
            response = f"Average sprint velocity is {round(avg_velocity,2)}"

        # Smart recommendations
        elif "recommend" in q:
            response = "Recommendations:\n"
            if delayed_tasks > 0:
                response += "- Fix delayed tasks immediately\n"
            if completion < 50:
                response += "- Improve execution speed\n"
            if delayed_tasks > total_tasks * 0.3:
                response += "- Re-plan timeline\n"

        # Sprint planning assistant
        elif "plan" in q and is_scrum:
            next_sprint_capacity = df["Story_Points"].mean() * 5
            response = f"Suggested sprint capacity: {round(next_sprint_capacity)} story points."

        else:
            response = "Try asking about risk, delay, summary, velocity or planning."

        st.session_state.chat.append(("Bot", response))

    for role, msg in st.session_state.chat:
        st.markdown(f"**{'🧑 You' if role=='User' else '🤖 Bot'}:** {msg}")

# ---------------- DATA ----------------
with tab4:
    st.dataframe(df)
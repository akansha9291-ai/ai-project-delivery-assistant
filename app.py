import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="AI Project Intelligence Dashboard", layout="wide")
st.title("🚀 AI Project Intelligence Dashboard")

# ---------------- SIDEBAR ----------------
st.sidebar.title("📂 Controls")
uploaded_file = st.sidebar.file_uploader("Upload File", type=["xlsx", "csv"])

# ---------------- LOAD FILE ----------------
if uploaded_file is None:
    st.warning("Upload a project file to begin")
    st.stop()

file_type = uploaded_file.name.split(".")[-1]
df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

required_cols = ["Task_ID", "Task_Name", "Start_Date", "End_Date", "Status", "%_Complete"]

if not all(col in df.columns for col in required_cols):
    st.error("Missing required columns")
    st.stop()

# Less aggressive cleaning
df = df.dropna(subset=["Task_ID", "Task_Name"])

# Convert dates
df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

# ---------------- PROJECT TYPE ----------------
is_scrum = "Sprint" in df.columns and "Story_Points" in df.columns

# ---------------- ADD WORK ITEM ----------------
st.sidebar.divider()
st.sidebar.subheader("➕ Add Work Item")

with st.sidebar.form("work_item_form"):
    project_name = st.text_input("Project Name *")
    owner = st.text_input("Owner *")
    due_date = st.date_input("Due Date *")

    submitted = st.form_submit_button("Submit")

    if submitted:
        if project_name and owner:
            if "work_items" not in st.session_state:
                st.session_state.work_items = []

            st.session_state.work_items.append({
                "Task_ID": f"NEW-{len(st.session_state.work_items)+1}",
                "Task_Name": project_name,
                "Start_Date": pd.to_datetime(datetime.today()),
                "End_Date": pd.to_datetime(due_date),
                "Status": "Not Started",
                "%_Complete": 0,
                "Owner": owner
            })
            st.sidebar.success("✅ Added")
        else:
            st.sidebar.error("Fill required fields")

# ---------------- MERGE ----------------
if "work_items" in st.session_state:
    df = pd.concat([df, pd.DataFrame(st.session_state.work_items)], ignore_index=True)

# Fix date types again
df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

today = pd.to_datetime(datetime.today())

# ---------------- METRICS ----------------
df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")
df["Days_Remaining"] = (df["End_Date"] - today).dt.days

def risk(row):
    if row["Is_Delayed"]:
        return "High"
    elif row["%_Complete"] < 50:
        return "Medium"
    return "Low"

df["Risk"] = df.apply(risk, axis=1)

total_tasks = len(df)
delayed_tasks = df["Is_Delayed"].sum()
completion = df["%_Complete"].mean()

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Timeline", "🤖 AI Chat", "📁 Data"])

# ---------------- DASHBOARD ----------------
with tab1:
    st.subheader("📊 Overview")

    # FIXED UI BUG HERE
    if is_scrum:
        st.success("🟢 Scrum Project")
    else:
        st.info("🔵 Traditional Project")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Delayed Tasks", int(delayed_tasks))
    col3.metric("Completion %", round(completion, 2))
    col4.metric("Avg Days Remaining", int(df["Days_Remaining"].mean()))

    st.divider()

    # -------- RAW vs AGGREGATED --------
    view_mode = st.radio("View Mode", ["Aggregated", "Raw Data"], horizontal=True)

    if view_mode == "Raw Data":
        st.dataframe(df)

    else:
        st.subheader("📊 Custom Analytics")

        col1, col2, col3 = st.columns(3)

        x_axis = col1.selectbox("X-axis", df.columns)
        numeric_cols = df.select_dtypes(include='number').columns
        y_axis = col2.selectbox("Y-axis", numeric_cols)
        agg = col3.selectbox("Aggregation", ["sum", "mean", "count"])

        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"])
        scale = st.radio("Scale", ["Linear", "Log"], horizontal=True)

        if agg == "count":
            chart_df = df.groupby(x_axis).size().reset_index(name="Count")
            y_plot = "Count"
        else:
            chart_df = df.groupby(x_axis)[y_axis].agg(agg).reset_index()
            y_plot = y_axis

        if chart_type == "Bar":
            fig = px.bar(chart_df, x=x_axis, y=y_plot)

        elif chart_type == "Line":
            fig = px.line(chart_df, x=x_axis, y=y_plot)

        elif chart_type == "Scatter":
            fig = px.scatter(chart_df, x=x_axis, y=y_plot)

        elif chart_type == "Pie":
            fig = px.pie(chart_df, names=x_axis, values=y_plot)

        if scale == "Log" and chart_type != "Pie":
            fig.update_yaxes(type="log")

        st.plotly_chart(fig, use_container_width=True)

# ---------------- TIMELINE ----------------
with tab2:
    fig = px.timeline(df, x_start="Start_Date", x_end="End_Date", y="Task_Name", color="Risk")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- AI CHAT ----------------
with tab3:
    st.subheader("🤖 AI Assistant (Smart Analysis)")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask about tasks, owners, risks, delays...")
        submitted = st.form_submit_button("Ask")

    if submitted:
        st.session_state.chat.append(("User", user_input))
        q = user_input.lower()
        response = ""

        if "Owner" in df.columns:
            owners = df["Owner"].dropna().unique()
            match = next((o for o in owners if str(o).lower() in q), None)

            if match:
                temp = df[df["Owner"] == match]
                response = f"{match}: {len(temp)} tasks, {temp['Is_Delayed'].sum()} delayed"

        elif "delay" in q:
            response = f"{len(df[df['Is_Delayed']])} delayed tasks"

        elif "risk" in q:
            response = f"{len(df[df['Risk']=='High'])} high-risk tasks"

        elif "summary" in q:
            response = f"Total {len(df)}, Delayed {delayed_tasks}, Completion {round(completion,2)}%"

        if response == "":
            response = "Try: tasks for [owner], delayed tasks, risk, summary"

        st.session_state.chat.append(("Bot", response))

    for role, msg in st.session_state.chat:
        st.markdown(f"**{'🧑 You' if role=='User' else '🤖 Bot'}:** {msg}")

# ---------------- EXPORT ----------------
with tab4:
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    st.download_button("⬇️ Download Excel", data=output.getvalue(), file_name="project_data.xlsx")

    jira_df = df.rename(columns={
        "Task_Name": "Summary",
        "Owner": "Assignee"
    })

    st.download_button("⬇️ Download Jira CSV", data=jira_df.to_csv(index=False), file_name="jira_import.csv")
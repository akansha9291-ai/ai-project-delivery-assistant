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

df = df.dropna(subset=required_cols)

# Convert dates
df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

# ---------------- PROJECT TYPE DETECTION ----------------
is_scrum = "Sprint" in df.columns and "Story_Points" in df.columns

# ---------------- ADD WORK ITEM ----------------
st.sidebar.divider()
st.sidebar.subheader("➕ Add Work Item")

with st.sidebar.form("work_item_form"):

    project_name = st.text_input("Project Name *")
    work_type = st.selectbox("Work Item Type *", ["Task", "Issue", "Risk", "Change Request"])
    priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Critical"])
    owner = st.text_input("Owner *")
    due_date = st.date_input("Due Date *")

    if work_type == "Issue":
        template = """Summary:
Steps to Reproduce:
Expected Result:
Actual Result:
Business Impact:"""
    elif work_type == "Change Request":
        template = """Summary:
Business Context:
Change Details:
Approval Required:
Rollback Plan:"""
    else:
        template = """Summary:
Business Context:
Details:
Acceptance Criteria:
Dependencies:
Risks:"""

    description = st.text_area("Description *", value=template, height=200)

    submitted = st.form_submit_button("Submit")

    if submitted:
        errors = []

        if not project_name:
            errors.append("Project Name is required")
        if not owner:
            errors.append("Owner is required")
        if not description.strip():
            errors.append("Description cannot be empty")

        required_sections = ["Summary"]

        if work_type == "Issue":
            required_sections += ["Steps to Reproduce", "Expected Result"]
        else:
            required_sections += ["Business Context", "Acceptance Criteria"]

        for section in required_sections:
            if section not in description or description.split(section + ":")[-1].strip() == "":
                errors.append(f"{section} section is incomplete")

        if errors:
            for e in errors:
                st.sidebar.error(e)
        else:
            st.sidebar.success("✅ Work item added")

            if "work_items" not in st.session_state:
                st.session_state.work_items = []

            st.session_state.work_items.append({
                "Task_ID": f"NEW-{len(st.session_state.work_items)+1}",
                "Task_Name": project_name,
                "Start_Date": pd.to_datetime(datetime.today()),
                "End_Date": pd.to_datetime(due_date),
                "Status": "Not Started",
                "%_Complete": 0,
                "Owner": owner,
                "Priority": priority,
                "Type": work_type,
                "Description": description
            })

# ---------------- MERGE ----------------
if "work_items" in st.session_state:
    new_df = pd.DataFrame(st.session_state.work_items)
    df = pd.concat([df, new_df], ignore_index=True)

# Fix dates again (important)
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

    # PROJECT TYPE DISPLAY
    if is_scrum:
        st.success("🟢 Scrum Project Detected")
    else:
        st.info("🔵 Traditional Project Detected")

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

    # ---------------- SCRUM DASHBOARD ----------------
    if is_scrum:
        st.subheader("🏃 Scrum Dashboard")

        velocity = df.groupby("Sprint")["Story_Points"].sum()
        st.bar_chart(velocity)

        sprint_filter = st.selectbox("Select Sprint", df["Sprint"].dropna().unique())
        sprint_df = df[df["Sprint"] == sprint_filter]

        total_points = sprint_df["Story_Points"].sum()
        completed_points = sprint_df[sprint_df["Status"] == "Completed"]["Story_Points"].sum()

        progress = (completed_points / total_points) * 100 if total_points > 0 else 0
        st.metric("Sprint Completion %", round(progress, 2))

# ---------------- TIMELINE ----------------
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

# ---------------- EXPORT ----------------
with tab4:
    st.subheader("📁 Data")
    st.dataframe(df)

    # Excel Export
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        "⬇️ Download Excel",
        data=output.getvalue(),
        file_name="project_data.xlsx"
    )

    # Jira Export
    jira_df = df.rename(columns={
        "Task_Name": "Summary",
        "Description": "Description",
        "Owner": "Assignee",
        "Priority": "Priority",
        "Type": "Issue Type"
    })

    st.download_button(
        "⬇️ Download Jira CSV",
        data=jira_df.to_csv(index=False),
        file_name="jira_import.csv"
    )
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI Project Delivery Assistant", layout="wide")

st.title("AI Project Delivery Assistant")
st.write("Upload your project plan Excel file to get insights.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is None:
    st.info("Please upload an Excel file to continue.")
else:
    try:
        df = pd.read_excel(uploaded_file)

        required_cols = ["Task_ID", "Task_Name", "Start_Date", "End_Date", "Status", "%_Complete"]

        if not all(col in df.columns for col in required_cols):
            st.error("Missing required columns")
        else:
            df = df.dropna(subset=required_cols)

            df["Start_Date"] = pd.to_datetime(df["Start_Date"])
            df["End_Date"] = pd.to_datetime(df["End_Date"])

            today = datetime.today()

            df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")

            def risk_level(row):
                if row["Is_Delayed"]:
                    return "High"
                elif row["%_Complete"] < 50:
                    return "Medium"
                return "Low"

            df["Risk"] = df.apply(risk_level, axis=1)

            total_tasks = len(df)
            delayed_tasks = df["Is_Delayed"].sum()
            completion = df["%_Complete"].mean()

            # Metrics
            st.subheader("Project Metrics")
            col1, col2, col3 = st.columns(3)

            col1.metric("Total Tasks", total_tasks)
            col2.metric("Delayed Tasks", int(delayed_tasks))
            col3.metric("Avg Completion (%)", round(completion, 2))

            # Charts
            st.subheader("Project Analytics")

            col1, col2 = st.columns(2)

            with col1:
                st.bar_chart(df["%_Complete"])

            with col2:
                st.bar_chart(df["Is_Delayed"].value_counts())

            # Filter
            st.subheader("Filter Tasks")
            status = st.selectbox("Select Status", ["All"] + list(df["Status"].unique()))

            if status != "All":
                df = df[df["Status"] == status]

            st.dataframe(df)

            # Health
            st.subheader("Project Health")

            if delayed_tasks > total_tasks * 0.3:
                st.error("🔴 High Risk Project")
            elif completion > 70:
                st.success("🟢 Healthy Project")
            else:
                st.warning("🟡 Moderate Risk Project")

            # Agentic AI (No API)
            st.subheader("AI Assistant")

            query = st.text_input("Ask about your project")

            if query:
                q = query.lower()

                if "risk" in q:
                    st.write(f"{len(df[df['Risk']=='High'])} tasks are high risk")

                elif "delay" in q:
                    delayed = df[df["Is_Delayed"]]
                    st.write(f"{len(delayed)} tasks are delayed")
                    st.dataframe(delayed)

                elif "summary" in q:
                    st.write(f"""
                    Total Tasks: {total_tasks}
                    Delayed Tasks: {delayed_tasks}
                    Avg Completion: {round(completion,2)}%
                    """)

                elif "recommend" in q:
                    st.write("Recommended Actions:")
                    if delayed_tasks > 0:
                        st.write("- Fix delayed tasks first")
                    if completion < 50:
                        st.write("- Increase progress speed")

                else:
                    st.write("Try: risk, delay, summary, recommend")

    except Exception as e:
        st.error(str(e))
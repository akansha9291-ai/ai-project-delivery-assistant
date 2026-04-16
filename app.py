import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="AI Project Delivery Assistant", layout="wide")

# --- Title ---
st.title("🚀 AI Project Delivery Assistant")

# --- Sidebar ---
st.sidebar.title("📂 Controls")

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

show_delayed = st.sidebar.checkbox("Show Only Delayed Tasks")
show_high_risk = st.sidebar.checkbox("Show Only High Risk Tasks")

# --- Empty State ---
if uploaded_file is None:
    st.warning("Upload a project plan to begin analysis")

    st.markdown("""
    ### Expected Columns:
    - Task_ID  
    - Task_Name  
    - Start_Date  
    - End_Date  
    - Status  
    - %_Complete  
    """)
else:
    try:
        df = pd.read_excel(uploaded_file)

        required_cols = ["Task_ID", "Task_Name", "Start_Date", "End_Date", "Status", "%_Complete"]

        if not all(col in df.columns for col in required_cols):
            st.error("Missing required columns")
        else:
            # --- Data Cleaning ---
            df = df.dropna(subset=required_cols)

            df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
            df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")

            today = datetime.today()

            # --- Delay Logic ---
            df["Is_Delayed"] = (df["End_Date"] < today) & (df["Status"] != "Completed")

            # --- Risk Logic ---
            def risk_level(row):
                if row["Is_Delayed"]:
                    return "High"
                elif row["%_Complete"] < 50:
                    return "Medium"
                return "Low"

            df["Risk"] = df.apply(risk_level, axis=1)

            # --- Risk Score ---
            df["Risk_Score"] = df["Risk"].map({"High": 3, "Medium": 2, "Low": 1})

            # --- Apply Filters ---
            if show_delayed:
                df = df[df["Is_Delayed"]]

            if show_high_risk:
                df = df[df["Risk"] == "High"]

            # --- Metrics ---
            total_tasks = len(df)
            delayed_tasks = df["Is_Delayed"].sum()
            completion = df["%_Complete"].mean()

            st.subheader("📊 Project Dashboard")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Tasks", total_tasks)
            col2.metric("Delayed Tasks", int(delayed_tasks))
            col3.metric("Completion %", round(completion, 2))

            # --- Charts ---
            st.subheader("📈 Analytics")

            col1, col2 = st.columns(2)

            with col1:
                st.write("Completion Distribution")
                st.bar_chart(df["%_Complete"])

            with col2:
                st.write("Task Status Breakdown")
                st.bar_chart(df["Status"].value_counts())

            # --- Top Risk Tasks ---
            st.subheader("🚨 Top Critical Tasks")

            top_tasks = df.sort_values(by="Risk_Score", ascending=False).head(5)

            if not top_tasks.empty:
                st.dataframe(top_tasks)
            else:
                st.success("No critical tasks")

            # --- SLA Risk ---
            st.subheader("⏱ SLA Risk")

            sla_risk = df[df["Is_Delayed"]]

            if not sla_risk.empty:
                st.error(f"{len(sla_risk)} tasks at SLA risk")
            else:
                st.success("No SLA risks")

            # --- Insights ---
            st.subheader("💡 Insights")

            if delayed_tasks > 0:
                st.warning(f"{delayed_tasks} tasks are delayed")

            if completion < 50:
                st.warning("Project progress is low")

            if delayed_tasks > total_tasks * 0.3:
                st.error("High project risk detected")

            if delayed_tasks == 0:
                st.success("Project is on track")

            # --- AI Assistant (Local Agent) ---
            st.subheader("🤖 AI Assistant")

            query = st.text_input("Ask about your project (risk, delay, summary, recommend)")

            if query:
                q = query.lower()

                if "risk" in q:
                    st.write(f"{len(df[df['Risk']=='High'])} tasks are high risk.")

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
                    st.write("Recommendations:")
                    if delayed_tasks > 0:
                        st.write("- Fix delayed tasks immediately")
                    if completion < 50:
                        st.write("- Increase execution speed")
                    if delayed_tasks > total_tasks * 0.3:
                        st.write("- Re-plan timeline")

                else:
                    st.write("Try: risk, delay, summary, recommend")

            # --- Footer ---
            st.markdown("---")
            st.caption("AI Project Delivery Assistant | Streamlit App")

    except Exception as e:
        st.error(f"Error: {e}")
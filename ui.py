import streamlit as st
import requests
import uuid
import pandas as pd

API_URL = "http://localhost:8000"  # Make sure your FastAPI is running here

st.set_page_config(page_title="AI Automation Tool", layout="centered")
st.title("🤖 No-Code AI Automation Builder")

# Toggle Admin Mode
is_admin = st.sidebar.checkbox("🔐 Admin Mode")

# AI Task Lists
user_ai_tasks = [
    "Sentiment Analysis",
    "Summarization",
    "Named Entity Recognition",
    "Text Classification",
    "Translation (EN→FR)"
]

admin_ai_tasks = [
    "Calculate Student Attendance",
    "Generate Monthly Report",
    "Schedule Alert Notifications",
    "Analyze Student Performance",
    "Detect Irregular Attendance",
    "Send Reminder Emails",
    "Summarize Class Feedback",
    "Translate Academic Notices"
]

# ---------------- USER MODE ----------------
if not is_admin:
    st.subheader("📄 Create Workflow")

    workflow_id = st.text_input("Workflow ID (leave blank to auto-generate)")
    trigger = st.selectbox("Select Trigger", ["Google Form Submission", "New Email", "Webhook Received"])
    ai_task = st.selectbox("Select AI Task", user_ai_tasks)
    action = st.selectbox("Select Action", ["Update Google Sheet", "Send Email", "Post to Slack"])

    if st.button("📂 Save Workflow"):
        if not workflow_id:
            workflow_id = str(uuid.uuid4())[:8]
        workflow = {"trigger": trigger, "ai_task": ai_task, "action": action}
        response = requests.post(f"{API_URL}/workflow/{workflow_id}", json=workflow)
        if response.ok:
            st.success(f"✅ Workflow saved with ID: `{workflow_id}`")
        else:
            st.error("❌ Failed to save workflow")

    st.markdown("---")
    st.header("🚀 Trigger Workflow")
    trigger_workflow_id = st.text_input("Enter Workflow ID to Trigger")
    text_input = st.text_area("Text input for AI task")

    if st.button("▶️ Run Workflow"):
        if not trigger_workflow_id:
            st.warning("Please enter a Workflow ID.")
        else:
            payload = {"text": text_input}
            response = requests.post(f"{API_URL}/trigger/{trigger_workflow_id}", json=payload)
            if response.ok:
                st.json(response.json())
            else:
                st.error("⚠️ Error running workflow")

# ---------------- ADMIN MODE ----------------
else:
    st.subheader("🧠 Admin Panel")

    if st.button("📂 Load All Workflows"):
        response = requests.get(f"{API_URL}/workflows")
        if response.ok:
            workflows = response.json()
            if workflows:
                for wid, wdata in workflows.items():
                    st.markdown(f"**Workflow ID:** `{wid}`")
                    st.json(wdata)
            else:
                st.info("📬 No workflows found.")
        else:
            st.error("Failed to load workflows")

    del_id = st.text_input("🗑️ Enter Workflow ID to Delete")
    if st.button("❌ Delete Workflow"):
        if del_id.strip() == "":
            st.warning("Please enter a Workflow ID.")
        else:
            response = requests.delete(f"{API_URL}/workflow/{del_id}")
            if response.ok:
                st.success(f"✅ Deleted workflow `{del_id}`")
            else:
                st.error(f"⚠️ Failed to delete workflow `{del_id}`")

    st.markdown("---")
    st.header("🧠 Run Admin AI Task")

    selected_admin_task = st.selectbox("Choose Admin AI Task", admin_ai_tasks)

    # ---------------- Admin Task: Calculate Student Attendance ----------------
    if selected_admin_task == "Calculate Student Attendance":
        uploaded_file = st.file_uploader("📄 Upload Attendance CSV", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("✅ File uploaded successfully.")
                st.dataframe(df)

                if "Status" not in df.columns:
                    st.warning("⚠️ CSV must include a 'Status' column (e.g., Present/Absent).")

                if st.button("📊 Process Attendance"):
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")
                    }
                    response = requests.post(f"{API_URL}/admin/upload-attendance", files=files)
                    if response.ok:
                        st.json(response.json())
                    else:
                        st.error("❌ Failed to process attendance")
            except Exception as e:
                st.error(f"⚠️ Error reading file: {str(e)}")

    # ---------------- Admin Task: Schedule Alert Notifications ----------------
    elif selected_admin_task == "Schedule Alert Notifications":
        uploaded_file = st.file_uploader("📄 Upload Schedule CSV", type=["csv"])
        notify_type = st.radio("Select Notification Type", ["email", "viber"])
        recipient = st.text_input("Recipient Email or Viber ID")

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("✅ File uploaded successfully.")
                st.dataframe(df)

                if "Task" not in df.columns or "Deadline" not in df.columns:
                    st.warning("⚠️ CSV must include 'Task' and 'Deadline' columns.")

                if st.button("📢 Send Schedule Alerts"):
                    if not recipient.strip():
                        st.warning("⚠️ Please enter a valid recipient email or Viber ID.")
                    else:
                        with st.spinner("Sending alert..."):
                            files = {
                                "file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")
                            }
                            params = {
                                "notify_type": notify_type.lower(),
                                "recipient": recipient
                            }
                            response = requests.post(
                                f"{API_URL}/admin/upload-schedule",
                                files=files,
                                params=params
                            )
                        if response.ok:
                            st.success("✅ Notification sent successfully!")
                            st.json(response.json())
                        else:
                            try:
                                st.error(f"❌ Error: {response.status_code} - {response.json().get('detail')}")
                            except Exception:
                                st.error("❌ Failed to process schedule or send alert.")
            except Exception as e:
                st.error(f"⚠️ Could not read CSV: {str(e)}")

    # ---------------- Other Admin AI Tasks ----------------
    else:
        admin_input = st.text_area("📝 Optional Input for Admin Task")
        if st.button("🧠 Run Admin Task"):
            payload = {"ai_task": selected_admin_task, "text": admin_input}
            response = requests.post(f"{API_URL}/admin/ai-task", json=payload)
            if response.ok:
                st.json(response.json())
            else:
                st.error("❌ Failed to run admin AI task")

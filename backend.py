from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from datetime import datetime, timedelta
from io import StringIO
import pandas as pd

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}

@app.post("/admin/upload-schedule")
async def upload_schedule(
    file: UploadFile = File(...),
    notify_type: str = Query(..., description="Notification method: email or viber"),
    recipient: str = Query(..., description="Recipient email or Viber ID")
):
    try:
        # Read and decode uploaded file content
        content = await file.read()
        try:
            df = pd.read_csv(StringIO(content.decode("utf-8")))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")

        # Check required columns
        required_columns = {"Task", "Deadline"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(
                status_code=400,
                detail="CSV must include 'Task' and 'Deadline' columns"
            )

        now = datetime.now()
        deadline_limit = now + timedelta(days=7)

        upcoming_tasks = []
        for _, row in df.iterrows():
            try:
                deadline = pd.to_datetime(row["Deadline"])
                if now <= deadline <= deadline_limit:
                    task = row["Task"]
                    note = str(row["Notes"]) if "Notes" in df.columns and pd.notna(row["Notes"]) else ""
                    upcoming_tasks.append({
                        "task": task,
                        "deadline": deadline.date().isoformat(),
                        "note": note
                    })
            except Exception:
                # Skip invalid date rows
                continue

        if not upcoming_tasks:
            return {
                "status": "no_tasks",
                "message": "No upcoming deadlines within 7 days."
            }

        # Create notification message text
        message_lines = [
            f"Task: {t['task']} | Deadline: {t['deadline']} | Notes: {t['note']}"
            for t in upcoming_tasks
        ]
        message_text = "\n".join(message_lines)

        # Simulate sending notification
        if notify_type.lower() == "email":
            print(f"📧 Sending email to {recipient}:\n{message_text}")
        elif notify_type.lower() == "viber":
            print(f"📱 Sending Viber message to {recipient}:\n{message_text}")
        else:
            raise HTTPException(status_code=400, detail="Invalid notify_type. Use 'email' or 'viber'.")

        return {
            "status": "success",
            "sent_to": recipient,
            "method": notify_type,
            "message_preview": message_lines,
            "total_upcoming": len(upcoming_tasks)
        }

    except HTTPException:
        raise  # Pass through FastAPI HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schedule processing failed: {str(e)}")

import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pdf_generator import render_pdf

# Initialize FastAPI application server
app = FastAPI(title="PDF Report Generator")


# Pydantic schema to parse optional JSON payload {"force": true}
class ReportRequest(BaseModel):
    force: Optional[bool] = False


def init_reports_db(db_path: str = "report.db"):
    """Creates the reports tracking table inside report.db if it does not exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# Ensure database table is initialized when application starts
init_reports_db()


@app.get("/health")
def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}


@app.post("/reports")
def generate_report(payload: Optional[ReportRequest] = None, response: Response = None):
    """
    Handles POST /reports with idempotency protection.
    1. Checks if a report was already generated today.
    2. If existing and force != True: returns existing metadata with 200 OK.
    3. If not found or force == True: renders new PDF to disk, saves metadata, returns 201 Created.
    """
    force_generate = payload.force if payload else False
    today_prefix = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # IDEMPOTENCY CHECK: Search database for existing report generated today
    if not force_generate:
        cursor.execute(
            "SELECT * FROM reports WHERE created_at LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"{today_prefix}%",),
        )
        existing_report = cursor.fetchone()

        # If report exists in database and physical PDF exists on disk, reuse it
        if existing_report and os.path.exists(existing_report["path"]):
            conn.close()
            response.status_code = status.HTTP_200_OK
            return {
                "id": existing_report["id"],
                "file": f"/reports/{existing_report['id']}/file",
                "created_at": existing_report["created_at"],
                "reused": True,
            }

    # GENERATE FRESH REPORT: If no report exists today or force=True
    report_id = str(uuid.uuid4())[:8]
    
    # Target absolute directory path to guarantee file creation inside reports/
    target_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(target_dir, exist_ok=True)
    pdf_filename = os.path.join(target_dir, "downloaded-report.pdf")

    # Render PDF via Playwright Chromium
    render_pdf(output_path=pdf_filename)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save metadata record into database
    cursor.execute(
        "INSERT INTO reports (id, path, created_at) VALUES (?, ?, ?)",
        (report_id, pdf_filename, created_at),
    )
    conn.commit()
    conn.close()

    # Set response code to 201 Created for freshly rendered reports
    response.status_code = status.HTTP_201_CREATED
    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
        "created_at": created_at,
        "reused": False,
    }


@app.get("/reports/{report_id}")
def get_report_metadata(report_id: str):
    """Retrieves metadata for a specific report ID."""
    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": row["id"],
        "file": f"/reports/{row['id']}/file",
        "created_at": row["created_at"],
    }


@app.get("/reports/{report_id}/file")
def download_report_file(report_id: str):
    """Serves the PDF file from disk."""
    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = row["path"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file missing from disk")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename="downloaded-report.pdf",
    )
import os
import sqlite3
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pdf_generator import render_pdf

# Initialize the FastAPI web server instance
app = FastAPI(title="PDF Report Generator")


def init_reports_db(db_path: str = "report.db"):
    """
    Connects to report.db and creates the 'reports' table if it does not exist.
    This table stores the unique ID, local file path, and creation timestamp.
    """
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


# Initialize database table when application boots
init_reports_db()


@app.get("/health")
def health_check():
    """
    Health check endpoint to verify server availability.
    Returns HTTP 200 OK.
    """
    return {"status": "ok"}


@app.post("/reports", status_code=status.HTTP_201_CREATED)
def generate_report():
    """
    Triggers PDF generation.
    1. Creates a unique report ID.
    2. Saves the output PDF file explicitly as 'reports/downloaded-report.pdf'.
    3. Saves metadata in report.db.
    4. Returns HTTP 201 Created with JSON containing the download link.
    """
    # Generate unique 8-character string identifier
    report_id = str(uuid.uuid4())[:8]

    # Explicit disk file location forced to downloaded-report.pdf
    pdf_filename = "reports/downloaded-report.pdf"

    # Execute Playwright rendering pipeline
    render_pdf(output_path=pdf_filename)

    # Record generation date and time
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insert metadata into SQLite database
    conn = sqlite3.connect("report.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (id, path, created_at) VALUES (?, ?, ?)",
        (report_id, pdf_filename, created_at),
    )
    conn.commit()
    conn.close()

    # Return response payload
    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
        "created_at": created_at,
    }


@app.get("/reports/{report_id}")
def get_report_metadata(report_id: str):
    """
    Queries report.db for metadata associated with report_id.
    Returns 404 Not Found if ID does not exist.
    """
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
    """
    Serves the PDF file from disk.
    Forces Content-Disposition filename header to 'downloaded-report.pdf'.
    """
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
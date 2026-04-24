import sqlite3
import os
import time
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# =========================
# GEMINI CONFIGURATION
# =========================
API_KEY = "AIzaSyBqs-TOLPm068SWbGtmUHXjBiYG_bo29-I"
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash-lite"

DB_NAME = "loan_app.db"

# =========================
# DATABASE CORE FUNCTIONS
# =========================
def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def recreate_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS loan_chat_history")
    cursor.execute("DROP TABLE IF EXISTS loan_leads")

    cursor.execute("""
    CREATE TABLE loan_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telecaller_name TEXT,
        call_date TEXT,
        lead_source TEXT,
        lead_id_ref TEXT,
        applicant_name TEXT,
        mobile TEXT,
        alternate_mobile TEXT,
        email TEXT,
        dob TEXT,
        gender TEXT,
        marital_status TEXT,
        city TEXT,
        state TEXT,
        address TEXT,
        loan_type TEXT,
        loan_amount TEXT,
        loan_purpose TEXT,
        property_type TEXT,
        property_location TEXT,
        property_value TEXT,
        emi_range TEXT,
        preferred_lender TEXT,
        urgency TEXT,
        employment_type TEXT,
        company_name TEXT,
        monthly_income TEXT,
        experience TEXT,
        existing_emi TEXT,
        cibil TEXT,
        income_proof TEXT,
        pan_available TEXT,
        aadhaar_available TEXT,
        bank_statement TEXT,
        itr_available TEXT,
        salary_slips TEXT,
        property_docs TEXT,
        lead_status TEXT DEFAULT 'Interested',
        eligibility TEXT,
        follow_up_date TEXT,
        remarks TEXT,
        consent TEXT,
        uploaded_files TEXT,
        extracted_text TEXT,
        user_name TEXT DEFAULT 'Visitor',
        status TEXT DEFAULT 'Interested',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE loan_chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_lead_id INTEGER,
        role TEXT,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (loan_lead_id) REFERENCES loan_leads (id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database Recreated Successfully.")

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telecaller_name TEXT,
        call_date TEXT,
        lead_source TEXT,
        lead_id_ref TEXT,
        applicant_name TEXT,
        mobile TEXT,
        alternate_mobile TEXT,
        email TEXT,
        dob TEXT,
        gender TEXT,
        marital_status TEXT,
        city TEXT,
        state TEXT,
        address TEXT,
        loan_type TEXT,
        loan_amount TEXT,
        loan_purpose TEXT,
        property_type TEXT,
        property_location TEXT,
        property_value TEXT,
        emi_range TEXT,
        preferred_lender TEXT,
        urgency TEXT,
        employment_type TEXT,
        company_name TEXT,
        monthly_income TEXT,
        experience TEXT,
        existing_emi TEXT,
        cibil TEXT,
        income_proof TEXT,
        pan_available TEXT,
        aadhaar_available TEXT,
        bank_statement TEXT,
        itr_available TEXT,
        salary_slips TEXT,
        property_docs TEXT,
        lead_status TEXT DEFAULT 'Interested',
        eligibility TEXT,
        follow_up_date TEXT,
        remarks TEXT,
        consent TEXT,
        uploaded_files TEXT,
        extracted_text TEXT,
        user_name TEXT DEFAULT 'Visitor',
        status TEXT DEFAULT 'Interested',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_lead_id INTEGER,
        role TEXT,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (loan_lead_id) REFERENCES loan_leads (id)
    )
    """)

    conn.commit()

    # Check if required column exists
    cursor.execute("PRAGMA table_info(loan_leads)")
    columns = [row["name"] for row in cursor.fetchall()]
    conn.close()

    if "applicant_name" not in columns:
        print("Old database schema detected. Recreating tables...")
        recreate_tables()
    else:
        print("Database Initialized Successfully.")

# =========================
# AI LOGIC
# =========================
def generate_ai_reply(user_message):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=f"You are a professional loan assistant. User asks: {user_message}"
            )
            return response.text.strip() if response.text else "No response generated."
        except Exception as e:
            if "503" in str(e):
                time.sleep(2)
                continue
            return f"AI Error: {str(e)}"
    return "Server busy. Please try later."

# =========================
# PAGE ROUTE
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# SAVE LEAD API
# =========================
@app.route("/api/save-loan-lead", methods=["POST"])
def save_loan_lead():
    try:
        data = request.get_json() or {}

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO loan_leads (
                telecaller_name, call_date, lead_source, lead_id_ref,
                applicant_name, mobile, alternate_mobile, email, dob, gender,
                marital_status, city, state, address,
                loan_type, loan_amount, loan_purpose, property_type, property_location,
                property_value, emi_range, preferred_lender, urgency,
                employment_type, company_name, monthly_income, experience,
                existing_emi, cibil, income_proof,
                pan_available, aadhaar_available, bank_statement, itr_available,
                salary_slips, property_docs,
                lead_status, eligibility, follow_up_date, remarks,
                consent, uploaded_files, extracted_text, user_name, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("telecallerName"),
            data.get("callDate"),
            data.get("leadSource"),
            data.get("leadId"),
            data.get("applicantName"),
            data.get("mobile"),
            data.get("alternateMobile"),
            data.get("email"),
            data.get("dob"),
            data.get("gender"),
            data.get("maritalStatus"),
            data.get("city"),
            data.get("state"),
            data.get("address"),
            data.get("loanType"),
            data.get("loanAmount"),
            data.get("loanPurpose"),
            data.get("propertyType"),
            data.get("propertyLocation"),
            data.get("propertyValue"),
            data.get("emiRange"),
            data.get("preferredLender"),
            data.get("urgency"),
            data.get("employmentType"),
            data.get("companyName"),
            data.get("monthlyIncome"),
            data.get("experience"),
            data.get("existingEmi"),
            data.get("cibil"),
            data.get("incomeProof"),
            data.get("panAvailable"),
            data.get("aadhaarAvailable"),
            data.get("bankStatement"),
            data.get("itrAvailable"),
            data.get("salarySlips"),
            data.get("propertyDocs"),
            data.get("leadStatus"),
            data.get("eligibility"),
            data.get("followUpDate"),
            data.get("remarks"),
            str(data.get("consent")),
            ", ".join(data.get("uploadedFiles", [])) if isinstance(data.get("uploadedFiles"), list) else str(data.get("uploadedFiles", "")),
            data.get("extractedText"),
            data.get("telecallerName") or "Visitor",
            data.get("leadStatus") or "Interested"
        ))

        conn.commit()
        lead_db_id = cursor.lastrowid
        conn.close()

        return jsonify({
            "success": True,
            "lead_db_id": lead_db_id,
            "message": "Lead saved successfully"
        })

    except Exception as e:
        print(f"Save Lead Error: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =========================
# AI CHAT API
# =========================
@app.route("/api/loan-ai-chat", methods=["POST"])
def loan_ai_chat():
    try:
        data = request.get_json() or {}
        user_msg = data.get("message", "").strip()
        lead_id = data.get("leadDbId")

        if not user_msg:
            return jsonify({"success": False, "error": "Empty message"}), 400

        conn = get_db()
        cursor = conn.cursor()

        if not lead_id:
            form_data = data.get("formData", {}) or {}
            cursor.execute("""
                INSERT INTO loan_leads (
                    telecaller_name, applicant_name, mobile, loan_type,
                    loan_amount, city, user_name, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                form_data.get("telecallerName"),
                form_data.get("applicantName"),
                form_data.get("mobile"),
                form_data.get("loanType"),
                form_data.get("loanAmount"),
                form_data.get("city"),
                form_data.get("telecallerName") or "New Web User",
                form_data.get("leadStatus") or "Interested"
            ))
            conn.commit()
            lead_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO loan_chat_history (loan_lead_id, role, message)
            VALUES (?, ?, ?)
        """, (lead_id, "user", user_msg))

        ai_reply = generate_ai_reply(user_msg)

        cursor.execute("""
            INSERT INTO loan_chat_history (loan_lead_id, role, message)
            VALUES (?, ?, ?)
        """, (lead_id, "assistant", ai_reply))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "reply": ai_reply,
            "leadDbId": lead_id
        })

    except Exception as e:
        print(f"Route Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
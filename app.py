import random
import sqlite3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
DB_FILE = "ats_database.db"

JOB_KEYWORDS = ["javascript", "react", "html5", "css3", "ui"]

def get_db_connection():
    """Establishes a safe connection to the local database file."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database tables and inserts mock data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the candidates table structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            skills TEXT NOT NULL,
            experience TEXT NOT NULL,
            stage TEXT NOT NULL
        )
    ''')
    
    # Add an initial baseline record if the database is brand new
    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?)",
            ("CAND-8831", "Frontend Engineer", "JavaScript, React, CSS3, HTML5, Tailwind", "3 years", "applied")
        )
        conn.commit()
    conn.close()

def calculate_fit_score(skills_string):
    """Calculates keyword match percentage from stored comma-separated skills."""
    skills_list = [s.strip().lower() for s in skills_string.split(',') if s.strip()]
    matched = set(skills_list) & set(JOB_KEYWORDS)
    return int((len(matched) / len(JOB_KEYWORDS)) * 100) if JOB_KEYWORDS else 0

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM candidates').fetchall()
    conn.close()
    
    candidate_list = []
    for row in rows:
        # Convert comma-separated string back to array list format for frontend mapping
        skills_array = [s.strip() for s in row['skills'].split(',') if s.strip()]
        
        candidate_list.append({
            "id": row['id'],
            "role": row['role'],
            "skills": skills_array,
            "experience": row['experience'],
            "stage": row['stage'],
            "fit_score": calculate_fit_score(row['skills'])
        })
    return jsonify(candidate_list)

@app.route('/api/candidates/apply', methods=['POST'])
def apply_candidate():
    data = request.json
    experience = data.get('experience')
    raw_skills = data.get('skills', '') # Expects comma-separated text input string
    
    new_id = f"CAND-{random.randint(1000, 9999)}"
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO candidates (id, role, skills, experience, stage) VALUES (?, ?, ?, ?, ?)",
        (new_id, "Frontend Engineer", raw_skills, experience, "applied")
    )
    conn.commit()
    conn.close()
    
    fit_score = calculate_fit_score(raw_skills)
    return jsonify({
        "status": "success", 
        "candidate": {"id": new_id}, 
        "fit_score": fit_score
    })

@app.route('/api/candidates/move', methods=['POST'])
def move_candidate():
    data = request.json
    cand_id = data.get('id')
    new_stage = data.get('stage')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET stage = ? WHERE id = ?", (new_stage, cand_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    
    if updated_rows > 0:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Candidate not found"}), 404

if __name__ == '__main__':
    init_db()  # Run schema initialization operations when app triggers setup
    app.run(debug=True)
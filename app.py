from flask import Flask,flash, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from flask import send_file
from reportlab.pdfgen import canvas
from io import BytesIO
import io
import random
import json
import os
import pandas as pd




app = Flask(__name__)

# Secret Key
app.secret_key = "smart_exam_secret"
app.config['UPLOAD_FOLDER'] = 'uploads'
# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'smart_exam_system'

mysql = MySQL(app)

# ==========================================
# HOME PAGE
# ==========================================

@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ==========================================
# STUDENT REGISTRATION
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO students(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard'))

    return render_template('register.html')


# ==========================================
# STUDENT LOGIN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM students WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()

        if user:

            session['student_id'] = user[0]
            session['student_name'] = user[1]

            return redirect(url_for('student_dashboard'))

        else:
            error = "Invalid Email or Password"

    return render_template('login.html', error=error)


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@app.route('/student_dashboard')
def student_dashboard():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    student_id = session['student_id']

    # Total exams available
    cur.execute("""
    SELECT COUNT(*)
    FROM exams
    """)
    total_exams = cur.fetchone()[0]

# Exams attempted by student
    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE student_id=%s
    """,
    (session['student_id'],))
    attempted_exams = cur.fetchone()[0]

    remaining_exams = total_exams - attempted_exams

    

    # Average Percentage
    cur.execute(
        """
        SELECT AVG(percentage)
        FROM results
        WHERE student_id=%s
        """,
        (student_id,)
    )

    avg_percentage = cur.fetchone()[0]

    if avg_percentage is None:
        avg_percentage = 0

    avg_percentage = round(avg_percentage, 2)

    # Best Score
    cur.execute(
        """
        SELECT MAX(score)
        FROM results
        WHERE student_id=%s
        """,
        (student_id,)
    )

    best_score = cur.fetchone()[0]

    if best_score is None:
        best_score = 0

    # Certificates Earned
    cur.execute(
        """
        SELECT COUNT(*)
        FROM results
        WHERE student_id=%s
        AND status='PASS'
        """,
        (student_id,)
    )

    certificates = cur.fetchone()[0]

    cur.close()

    return render_template(
        'student_dashboard.html',
        student_name=session['student_name'],
        total_exams=total_exams,
    attempted_exams=attempted_exams,
    remaining_exams=remaining_exams,
        avg_percentage=avg_percentage,
        best_score=best_score,
        certificates=certificates
    )

@app.route('/profile')
def profile():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Student Details
    cur.execute("""
    SELECT
        name,
        email
    FROM students
    WHERE id=%s
    """,
    (session['student_id'],))

    student = cur.fetchone()

    # Total Exams
    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE student_id=%s
    """,
    (session['student_id'],))

    total_exams = cur.fetchone()[0]

    # Average Percentage
    cur.execute("""
    SELECT AVG(percentage)
    FROM results
    WHERE student_id=%s
    """,
    (session['student_id'],))

    avg_percentage = cur.fetchone()[0]

    if avg_percentage:
        avg_percentage = round(avg_percentage, 2)
    else:
        avg_percentage = 0

    # Best Score
    cur.execute("""
    SELECT MAX(percentage)
    FROM results
    WHERE student_id=%s
    """,
    (session['student_id'],))

    best_score = cur.fetchone()[0]

    if best_score is None:
        best_score = 0

    # Certificates Earned
    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE student_id=%s
    AND status='PASS'
    """,
    (session['student_id'],))

    certificates = cur.fetchone()[0]

    cur.close()

    return render_template(
        'profile.html',
        student=student,
        total_exams=total_exams,
        avg_percentage=avg_percentage,
        best_score=best_score,
        certificates=certificates
    )
# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    error = None

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (username, password)
        )

        admin = cur.fetchone()

        cur.close()

        if admin:

            session['admin_id'] = admin[0]
            session['admin_name'] = admin[1]

            return redirect(url_for('admin_dashboard'))

        else:
            error = "Invalid Admin Credentials"

    return render_template(
        'admin_login.html',
        error=error
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    cur.execute(
    "SELECT COUNT(*) FROM students"
    )

    total_students = cur.fetchone()[0]

# ==========================
# TOTAL EXAMS
# ==========================

    cur.execute(
    "SELECT COUNT(*) FROM exams"
    )

    total_exams = cur.fetchone()[0]

# ==========================
# TOTAL QUESTIONS
# ==========================

    cur.execute(
    "SELECT COUNT(*) FROM questions"
    )

    total_questions = cur.fetchone()[0]

# ==========================
# TOTAL ATTEMPTS
# ==========================

    cur.execute(
    "SELECT COUNT(*) FROM results"
    )

    total_attempts = cur.fetchone()[0]

# ==========================
# PASS COUNT
# ==========================

    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE status='PASS'
    """)

    pass_count = cur.fetchone()[0]

# ==========================
# PASS PERCENTAGE
# ==========================

    if total_attempts > 0:

        pass_percentage = round(
        (pass_count / total_attempts) * 100,
        2
        )

    else:

        pass_percentage = 0

# ==========================
# TOP 5 STUDENTS
# ==========================

    cur.execute("""
    SELECT
        students.name,
        MAX(results.percentage)

    FROM results

    JOIN students
    ON results.student_id = students.id

    GROUP BY students.id

    ORDER BY MAX(results.percentage) DESC

    LIMIT 5
    """)

    top_students = cur.fetchall()

# ==========================
# RECENT RESULTS
# ==========================

    cur.execute("""
    SELECT
        students.name,
        exams.exam_name,
        results.percentage,
        results.status

    FROM results

    JOIN students
    ON results.student_id = students.id

    JOIN exams
    ON results.exam_id = exams.exam_id

    ORDER BY results.submitted_at DESC

    LIMIT 5
    """)

    recent_results = cur.fetchall()

    # ==========================
# PASS VS FAIL
# ==========================

    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE status='PASS'
    """)

    pass_count = cur.fetchone()[0]

    cur.execute("""
    SELECT COUNT(*)
    FROM results
    WHERE status='FAIL'
    """)

    fail_count = cur.fetchone()[0]


# ==========================
# EXAM ATTEMPTS
# ==========================

    cur.execute("""
    SELECT
    exams.exam_name,
    COUNT(results.result_id)

    FROM exams

    LEFT JOIN results
    ON exams.exam_id = results.exam_id

    GROUP BY exams.exam_id
    """)

    exam_attempts = cur.fetchall()
    cur.close()
    exam_labels = [row[0] for row in exam_attempts]
    exam_counts = [row[1] for row in exam_attempts]

    return render_template(
    'admin_dashboard.html',

    total_students=total_students,
    total_exams=total_exams,
    total_questions=total_questions,
    total_attempts=total_attempts,
    pass_percentage=pass_percentage,

    top_students=top_students,
    recent_results=recent_results,

    pass_count=pass_count,
    fail_count=fail_count,

    exam_labels=exam_labels,
    exam_counts=exam_counts,


    exam_attempts=exam_attempts,

    admin_name=session['admin_name']
)




# ==========================================
# CREATE EXAM
# ==========================================

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':

        exam_name = request.form['exam_name']
        subject = request.form['subject']
        duration = request.form['duration']
        total_marks = request.form['total_marks']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO exams
            (exam_name, subject, duration, total_marks)
            VALUES (%s, %s, %s, %s)
            """,
            (exam_name, subject, duration, total_marks)
        )

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('create_exam.html')


# ==========================================
# VIEW EXAMS
# ==========================================

@app.route('/view_exams')
def view_exams():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT
        e.exam_id,
        e.exam_name,
        e.subject,
        e.duration,
        e.total_marks,

        COUNT(DISTINCT q.question_id) AS total_questions,

        COUNT(DISTINCT r.result_id) AS total_attempts

    FROM exams e

    LEFT JOIN questions q
    ON e.exam_id = q.exam_id

    LEFT JOIN results r
    ON e.exam_id = r.exam_id

    GROUP BY e.exam_id
    """)

    exams = cur.fetchall()

    cur.close()

    return render_template(
        'view_exams.html',
        exams=exams
    )

@app.route('/view_questions/<int:exam_id>')
def view_questions(exam_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    # Exam Details
    cur.execute("""
    SELECT exam_name
    FROM exams
    WHERE exam_id=%s
    """,
    (exam_id,))
    
    exam = cur.fetchone()

    # Questions
    cur.execute("""
    SELECT *
    FROM questions
    WHERE exam_id=%s
    """,
    (exam_id,))

    questions = cur.fetchall()

    cur.close()

    return render_template(
        'view_questions.html',
        questions=questions,
        exam_name=exam[0]
    )
# ==========================================
# ADD QUESTION
# ==========================================

@app.route('/add_questions/<int:exam_id>', methods=['GET', 'POST'])
def add_questions(exam_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':

        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO questions
            (
                exam_id,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                exam_id,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option
            )
        )

        mysql.connection.commit()
        cur.close()

        return redirect(
            url_for(
                'add_questions',
                exam_id=exam_id
            )
        )

    return render_template(
        'add_questions.html',
        exam_id=exam_id
    )

@app.route('/available_exams')
def available_exams():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT *
    FROM exams
    """)

    exams = cur.fetchall()

    exam_list = []

    for exam in exams:
        exam_id = exam[0]
        cur.execute("""
        SELECT result_id
        FROM results
        WHERE student_id=%s
        AND exam_id=%s
        """,
        (
            session['student_id'],
            exam_id
        ))

        attempted = cur.fetchone()
        exam_id = exam[0]

        cur.execute("""
        SELECT remaining_time
        FROM exam_sessions
        WHERE student_id=%s
        AND exam_id=%s
        AND is_submitted=0
        """,
        (
            session['student_id'],
            exam_id
        ))

        resume_exam = cur.fetchone()

        exam_list.append({
    "exam_id": exam[0],
    "exam_name": exam[1],
    "subject": exam[2],
    "duration": exam[3],
    "attempted": True if attempted else False,
    "resume": True if resume_exam and not attempted else False,
    "remaining_time": resume_exam[0] if resume_exam else None
        })

    cur.close()

    return render_template(
        'available_exams.html',
        exams=exam_list
    )
@app.route('/resume_exam/<int:exam_id>')
def resume_exam(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    return redirect(
        url_for(
            'take_exam',
            exam_id=exam_id
        )
    )
@app.route('/start_exam/<int:exam_id>')
def start_exam(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT *
    FROM results
    WHERE student_id=%s
    AND exam_id=%s
    """,
    (
        session['student_id'],
        exam_id
    ))

    attempt = cur.fetchone()

    cur.close()

    if attempt:
        return render_template(
            'already_attempted.html'
        )

    return redirect(
        url_for(
            'exam_instructions',
            exam_id=exam_id
        )
    )
@app.route('/exam_instructions/<int:exam_id>')
def exam_instructions(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT exam_name,
               subject,
               duration,
               total_marks
        FROM exams
        WHERE exam_id=%s
        """,
        (exam_id,)
    )

    exam = cur.fetchone()

    cur.close()

    if not exam:
        return "Exam Not Found"

    return render_template(
        'exam_instructions.html',
        exam_id=exam_id,
        exam=exam
    )

@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    print("METHOD =", request.method)
    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Check if already attempted
    cur.execute(
        """
        SELECT *
        FROM results
        WHERE student_id=%s
        AND exam_id=%s
        """,
        (
            session['student_id'],
            exam_id
        )
    )

    attempt = cur.fetchone()

    if attempt:
        cur.close()
        return render_template('already_attempted.html')

    # ===============================
    # SUBMIT EXAM
    # ===============================
    if request.method == 'POST':

        cur.execute("""
    SELECT *
    FROM questions
    WHERE exam_id=%s
    ORDER BY RAND()
    """,
    (exam_id,))
        questions = list(cur.fetchall())

        score = 0
        total_questions = len(questions)

        for q in questions:

            question_id = q[0]

            student_answer = request.form.get(
                f'question_{question_id}'
            )

            correct_answer = q[7]

            if student_answer == correct_answer:
                score += 1
            is_correct = (student_answer == correct_answer)

            cur.execute("""
UPDATE student_answers
SET
    student_answer=%s,
    correct_answer=%s,
    is_correct=%s
WHERE student_id=%s
AND exam_id=%s
AND question_id=%s
""",
(
            student_answer,
            correct_answer,
            is_correct,
            session['student_id'],
            exam_id,
            question_id
))

        # Calculate percentage
        percentage = round(
            (score / total_questions) * 100,
            2
        )

        # Pass / Fail
        if percentage >= 40:
            status = "PASS"
        else:
            status = "FAIL"

        # Save result
        cur.execute(
            """
            INSERT INTO results
            (
                student_id,
                exam_id,
                score,
                total_questions,
                percentage,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s)
            """,
            (
                session['student_id'],
                exam_id,
                score,
                total_questions,
                percentage,
                status
            )
        )
        cur.execute("""
        UPDATE exam_sessions
    SET is_submitted=1
    WHERE student_id=%s
    AND exam_id=%s
    """,
    (
        session['student_id'],
        exam_id
    ))
        mysql.connection.commit()
        cur.close()

        # Show success message page
        return render_template(
            'exam_submitted.html'
        )

# ===============================
# LOAD EXAM PAGE
# ===============================

    cur.execute("""SELECT exam_name,
       subject,
       duration FROM exams WHERE exam_id=%s """,(exam_id,))
    exam = cur.fetchone()

    if not exam:
        cur.close()
        return "Exam Not Found"

    exam_name = exam[0]
    subject = exam[1]
    duration = exam[2]

# ---------------------------------
# CHECK SAVED SESSION
# ---------------------------------

    cur.execute(""" SELECT remaining_time
    FROM exam_sessions
    WHERE student_id=%s
    AND exam_id=%s
    AND is_submitted=0
    """,
    (
    session['student_id'],
    exam_id
    ))

    saved_session = cur.fetchone()

    if saved_session:
        remaining_time = saved_session[0]
    else:
        remaining_time = duration * 60

# ---------------------------------
# LOAD QUESTIONS
# ---------------------------------

    cur.execute("""
    SELECT *
    FROM questions
    WHERE exam_id=%s
    """,
    (exam_id,))

    questions = list(cur.fetchall())

# Randomize only when first opening exam
    if not saved_session:
        import random
        random.shuffle(questions)

# ---------------------------------
# LOAD SAVED ANSWERS
# ---------------------------------

    cur.execute("""
    SELECT question_id,
       student_answer
    FROM student_answers
    WHERE student_id=%s
    AND exam_id=%s
    """,
    (
    session['student_id'],
    exam_id
    ))

    saved_answers = {}

    for row in cur.fetchall():
        saved_answers[row[0]] = row[1]

    cur.close()
    print("Saved Answers =", saved_answers)
    return render_template(
    'take_exam.html',
    questions=questions,
    duration=duration,
    remaining_time=remaining_time,
    exam_name=exam_name,
    subject=subject,
    exam_id=exam_id,
    saved_answers=saved_answers
) # change index if duration is in another column

@app.route('/autosave_exam', methods=['POST'])
def autosave_exam():

    if 'student_id' not in session:
        return jsonify({'status':'error'})

    data = request.json

    exam_id = data['exam_id']
    question_id = data['question_id']
    answer = data['answer']
    remaining_time = data['remaining_time']

    cur = mysql.connection.cursor()

    cur.execute("""
    INSERT INTO student_answers
    (
        student_id,
        exam_id,
        question_id,
        student_answer
    )
    VALUES(%s,%s,%s,%s)

    ON DUPLICATE KEY UPDATE

    student_answer=%s
    """,
    (
        session['student_id'],
        exam_id,
        question_id,
        answer,
        answer
    ))

    cur.execute("""
    INSERT INTO exam_sessions
    (
        student_id,
        exam_id,
        remaining_time
    )
    VALUES(%s,%s,%s)

    ON DUPLICATE KEY UPDATE

    remaining_time=%s
    """,
    (
        session['student_id'],
        exam_id,
        remaining_time,
        remaining_time
    ))

    mysql.connection.commit()

    cur.close()

    return jsonify({'status':'success'})

@app.route('/analysis/<int:exam_id>')
def analysis(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
SELECT
    q.question,
    q.option_a,
    q.option_b,
    q.option_c,
    q.option_d,

    sa.student_answer,

    q.correct_option,

    CASE
        WHEN sa.student_answer = q.correct_option
        THEN 1
        ELSE 0
    END

FROM questions q

LEFT JOIN student_answers sa
ON q.question_id = sa.question_id
AND sa.student_id=%s
AND sa.exam_id=%s

WHERE q.exam_id=%s
""",
(
    session['student_id'],
    exam_id,
    exam_id
))

    analysis_data = cur.fetchall()

    total = len(analysis_data)

    correct = sum(
    1 for q in analysis_data
    if q[5] is not None and q[7] == 1
    )

    wrong = sum(
    1 for q in analysis_data
    if q[5] is not None and q[7] == 0
    )

    unanswered = total - correct - wrong
    percentage = round((correct / total) * 100, 2) if total else 0

    cur.close()

    return render_template(
    'analysis.html',
    analysis_data=analysis_data,
    total=total,
    correct=correct,
    wrong=wrong,
    unanswered=unanswered,
    percentage=percentage
)

@app.route('/exam_submitted')
def exam_submitted():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    return render_template('exam_submitted.html')
# ==========================================
# LOGOUT
# ==========================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('home'))

@app.route('/view_results')
def view_results():

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT
    exams.exam_id,
    exams.exam_name,
    results.score,
    results.total_questions,
    results.percentage,
    results.status,
    results.submitted_at
    FROM results
    JOIN exams
    ON results.exam_id = exams.exam_id
    WHERE results.student_id=%s
    """,
    (session['student_id'],))

    results = cur.fetchall()

    cur.close()

    return render_template(
        'view_results.html',
        results=results
    )

@app.route('/all_results')
def all_results():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT
        r.result_id,
        s.name,
        e.exam_name,
        r.score,
        r.total_questions,
        r.percentage,
        r.status,
        r.submitted_at

    FROM results r

    JOIN students s
    ON r.student_id = s.id

    JOIN exams e
    ON r.exam_id = e.exam_id

    ORDER BY r.submitted_at DESC
    """)

    results = cur.fetchall()

    cur.close()

    return render_template(
        'all_results.html',
        results=results
    )

@app.route('/track_cheating', methods=['POST'])
def track_cheating():

    if 'student_id' not in session:
        return jsonify({'status':'error'})

    data = request.json

    exam_id = data['exam_id']
    cheating_count = data['cheating_count']

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE exam_sessions
    SET cheating_count=%s
    WHERE student_id=%s
    AND exam_id=%s
    """,
    (
        cheating_count,
        session['student_id'],
        exam_id
    ))

    mysql.connection.commit()

    cur.close()

    return jsonify({'status':'success'})

@app.route('/delete_exam/<int:exam_id>')
def delete_exam(exam_id):

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM exams WHERE exam_id=%s",
        (exam_id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect(url_for('view_exams'))


@app.route('/certificate/<int:exam_id>')
def certificate(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT
        s.name,
        e.exam_name,
        r.score,
        r.total_questions,
        r.percentage,
        r.status,
        r.submitted_at

    FROM results r

    JOIN students s
        ON r.student_id = s.id

    JOIN exams e
        ON r.exam_id = e.exam_id

    WHERE r.student_id = %s
    AND r.exam_id = %s
    """,
    (
        session['student_id'],
        exam_id
    ))

    data = cur.fetchone()

    cur.close()

    if not data:
        return "Certificate Not Found"

    student_name = data[0]
    exam_name = data[1]
    score = data[2]
    total_questions = data[3]
    percentage = data[4]
    status = data[5]
    exam_date = str(data[6])

    if status != "PASS":
        return "Certificate available only for passed students"

    certificate_id = (
        f"CERT-{exam_id}-{session['student_id']}"
    )

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    width = 595
    height = 842

    # =========================
    # OUTER BORDER
    # =========================

    pdf.setLineWidth(4)
    pdf.rect(
        20,
        20,
        555,
        802
    )

    # =========================
    # INNER BORDER
    # =========================

    pdf.setLineWidth(1)

    pdf.rect(
        35,
        35,
        525,
        772
    )

    # =========================
    # SYSTEM NAME
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawCentredString(
        width/2,
        790,
        "ONLINE EXAMINATION SYSTEM"
    )

    # =========================
    # CERTIFICATE TITLE
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        28
    )

    pdf.drawCentredString(
        width/2,
        740,
        "CERTIFICATE OF ACHIEVEMENT"
    )

    pdf.line(
        120,
        720,
        475,
        720
    )

    # =========================
    # SUBTITLE
    # =========================

    pdf.setFont(
        "Helvetica",
        15
    )

    pdf.drawCentredString(
        width/2,
        680,
        "This Certificate is Proudly Presented To"
    )

    # =========================
    # STUDENT NAME
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        30
    )

    pdf.drawCentredString(
        width/2,
        620,
        student_name
    )

    pdf.line(
        150,
        600,
        445,
        600
    )

    # =========================
    # DESCRIPTION
    # =========================

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        width/2,
        550,
        "For Successfully Passing"
    )

    # =========================
    # EXAM NAME
    # =========================

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawCentredString(
        width/2,
        510,
        exam_name
    )

    # =========================
    # DETAILS
    # =========================

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawString(
        100,
        430,
        f"Score : {score}/{total_questions}"
    )

    pdf.drawString(
        100,
        400,
        f"Percentage : {percentage}%"
    )

    pdf.drawString(
        100,
        370,
        f"Status : {status}"
    )

    pdf.drawString(
        100,
        340,
        f"Issue Date : {exam_date}"
    )

    pdf.drawString(
        100,
        310,
        f"Certificate ID : {certificate_id}"
    )

    # =========================
    # SEAL
    # =========================

    pdf.circle(
        140,
        170,
        40
    )

    pdf.drawCentredString(
        140,
        170,
        "SEAL"
    )

    # =========================
    # SIGNATURE
    # =========================

    pdf.line(
        380,
        180,
        520,
        180
    )

    pdf.drawString(
        400,
        160,
        "Authorized Signatory"
    )

    # =========================
    # FOOTER
    # =========================

    pdf.setFont(
        "Helvetica-Oblique",
        11
    )

    pdf.drawCentredString(
        width/2,
        80,
        "Generated by Online Examination System"
    )

    pdf.drawCentredString(
        width/2,
        60,
        "This certificate can be verified using Certificate ID"
    )

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="certificate.pdf",
        mimetype="application/pdf"
    )

@app.route('/leaderboard')
def leaderboard():

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT
        students.name,
        MAX(results.percentage) AS best_score

    FROM results

    JOIN students
    ON results.student_id = students.id

    GROUP BY students.id

    ORDER BY best_score DESC

    LIMIT 20
    """)

    leaderboard_data = cur.fetchall()

    cur.close()

    return render_template(
        'leaderboard.html',
        leaderboard_data=leaderboard_data
    )

@app.route('/upload_question_bank', methods=['GET', 'POST'])
def upload_question_bank():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    message = None

    if request.method == 'POST':

        file = request.files['excel_file']

        if file.filename == '':
            message = "No file selected"
            return render_template(
                'upload_question_bank.html',
                message=message
            )

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file.filename
        )

        file.save(filepath)

        df = pd.read_excel(filepath)

        df = df.fillna('')

        cur = mysql.connection.cursor()

        for _, row in df.iterrows():

            cur.execute(
                """
                INSERT INTO question_bank
                (
                    subject,
                    topic,
                    difficulty,
                    question,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_option
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    row['subject'],
                    row['topic'],
                    row['difficulty'],
                    row['question'],
                    row['option_a'],
                    row['option_b'],
                    row['option_c'],
                    row['option_d'],
                    row['correct_option']
                )
            )

        mysql.connection.commit()
        cur.close()

        message = f"{file.filename} uploaded successfully"

    return render_template(
        'upload_question_bank.html',
        message=message
    )


@app.route('/generate_exam', methods=['GET', 'POST'])
def generate_exam():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    message = None

    if request.method == 'POST':

        exam_name = request.form['exam_name']
        subject = request.form['subject']
        difficulty = request.form['difficulty']
        duration = request.form['duration']
        num_questions = int(request.form['num_questions'])

        cur = mysql.connection.cursor()

        # Create Exam
        cur.execute(
            """
            INSERT INTO exams
            (
                exam_name,
                subject,
                duration,
                total_marks
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                exam_name,
                subject,
                duration,
                num_questions
            )
        )

        mysql.connection.commit()

        exam_id = cur.lastrowid

        # Fetch Questions
        if difficulty == "All":

            cur.execute(
                """
                SELECT *
                FROM question_bank
                WHERE subject=%s
                ORDER BY RAND()
                LIMIT %s
                """,
                (
                    subject,
                    num_questions
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM question_bank
                WHERE subject=%s
                AND difficulty=%s
                ORDER BY RAND()
                LIMIT %s
                """,
                (
                    subject,
                    difficulty,
                    num_questions
                )
            )

        selected_questions = cur.fetchall()
        print("Subject =", subject)
        print("Difficulty =", difficulty)
        print("Questions Found =", len(selected_questions))

        # Check availability
        if len(selected_questions) == 0:

            cur.close()

            return render_template(
                'generate_exam.html',
                message="No questions found for selected criteria."
            )

        # Insert Questions into Exam
        for q in selected_questions:

            cur.execute(
                """
                INSERT INTO questions
                (
                    exam_id,
                    question,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_option
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    exam_id,
                    q[4],  # question
                    q[5],  # option_a
                    q[6],  # option_b
                    q[7],  # option_c
                    q[8],  # option_d
                    q[9]   # correct_option
                )
            )

        mysql.connection.commit()
        cur.close()

        message = (
            f"Exam '{exam_name}' generated successfully "
            f"with {len(selected_questions)} questions."
        )

        return render_template(
            'generate_exam.html',
            message=message
        )

    return render_template(
        'generate_exam.html',
        message=message
    )
@app.route('/feedback/<int:exam_id>', methods=['GET','POST'])
def feedback(exam_id):

    if 'student_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        rating = request.form['rating']
        comments = request.form['comments']

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO feedback
        (
            student_id,
            exam_id,
            rating,
            comments
        )
        VALUES
        (%s,%s,%s,%s)
        """,
        (
            session['student_id'],
            exam_id,
            rating,
            comments
        ))

        mysql.connection.commit()
        cur.close()

        flash(
            "Thank you for your feedback!",
            "success"
        )

        return redirect(url_for('view_results'))

    return render_template(
        'feedback.html',
        exam_id=exam_id
    )
@app.route('/view_feedback')
def view_feedback():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT f.student_id, f.exam_id, f.rating, f.comments
        FROM feedback f
        ORDER BY feedback_id DESC
    """)

    feedbacks = cur.fetchall()

    return render_template("view_feedback.html", feedbacks=feedbacks)
# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == '__main__':
    app.run(debug=True)
from fastapi_restful import Resource
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/lms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# Define database models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    assignments = db.relationship('Assignment', back_populates='course', lazy=True)  # Bidirectional relationship
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    submissions = db.relationship('Submission', backref='assignment', lazy=True)
    course = db.relationship('Course', back_populates='assignments')  # Add this line
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    content = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Float, nullable=True)
    student = db.relationship('Student', backref='submissions')
class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(200), nullable=False)

# Routes for authentication
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admindashboard')
def admindashboard():
    return render_template('admin_dashboard.html')

@app.route('/studentdashboard')
def studentdashboard():
    if 'role' in session and session['role'] == 'student':
        student = Student.query.get(session['user_id'])
        return render_template('student_dashboard.html', student_name=student.name)        


@app.route('/facultydashboard')
def facultydashboard():
    if 'role' in session and session['role'] == 'faculty':
        faculty = Faculty.query.get(session['user_id'])
    return render_template('teacher_dashboard.html', faculty_name=faculty.name)

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        phone = request.form['phone']
        branch = request.form['branch']
        profile_picture = request.files['profile_picture'] if 'profile_picture' in request.files else None

        if Student.query.filter_by(email=email).first() or Student.query.filter_by(student_id=student_id).first():
            flash('Student ID or Email already exists!')
            return redirect(url_for('student_register'))

        profile_picture_path = None
        if profile_picture:
            profile_picture_path = f'static/uploads/{profile_picture.filename}'
            profile_picture.save(profile_picture_path)

        new_student = Student(student_id=student_id, name=name, email=email, password=password, phone=phone, branch=branch, profile_picture=profile_picture_path)
        db.session.add(new_student)
        db.session.commit()
        flash('Student registration successful!')
        return redirect(url_for('login'))

    return render_template('student_register.html')

@app.route('/faculty_register', methods=['GET', 'POST'])
def faculty_register():
    if request.method == 'POST':
        faculty_id = request.form['faculty_id']
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        phone = request.form['phone']
        course = request.form['course']
        profile_picture = request.files['profile_picture'] if 'profile_picture' in request.files else None

        if Faculty.query.filter_by(email=email).first() or Faculty.query.filter_by(faculty_id=faculty_id).first():
            flash('Faculty ID or Email already exists!')
            return redirect(url_for('faculty_register'))

        profile_picture_path = None
        if profile_picture:
            profile_picture_path = f'static/uploads/{profile_picture.filename}'
            profile_picture.save(profile_picture_path)

        new_faculty = Faculty(faculty_id=faculty_id, name=name, email=email, password=password, phone=phone, course=course, profile_picture=profile_picture_path)
        db.session.add(new_faculty)
        db.session.commit()
        flash('Faculty registration successful!')
        return redirect(url_for('login'))

    return render_template('faculty_register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        # Check for student login
        student = Student.query.filter((Student.email == identifier) | (Student.student_id == identifier)).first()
        if student and bcrypt.check_password_hash(student.password, password):
            session['user_id'] = student.id
            session['role'] = 'student'
            flash('Login successful!')
            return redirect(url_for('student_dashboard'))

        # Check for faculty login
        faculty = Faculty.query.filter((Faculty.email == identifier) | (Faculty.faculty_id == identifier)).first()
        if faculty and bcrypt.check_password_hash(faculty.password, password):
            session['user_id'] = faculty.id
            session['role'] = 'faculty'
            flash('Login successful!')
            return redirect(url_for('teacher_dashboard'))

        # Check for admin login
        admin = Admin.query.filter_by(name=identifier).first()
        if admin and admin.password == password:
            session['user_id'] = admin.id
            session['role'] = 'admin'
            flash('Login successful!')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid credentials!')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    flash('Access denied!')
    return redirect(url_for('login'))

# Teacher dashboard
@app.route('/teacher')
def teacher_dashboard():
    if 'role' in session and session['role'] == 'faculty':
        faculty = Faculty.query.get(session['user_id'])
        return render_template('teacher_dashboard.html', faculty_name=faculty.name)
    flash('Access denied!')
    return redirect(url_for('login'))

# Student dashboard
@app.route('/student')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        student = Student.query.get(session['user_id'])
        return render_template('student_dashboard.html', student_name=student.name)        
    flash('Access denied!')
    return redirect(url_for('login'))

@app.route('/studentdash')
def student_dash():
    # Path to the resources directory
    resources_path = os.path.join('static', 'resources')
    
    # Organize files into categories
    images = []
    documents = []
    others = []

    if os.path.exists(resources_path):
        for file in os.listdir(resources_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                images.append(file)
            elif file.lower().endswith(('.pdf', '.txt', '.docx')):
                documents.append(file)
            else:
                others.append(file)
    
    # Render the dashboard with categorized resources
    return render_template('student_resource.html', images=images, documents=documents, others=others)
# Manage Users
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'role' in session and session['role'] == 'admin':
        students = Student.query.all()
        faculty = Faculty.query.all()
        return render_template('manage_users.html', students=students, faculty=faculty)
    flash('Access denied!')
    return redirect(url_for('login'))

# Manage Courses
@app.route('/manage_courses_faculty', methods=['GET', 'POST'])
def manage_courses_faculty():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']

            new_course = Course(name=name, description=description, faculty_id=session['user_id'])
            db.session.add(new_course)
            db.session.commit()
            flash('Course created successfully!')

        courses = Course.query.filter_by(faculty_id=session['user_id']).all()
        return render_template('manage_courses_faculty.html', courses=courses)
    flash('Access denied!')
    return redirect(url_for('login'))

# Manage Courses
@app.route('/manage_courses_admin', methods=['GET', 'POST'])
def manage_courses_admin():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            teacher_id = request.form['teacher_id']
            # Validate if the teacher exists
            teacher = Faculty.query.get(teacher_id)
            if not teacher:
                flash('Invalid teacher selected.')
                return redirect(url_for('manage_courses'))

            new_course = Course(name=name, description=description, faculty_id=teacher_id)
            db.session.add(new_course)
            db.session.commit()
            flash('Course added successfully!')

        courses = Course.query.all()
        teachers = Faculty.query.all()
        return render_template('manage_courses_admin.html', courses=courses, teachers=teachers)
    flash('Access denied!')
    return redirect(url_for('login'))
# Assignments
@app.route('/assignments', methods=['GET', 'POST'])
def assignments():
    if 'role' in session and session['role'] in ['faculty', 'student']:
        if request.method == 'POST' and session['role'] == 'faculty':
            title = request.form['title']
            description = request.form['description']
            due_date = request.form['due_date']
            course_id = request.form['course_id']

            new_assignment = Assignment(title=title, description=description, due_date=due_date, course_id=course_id)
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!')

        assignments = Assignment.query.all()
        return render_template('assignments.html', assignments=assignments)
    flash('Access denied!')
    return redirect(url_for('login'))


# Assignments
@app.route('/assignments_Faculty', methods=['GET', 'POST'])
def assignments_Faculty():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            due_date = request.form['due_date']
            course_id = request.form['course_id']

            # Validate if the course exists
            course = Course.query.get(course_id)
            if not course:
                flash('Invalid course selected.')
                return redirect(url_for('assignments'))

            new_assignment = Assignment(title=title, description=description, due_date=due_date, course_id=course_id)
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!')
        assignments = Assignment.query.all()
        courses = Course.query.all()
        return render_template('assignments_Faculty.html', assignments=assignments, courses=courses)
    flash('Access denied!')
    return redirect(url_for('login'))


# Performance
@app.route('/performance')
def performance():
    if 'role' in session and session['role'] == 'student':
        submissions = Submission.query.filter_by(student_id=session['user_id']).all()
        return render_template('performance.html', submissions=submissions)
    elif 'role' in session and session['role'] == 'faculty':
        courses = Course.query.filter_by(faculty_id=session['user_id']).all()
        return render_template('faculty_performance.html', courses=courses)
    flash('Access denied!')
    return redirect(url_for('login'))

@app.route('/course_performance/<int:course_id>')
def course_performance(course_id):
    if 'role' in session and session['role'] == 'faculty':
        course = Course.query.get(course_id)
        if not course:
            flash('Course not found!')
            return redirect(url_for('teacher_dashboard'))

        # Query submissions and include related student and assignment data
        submissions = Submission.query.join(Assignment).filter(Assignment.course_id == course_id).all()

        return render_template('faculty_performance.html', course=course, submissions=submissions)

    flash('Access denied!')
    return redirect(url_for('login'))



# View Analytics
@app.route('/analytics')
def analytics():
    if 'role' in session and session['role'] == 'admin':
        student_count = Student.query.count()
        faculty_count = Faculty.query.count()
        course_count = Course.query.count()
        return render_template('analytics.html', student_count=student_count, faculty_count=faculty_count, course_count=course_count)
    flash('Access denied!')
    return redirect(url_for('login'))

# Manage FAQs
@app.route('/manage_faqs', methods=['GET', 'POST'])
def manage_faqs():
    if 'role' in session and session['role'] == 'admin':
        faqs = FAQ.query.all()
        print(FAQ.query.all())
        if request.method == 'POST':
            question = request.form['question']
            answer = request.form['answer']

            new_faq = FAQ(question=question, answer=answer)
            db.session.add(new_faq)
            db.session.commit()
            flash('FAQ added successfully!')

        return render_template('manage_faqs.html', faqs=faqs)
    flash('Access denied!')
    return redirect(url_for('login'))


# Database Management
@app.route('/database_management')
def database_management():
    if 'role' in session and session['role'] == 'admin':
        return render_template('database_management.html')
    flash('Access denied!')
    return redirect(url_for('login'))


# Resources
# Resources
@app.route('/resources', methods=['GET', 'POST'])
def resources():
    if 'role' not in session or session['role'] not in ['faculty', 'student']:
        flash('Access denied!')
        return redirect(url_for('login'))
    
    courses = Course.query.all()  # Retrieve all courses for the dropdown
    
    if request.method == 'POST' and session['role'] == 'faculty':
        # Handle resource upload
        course_id = request.form['course_id']
        title = request.form['title']
        description = request.form['description']
        file = request.files['file'] if 'file' in request.files else None

        # Validate course
        course = Course.query.get(course_id)
        if not course:
            flash('Invalid course selected.')
            return redirect(url_for('resources'))

        # Save the file
        file_path = None
        if file:
            file_dir = 'static/resources'
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)  # Create directory if it doesn't exist
            file_path = os.path.join(file_dir, file.filename)
            file.save(file_path)

        # Add the resource to the database
        new_resource = Resource(course_id=course_id, title=title, description=description, file_path=file_path)
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource uploaded successfully!')

    if session['role'] == 'student':
        # Retrieve resources for the student's courses
        student_courses = [course.id for course in Course.query.filter(Course.students.any(id=session['user_id'])).all()]
        resources = Resource.query.filter(Resource.course_id.in_(student_courses)).all()
    elif session['role'] == 'faculty':
        # Retrieve resources for courses the faculty is assigned to
        resources = Resource.query.join(Course).filter(Course.faculty_id == session['user_id']).all()
    else:
        # Admin or other roles can view all resources
        resources = Resource.query.all()

    return render_template('resources.html', resources=resources, courses=courses)


from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import tensorflow as tf
import pickle
import numpy as np
import random
import json

# Load model and components
model = tf.keras.models.load_model("chatbot_model.h5")
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)
with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

# Load intents data
with open("lms.json") as file:
    data = json.load(file)

@app.route("/chatbot.html", methods=["GET", "POST"])
def chatbot():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Please provide a message."})
    
    # Preprocess user input
    X_input = vectorizer.transform([user_input]).toarray()
    
    # Predict
    prediction = model.predict(X_input)
    predicted_tag = label_encoder.inverse_transform([np.argmax(prediction)])
    
    # Get response
    for intent in data["intents"]:
        if intent["tag"] == predicted_tag[0]:
            response = random.choice(intent["responses"])
            return jsonify({"response": response})

    return jsonify({"response": "I am not sure how to respond to that."})



from werkzeug.utils import secure_filename
import os

# Ensure upload folder exists
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'submissions')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'png', 'jpg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    if 'role' in session and session['role'] == 'student':
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            flash('Assignment not found!')
            return redirect(url_for('assignments'))

        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part!')
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                flash('No selected file!')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Save the submission to the database
                new_submission = Submission(
                    assignment_id=assignment_id,
                    student_id=session['user_id'],
                    content=filename  # Store only the filename
                )
                db.session.add(new_submission)
                db.session.commit()

                flash('Assignment submitted successfully!')
                return redirect(url_for('assignments'))
            else:
                flash('Invalid file type!')
                return redirect(request.url)

        return render_template('submit_assignment.html', assignment=assignment)

    flash('Access denied!')
    return redirect(url_for('login'))



# Routes for Teacher Assignment Management
@app.route('/teacher/assignments', methods=['GET', 'POST'])
def teacher_assignments():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            due_date = request.form['due_date']
            course_id = request.form['course_id']

            course = Course.query.get(course_id)
            if not course or course.faculty_id != session['user_id']:
                flash('Invalid course selected or you are not authorized.')
                return redirect(url_for('teacher_assignments'))

            new_assignment = Assignment(title=title, description=description, due_date=due_date, course_id=course_id)
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!')

        assignments = Assignment.query.join(Course).filter(Course.faculty_id == session['user_id']).all()
        courses = Course.query.filter_by(faculty_id=session['user_id']).all()
        return render_template('teacher_assignments.html', assignments=assignments, courses=courses)

    flash('Access denied!')
    return redirect(url_for('login'))

@app.route('/teacher/submissions/<int:assignment_id>', methods=['GET', 'POST'])
def view_submissions(assignment_id):
    if 'role' in session and session['role'] == 'faculty':
        assignment = Assignment.query.get(assignment_id)
        if not assignment or assignment.course.faculty_id != session['user_id']:
            flash('Invalid assignment or you are not authorized.')
            return redirect(url_for('teacher_assignments'))

        if request.method == 'POST':
            submission_id = request.form['submission_id']
            grade = request.form['grade']
            submission = Submission.query.get(submission_id)
            if submission:
                submission.grade = grade
                db.session.commit()
                flash('Grade updated successfully!')

        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        return render_template('view_submissions.html', assignment=assignment, submissions=submissions)

    flash('Access denied!')
    return redirect(url_for('login'))


import os
from flask import send_from_directory

# Define the folder where submission files are stored
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'submissions')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# from werkzeug.utils import secure_filename

# @app.route('/view_submission/<filename>')
# def view_submission(filename):
#     filename = secure_filename(filename)  # Sanitize the filename
#     try:
#         return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
#     except FileNotFoundError:
#         flash('File not found!')
#         return redirect(request.referrer)

import os

@app.route('/view_submission/<filename>')
def view_submission(filename):
    from werkzeug.utils import secure_filename
    filename = secure_filename(filename)  # Sanitize filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        flash('File not found!')
        return redirect(request.referrer)

    # Check file extension to determine how to handle it
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension in ['.txt', '.csv', '.html']:
        # Render text-based files
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('view_text_file.html', content=content, filename=filename)

    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
        # Render image files
        return render_template('view_image_file.html', file_url=url_for('static', filename=f'submissions/{filename}'))

    elif file_extension in ['.pdf']:
        # Embed PDF files
        return render_template('view_pdf_file.html', file_url=url_for('static', filename=f'submissions/{filename}'))

    else:
        # For unsupported formats, provide a download option
        return redirect(url_for('static', filename=f'submissions/{filename}'))



if __name__ == '__main__':
    db.create_all()
    # Prepopulate admin credentials
    if not Admin.query.filter_by(name='admin').first():
        admin_password = bcrypt.generate_password_hash('admin').decode('utf-8')
        new_admin = Admin(name='admin', password='admin')
        db.session.add(new_admin)
        db.session.commit()
    app.run(debug=True)

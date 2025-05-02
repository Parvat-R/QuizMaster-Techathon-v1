import datetime
from flask import (
    Blueprint, request, jsonify, session,
    redirect, url_for, render_template, flash,
    get_flashed_messages
)
from models.models import Student, Session
from models.handler import Handler, StudentHandler, SessionHandler

bp = Blueprint('student', __name__, url_prefix='/student')

handler = Handler()
student_handler = StudentHandler(handler)
session_handler = SessionHandler(handler)

@bp.before_request
def before_request():
    if request.endpoint in ['static', 'student.login', 'student.register', 'student.logout']:
        return
    session_id = session.get('session_id', None)
    user_id = session.get('user_id', None)
    ip_address =  request.remote_addr if request.remote_addr else '-1'
    if (user_id and session_id) and session_handler.check_session(session_id, user_id, ip_address):
        session['session_id'] = session_id
        session['user_id'] = user_id
        
        user_type = session.get('user_type', None)
    
        if user_type != 'student':
            return redirect(url_for('student.login'))
    
        student = student_handler.get_student(user_id)
        if not student:
            return redirect(url_for('student.login'))
        
        session['user_data'] = student    
    else:
        return redirect(url_for('student.login'))

@bp.after_request
def after_request(response):
    session.pop("user_data", None)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('student/login.html')
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if student_handler.match_username_password(username, password):
            student = student_handler.get_student_from_username(username)
            
            if not student:
                return render_template('student/login.html', error='Invalid username or password')
            
            session_id = session_handler.create_session(student['id'])
            session['session_id'] = session_id
            ip_address = request.remote_addr if request.remote_addr else '-1'
            
            _session = Session(
                user_id=student['id'],
                user_type='student',
                created_on=datetime.datetime.now(),
                ip_address=ip_address
            )
            
            session["session_id"] = session_handler.create_session(_session)
            
            return redirect(url_for('student.index'))
        
        return render_template('student/login.html', error='Invalid username or password')
    
    return render_template('student/login.html')

@bp.route('/logout')
def logout():
    session_id = session.pop('session_id', None)
    session_handler.delete_session(session_id)
    session.clear()
    return redirect(url_for('student.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('student/register.html')
    elif request.method == 'POST':
        student = Student(
            username=request.form['username'],
            password=request.form['password'],
            name=request.form['name'],
            email=request.form['email'],
            dob=request.form['dob'],
            created_on=datetime.datetime.now()
        )
        
        # Student Data Validation
        if student_handler.student_username_exists(student.username):
            return render_template('student/register.html', error='Username already exists')
        if student_handler.student_email_exists(student.email):
            return render_template('student/register.html', error='Email already exists')
        
        if student_handler.create_student(student):
            flash('Registration successful!', 'success')
            return redirect(url_for('student.login'))
        return render_template('student/register.html', error='Registration failed! Could not insert student!')
    return render_template('student/register.html')

@bp.route('/')
def index():    
    return render_template('student/index.html')
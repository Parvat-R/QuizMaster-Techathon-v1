import datetime
from flask import (
    Blueprint, request, jsonify, session,
    redirect, url_for, render_template, flash,
    get_flashed_messages
)
from models.models import Teacher, Session
from models.handler import Handler, TeacherHandler, SessionHandler

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

handler = Handler()
teacher_handler = TeacherHandler(handler)
session_handler = SessionHandler(handler)


@bp.before_request
def before_request():
    if request.endpoint in ['static', 'teacher.login', 'teacher.register', 'teacher.logout']:
        return
    session_id = session.get('session_id', None)
    user_id = session.get('user_id', None)
    ip_address =  request.remote_addr if request.remote_addr else '-1'
    if (user_id and session_id) and session_handler.check_session(session_id, user_id, ip_address):
        session['session_id'] = session_id
        session['user_id'] = user_id
        
        user_type = session.get('user_type', None)
        if user_type != 'teacher':
            return redirect(url_for('teacher.login'))
    
        teacher = teacher_handler.get_teacher(user_id)
        if not teacher:
            return redirect(url_for('teacher.login'))
        
        session['user_data'] = teacher    
    else:
        return redirect(url_for('teacher.login'))

@bp.after_request
def after_request(response):
    session.pop("user_data", None)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('teacher/login.html')
    
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if teacher_handler.match_username_password(username, password):
            teacher = teacher_handler.get_teacher_from_username(username)
            
            if not teacher:
                return render_template('teacher/login.html', error='Invalid username or password')
            
            session_id = session_handler.create_session(teacher['id'])
            session['session_id'] = session_id
            ip_address = request.remote_addr if request.remote_addr else '-1'
            
            _session = Session(
                user_id=teacher['id'],
                user_type='teacher',
                created_on=datetime.datetime.now(),
                ip_address=ip_address
            )
            
            session["session_id"] = session_handler.create_session(_session)
            
            return redirect(url_for('teacher.index'))
        
        return render_template('teacher/login.html', error='Invalid username or password')
    
    return render_template('teacher/login.html')

@bp.route('/logout')
def logout():
    session_id = session.pop('session_id', None)
    session_handler.delete_session(session_id)
    session.clear()
    return redirect(url_for('teacher.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('teacher/register.html')
    elif request.method == 'POST':
        teacher = Teacher(
            username=request.form['username'],
            password=request.form['password'],
            name=request.form['name'],
            email=request.form['email'],
            dob=request.form['dob'],
            created_on=datetime.datetime.now()
        )
        
        # teacher Data Validation
        if teacher_handler.teacher_username_exists(teacher.username):
            return render_template('teacher/register.html', error='Username already exists')
        if teacher_handler.teacher_email_exists(teacher.email):
            return render_template('teacher/register.html', error='Email already exists')
        
        if teacher_handler.create_teacher(teacher):
            flash('Registration successful!', 'success')
            return redirect(url_for('teacher.login'))
        return render_template('teacher/register.html', error='Registration failed! Could not insert teacher!')
    return render_template('teacher/register.html')

@bp.route('/')
def index():    
    return render_template('teacher/index.html')
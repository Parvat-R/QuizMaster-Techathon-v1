import datetime
from flask import (
    Blueprint, request, jsonify, session,
    redirect, url_for, render_template, flash,
    get_flashed_messages
)
from models.models import Student, Session, Result
from models.handler import Handler, StudentHandler, ResultHandler, ClassHandler, QuizHandler, QuestionHandler, SessionHandler

bp = Blueprint('student', __name__, url_prefix='/student')

handler = Handler()
student_handler = StudentHandler(handler)
session_handler = SessionHandler(handler)
quiz_handler = QuizHandler(handler)
question_handler = QuestionHandler(handler)
class_handler = ClassHandler(handler)
result_handler = ResultHandler(handler)

@bp.before_request
def before_request():
    if request.endpoint in ['static', 'student.login', 'student.register']:
        return
    print(request.endpoint)
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
        return None
    else:
        return redirect(url_for('student.login'))

@bp.after_request
def after_request(response):
    session.pop("user_data", None)
    return response  # Return the response object

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
            
            ip_address = request.remote_addr if request.remote_addr else '-1'
            
            _session = Session(
                user_id=student['student_id'],
                user_type='student',
                created_on=datetime.datetime.now(),
                ip_address=ip_address
            )
            
            session["session_id"] = session_handler.create_session(_session)
            session["user_id"] = student['student_id']  # Added missing user_id in session
            session["user_type"] = "student"    # Added missing user_type in session
            
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
        try:
            dob = datetime.datetime.fromisoformat(request.form['dob'])  # Fixed date format
        except ValueError:
            return render_template('student/register.html', error='Invalid date format. Use dd-mm-yyyy')
            
        student = Student(
            username=request.form['username'],
            password=request.form['password'],
            name=request.form['name'],
            email=request.form['email'],
            dob=dob,
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
    classes = []
    for class_ in class_handler.get_student_classes(session['user_id']):
        classes.append(
            class_handler.get_class(class_)
        )
    student = student_handler.get_student(session['user_id'])
    return render_template('student/index.html', classes=classes, student=student)

@bp.route('/class/<class_id>')
def class_with_id(class_id):
    class_obj = class_handler.get_class(class_id)
    if class_obj is None:
        flash(f"Class #{class_id} not found!", "error")
        return redirect(url_for("student.index"))  # Fixed redirect
    
    quizzes = []
    
    user_id = session['user_id']
    attended_quizzes = quiz_handler.get_student_class_quizzes(user_id, class_id)
    
    for _quiz in quiz_handler.get_student_class_quizzes(user_id, class_id):
        _quiz = quiz_handler.get_quiz(_quiz)
        if _quiz:
            _quiz['attended'] = _quiz.get('quiz_id') in attended_quizzes
            quizzes.append(
                _quiz
            )
    
    return render_template('student/class.html', class_=class_obj, quizzes=quizzes)  # Added quizzes to template


@bp.route("/class/join", methods = ['POST'])
def class_join():
    class_id = request.form.get("class_id", None)
    if class_id and class_handler.get_class(class_id):
        if session['user_id'] not in class_handler.get_class_students(class_id):
            class_handler.add_student_to_class(class_id, session['user_id'])
            flash("Class joined!")
        else:
            flash("Already in class!", 'warning')
        return redirect(url_for('student.index'))
    flash(f"Could not join class #{class_id}")
    return redirect(url_for("student.index"))

@bp.route('/attend')
def attend_quiz():
    return render_template("student/attend_quiz.html")


# @bp.route('/quiz/<quiz_id>')
# def quiz(quiz_id):
#     quiz = quiz_handler.get_quiz(quiz_id)
#     questions = []
    
#     if not quiz:
#         flash(f"Quiz #{quiz_id} not found!", "error")
#         return redirect(url_for('student.index'))
    
#     for question_id in quiz_handler.get_quiz_questions(quiz_id):
#         questions.append(question_handler.get_question(question_id))
    
#     if session['user_id'] in result_handler.get_quiz_attended_students(quiz_id):
#         student_result = result_handler.get_result_by_student_and_quiz(session['user_id'], quiz_id)
#         student_result = { i.question_id: i.option_id for i in student_result }
#         return render_template('student/quiz_submit.html', quiz=quiz, questions = questions, student_result=student_result)
    
#     return render_template('student/quiz.html', quiz=quiz, questions=questions)


@bp.route('/quiz/<quiz_id>')
def quiz(quiz_id):
    quiz = quiz_handler.get_quiz(quiz_id)
    
    if not quiz:
        flash(f"Quiz #{quiz_id} not found!", "error")
        return redirect(url_for('student.index'))
    
    # Get all questions for this quiz
    questions = []
    for question_id in quiz_handler.get_quiz_questions(quiz_id):
        questions.append(question_handler.get_question(question_id))
    
    # Check if student has already taken this quiz
    if session['user_id'] in result_handler.get_quiz_attended_students(quiz_id):
        # Get student's results and format them as a dictionary for easy lookup
        results = result_handler.get_result_by_student_and_quiz(session['user_id'], quiz_id)
        student_result = {result['question_id']: result['option_id'] for result in results}
        
        return render_template('student/quiz_submit.html', 
                              quiz=quiz, 
                              questions=questions,
                              student_result=student_result)
    
    # If student hasn't taken the quiz yet, show the quiz taking page
    return render_template('student/quiz.html', quiz=quiz, questions=questions)


@bp.route('/quiz/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    quiz = quiz_handler.get_quiz(quiz_id)
    
    if not quiz:
        flash(f'Quiz #{quiz_id} does not exist!', 'error')
        return redirect(url_for('student.index'))
    
    questions = []
    
    for question_id in quiz_handler.get_quiz_questions(quiz_id):
        questions.append(question_handler.get_question(question_id))
    
    answers = []
    for question in questions:
        question_id = question['question_id']  # Accessing question id properly
        option_id = request.form.get(str(question_id))
        
        if option_id is None:
            flash(f'Please answer question {question_id}!', 'error')
            return redirect(url_for('student.quiz', quiz_id=quiz_id))
        
        answers.append(option_id)
        
        result = Result(
            student_id=session['user_id'],
            quiz_id=quiz_id,
            question_id=question_id,
            option_id=option_id,
            marks=0,  # You might want to calculate marks here
            created_on=datetime.datetime.now()
        )
        result_handler.create_result(result)
    
    return redirect(url_for('student.quiz', quiz_id=quiz_id))
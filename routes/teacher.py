from datetime import datetime
from flask import (
    Blueprint, request, jsonify, session,
    redirect, url_for, render_template, flash,
    get_flashed_messages
)
from utils import generate_uuid
from utils.gemini_api_old import generate_quiz_questions, create_quiz_prompt, process_questions
from models.models import MCQType, Teacher, Session, Class, Question, Quiz, QuizPrompt, TrueOrFalseType
from models.handler import Handler, StudentHandler, TeacherHandler, SessionHandler, ResultHandler, ClassHandler, QuizHandler, QuestionHandler

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

handler = Handler()
teacher_handler = TeacherHandler(handler)
student_handler = StudentHandler(handler)
session_handler = SessionHandler(handler)
quiz_handler = QuizHandler(handler)
question_handler = QuestionHandler(handler)
class_handler = ClassHandler(handler)
result_handler = ResultHandler(handler)



""" WRAPPER FUNCTIONS """
@bp.before_request
def before_request():
    if request.endpoint in ['static', 'teacher.login', 'teacher.register']:
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
    return response



""" USER FUNCTIONS"""
@bp.route('/')
def index():
    teacher_id = session['user_id']
    teacher = session['user_data']
    
    if not teacher:
        teacher = teacher_handler.get_teacher(teacher_id)
    
    classes = [class_handler.get_class(i) for i in  class_handler.get_teacher_classes(teacher_id)]
    
    return render_template('teacher/index.html', classes = classes, teacher = teacher)


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
            
            ip_address = request.remote_addr if request.remote_addr else '-1'
            
            _session = Session(
                user_id=teacher['teacher_id'],
                user_type='teacher',
                created_on=datetime.now(),
                ip_address=ip_address
            )
            session["session_id"] = session_handler.create_session(_session)
            session["user_id"] = teacher['teacher_id']
            session["user_type"] = 'teacher'

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
        print(datetime.fromisoformat)
        teacher = Teacher(
            username=request.form['username'],
            password=request.form['password'],
            name=request.form['name'],
            email=request.form['email'],
            dob=datetime.fromisoformat(request.form['dob']), #request.form['dob'],
            created_on=datetime.now()
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




""" CLASS FUNCTIONS """
@bp.route('/class/<class_id>')
def class_with_id(class_id):
    
    if (class_ := class_handler.get_class(class_id)) is None:
        flash(f"Class #{class_id} not found!", "error")
        return redirect("teacher.index")
    
    quizzes = []
    for _quiz in quiz_handler.get_teacher_class_quizzes(session['user_id'], class_id):
        if _quiz:
            quizzes.append(
                quiz_handler.get_quiz(_quiz)
            )
     
    return render_template('teacher/class.html', class_ = class_, quizzes = quizzes)


@bp.route('/class/create', methods = ['POST'])
def class_create():
    students = request.form['students'].split(',')
    for i in students:
        if not student_handler.get_student_from_username(i):
           students.remove(i)
            
    new_class = Class(
        class_id=generate_uuid(),
        name=request.form['name'],
        teacher_id=session['user_id'],
        created_on=datetime.now(),
        students=students
    )
    
    result = class_handler.create_class(new_class)
    if result:
        return redirect(url_for('teacher.index'))
    return {
        "error": "error"
    }
    

@bp.route('/class/delete', methods = ['DELETE'])
def class_delete():
    class_id = request.form.get('class_id')
    if class_id and (class_ := class_handler.get_class(class_id)):
        class_handler.class_delete(class_id)
        return {
            "success": True,
            "class_": class_
        }
        
    return {
        'success': False
    }
    
@bp.route('/class/<class_id>/add_student', methods = ['POST'])
def class_add_student(class_id):
    student_username = request.form.get('username', None)
    if not student_username:
        flash(f'Student @{student_username} not found!', 'error')
        return redirect(url_for('teacher.class_with_id', class_id=class_id))
    if not student_handler.get_student_from_username(student_username):
        return redirect(url_for('teacher.class_with_id', class_id=class_id))
    class_handler.add_student_to_class(class_id, student_username)
    return redirect(url_for('teacher.class_with_id', class_id=class_id))
    


""" QUIZ FUNCTIONS """
# @bp.route('/quiz/<quiz_id>')
# def quiz(quiz_id):
#     quiz = quiz_handler.get_quiz(quiz_id)
#     questions = []
    
#     if not quiz:
#         return redirect(url_for('teacher.index'))
    
#     for question_id in quiz_handler.get_quiz_questions(quiz_id):
#         questions.append(question_handler.get_question(question_id))
    
#     return render_template('teacher/quiz.html', quiz = quiz, questions = questions)

@bp.route('/quiz/<quiz_id>')
def quiz(quiz_id):
    quiz = quiz_handler.get_quiz(quiz_id)
    questions = []
    
    if not quiz:
        return redirect(url_for('teacher.index'))
    
    question_data = {}
    
    for question_id in quiz_handler.get_quiz_questions(quiz_id):
        _q = question_handler.get_question(question_id)
        questions.append(_q)
        question_data[question_id] = _q
    
    # Get students who have attended this quiz
    student_ids = result_handler.get_quiz_attended_students(quiz_id)
    
    # Group results by student for easier processing in template
    students_with_results = {}
    for student_id in student_ids:
        # Get student details from student handler
        student = student_handler.get_student(student_id)
        if not student:
            continue
            
        # Get all results for this student on this quiz
        student_answers = list(result_handler.get_result_by_student_and_quiz(student_id, quiz_id))
        
        # Calculate correct answers for this student
        correct_answers = 0
        for answer in student_answers:
            question = question_data.get(answer['question_id'])
            if question:
                if question['type'] == 'mcq':
                    s_options = [i['option_id'] for i in result_handler.get_result_by_student_and_question(student_id, answer['question_id'])]
                    if s_options == question['data']['correct_options']:
                        correct_answers += 1
                elif question['type'] == 'trueorfalse':
                    if (answer['option_id'] == 'true' and question['data']['answer'] == True) or \
                       (answer['option_id'] == 'false' and question['data']['answer'] == False):
                        correct_answers += 1
        
        students_with_results[student_id] = {
            'name': student.get('name'),
            'results': student_answers,
            'correct_answers': correct_answers,
            'total_questions': len(questions)
        }
    
    return render_template('teacher/quiz.html', 
                          quiz=quiz, 
                          questions=questions, 
                          students=students_with_results)
    

@bp.get('/quiz/create/<class_id>')
def quiz_create(class_id):
    class_ = class_handler.get_class(class_id)
    return render_template('teacher/quiz_create.html', class_ = class_)

@bp.route('/quiz/create/<class_id>', methods=['POST'])
def quiz_create_post(class_id):
    # Check if request is JSON
    if not request.is_json:
        if request.content_type and 'application/json' not in request.content_type:
            flash('Invalid content type. Expected JSON data.', 'error')
            return redirect(url_for('teacher.quiz_create'))
        return jsonify({'error': 'Expected JSON data'}), 400
    
    try:
        # Get quiz data from request
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['title', 'description', 'questions']):
            return jsonify({'error': 'Missing required fields (title, description, questions)'}), 400
        
        # Create Quiz object
        new_quiz = Quiz(
            quiz_id=generate_uuid(),
            title=data['title'],
            description=data['description'],
            teacher_id=session.get('user_id', ''),
            created_on=datetime.now(),
            class_id=class_id,
            question_ids=[]  # We'll add questions later
        )
        
        # Create the quiz first
        quiz_id = quiz_handler.create_quiz(new_quiz)
        if not quiz_id:
            return jsonify({'error': 'Failed to create quiz'}), 500
        
        # Process each question
        questions_data = data['questions']
        question_ids = []
        
        for q_id, q_data in questions_data.items():
            # Validate question data
            if not all(key in q_data for key in ['title', 'type']):
                continue  # Skip invalid questions
            
            # For MCQ questions
            if q_data['type'] == 'mcq':
                if not all(key in q_data for key in ['options', 'correct_options']):
                    continue  # Skip if missing required MCQ fields
                
                # Convert options from array to dictionary format as required by the model
                options_dict = {}
                for option in q_data['options']:
                    options_dict[option['opt_id']] = option['opt_val']
                
                # Create MCQType data
                question_data = MCQType(
                    title=q_data['title'],
                    options=options_dict,
                    correct_options=q_data['correct_options']
                )
                
                # Create Question object
                new_question = Question(
                    created_by=session.get('user_id', ''),
                    created_on=datetime.now(),
                    marks=q_data.get('marks', 1.0),  # Default mark value if not provided
                    type='mcq',
                    data=question_data
                )
                
                # Save the question
                question_id = question_handler.create_question(new_question)
                if question_id:
                    question_ids.append(question_id)
                    # Add question to quiz
                    quiz_handler.add_question_to_quiz(quiz_id, question_id)
            
            # Add support for True/False questions
            elif q_data['type'] == 'trueorfalse':
                if 'answer' not in q_data:
                    continue  # Skip if missing required trueorfalse fields
                
                # Create TrueOrFalseType data
                question_data = TrueOrFalseType(
                    title=q_data['title'],
                    answer=bool(q_data['answer'])
                )
                
                # Create Question object
                new_question = Question(
                    created_by=session.get('user_id', ''),
                    created_on=datetime.now(),
                    marks=q_data.get('marks', 1.0),  # Default mark value if not provided
                    type='trueorfalse',
                    data=question_data
                )
                
                # Save the question
                question_id = question_handler.create_question(new_question)
                if question_id:
                    question_ids.append(question_id)
                    # Add question to quiz
                    quiz_handler.add_question_to_quiz(quiz_id, question_id)
        
        # Check if class_id was provided and add it to the quiz
        if 'class_id' in data and data['class_id']:
            quiz_handler.add_class_to_quiz(quiz_id, data['class_id'])
        
        # Set quiz visibility
        if 'public' in data:
            quiz_handler.set_public(quiz_id, bool(data['public']))
        
        # Add excluded students if provided
        if 'excluded_students_id' in data and isinstance(data['excluded_students_id'], list):
            for student_username in data['excluded_students_id']:
                quiz_handler.add_excluded_student_to_quiz(quiz_id, student_username)
        
        # Return success response with quiz ID
        return jsonify({
            'success': True,
            'message': 'Quiz created successfully',
            'id': quiz_id,
            'question_count': len(question_ids)
        }), 201
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating quiz: {str(e)}")
        return jsonify({'error': f'Failed to create quiz: {str(e)}'}), 500


@bp.route('/quiz/edit/<quiz_id>', methods=['GET', 'POST'])
def quiz_edit(quiz_id):
    # GET request - render the edit page with quiz data
    if request.method == 'GET':
        # Get the quiz data
        quiz = quiz_handler.get_quiz(quiz_id)
        if not quiz:
            flash('Quiz not found', 'error')
            return redirect(url_for('teacher.quizzes'))
        
        # Get class information
        class_ = class_handler.get_class(quiz['class_id'])
        
        # Get all questions for this quiz
        questions = {}
        for q_id in quiz['question_ids']:
            question = question_handler.get_question(q_id)
            if question:
                questions[q_id] = question
        
        return render_template('teacher/quiz_edit.html', quiz=quiz, questions=questions, class_=class_)
    
    # POST request - update the quiz
    elif request.method == 'POST':
        # Check if request is JSON
        if not request.is_json:
            if request.content_type and 'application/json' not in request.content_type:
                flash('Invalid content type. Expected JSON data.', 'error')
                return redirect(url_for('teacher.quiz_edit', quiz_id=quiz_id))
            return jsonify({'error': 'Expected JSON data'}), 400
        
        try:
            # Get existing quiz
            existing_quiz = quiz_handler.get_quiz(quiz_id)
            if not existing_quiz:
                return jsonify({'error': 'Quiz not found'}), 404
            
            # Get quiz data from request
            data = request.get_json()
            
            # Validate required fields
            if not all(key in data for key in ['title', 'description', 'questions']):
                return jsonify({'error': 'Missing required fields (title, description, questions)'}), 400
            
            # Update basic quiz properties
            quiz_handler.update_quiz(quiz_id, {
                'title': data['title'],
                'description': data['description'],
                'public': data.get('public', existing_quiz.get('public', False))
            })
            
            # Get current question IDs
            old_question_ids = existing_quiz.get('question_ids', [])
            
            # Process each question
            questions_data = data['questions']
            new_question_ids = []
            
            for q_id, q_data in questions_data.items():
                # Validate question data
                if not all(key in q_data for key in ['title', 'type']):
                    continue  # Skip invalid questions
                
                question_id = None
                
                # Check if this is a new question or an existing one
                is_existing = q_id in old_question_ids
                
                # For MCQ questions
                if q_data['type'] == 'mcq':
                    if not all(key in q_data for key in ['options', 'correct_options']):
                        continue  # Skip if missing required MCQ fields
                    
                    # Convert options from array to dictionary format
                    options_dict = {}
                    for option in q_data['options']:
                        options_dict[option['opt_id']] = option['opt_val']
                    
                    # Create MCQType data
                    question_data = MCQType(
                        title=q_data['title'],
                        options=options_dict,
                        correct_options=q_data['correct_options']
                    )
                    
                    if is_existing:
                        # Update existing question
                        question_handler.update_question(q_id, {
                            'marks': q_data.get('marks', 1.0),
                            'data': question_data.model_dump()
                        })
                        question_id = q_id
                    else:
                        # Create new Question object
                        new_question = Question(
                            created_by=session.get('user_id', ''),
                            created_on=datetime.now(),
                            marks=q_data.get('marks', 1.0),
                            type='mcq',
                            data=question_data
                        )
                        # Save the question
                        question_id = question_handler.create_question(new_question)
                
                # Add support for True/False questions
                elif q_data['type'] == 'trueorfalse':
                    if 'answer' not in q_data:
                        continue  # Skip if missing required trueorfalse fields
                    
                    # Create TrueOrFalseType data
                    question_data = TrueOrFalseType(
                        title=q_data['title'],
                        answer=bool(q_data['answer'])
                    )
                    
                    if is_existing:
                        # Update existing question
                        question_handler.update_question(q_id, {
                            'marks': q_data.get('marks', 1.0),
                            'data': question_data.model_dump()
                        })
                        question_id = q_id
                    else:
                        # Create new Question object
                        new_question = Question(
                            created_by=session.get('user_id', ''),
                            created_on=datetime.now(),
                            marks=q_data.get('marks', 1.0),
                            type='trueorfalse',
                            data=question_data
                        )
                        # Save the question
                        question_id = question_handler.create_question(new_question)
                
                if question_id:
                    new_question_ids.append(question_id)
            
            # Update quiz with new question IDs
            quiz_handler.update_quiz(quiz_id, {'question_ids': new_question_ids})
            
            # Remove results for this quiz since it has been modified
            result_handler.delete_quiz_results(quiz_id)
            
            # Return success response
            return jsonify({
                'success': True,
                'message': 'Quiz updated successfully',
                'id': quiz_id,
                'question_count': len(new_question_ids)
            }), 200
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error updating quiz: {str(e)}")
            return jsonify({'error': f'Failed to update quiz: {str(e)}'}), 500

@bp.route('/api/generate-quiz', methods=['POST'])
def generate_quiz_endpoint():
    try:
        # Get data from request
        request_data = request.json
        
        if request_data is None:
            return jsonify({"error": "Invalid request data"}), 400
    
        teacher_id = session['user_id']
        
        if not teacher_id:
            return jsonify({"error": "Teacher ID is required"}), 400
        
        # Create quiz prompt from request data
        quiz_prompt_data = QuizPrompt(
            syllabus=request_data.get("syllabus", ""),
            tags=request_data.get("tags", []),
            image_data=request_data.get("image_data"),
            number_of_questions=request_data.get("number_of_questions", 5),
            hard_questions_percent=request_data.get("hard_questions_percent", 0.3),
            easy_questions_percent=request_data.get("easy_questions_percent", 0.7),
            mcq_questions_percent=request_data.get("mcq_questions_percent", 0.7),
            true_or_false_questions_percent=request_data.get("true_or_false_questions_percent", 0.3)
        )
        
        print(request_data, request_data.get("language"))
        # Create prompt for ChatGPT
        prompt = create_quiz_prompt(quiz_prompt_data, teacher_id, request_data.get("language", "english"))
        
        # Generate questions
        generated_questions = generate_quiz_questions(prompt)
        
        # Process and validate questions
        processed_questions = process_questions(generated_questions, teacher_id)
        
        return jsonify(processed_questions), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


from pymongo import MongoClient
from .models import Student, Teacher, Class, Quiz, Question, Result, Session
from utils import generate_uuid, hash_password
from datetime import datetime

class Handler:
    def __init__(self):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['database']
        self.teachers = self.db['teachers']
        self.students = self.db['students']
        self.classes = self.db['classes']
        self.quizzes = self.db['quizzes']
        self.questions = self.db['questions']
        self.results = self.db['results']
    
    def close(self):
        self.client.close()
        self.db.close()


class StudentHandler:
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.students
    
    def student_id_exists(self, student_id: str) -> bool:
        return bool(self.collection.find_one({'student_id': student_id}))
    
    def student_username_exists(self, username: str):
        return bool(self.collection.find_one({'username': username}))
    
    def student_email_exists(self, email: str):
        return bool(self.collection.find_one({'email': email}))
    
    def get_student(self, student_id: str):
        return self.collection.find_one({'student_id': student_id})
    
    def get_student_from_username(self, username: str):
        return self.collection.find_one({'username': username})
    
    def get_student_from_email(self, email: str):
        return self.collection.find_one({'email': email})
    
    def create_student(self, student: Student):
        student.student_id = generate_uuid()
        student.created_on = datetime.now()
        if self.student_username_exists(student.username):
            raise Exception('Username already exists')
        student.student_id = generate_uuid()
        student.password = hash_password(student.password)
        if self.collection.insert_one(student.model_dump()):
            return student.student_id
        return None
    
    def match_username_password(self, username: str, password: str):
        student = self.get_student_from_username(username)
        if not student:
            return False
        return student['password'] == hash_password(password)
    
    def match_email_password(self, email: str, password: str):
        student = self.get_student_from_email(email)
        if not student:
            return False
        return student['password'] == hash_password(password)
    
    
    def change_name(self, student_id: str, name: str):
        return self.collection.update_one({'student_id': student_id}, {'$set': {'name': name}})
    
    def change_password(self, student_id: str, password: str):
        return self.collection.update_one({'student_id': student_id}, {'$set': {'password': hash_password(password)}})


class TeacherHandler:
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.teachers
        
    def get_teacher(self, teacher_id: str):
        return self.collection.find_one({'teacher_id': teacher_id})
    
    def teacher_username_exists(self, username: str):
        return bool(self.collection.find_one({'username': username}))
    
    def teacher_email_exists(self, email: str):
        return bool(self.collection.find_one({'email': email}))
    
    def create_teacher(self, teacher: Teacher):
        teacher.teacher_id = generate_uuid()
        teacher.created_on = datetime.now()
        if self.teacher_username_exists(teacher.username):
            raise Exception('Username already exists')
        if self.teacher_email_exists(teacher.email):
            raise Exception('Email already exists')
        teacher.teacher_id = generate_uuid()
        teacher.password = hash_password(teacher.password)
        if self.collection.insert_one(teacher.model_dump()):
            return teacher.teacher_id
        return None

    
    def match_username_password(self, username: str, password: str):
        teacher = self.get_teacher_from_username(username)
        if not teacher:
            return False
        return teacher['password'] == hash_password(password)
    
    def match_email_password(self, email: str, password: str):
        teacher = self.get_teacher_from_email(email)
        if not teacher:
            return False
        return teacher['password'] == hash_password(password)
    
    def get_teacher_from_username(self, username: str):
        return self.collection.find_one({'username': username})
    
    def get_teacher_from_email(self, email: str):
        return self.collection.find_one({'email': email})
    
    def change_name(self, teacher_id: str, name: str):
        return self.collection.update_one({'teacher_id': teacher_id}, {'$set': {'name': name}})
    
    def change_password(self, teacher_id: str, password: str):
        return self.collection.update_one({'teacher_id': teacher_id}, {'$set': {'password': hash_password(password)}})
    
    
class SessionHandler:
    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.sessions = handler.db['sessions']
    
    def get_session(self, session_id: str) -> Session | None:
        return self.sessions.find_one({'session_id': session_id})
    
    def get_user_session(self, session_id: str) -> Session | None:
        session = self.get_session(session_id)
        if not session:
            return None
        return session
    
    def create_session(self, _session: Session):
        _session.session_id = generate_uuid()
        _session.created_on = datetime.now()
        if self.sessions.insert_one(_session.model_dump()):
            return _session.session_id
        return None
    
    def check_session(self, session_id: str, user_id, ip_address: str):
        return bool(self.sessions.find_one({'session_id': session_id, 'user_id': user_id, 'ip_address': ip_address}))
    
    def delete_session(self, session_id: str):
        return self.sessions.delete_one({'session_id': session_id})
    
    
class ClassHandler:
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.classes
    
    def get_class(self, class_id: str):
        return self.collection.find_one({'class_id': class_id})
    
    def create_class(self, class_: Class):
        class_.class_id = generate_uuid()
        if self.collection.insert_one(class_.model_dump()):
            return class_.class_id
        return None
    
    def change_class_name(self, class_id: str, name: str):
        return self.collection.update_one({'class_id': class_id}, {'$set': {'name': name}})
    
    def change_class_description(self, class_id: str, description: str):
        return self.collection.update_one({'class_id': class_id}, {'$set': {'description': description}})
    
    def add_student_to_class(self, class_id: str, student_id: str):
        return self.collection.update_one({'class_id': class_id}, {'$push': {'student_ids': student_id}})
    
    def get_class_students(self, class_id: str):
        if (a := self.collection.find_one({'class_id': class_id})):
            return a.get('student_ids')
    
    def remove_student_from_class(self, class_id: str, student_id: str):
        return self.collection.update_one({'class_id': class_id}, {'$pull': {'student_ids': student_id}})
    
    def get_student_classes(self, student_id: str):
        return self.collection.find({'student_ids': student_id}).distinct('class_id')
    
    def get_teacher_classes(self, teacher_id: str):
        return self.collection.find({'teacher_id': teacher_id}).distinct('class_id')

    def class_delete(self, class_id: str):
        return self.collection.delete_one({'class_id': class_id})
    
class QuizHandler:
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.quizzes
        
    def get_quiz(self, quiz_id: str):
        return self.collection.find_one({'quiz_id': quiz_id})
    
    def create_quiz(self, quiz: Quiz):
        quiz.quiz_id = generate_uuid()
        if self.collection.insert_one(quiz.model_dump()):
            return quiz.quiz_id
        return None
    
    def change_quiz_title(self, quiz_id: str, title: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$set': {'title': title}})
    
    def change_quiz_description(self, quiz_id: str, description: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$set': {'description': description}})
    
    def add_question_to_quiz(self, quiz_id: str, question_id: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$push': {'question_ids': question_id}})
    
    def get_quiz_questions(self, quiz_id: str):
        if (a := self.collection.find_one({'quiz_id': quiz_id})):
            return a.get('question_ids')
        else:
            return []
    
    def remove_question_from_quiz(self, quiz_id: str, question_id: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$pull': {'question_ids': question_id}})
    
    def add_class_to_quiz(self, quiz_id: str, class_id: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$set': {'class_id': class_id}})
    
    def get_quiz_class(self, quiz_id: str):
        if (a := self.collection.find_one({'quiz_id': quiz_id})):
            return a.get('class_id')
    
    def set_public(self, quiz_id: str, is_public: bool):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$set': {'is_public': is_public}})
    
    def add_excluded_student_to_quiz(self, quiz_id: str, student_id: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$push': {'excluded_student_ids': student_id}})
    
    def get_excluded_students(self, quiz_id: str):
        if (a := self.collection.find_one({'quiz_id': quiz_id})):
            return a.get('excluded_student_ids')
        
    def remove_excluded_student_from_quiz(self, quiz_id: str, student_id: str):
        return self.collection.update_one({'quiz_id': quiz_id}, {'$pull': {'excluded_student_ids': student_id}})

    def get_student_class_quizzes(self, student_id: str, class_id: str):
        return self.collection.find({'class_id': class_id, 'exclude': {'$ne': student_id}}).distinct('quiz_id')

    def get_teacher_class_quizzes(self, teacher_id: str, class_id: str):
        return self.collection.find({'class_id': class_id, 'teacher_id': teacher_id}).distinct('quiz_id')


class QuestionHandler:
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.questions

    def get_question(self, question_id: str):
        return self.collection.find_one({'question_id': question_id})
    
    def get_question_type(self, question_id: str):
        if (a := self.collection.find_one({'question_id': question_id})):
            return a.get('type')
    
    def set_question_data(self, question_id: str, data: dict):
        return self.collection.update_one({'question_id': question_id}, {'$set': {'data': data}})

    def get_question_data(self, question_id: str):
        if (a := self.collection.find_one({'question_id': question_id})):
            return a.get('data')
        
    def create_question(self, question: Question):
        question.question_id = generate_uuid()
        if self.collection.insert_one(question.model_dump()):
            return question.question_id
        else:
            return False
    
    def delete_question(self, question_id: str):
        return self.collection.delete_one({'question_id': question_id})
    
    def get_correct_answer(self, question_id: str):
        qtype = self.get_question_type(question_id)
        data = self.get_question_data(question_id)
        if data and qtype:
            if qtype == 'mcq':
                return data.get('correct_option')
            elif qtype == 'tf':
                return data.get('answer')
    
        return None

class ResultHandler :
    def __init__(self, handler: Handler):
        self.handler = handler
        self.collection = handler.results
        
    def create_result(self, result: Result):
        result.result_id = generate_uuid()
        return self.collection.insert_one(result.model_dump())
    
    def get_result(self, result_id: str):
        return self.collection.find_one({'result_id': result_id})
    
    def get_student_quiz_results(self, student_id: str, quiz_id: str):
        return self.collection.find({'student_id': student_id, 'quiz_id': quiz_id})
    
    def get_quiz_attended_students(self, quiz_id: str):
        return self.collection.find({'quiz_id': quiz_id}).distinct('student_id')
    
    def get_student_attended_quizzes(self, student_id: str):
        return self.collection.find({'student_id': student_id}).distinct('quiz_id')
    
    def get_class_attended_quizzes(self, class_id: str):
        return self.collection.find({'class_id': class_id}).distinct('quiz_id')
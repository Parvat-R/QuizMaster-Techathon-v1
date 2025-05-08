from typing import List, Dict, Union, Optional, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime


# --------------------------------------
# Type Definitions
# --------------------------------------

class MCQType(BaseModel):
    title: str
    options: Dict[str, str]
    correct_options: List[str]


class TrueOrFalseType(BaseModel):
    title: str
    answer: bool


QuestionDataType = Union[MCQType, TrueOrFalseType]


# --------------------------------------
# User Models
# --------------------------------------

class Student(BaseModel):
    student_id: str = ""
    username: str
    name: str
    email: EmailStr
    password: str
    dob: datetime  # Can be changed to datetime if stored that way
    created_on: datetime


class Teacher(BaseModel):
    teacher_id: str = ""
    username: str
    email: EmailStr
    name: str
    password: str
    dob: datetime  # Can be changed to datetime
    created_on: datetime


# --------------------------------------
# Class Model
# --------------------------------------

class Class(BaseModel):
    class_id: str = ""
    name: str
    created_on: datetime  # Can be datetime if parsed accordingly
    students: List[str]  # List of student_ids
    teacher_id: str = ""


# --------------------------------------
# Quiz Model
# --------------------------------------

class Quiz(BaseModel):
    quiz_id: str = ""
    title: str
    teacher_id: str = ""
    description: str
    class_id: str
    excluded_students_id: List[str] = []
    public: bool = False
    created_on: datetime
    question_ids: List[str] = []


# --------------------------------------
# Question Model
# --------------------------------------

class Question(BaseModel):
    question_id: str = ""
    created_by: str  # teacher_id
    created_on: datetime
    marks: float
    type: str  # Should be 'mcq' or 'trueorfalse'
    data: QuestionDataType


# --------------------------------------
# Result Model
# --------------------------------------
class Result(BaseModel):
    result_id: str = ""
    student_id: str = ""
    quiz_id: str = ""
    question_id: str = ""
    option_id: str = ""
    marks: float
    created_on: datetime
    

# --------------------------------------
# Result Model
# --------------------------------------
class Session(BaseModel):
    session_id: str = ""
    user_id: str
    user_type: str
    created_on: datetime
    ip_address: str



# --------------------------------------
# Prompt Model
# --------------------------------------
class QuizPrompt(BaseModel):
    syllabus: str
    tags: List[str]
    image_data: Optional[str] = None
    
    number_of_questions: int
    hard_questions_percent: float
    easy_questions_percent: float
    mcq_questions_percent: float
    true_or_false_questions_percent: float

from typing import Dict, List, Union, Optional, Any
import requests, uuid, json
from datetime import datetime
import os
from models.models import Question, QuizPrompt, QuestionDataType, MCQType, TrueOrFalseType
import google.generativeai as genai

def create_quiz_prompt(quiz_data: QuizPrompt, teacher_id: str) -> str:
    # Calculate the number of each type of question
    total_questions = quiz_data.number_of_questions
    hard_questions = int(total_questions * quiz_data.hard_questions_percent)
    easy_questions = int(total_questions * quiz_data.easy_questions_percent)
    # Adjust if rounding causes issues
    if hard_questions + easy_questions != total_questions:
        easy_questions = total_questions - hard_questions
    
    mcq_questions = int(total_questions * quiz_data.mcq_questions_percent)
    true_false_questions = int(total_questions * quiz_data.true_or_false_questions_percent)
    # Adjust if rounding causes issues
    if mcq_questions + true_false_questions != total_questions:
        mcq_questions = total_questions - true_false_questions
    
    # Create the prompt
    prompt = f"""
    Generate {total_questions} quiz questions based on the following syllabus:
    
    {quiz_data.syllabus}
    
    The questions should be distributed as follows:
    - Hard questions: {hard_questions} ({quiz_data.hard_questions_percent * 100}%)
    - Easy questions: {easy_questions} ({quiz_data.easy_questions_percent * 100}%)
    - Multiple Choice Questions: {mcq_questions} ({quiz_data.mcq_questions_percent * 100}%)
    - True/False Questions: {true_false_questions} ({quiz_data.true_or_false_questions_percent * 100}%)
    
    Tags to focus on: {', '.join(quiz_data.tags)}
    
    Return the questions in the following JSON format:
    {{
        "questions": {{
            "question_id1": {{
                "question_id": "unique_id",
                "created_by": "{teacher_id}",
                "created_on": "ISO datetime string",
                "marks": "points for this question (float)",
                "type": "mcq or trueorfalse",
                "data": {{
                    // For MCQ:
                    "title": "question text",
                    "options": {{"A": "option text", "B": "option text", ...}},
                    "correct_options": ["A", "B", ...] 
                    
                    // For True/False:
                    "title": "question text",
                    "answer": true or false
                }}
            }},
            // More questions...
        }}
    }}
    
    Make sure the questions are relevant to the syllabus and cover the topics thoroughly.
    Each MCQ should have 4 options (A, B, C, D) with at least one correct answer.
    The marks for each question should be between 1.0 and 5.0, with harder questions worth more points.
    """
    
    # Add image data if provided
    if quiz_data.image_data:
        prompt += f"""
        
        Use the following image data for context when creating relevant questions:
        {quiz_data.image_data}
        """
    
    return prompt


# Function to call Gemini API
def generate_quiz_questions(prompt: str) -> Dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not found in environment variables")
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # Use the Gemini 1.5 Pro model (Gemini's most capable model for quiz generation)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Configure generation parameters for better quiz creation
    generation_config = {
        "temperature": 0.7,  # Balance between creativity and consistency
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,  # Allow sufficient tokens for detailed quiz generation
        "response_mime_type": "application/json",  # Specify JSON response format
    }
    
    # Create system instructions for quiz generation
    system_instruction = """You are an expert educational content creator specializing in quiz generation. 
    Create high-quality, educationally sound quiz questions that accurately reflect the provided syllabus 
    and difficulty distribution. Format your response exactly as the JSON structure requested."""
    
    try:
        # Generate content with Gemini
        response = model.generate_content(
            [system_instruction, prompt],
            generation_config=generation_config
        )
        
        # Parse the JSON response
        content = response.text
        return json.loads(content)
    except Exception as e:
        raise Exception(f"Gemini API call failed: {str(e)}")


# Process the generated questions to ensure they match our model
def process_questions(generated_questions: Dict, teacher_id: str) -> Dict:
    questions = {}
    
    for question_id, question_data in generated_questions["questions"].items():
        # Ensure question_id is unique
        new_id = str(uuid.uuid4())
        
        # Convert string datetime to actual datetime object if needed
        if isinstance(question_data["created_on"], str):
            created_on = datetime.fromisoformat(question_data["created_on"].replace('Z', '+00:00'))
        else:
            created_on = datetime.now()
        
        # Process based on question type
        question_type = question_data["type"]
        
        if question_type == "mcq":
            data = MCQType(
                title=question_data["data"]["title"],
                options=question_data["data"]["options"],
                correct_options=question_data["data"]["correct_options"]
            )
        elif question_type == "trueorfalse":
            data = TrueOrFalseType(
                title=question_data["data"]["title"],
                answer=question_data["data"]["answer"]
            )
        else:
            # Skip invalid question types
            continue
        
        # Create the question object
        question = {
            "question_id": new_id,
            "created_by": teacher_id,
            "created_on": created_on.isoformat(),
            "marks": float(question_data["marks"]),
            "type": question_type,
            "data": question_data["data"]
        }
        
        questions[new_id] = question
    
    return {"questions": questions}
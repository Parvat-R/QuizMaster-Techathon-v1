from typing import Dict, List, Union, Optional, Any
import requests, uuid, json
from datetime import datetime
import os
from models.models import Question, QuizPrompt, QuestionDataType, MCQType, TrueOrFalseType

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


# Function to call ChatGPT API
def generate_quiz_questions(prompt: str) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-4-turbo",  # or your preferred model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates quiz questions based on syllabus content."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


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
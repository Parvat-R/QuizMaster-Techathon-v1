from typing import Dict, List, Union, Optional, Any, Tuple
import requests, uuid, json
from datetime import datetime
import os
from models.models import Question, QuizPrompt, QuestionDataType, MCQType, TrueOrFalseType
import google.generativeai as genai
import base64
from io import BytesIO
from PIL import Image

# Dictionary of supported languages with their ISO codes
SUPPORTED_LANGUAGES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "russian": "ru",
    "hindi": "hi",
    "bengali": "bn",
    "urdu": "ur",
    "swahili": "sw",
    "hebrew": "he",
    "turkish": "tr",
    "tamil": "ta",
    # Add more languages as needed
}

# Language-specific terms for quiz elements
LANGUAGE_TERMS = {
    "en": {
        "question": "Question",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "true": "True",
        "false": "False",
        "correct_answer": "Correct Answer",
        "hard": "Hard",
        "easy": "Easy",
        "medium": "Medium"
    },
    "es": {
        "question": "Pregunta",
        "option_a": "Opción A",
        "option_b": "Opción B",
        "option_c": "Opción C",
        "option_d": "Opción D",
        "true": "Verdadero",
        "false": "Falso",
        "correct_answer": "Respuesta Correcta",
        "hard": "Difícil",
        "easy": "Fácil",
        "medium": "Medio"
    },
    "fr": {
        "question": "Question",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "true": "Vrai",
        "false": "Faux",
        "correct_answer": "Réponse Correcte",
        "hard": "Difficile",
        "easy": "Facile",
        "medium": "Moyen"
    },
    # Add more languages with their terms
}

def get_language_code(language_name: str) -> str:
    """
    Get the ISO language code from a language name.
    Falls back to 'en' if the language is not supported.
    
    Args:
        language_name: The name of the language
        
    Returns:
        ISO language code
    """
    return SUPPORTED_LANGUAGES.get(language_name.lower(), "en")

def get_language_terms(language_code: str) -> Dict[str, str]:
    """
    Get language-specific terms for quiz elements.
    
    Args:
        language_code: ISO language code
        
    Returns:
        Dictionary of terms in the specified language
    """
    return LANGUAGE_TERMS.get(language_code, LANGUAGE_TERMS["en"])

def create_quiz_prompt(quiz_data: QuizPrompt, teacher_id: str, values_language: str = 'english') -> Tuple[str, str]:
    """
    Create a prompt for quiz generation in the specified language.
    
    Args:
        quiz_data: Quiz prompt data
        teacher_id: ID of the teacher
        values_language: Language for quiz content
        
    Returns:
        Tuple of (prompt, language_code)
    """
    # Get language code and terms
    language_code = get_language_code(values_language)
    
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
    Generate {total_questions} quiz questions in {values_language} based on the following syllabus:
    
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
                    "title": "question text in {values_language}",
                    "options": {{"A": "option text in {values_language}", "B": "option text in {values_language}", ...}},
                    "correct_options": ["A", "B", ...] 
                    
                    // For True/False:
                    "title": "question text in {values_language}",
                    "answer": true or false
                }},
                "difficulty": "easy or hard"
            }},
            // More questions...
        }}
    }}
    
    Make sure the questions are relevant to the syllabus and cover the topics thoroughly.
    Each MCQ should have 4 options (A, B, C, D) with at least one correct answer.
    The marks for each question should be between 1.0 and 5.0, with harder questions worth more points.
    
    ALL content inside the data field MUST be in {values_language}. Only the JSON keys (like "title", "options", etc.) should remain in English.
    """
    print(prompt)
    # Add image data if provided
    if quiz_data.image_data:
        prompt += f"""
        
        Use the following image for context when creating relevant questions
        """
    
    return prompt, language_code

def setup_genai():
    """Initialize Google Generative AI with the API key."""
    api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
    if not api_key:
        # Fallback to hardcoded key - not recommended for production
        api_key = "AIzaSyBiI0CTen-6R6rKcEJTm4rGWsjtu8dq4Ks"
    
    genai.configure(api_key=api_key)

def process_image(image_data_url: str) -> Union[BytesIO, None]:
    """
    Process image data from a data URL.
    Returns a BytesIO object or None if processing fails.
    """
    try:
        # Check if it's a data URL
        if image_data_url.startswith('data:image'):
            # Extract the base64 part
            image_base64 = image_data_url.split(',')[1]
            image_bytes = base64.b64decode(image_base64)
            return BytesIO(image_bytes)
        return None
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

def generate_quiz_questions(prompt: str, image_data: Optional[str] = None, language_code: str = "en") -> Dict[str, Any]:
    """
    Generate quiz questions using Google Generative AI.
    
    Args:
        prompt: The prompt for generating questions
        image_data: Optional base64 image data URL
        language_code: ISO language code to help model generate better responses
        
    Returns:
        Dictionary containing generated questions
    """
    try:
        # Setup Google Generative AI
        setup_genai()
        
        # List available models first to debug
        try:
            available_models = genai.list_models()
            print("Available models:")
            for model in available_models:
                print(f"- {model.name}")
        except Exception as e:
            print(f"Error listing models: {str(e)}")
        
        # Select the appropriate model - use the full model name with correct version
        # Update these model names according to the available models from list_models()
        text_model_name = "models/gemini-1.5-flash"  # Free tier model
        vision_model_name = "models/gemini-1.5-flash"  # Free tier model
        
        # Prepare generation config
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
        
        # Safety settings - allows educational content while maintaining safety
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # If image data is provided
        if image_data:
            # Process image
            image_bytes = process_image(image_data)
            if image_bytes:
                # Use the vision model
                model = genai.GenerativeModel(
                    vision_model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                image = Image.open(image_bytes)
                
                # Generate content with image
                response = model.generate_content([prompt, image])
            else:
                # Generate without image if processing failed
                model = genai.GenerativeModel(
                    text_model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                response = model.generate_content(prompt)
        else:
            # Generate without image
            model = genai.GenerativeModel(
                text_model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
        
        # Get the response text
        response_text = response.text
        print(response_text)
        # Parse the JSON response
        try:
            # The response might be wrapped in code blocks or have other formatting
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].strip()
            else:
                json_text = response_text
                
            # Parse the JSON
            quiz_data = json.loads(json_text)
            return quiz_data
            
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON-like content
            import re
            json_pattern = r'\{\s*"questions"\s*:\s*\{.*?\}\s*\}'
            match = re.search(json_pattern, response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse AI-generated response as JSON")
            else:
                raise ValueError("AI response did not contain valid JSON data")
    
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        raise

def validate_question(question: Dict[str, Any], language_code: str = "en") -> bool:
    """
    Validate a question to ensure it has the required fields and format.
    
    Args:
        question: The question dictionary to validate
        language_code: ISO language code for language-specific validation
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ["question_id", "created_by", "created_on", "marks", "type", "data"]
    if not all(field in question for field in required_fields):
        return False
    
    # Validate based on question type
    if question["type"] == "mcq":
        # Check MCQ-specific fields
        mcq_fields = ["title", "options", "correct_options"]
        if not all(field in question["data"] for field in mcq_fields):
            return False
        
        # Ensure options and correct_options are valid
        options = question["data"].get("options", {})
        correct_options = question["data"].get("correct_options", [])
        
        if not isinstance(options, dict) or len(options) < 2:
            return False
        
        if not isinstance(correct_options, list) or not correct_options:
            return False
        
        # Make sure all correct options exist in options
        if not all(opt in options for opt in correct_options):
            return False
            
    elif question["type"] == "trueorfalse":
        # Check True/False-specific fields
        tf_fields = ["title", "answer"]
        if not all(field in question["data"] for field in tf_fields):
            return False
        
        # Ensure answer is boolean
        if not isinstance(question["data"]["answer"], bool):
            return False
    else:
        # Invalid question type
        return False
    
    # Make sure marks is a number between 1.0 and 5.0
    try:
        marks = float(question["marks"])
        if marks < 1.0 or marks > 5.0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True

def process_questions(generated_data: Dict[str, Any], teacher_id: str, language_code: str = "en") -> Dict[str, Any]:
    """
    Process and validate the generated questions.
    
    Args:
        generated_data: The data generated by the AI
        teacher_id: The ID of the teacher creating the quiz
        language_code: ISO language code for language-specific processing
        
    Returns:
        Processed and validated questions
    """
    result = {"questions": {}}
    language_terms = get_language_terms(language_code)
    
    # Check if we have questions
    if not generated_data or "questions" not in generated_data:
        raise ValueError("No questions were generated")
    
    questions = generated_data["questions"]
    
    # Process each question
    for q_id, question in questions.items():
        # Ensure the question has a unique ID
        if "question_id" not in question:
            question["question_id"] = str(uuid.uuid4())
        
        # Set or correct the teacher ID
        question["created_by"] = teacher_id
        
        # Set or correct the creation timestamp
        if "created_on" not in question:
            question["created_on"] = datetime.utcnow().isoformat()
        
        # Add language code to metadata
        question["language"] = language_code
            
        # Validate the question
        if validate_question(question, language_code):
            result["questions"][q_id] = question
    
    # Ensure we have at least one valid question
    if not result["questions"]:
        raise ValueError("No valid questions were generated")
    
    return result

def save_questions_to_database(processed_questions: Dict[str, Any]) -> List[str]:
    """
    Save the processed questions to the database.
    
    Args:
        processed_questions: The processed and validated questions
    
    Returns:
        List of saved question IDs
    """
    saved_ids = []
    
    for q_id, q_data in processed_questions["questions"].items():
        try:
            # Create the appropriate question object based on type
            if q_data["type"] == "mcq":
                # Create MCQ question data
                question_data = MCQType(
                    title=q_data["data"]["title"],
                    options=q_data["data"]["options"],
                    correct_options=q_data["data"]["correct_options"]
                )
            else:  # trueorfalse
                # Create True/False question data
                question_data = TrueOrFalseType(
                    title=q_data["data"]["title"],
                    answer=q_data["data"]["answer"]
                )
            
            # Create the question object
            question = Question(
                question_id=q_data["question_id"],
                created_by=q_data["created_by"],
                created_on=datetime.fromisoformat(q_data["created_on"]),
                marks=float(q_data["marks"]),
                type=q_data["type"],
                data=question_data,
                # Add language as a new field
                language=q_data.get("language", "en")
            )
            
            # Save to database (actual implementation depends on your ORM/database)
            # db.session.add(question)
            # db.session.commit()
            
            saved_ids.append(q_data["question_id"])
            
        except Exception as e:
            print(f"Error saving question {q_id}: {str(e)}")
            continue
    
    return saved_ids

# Main integration function
def generate_quiz_in_language(quiz_data: QuizPrompt, teacher_id: str, values_language: str = 'english') -> Dict[str, Any]:
    """
    Generate a quiz in the specified language.
    
    Args:
        quiz_data: Quiz prompt data
        teacher_id: ID of the teacher
        values_language: Language for quiz content
        
    Returns:
        The generated quiz data
    """
    # Create prompt with language support
    prompt, language_code = create_quiz_prompt(quiz_data, teacher_id, values_language)
    
    # Generate questions
    generated_data = generate_quiz_questions(
        prompt, 
        quiz_data.image_data if hasattr(quiz_data, 'image_data') else None,
        language_code
    )
    
    # Process and validate questions
    processed_data = process_questions(generated_data, teacher_id, language_code)
    
    # Save to database
    saved_ids = save_questions_to_database(processed_data)
    
    return {
        "quiz_data": processed_data,
        "saved_question_ids": saved_ids,
        "language": values_language,
        "language_code": language_code
    }

# Function to check if language is supported
def is_language_supported(language: str) -> bool:
    """
    Check if a language is supported for quiz generation.
    
    Args:
        language: Language name to check
        
    Returns:
        True if supported, False otherwise
    """
    return language.lower() in SUPPORTED_LANGUAGES
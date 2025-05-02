## **Problem 2805**

Sustainable EduTech Solutions

### **Problem Statement**

QuizMaster is dedicated to enhancing assessment methods in education. Your challenge is to develop an AI-powered quiz generator that creates customized quizzes based on specific curriculum topics and student performance analytics. The tool should provide instant feedback to students and offer analytics for teachers to track progress.

## The main goal of the project

The app is designed to create custom quizzes using AI dynamically based on the given syllabus. If the important topics are given and the number of questions are given, we can have a custom prompt for that question that makes the LLM model generate the JSON response in the same schema.

Another main goal is to conduct quiz and organize the data and also to give the report to the teacher.

To make the project stand unique besides all the quiz apps already present, it aims to provide better user interactions along with better analytics and data organization

## How to generate quiz?

This is the main goal of the project and needs to be figured out first. There are two possible ways I can think of:

1. Create APIs by running LLMs locally using ollama.
2. Use the already existing APIs and to fetch data.

Either way, both the options receive the same prompt and are expected to produce identical output schema. Hence, either of the two approach is allowed.

## What this project does?

This project is actually a quiz platform, where the students can take the quiz assigned by the teacher. Hence, there should be two main database users. One is the teacher and other is the User. Along with these, the Admin is also a part of the database who has overall access.

The teacher creates a class where he can add the students through their email or through their id or username. The students can view all the classes they are in. Each class hence has its own properties, along with the students and teachers. The quizzes are mainly attached with the class and on who has created it. The teacher is able to change who can access it, along with the number of attempts and also some other features like time limit and other stuffs.

When the teacher wants to create the quiz, he can either generate quiz using out Generate Quiz option or they an do it via the importing their own questions by manually typing in. They are also allowed to add some questions and then generate the follow up questions which are used as few shot examples for the AI model, providing much similar questions and options. After adding all the required questions, he shall enter the questions to be displayed to each student along with if the questions have to be shuffled, if reattempt is allowed or not, mark for each question, and other stuffs.

After creating and saving a quiz, the quiz is mapped to the respective class, and the selected students are notified via email or notification (if the teacher selects to notify). He can even schedule the quizzes to start at a particular time, notify at a particular time and much more.

When the students want to take the test, they can find the test in their inbox or the class where the test is mapped to. After finding the test, they will attend the test and each of their answers are stored for analytics.

The teacher can view all the reports and analytics when they enter the quiz. They can also opt to stop submission, restrain particular students from attending that particular quiz, delete response and much more.

Hence the data models required will be:

```jsx
Admin
Student
Teacher
Quiz
QuizQuestions
QuizAnswers
```

So, when a student registers, a new data is added in the “Students” json. So for the teacher in the Teachers data. When the teacher creates a new classroom, he is able to add students into that class. So, the classes will be maintained in the JSON format, cause each class will be of this format:

```json
"$students": {
	"student_id": {
		"id": "id",
		"username": "",
		"name": "",
		"email": "",
		"password": "",
		"dob": "",
		"created_on": ""
	}
},
"$teachers": {
	"teacher_id": {
		"id": "",
		"username": "",
		"email": "",
		"password": "",
		"dob": "",
		"created_on": ""
	}
},
"$classes": {
	"class_id": {
		"id": "id",
		"name": "str",
		"created_on": "str",
		"students": [ "student_id" ],
		"teacher_id": "teacher_id"
	}
},
"$quiz": {
	"quiz_id": {
		"id": "id",
		"title": "title",
		"teacher_id": "id",
		"class_id": "id",
		"excluded_students_id": [],
		"public": false,
		"created_on": "datetime",
		"question_ids": []
	}
},
"$questions": {
	"question_id": {
		"id": "id",
		"created_by": "teacher_id",
		"created_on": "datetime",
		"marks": 0.0,
		"type": "$TYPE",
		"data": {..$TYPE}
	}
}
"$TYPE": {
	"mcq": {
		"title": "str",
		"options": { "opt_id": "opt_val" },
		"correct_options": [ "opt_id" ]
	},
	"trueorfalse": {
		"title": "str",
		"answer": bool
	} 
}
```

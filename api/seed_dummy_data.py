"""
VisionFlow Database Seeder
Populates the database with 3 courses: Java Mastery, C Programming, and C++ Zero to Hero
Each lesson includes a YouTube video, quiz question, and practice coding problem.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from index import app, db, Course, Module, Lesson, Quiz, PracticeQuestion

def clear_data():
    """Clear existing data to avoid duplicates"""
    with app.app_context():
        print("🗑️  Clearing existing data...")
        Quiz.query.delete()
        PracticeQuestion.query.delete()
        Lesson.query.delete()
        Module.query.delete()
        Course.query.delete()
        db.session.commit()
        print("✅ Data cleared!")

def seed_java_course():
    """Create Java Mastery course"""
    course = Course(
        id="java",
        title="Java Mastery",
        description="Master Java programming from basics to advanced concepts including OOP, Collections, and Spring Framework.",
        thumbnail_url="https://img.youtube.com/vi/eIrMbAQSU34/maxresdefault.jpg",
        is_generated=False
    )
    db.session.add(course)
    
    # Module 1: Java Basics
    m1 = Module(course_id="java", title="Java Basics", order_index=1)
    db.session.add(m1)
    db.session.flush()
    
    lessons_m1 = [
        ("Introduction to Java", "eIrMbAQSU34", "15:30"),
        ("Variables and Data Types", "le0A7YrSbMo", "12:45"),
        ("Control Flow Statements", "ldYLYRNaucM", "18:20"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m1, 1):
        lesson = Lesson(module_id=m1.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        # Add quiz
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"What is the correct way to declare a {title.lower().split()[0]} in Java?",
            options=["int x = 5;", "x = 5 int;", "integer x = 5;", "var int x = 5;"],
            correct_answer="int x = 5;"
        )
        db.session.add(quiz)
        
        # Add practice question
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Write a Java program that demonstrates {title.lower()}.",
            test_cases=[
                {"input": "5", "expected": "5"},
                {"input": "10", "expected": "10"}
            ],
            hints=["Start with public class", "Use System.out.println() for output"]
        )
        db.session.add(practice)
    
    # Module 2: Object-Oriented Programming
    m2 = Module(course_id="java", title="Object-Oriented Programming", order_index=2)
    db.session.add(m2)
    db.session.flush()
    
    lessons_m2 = [
        ("Classes and Objects", "IUqKuGNasdM", "20:15"),
        ("Inheritance", "Zs342eBFQo8", "16:40"),
        ("Polymorphism", "jhDUxynEQRI", "14:55"),
        ("Encapsulation", "jNrduvnMmDc", "11:30"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m2, 1):
        lesson = Lesson(module_id=m2.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"Which keyword is used for {title.lower()} in Java?",
            options=["extends", "implements", "inherits", "super"],
            correct_answer="extends" if "Inheritance" in title else "extends"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Create a class hierarchy demonstrating {title.lower()}.",
            test_cases=[{"input": "Animal", "expected": "Dog extends Animal"}],
            hints=["Use the extends keyword", "Override methods as needed"]
        )
        db.session.add(practice)
    
    # Module 3: Collections Framework
    m3 = Module(course_id="java", title="Collections Framework", order_index=3)
    db.session.add(m3)
    db.session.flush()
    
    lessons_m3 = [
        ("ArrayList and LinkedList", "1nRj4ALuw7A", "17:25"),
        ("HashMap and HashSet", "H62Jfv1DJlU", "19:10"),
        ("Iterators and Streams", "Q93JsQ8vcwY", "22:00"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m3, 1):
        lesson = Lesson(module_id=m3.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"What is the time complexity of adding an element to {title.split()[0]}?",
            options=["O(1)", "O(n)", "O(log n)", "O(n²)"],
            correct_answer="O(1)"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Implement a program using {title.split()[0]} to store and retrieve data.",
            test_cases=[{"input": "[1,2,3]", "expected": "3 elements"}],
            hints=["Import java.util.*", "Use add() method to insert elements"]
        )
        db.session.add(practice)
    
    # Module 4: Advanced Java
    m4 = Module(course_id="java", title="Advanced Java", order_index=4)
    db.session.add(m4)
    db.session.flush()
    
    lessons_m4 = [
        ("Exception Handling", "1XAfapkBQjk", "14:50"),
        ("Multithreading", "r_MbozD32eo", "25:30"),
        ("File I/O", "ScUJx4aWRi0", "18:45"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m4, 1):
        lesson = Lesson(module_id=m4.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"Which class is commonly used for {title.lower()} in Java?",
            options=["Thread", "Exception", "File", "Stream"],
            correct_answer="Thread" if "Multithreading" in title else "Exception"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Write a program demonstrating {title.lower()} concepts.",
            test_cases=[{"input": "test.txt", "expected": "File processed"}],
            hints=["Use try-catch blocks", "Remember to close resources"]
        )
        db.session.add(practice)

def seed_c_course():
    """Create C Programming course"""
    course = Course(
        id="c",
        title="C Programming",
        description="Learn C programming from scratch - pointers, memory management, file handling and more.",
        thumbnail_url="https://img.youtube.com/vi/KJgsSFOSQv0/maxresdefault.jpg",
        is_generated=False
    )
    db.session.add(course)
    
    # Module 1: C Basics
    m1 = Module(course_id="c", title="C Fundamentals", order_index=1)
    db.session.add(m1)
    db.session.flush()
    
    lessons_m1 = [
        ("Hello World in C", "KJgsSFOSQv0", "8:30"),
        ("Variables and Constants", "aZb0iu4uGwA", "11:20"),
        ("Operators in C", "_r5i5ZtUpUM", "15:45"),
        ("Control Structures", "kyZ6bHS-pIk", "18:10"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m1, 1):
        lesson = Lesson(module_id=m1.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"What is the correct syntax for {title.lower()} in C?",
            options=["printf()", "print()", "cout<<", "System.out"],
            correct_answer="printf()"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Write a C program that demonstrates {title.lower()}.",
            test_cases=[{"input": "5", "expected": "5"}],
            hints=["Include stdio.h", "Use printf for output"]
        )
        db.session.add(practice)
    
    # Module 2: Pointers
    m2 = Module(course_id="c", title="Pointers and Memory", order_index=2)
    db.session.add(m2)
    db.session.flush()
    
    lessons_m2 = [
        ("Introduction to Pointers", "zuegQmMdy8M", "20:00"),
        ("Pointer Arithmetic", "JTttg85xsbo", "16:30"),
        ("Dynamic Memory Allocation", "xDVC3wKjS64", "22:15"),
        ("Double Pointers", "k6ESk9zafHM", "14:40"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m2, 1):
        lesson = Lesson(module_id=m2.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question="What does the * operator do in pointer context?",
            options=["Multiplication", "Dereference", "Address-of", "Division"],
            correct_answer="Dereference"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Implement {title.lower()} to swap two numbers.",
            test_cases=[{"input": "a=5, b=10", "expected": "a=10, b=5"}],
            hints=["Use & to get address", "Use * to dereference"]
        )
        db.session.add(practice)
    
    # Module 3: File I/O
    m3 = Module(course_id="c", title="File Handling", order_index=3)
    db.session.add(m3)
    db.session.flush()
    
    lessons_m3 = [
        ("File Operations", "BnYmbpVYx8k", "19:30"),
        ("Reading and Writing Files", "dqnU7dZmPFo", "17:45"),
        ("Binary Files", "x6Q5Y5xv7Xk", "21:00"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m3, 1):
        lesson = Lesson(module_id=m3.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question="Which function opens a file in C?",
            options=["fopen()", "open()", "file_open()", "openfile()"],
            correct_answer="fopen()"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Write a program for {title.lower()} in C.",
            test_cases=[{"input": "data.txt", "expected": "File processed successfully"}],
            hints=["Use fopen with mode 'r' or 'w'", "Always check if file opened successfully"]
        )
        db.session.add(practice)

def seed_cpp_course():
    """Create C++ Zero to Hero course"""
    course = Course(
        id="cpp",
        title="C++ Zero to Hero",
        description="Complete C++ course covering basics to advanced topics including STL, Templates, and Modern C++ features.",
        thumbnail_url="https://img.youtube.com/vi/vLnPwxZdW4Y/maxresdefault.jpg",
        is_generated=False
    )
    db.session.add(course)
    
    # Module 1: C++ Basics
    m1 = Module(course_id="cpp", title="C++ Fundamentals", order_index=1)
    db.session.add(m1)
    db.session.flush()
    
    lessons_m1 = [
        ("Introduction to C++", "vLnPwxZdW4Y", "12:00"),
        ("Variables and Data Types", "1v_4dL8l8pQ", "14:30"),
        ("Input/Output in C++", "nGJTWaaFdjc", "10:15"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m1, 1):
        lesson = Lesson(module_id=m1.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question="What is the correct way to output in C++?",
            options=["cout <<", "printf()", "print()", "System.out"],
            correct_answer="cout <<"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Write a C++ program demonstrating {title.lower()}.",
            test_cases=[{"input": "Hello", "expected": "Hello World"}],
            hints=["Include iostream", "Use std::cout or using namespace std"]
        )
        db.session.add(practice)
    
    # Module 2: OOP in C++
    m2 = Module(course_id="cpp", title="Object-Oriented C++", order_index=2)
    db.session.add(m2)
    db.session.flush()
    
    lessons_m2 = [
        ("Classes and Objects", "2BP8NhxjrO0", "18:45"),
        ("Constructors and Destructors", "FXhALMsHwEY", "16:20"),
        ("Inheritance in C++", "gq2Igdc-OSI", "20:10"),
        ("Virtual Functions", "oIV2KchSyGQ", "15:30"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m2, 1):
        lesson = Lesson(module_id=m2.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"Which access specifier is default in C++ classes?",
            options=["private", "public", "protected", "internal"],
            correct_answer="private"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Implement a class demonstrating {title.lower()}.",
            test_cases=[{"input": "Object", "expected": "Constructor called"}],
            hints=["Use class keyword", "Define constructor with same name as class"]
        )
        db.session.add(practice)
    
    # Module 3: STL
    m3 = Module(course_id="cpp", title="Standard Template Library", order_index=3)
    db.session.add(m3)
    db.session.flush()
    
    lessons_m3 = [
        ("Vectors", "SGyutdso6_c", "17:00"),
        ("Maps and Sets", "V-oc6r_R4P8", "19:30"),
        ("Algorithms", "COQHn8xuEcU", "21:45"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m3, 1):
        lesson = Lesson(module_id=m3.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"Which header is needed for {title.lower()} in C++?",
            options=["<vector>", "<algorithm>", "<map>", "<set>"],
            correct_answer="<vector>" if "Vector" in title else "<algorithm>"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Solve a problem using STL {title.lower()}.",
            test_cases=[{"input": "[3,1,2]", "expected": "[1,2,3]"}],
            hints=["Include the appropriate STL header", "Use iterators for traversal"]
        )
        db.session.add(practice)
    
    # Module 4: Templates
    m4 = Module(course_id="cpp", title="Templates", order_index=4)
    db.session.add(m4)
    db.session.flush()
    
    lessons_m4 = [
        ("Function Templates", "I-hZkUa9mIs", "14:30"),
        ("Class Templates", "XN319PMv3Bk", "16:45"),
        ("Template Specialization", "H_Gh_lbKuKI", "18:20"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m4, 1):
        lesson = Lesson(module_id=m4.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question="What keyword declares a template in C++?",
            options=["template", "generic", "typename", "class"],
            correct_answer="template"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Create a {title.lower()} that works with multiple data types.",
            test_cases=[{"input": "int, double", "expected": "Both types work"}],
            hints=["Use template<typename T>", "Templates are defined in header files"]
        )
        db.session.add(practice)
    
    # Module 5: Modern C++
    m5 = Module(course_id="cpp", title="Modern C++ (C++11/14/17)", order_index=5)
    db.session.add(m5)
    db.session.flush()
    
    lessons_m5 = [
        ("Auto and Decltype", "2vOPEuiGXVo", "12:15"),
        ("Lambda Expressions", "mWgmBBz0y8c", "18:40"),
        ("Smart Pointers", "UOB7-B2MfwA", "22:00"),
        ("Move Semantics", "IOkgBrXCtfo", "25:30"),
    ]
    
    for idx, (title, video_id, duration) in enumerate(lessons_m5, 1):
        lesson = Lesson(module_id=m5.id, title=title, video_url=video_id, duration=duration, order_index=idx)
        db.session.add(lesson)
        db.session.flush()
        
        quiz = Quiz(
            lesson_id=lesson.id,
            question=f"Which C++ version introduced {title.lower()}?",
            options=["C++11", "C++14", "C++17", "C++20"],
            correct_answer="C++11"
        )
        db.session.add(quiz)
        
        practice = PracticeQuestion(
            lesson_id=lesson.id,
            problem_statement=f"Demonstrate the use of {title.lower()} in a practical example.",
            test_cases=[{"input": "test", "expected": "Modern feature working"}],
            hints=["Compile with -std=c++11 or higher", "Check compiler support"]
        )
        db.session.add(practice)

def main():
    print("🚀 VisionFlow Database Seeder")
    print("=" * 40)
    
    clear_data()
    
    with app.app_context():
        print("\n📚 Seeding Java Mastery course...")
        seed_java_course()
        print("✅ Java course added!")
        
        print("\n📚 Seeding C Programming course...")
        seed_c_course()
        print("✅ C course added!")
        
        print("\n📚 Seeding C++ Zero to Hero course...")
        seed_cpp_course()
        print("✅ C++ course added!")
        
        db.session.commit()
        
        # Print summary
        courses = Course.query.count()
        modules = Module.query.count()
        lessons = Lesson.query.count()
        quizzes = Quiz.query.count()
        practices = PracticeQuestion.query.count()
        
        print("\n" + "=" * 40)
        print("📊 SEEDING COMPLETE!")
        print(f"   • Courses: {courses}")
        print(f"   • Modules: {modules}")
        print(f"   • Lessons: {lessons}")
        print(f"   • Quizzes: {quizzes}")
        print(f"   • Practice Questions: {practices}")
        print("=" * 40)

if __name__ == "__main__":
    main()

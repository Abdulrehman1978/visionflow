from api.index import app, db, Course, Module, Lesson

def seed_courses():
    with app.app_context():
        # Check if Python course exists
        if Course.query.filter_by(id="python").first():
            print("Skipping: Python course already exists.")
            return

        print("Seeding Python Mastery Course...")

        # 1. Create Course
        python_course = Course(
            id="python",
            title="Python Mastery",
            description="Master Python from scratch to advanced concepts.",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg",
            is_generated=False
        )
        db.session.add(python_course)
        db.session.flush() # Flush to get the ID if it wasn't manual (here it is manual 'python')

        # 2. Create Modules & Lessons
        modules_data = [
            {
                "title": "Basics",
                "order": 1,
                "lessons": [
                    {"title": "Variables & Data Types", "video_id": "_uQrJ0TkZlc", "duration": "10:00"},
                    {"title": "Control Flow (If/Else)", "video_id": "Zp5MuPOtsSY", "duration": "12:30"},
                    {"title": "Loops (For/While)", "video_id": "6iF8Xb7Z3wQ", "duration": "15:00"}
                ]
            },
            {
                "title": "Data Structures",
                "order": 2,
                "lessons": [
                    {"title": "Lists & Tuples", "video_id": "ohCDkTuyIPg", "duration": "14:20"},
                    {"title": "Dictionaries & Sets", "video_id": "daefaLgNkw0", "duration": "11:45"}
                ]
            },
            {
                "title": "Object-Oriented Programming",
                "order": 3,
                "lessons": [
                    {"title": "Classes & Objects", "video_id": "ZDa-Z5JzLYM", "duration": "18:00"},
                    {"title": "Inheritance & Polymorphism", "video_id": "JeznW_7DlB0", "duration": "16:10"}
                ]
            }
        ]

        for mod_data in modules_data:
            module = Module(
                course_id=python_course.id,
                title=mod_data["title"],
                order_index=mod_data["order"]
            )
            db.session.add(module)
            db.session.flush() # Needed to get module.id for lessons

            for i, lesson_data in enumerate(mod_data["lessons"]):
                lesson = Lesson(
                    module_id=module.id,
                    title=lesson_data["title"],
                    video_url=lesson_data["video_id"],
                    duration=lesson_data["duration"],
                    order_index=i + 1
                )
                db.session.add(lesson)

        db.session.commit()
        print("✅ Python Mastery Course Seeded Successfully!")

if __name__ == "__main__":
    seed_courses()

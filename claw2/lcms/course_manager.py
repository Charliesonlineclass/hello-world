"""
SCORPION CLAW2 - Learning Content Management System
=====================================================

Course creation, student enrollment, and progress tracking.

Features:
- Create courses with modules and lessons
- Enroll students in courses
- Track completion progress
- Generate certificates
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLAW2.course_manager")


class ContentType(Enum):
    """Content types for lessons."""
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    DOWNLOAD = "download"


class EnrollmentStatus(Enum):
    """Student enrollment status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    DROPPED = "dropped"


@dataclass
class Lesson:
    """Individual lesson within a module."""
    id: str
    title: str
    content_type: str
    content_url: str = ""
    content_text: str = ""
    duration_minutes: int = 0
    order: int = 0
    is_required: bool = True


@dataclass
class Module:
    """Course module containing lessons."""
    id: str
    title: str
    description: str = ""
    lessons: List[Lesson] = field(default_factory=list)
    order: int = 0
    is_required: bool = True


@dataclass
class Course:
    """Course structure."""
    id: str
    title: str
    description: str
    instructor: str
    modules: List[Module] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_published: bool = False
    price: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def total_lessons(self) -> int:
        return sum(len(m.lessons) for m in self.modules)

    @property
    def total_duration(self) -> int:
        return sum(l.duration_minutes for m in self.modules for l in m.lessons)


@dataclass
class Enrollment:
    """Student enrollment in a course."""
    id: str
    student_id: str
    course_id: str
    status: str = "active"
    progress: float = 0.0
    completed_lessons: List[str] = field(default_factory=list)
    quiz_scores: Dict[str, float] = field(default_factory=dict)
    started_at: str = ""
    completed_at: Optional[str] = None
    last_activity: str = ""
    certificate_id: Optional[str] = None

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.last_activity:
            self.last_activity = self.started_at


@dataclass
class Student:
    """Student profile."""
    id: str
    name: str
    email: str
    enrollments: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class CourseManager:
    """
    Learning Content Management System.

    Usage:
        manager = CourseManager()
        course_id = manager.create_course("Python 101", [
            {"title": "Basics", "lessons": [
                {"title": "Variables", "content_type": "video", "duration": 15}
            ]}
        ])
        manager.enroll_student("student-001", course_id)
        manager.complete_lesson("student-001", course_id, "lesson-001")
    """

    def __init__(self, data_dir: str = "lcms_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self._courses: Dict[str, Course] = {}
        self._students: Dict[str, Student] = {}
        self._enrollments: Dict[str, Enrollment] = {}
        self._counters = {"course": 0, "module": 0, "lesson": 0, "student": 0, "enrollment": 0}

        self._load_data()

    def _load_data(self):
        """Load all data from files."""
        for data_type in ["courses", "students", "enrollments"]:
            file_path = self.data_dir / f"{data_type}.json"
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text())
                    if data_type == "courses":
                        for item in data:
                            # Reconstruct nested objects
                            modules = []
                            for m in item.get("modules", []):
                                lessons = [Lesson(**l) for l in m.get("lessons", [])]
                                m["lessons"] = lessons
                                modules.append(Module(**m))
                            item["modules"] = modules
                            course = Course(**item)
                            self._courses[course.id] = course
                    elif data_type == "students":
                        for item in data:
                            student = Student(**item)
                            self._students[student.id] = student
                    elif data_type == "enrollments":
                        for item in data:
                            enrollment = Enrollment(**item)
                            self._enrollments[enrollment.id] = enrollment
                except Exception as e:
                    logger.error(f"Error loading {data_type}: {e}")

    def _save_data(self):
        """Save all data to files."""
        # Courses
        courses_data = []
        for course in self._courses.values():
            course_dict = asdict(course)
            courses_data.append(course_dict)
        (self.data_dir / "courses.json").write_text(json.dumps(courses_data, indent=2))

        # Students
        students_data = [asdict(s) for s in self._students.values()]
        (self.data_dir / "students.json").write_text(json.dumps(students_data, indent=2))

        # Enrollments
        enrollments_data = [asdict(e) for e in self._enrollments.values()]
        (self.data_dir / "enrollments.json").write_text(json.dumps(enrollments_data, indent=2))

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    def create_course(
        self,
        title: str,
        modules: List[Dict],
        description: str = "",
        instructor: str = "",
        tags: List[str] = None,
        price: float = 0.0
    ) -> str:
        """
        Create a new course.

        Args:
            title: Course title
            modules: List of module dicts with 'title' and 'lessons'
            description: Course description
            instructor: Instructor name
            tags: Course tags
            price: Course price

        Returns:
            Course ID
        """
        course_id = self._generate_id("course")

        # Build module and lesson objects
        module_objects = []
        for i, mod_data in enumerate(modules):
            module_id = self._generate_id("module")

            lesson_objects = []
            for j, lesson_data in enumerate(mod_data.get("lessons", [])):
                lesson_id = self._generate_id("lesson")
                lesson = Lesson(
                    id=lesson_id,
                    title=lesson_data.get("title", f"Lesson {j+1}"),
                    content_type=lesson_data.get("content_type", "text"),
                    content_url=lesson_data.get("content_url", ""),
                    content_text=lesson_data.get("content_text", ""),
                    duration_minutes=lesson_data.get("duration", 10),
                    order=j,
                    is_required=lesson_data.get("is_required", True)
                )
                lesson_objects.append(lesson)

            module = Module(
                id=module_id,
                title=mod_data.get("title", f"Module {i+1}"),
                description=mod_data.get("description", ""),
                lessons=lesson_objects,
                order=i,
                is_required=mod_data.get("is_required", True)
            )
            module_objects.append(module)

        course = Course(
            id=course_id,
            title=title,
            description=description,
            instructor=instructor,
            modules=module_objects,
            tags=tags or [],
            price=price
        )

        self._courses[course_id] = course
        self._save_data()

        logger.info(f"Course created: {course_id} - {title}")
        return course_id

    def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID."""
        return self._courses.get(course_id)

    def publish_course(self, course_id: str) -> bool:
        """Publish a course."""
        course = self._courses.get(course_id)
        if course:
            course.is_published = True
            course.updated_at = datetime.now().isoformat()
            self._save_data()
            return True
        return False

    def add_student(
        self,
        name: str,
        email: str,
        student_id: Optional[str] = None
    ) -> str:
        """Add a new student."""
        if student_id is None:
            student_id = self._generate_id("student")

        student = Student(
            id=student_id,
            name=name,
            email=email
        )

        self._students[student_id] = student
        self._save_data()

        logger.info(f"Student added: {student_id} - {name}")
        return student_id

    def get_student(self, student_id: str) -> Optional[Student]:
        """Get student by ID."""
        return self._students.get(student_id)

    def enroll_student(
        self,
        student_id: str,
        course_id: str
    ) -> Optional[str]:
        """
        Enroll a student in a course.

        Args:
            student_id: Student ID
            course_id: Course ID

        Returns:
            Enrollment ID or None
        """
        student = self._students.get(student_id)
        course = self._courses.get(course_id)

        if not student:
            logger.error(f"Student not found: {student_id}")
            return None

        if not course:
            logger.error(f"Course not found: {course_id}")
            return None

        # Check for existing enrollment
        for enrollment in self._enrollments.values():
            if enrollment.student_id == student_id and enrollment.course_id == course_id:
                if enrollment.status == "active":
                    logger.warning(f"Student already enrolled in course")
                    return enrollment.id

        enrollment_id = self._generate_id("enrollment")
        enrollment = Enrollment(
            id=enrollment_id,
            student_id=student_id,
            course_id=course_id
        )

        self._enrollments[enrollment_id] = enrollment
        student.enrollments.append(enrollment_id)
        self._save_data()

        logger.info(f"Enrolled {student_id} in {course_id}")
        return enrollment_id

    def complete_lesson(
        self,
        student_id: str,
        course_id: str,
        lesson_id: str,
        quiz_score: Optional[float] = None
    ) -> bool:
        """
        Mark a lesson as completed.

        Args:
            student_id: Student ID
            course_id: Course ID
            lesson_id: Lesson ID
            quiz_score: Optional quiz score (0-100)

        Returns:
            Success status
        """
        enrollment = self._get_enrollment(student_id, course_id)
        if not enrollment:
            return False

        if lesson_id not in enrollment.completed_lessons:
            enrollment.completed_lessons.append(lesson_id)

        if quiz_score is not None:
            enrollment.quiz_scores[lesson_id] = quiz_score

        enrollment.last_activity = datetime.now().isoformat()

        # Recalculate progress
        course = self._courses.get(course_id)
        if course:
            total_lessons = course.total_lessons
            if total_lessons > 0:
                enrollment.progress = len(enrollment.completed_lessons) / total_lessons * 100

            # Check for course completion
            if enrollment.progress >= 100:
                enrollment.status = "completed"
                enrollment.completed_at = datetime.now().isoformat()
                enrollment.certificate_id = self._generate_certificate(enrollment)

        self._save_data()
        return True

    def _get_enrollment(self, student_id: str, course_id: str) -> Optional[Enrollment]:
        """Get enrollment for student in course."""
        for enrollment in self._enrollments.values():
            if enrollment.student_id == student_id and enrollment.course_id == course_id:
                return enrollment
        return None

    def track_progress(
        self,
        student_id: str,
        course_id: str
    ) -> Dict:
        """
        Get student's progress in a course.

        Returns progress report with completion %, completed lessons, etc.
        """
        enrollment = self._get_enrollment(student_id, course_id)
        if not enrollment:
            return {"error": "Not enrolled"}

        course = self._courses.get(course_id)
        if not course:
            return {"error": "Course not found"}

        # Build detailed progress
        module_progress = []
        for module in course.modules:
            completed_in_module = [
                l.id for l in module.lessons
                if l.id in enrollment.completed_lessons
            ]
            module_progress.append({
                "module_id": module.id,
                "title": module.title,
                "total_lessons": len(module.lessons),
                "completed_lessons": len(completed_in_module),
                "progress": len(completed_in_module) / len(module.lessons) * 100 if module.lessons else 100
            })

        return {
            "student_id": student_id,
            "course_id": course_id,
            "course_title": course.title,
            "enrollment_status": enrollment.status,
            "overall_progress": round(enrollment.progress, 1),
            "completed_lessons": len(enrollment.completed_lessons),
            "total_lessons": course.total_lessons,
            "module_progress": module_progress,
            "quiz_scores": enrollment.quiz_scores,
            "avg_quiz_score": (
                sum(enrollment.quiz_scores.values()) / len(enrollment.quiz_scores)
                if enrollment.quiz_scores else None
            ),
            "started_at": enrollment.started_at,
            "last_activity": enrollment.last_activity,
            "completed_at": enrollment.completed_at,
            "certificate_id": enrollment.certificate_id
        }

    def _generate_certificate(self, enrollment: Enrollment) -> str:
        """Generate certificate ID for completed course."""
        data = f"{enrollment.student_id}-{enrollment.course_id}-{datetime.now().isoformat()}"
        cert_id = hashlib.sha256(data.encode()).hexdigest()[:12].upper()
        return f"CERT-{cert_id}"

    def get_student_courses(self, student_id: str) -> List[Dict]:
        """Get all courses for a student."""
        courses = []
        for enrollment in self._enrollments.values():
            if enrollment.student_id == student_id:
                course = self._courses.get(enrollment.course_id)
                if course:
                    courses.append({
                        "course_id": course.id,
                        "title": course.title,
                        "status": enrollment.status,
                        "progress": enrollment.progress
                    })
        return courses

    def get_course_students(self, course_id: str) -> List[Dict]:
        """Get all students in a course."""
        students = []
        for enrollment in self._enrollments.values():
            if enrollment.course_id == course_id:
                student = self._students.get(enrollment.student_id)
                if student:
                    students.append({
                        "student_id": student.id,
                        "name": student.name,
                        "status": enrollment.status,
                        "progress": enrollment.progress
                    })
        return students

    def get_stats(self) -> Dict:
        """Get LCMS statistics."""
        return {
            "total_courses": len(self._courses),
            "published_courses": len([c for c in self._courses.values() if c.is_published]),
            "total_students": len(self._students),
            "total_enrollments": len(self._enrollments),
            "active_enrollments": len([e for e in self._enrollments.values() if e.status == "active"]),
            "completions": len([e for e in self._enrollments.values() if e.status == "completed"]),
            "avg_progress": (
                sum(e.progress for e in self._enrollments.values()) / len(self._enrollments)
                if self._enrollments else 0
            )
        }


# Convenience functions
_manager: Optional[CourseManager] = None


def create_course(title: str, modules: List[Dict], **kwargs) -> str:
    """Create course using default manager."""
    global _manager
    if _manager is None:
        _manager = CourseManager()
    return _manager.create_course(title, modules, **kwargs)


def enroll_student(student_id: str, course_id: str) -> Optional[str]:
    """Enroll student using default manager."""
    global _manager
    if _manager is None:
        _manager = CourseManager()
    return _manager.enroll_student(student_id, course_id)


def track_progress(student_id: str, course_id: str) -> Dict:
    """Track progress using default manager."""
    global _manager
    if _manager is None:
        _manager = CourseManager()
    return _manager.track_progress(student_id, course_id)


if __name__ == "__main__":
    print("CLAW2 Course Manager - Demo")
    print("=" * 40)

    manager = CourseManager()

    # Create a course
    course_id = manager.create_course(
        title="Python Fundamentals",
        description="Learn Python from scratch",
        instructor="SCORPION",
        modules=[
            {
                "title": "Getting Started",
                "lessons": [
                    {"title": "Installing Python", "content_type": "video", "duration": 10},
                    {"title": "Your First Script", "content_type": "text", "duration": 15},
                    {"title": "Variables Quiz", "content_type": "quiz", "duration": 5}
                ]
            },
            {
                "title": "Data Types",
                "lessons": [
                    {"title": "Strings", "content_type": "video", "duration": 20},
                    {"title": "Numbers", "content_type": "video", "duration": 15},
                    {"title": "Lists", "content_type": "video", "duration": 25}
                ]
            }
        ]
    )

    manager.publish_course(course_id)

    # Add student
    student_id = manager.add_student("John Doe", "john@example.com")

    # Enroll
    manager.enroll_student(student_id, course_id)

    # Complete some lessons
    course = manager.get_course(course_id)
    lesson_ids = [l.id for m in course.modules for l in m.lessons]

    for lid in lesson_ids[:3]:
        manager.complete_lesson(student_id, course_id, lid, quiz_score=85)

    # Check progress
    progress = manager.track_progress(student_id, course_id)

    print(f"\nCourse: {progress['course_title']}")
    print(f"Progress: {progress['overall_progress']}%")
    print(f"Lessons: {progress['completed_lessons']}/{progress['total_lessons']}")
    print(f"\nModule Progress:")
    for mp in progress['module_progress']:
        print(f"  {mp['title']}: {mp['progress']:.0f}%")

    print("\nStats:")
    stats = manager.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

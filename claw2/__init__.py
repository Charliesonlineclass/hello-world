"""
SCORPION CLAW 2 - Learning & Content Management
=================================================

Learning management system for courses and training.

Modules:
    - lcms.course_manager: Course creation and student tracking

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

from .lcms.course_manager import (
    CourseManager,
    Course,
    create_course,
    enroll_student,
    track_progress
)

__version__ = "1.0.0"
__codename__ = "TESTUDO"

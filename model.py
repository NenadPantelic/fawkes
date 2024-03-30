import enum
from datetime import datetime
from enum import Enum

from app import db


class StudentCohort(db.Model):
    __tablename__ = "student_cohort"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Role(enum.Enum):
    STUDENT = 'STUDENT'
    STAFF = 'STAFF'


class User(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def role(self):
        return


class Student(User):
    __tablename__ = "student"
    __table_args__ = {"extend_existing": True}

    identifier = db.Column(db.String(50), unique=True, nullable=False)
    cohort_id = db.Column(db.Integer, db.ForeignKey('student_cohort.id'))
    active = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def role(self):
        return Role.STUDENT


class Staff(User):
    __tablename__ = 'staff'
    __table_args__ = {"extend_existing": True}

    @property
    def role(self):
        return Role.STAFF


class AccessIdentifier(db.Model):
    __tablename__ = "access_url"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.String(36), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, identifier, user_id, active=False):
        self.identifier = identifier
        self.user_id = user_id
        self.active = active

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'docker_image': self.docker_image,
        }


class ExamCompletion(db.Model):
    __tablename__ = 'exam_completion'

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    completion_reason = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, exam_id, student_id, completion_reason='Student completed it'):
        self.exam_id = exam_id
        self.student_id = student_id
        self.completion_reason = completion_reason


class ExamViolation(db.Model):
    __tablename__ = 'exam_violation'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    assignment_id = db.Column(db.String)
    violation_type = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, student_id, assignment_id, violation_type):
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.violation_type = violation_type

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'assignment_id': self.assignment_id,
            'violation_type': self.violation_type
        }


class ViolationType(Enum):
    COPY_PASTE_VIOLATION = 'COPY_PASTE_VIOLATION'
    TAB_VIOLATION = 'TAB_VIOLATION'

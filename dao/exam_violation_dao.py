from dao.generic_dao import GenericDAO
from model import ExamViolation


class ExamViolationDAO(GenericDAO):
    def __init__(self, session):
        super().__init__(session, ExamViolation)

    def count_exam_violations(self, student_id, exam_id):
        return ExamViolation.query.filter_by(student_id=student_id, exam_id=exam_id).count()

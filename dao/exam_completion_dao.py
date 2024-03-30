from dao.generic_dao import GenericDAO
from model import ExamCompletion


class ExamCompletionDAO(GenericDAO):
    def __init__(self, session):
        super().__init__(session, ExamCompletion)

    def find_by_exam_and_student(self, exam_id, student_id):
        return ExamCompletion.query.filter_by(exam_id=exam_id, student_id=student_id).first()

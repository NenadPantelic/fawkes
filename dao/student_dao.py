from dao.generic_dao import GenericDAO
from model import Student


class StudentDAO(GenericDAO):
    def __init__(self, session):
        super().__init__(session, Student)

    def find_active_by_identifier(self, identifier: str):
        return Student.query.filter_by(identifier=identifier, active=True).first()

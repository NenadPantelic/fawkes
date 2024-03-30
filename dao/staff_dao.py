from dao.generic_dao import GenericDAO
from model import Staff


class StaffDAO(GenericDAO):
    def __init__(self, session):
        super().__init__(session, Staff)

    def find_by_identifier(self, identifier: str):
        return Staff.query.filter_by(email=identifier).first()

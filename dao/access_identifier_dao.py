from dao.generic_dao import GenericDAO
from model import AccessIdentifier


class AccessIdentifierDAO(GenericDAO):
    def __init__(self, session):
        super().__init__(session, AccessIdentifier)

    def find_by_identifier(self, identifier) -> AccessIdentifier:
        return AccessIdentifier.query.filter_by(identifier=identifier).first()

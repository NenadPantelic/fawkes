from exception import HogwartsException


class GenericDAO:
    def __init__(self, session, entity):
        self._session = session
        self._entity = entity

    def session_commit(self):
        try:
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def insert(self, entity):
        try:
            self._session.add(entity)
            self._session.commit()
            return entity
        except Exception as e:
            self._session.rollback()
            raise e

    def find_all(self):
        return self._entity.query.all()

    def find_by_id(self, entity_id):
        return self._entity.query.get(entity_id)

    def delete_by_id(self, entity_id):
        try:
            entity = self.find_by_id(entity_id)
            if entity is None:
                raise HogwartsException(f'The entity with id {entity_id} not found', 404)

            self._session.delete(entity)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

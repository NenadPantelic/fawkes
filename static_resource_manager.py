import json
from dataclasses import dataclass
from typing import List

from exception import HogwartsException


def _load_data_from_json_file(file_path):
    with open(file_path, 'r') as fin:
        return json.load(fin)


def _parse_to_object(data, _type, collection_type=None):
    if not collection_type:
        return _type(**data)

    if collection_type == 'list':
        return [_type(**item) for item in data]

    if collection_type == 'dict':
        # must have an 'id' attribute
        return {item['id']: _type(**item) for item in data}

    raise TypeError(f'Cannot parse to object: data = {data}, type = {_type}, collection_type = {collection_type}')


@dataclass
class Environment:
    id: str
    name: str
    docker_image: str


@dataclass
class Exam:
    id: str
    description: str


@dataclass
class Assignment:
    id: str
    name: str
    description: str


class StaticResourceManager:
    def __init__(self, environments_file, exam_file, assignments_file):
        self._environments = _parse_to_object(_load_data_from_json_file(environments_file), Environment, 'list')
        self._exam = _parse_to_object(_load_data_from_json_file(exam_file), Exam)
        self._assignments = _parse_to_object(_load_data_from_json_file(assignments_file), Assignment, 'dict')

    def get_environments(self) -> List[Environment]:
        return self._environments

    def get_exam(self) -> Exam:
        if not self._exam:
            raise HogwartsException('Exam not found', 404)

        return self._exam

    def get_exam_by_id(self, _id):
        if not self._exam or self._exam.get('id') != _id:
            raise HogwartsException('Exam not found', 404)

        return self._exam

    def get_assignments(self) -> List[Assignment]:
        return list(self._assignments.values())

    def get_assignment(self, assignment_id) -> Assignment:
        assignment = self._assignments.get(assignment_id)
        if not assignment:
            raise HogwartsException('Assignment not found', 404)

        return assignment

    def deactivate_exam(self):
        self._exam = None

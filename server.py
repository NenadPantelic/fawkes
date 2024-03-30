from functools import wraps

from dao.exam_violation_dao import ExamViolationDAO
from dao.staff_dao import StaffDAO
from dao.student_dao import StudentDAO
from flask import jsonify, request, g

from app import db, app, session, violations_limit_per_exam
from auth import AuthManager, UserContext
from dao.access_identifier_dao import AccessIdentifierDAO
from dao.exam_completion_dao import ExamCompletionDAO
from exception import HogwartsException, UNAUTHORIZED
from minerva_client import MinervaClient
from model import ExamCompletion, Role, ExamViolation
from static_resource_manager import StaticResourceManager
from util.logging import logger

auth_manager = AuthManager(180)
static_resource_manager = StaticResourceManager(
    'resources/environments.json',
    'resources/exam.json',
    'resources/assignments.json',
)
BEARER = 'Bearer '

WHITELISTED_URLS = ['/api/v1/auth']

student_dao = StudentDAO(session)
staff_dao = StaffDAO(session)
exam_completion_dao = ExamCompletionDAO(session)
exam_violation_dao = ExamViolationDAO(session)
access_identifier_dao = AccessIdentifierDAO(session)
minerva_client = MinervaClient('http://localhost:9091', 'X-albus-user-id', 3)


# Authorization decorator for any authenticated user
def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            identity = get_identity()
        except Exception as e:
            raise UNAUTHORIZED
        return fn(*args, **kwargs)

    return wrapper


# Authorization decorator for staff
def staff_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_identity()
        if current_user.role != Role.STAFF:
            return forbidden('Staff access required')
        return fn(*args, **kwargs)

    return wrapper


# Authorization decorator for students
def student_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_identity()
        if current_user.role != Role.STUDENT:
            return forbidden('Student access required')
        return fn(*args, **kwargs)

    return wrapper


@app.before_request
def set_auth_token():
    target_url = request.url
    for url in WHITELISTED_URLS:
        if target_url.endswith(url):
            return

    authz_header = request.headers.get('Authorization')
    token = None
    if authz_header and authz_header.startswith('Bearer '):
        token = authz_header[len(BEARER):]
    g.token = token


def get_identity() -> UserContext:
    return auth_manager.get_user(g.token)


#### Authn/z
# Authentication endpoint
@app.route('/access_url/<str:identifier>', methods=['GET'])
def get_access_parameters(identifier):
    if not identifier:
        return unauthorized()

    access_identifier = access_identifier_dao.find_by_identifier(identifier)
    if not access_identifier or not access_identifier.active:
        return unauthorized()

    user_identifier = access_identifier.user_id
    user = student_dao.find_active_by_identifier(user_identifier)
    if not user:
        user = staff_dao.find_by_identifier(user_identifier)

    access_token = auth_manager.create_token(user)
    g.token = access_token

    exam = static_resource_manager.get_exam()
    return {'access_token': access_token, 'role': user.role.value, 'exam_id': exam.id}, 200


# # --------------------
# ACCESS_IDENTIFIER

@app.route('/api/v1/access_identifiers/cohort/<str:cohort_id>/enable', methods=['POST'])
@staff_required
def enable_access_identifiers_for_cohort(cohort_id):
    raise HogwartsException('Not implemented', 501)


@app.route('/api/v1/access_identifiers/cohort/<str:cohort_id>/disable', methods=['POST'])
@staff_required
def disable_access_identifiers_for_cohort(cohort_id):
    raise HogwartsException('Not implemented', 501)


@app.route('/api/v1/access_identifiers/user/<str:user_id>/enable', methods=['POST'])
@staff_required
def enable_access_identifiers_for_user(user_id):
    raise HogwartsException('Not implemented', 501)


@app.route('/api/v1/access_identifiers/user/<str:user_id>/disable', methods=['POST'])
@staff_required
def disable_access_identifiers_for_user(user_id):
    raise HogwartsException('Not implemented', 501)


# # --------------------

def get_exam_with_validation(exam_id):
    exam = static_resource_manager.get_exam()

    current_user = get_identity()
    if current_user.role != Role.STAFF:
        student_id = current_user.id
        # Check if the student has completed the exam
        exam_completion = exam_completion_dao.find_by_exam_and_student(exam_id=exam_id, student_id=student_id)
        if exam_completion:
            return forbidden('Exam already completed, no permission to access.')

    return exam


@app.route('/api/v1/exams/<str:exam_id>', methods=['GET'])
@auth_required
def get_exam(exam_id):
    exam = get_exam_with_validation(exam_id)

    environments = static_resource_manager.get_environments()
    assignments = static_resource_manager.get_assignments()

    return {
               'exam': exam,
               'environments': environments,
               'assignments': assignments
           }, 200


# # --------------------
# STUDENT EXAMS
# Endpoint for completing an exam
@app.route('/api/v1/exams/<int:exam_id>/complete', methods=['POST'])
@student_required
def complete_exam(exam_id):
    static_resource_manager.get_exam()

    student_id = get_identity().id
    exam_completion = exam_completion_dao.find_by_exam_and_student(exam_id=exam_id, student_id=student_id)
    if exam_completion:
        return conflict('Exam already completed')

    exam_completion_dao.insert(ExamCompletion(exam_id, student_id))

    return {}, 201


# Endpoint for completing an exam
@app.route('/api/v1/exams/<int:exam_id>/violation', methods=['POST'])
@student_required
def report_exam_violation(exam_id):
    get_exam_with_validation(exam_id)

    data = request.get_json() or {}
    assignment_id = data.get('assignment_id')
    violation_type = data.get('violation_type')

    student_id = get_identity().id

    exam_violation = exam_violation_dao.insert(
        ExamViolation(student_id, assignment_id, violation_type)
    )

    num_of_exam_violations = exam_violation_dao.count_exam_violations(student_id, assignment_id)
    # if violations limit reached, complete the exam for this user
    if num_of_exam_violations >= violations_limit_per_exam:
        exam_completion_dao.insert(
            ExamCompletion(exam_id, student_id, "Course policy violated")
        )

    return exam_violation.to_dict(), 200


# --------------------
# SUBMISSIONS
@app.route('/api/v1/exams/<int:exam_id>/assignments/<int:assignment_id>/submit', methods=['GET'])
@auth_required
def submit(exam_id, assignment_id):
    data = request.get_json() or {}
    environment = data.get('environment')
    content = data.get('content')

    if not environment or not content:
        return bad_request('Code submission is invalid.')

    get_exam_with_validation(exam_id)

    assignment = static_resource_manager.get_assignment(assignment_id)
    if not assignment:
        return not_found("Assignment not found.")

    submission = minerva_client.submit(
        assignment_id, assignment.name, environment, exam_id, content, get_identity().id
    )
    return {'data': submission}, 202


@app.route('/api/v1/exams/<int:exam_id>/submissions', methods=['GET'])
@auth_required
def list_submissions(exam_id):
    get_exam_with_validation(exam_id)
    return {'data': minerva_client.list_my_submissions(exam_id, 0, 50, get_identity().id)}, 200


@app.route('/api/v1/submissions', methods=['GET'])
@staff_required
def list_all_submissions():
    return {'data': minerva_client.list_all_submissions(0, 50, get_identity().id)}, 200


@app.route('/api/v1/exams/<int:exam_id>/submissions/<int:submission_id>', methods=['GET'])
@auth_required
def get_submission(exam_id, submission_id):
    get_exam_with_validation(exam_id)
    return {'data': minerva_client.get_submission(submission_id, get_identity().id)}, 200


@app.route('/api/v1/assignments/<int:assignment_id>/allowance', methods=['GET'])
@auth_required
def get_submission_allowance(assignment_id):
    static_resource_manager.get_assignment(assignment_id)
    return {'data': minerva_client.get_allowance(assignment_id, get_identity().id)}, 200


# --------------------
# RESULTS
@app.route('/api/v1/exams/<int:exam_id>/results', methods=['GET'])
@auth_required
def get_exam_results(exam_id):
    get_exam_with_validation(exam_id)

    exam_completion = exam_completion_dao.find_by_exam_and_student(exam_id=exam_id, student_id=get_identity().id)
    if not exam_completion:
        return forbidden('Exam not completed')

    return {'data': minerva_client.get_exam_results(exam_id, get_identity().id)}, 200


##########
# RESULTS
@app.route('/api/v1/exams/<int:exam_id>/complete', methods=['GET'])
@staff_required
def complete_exam(exam_id):
    get_exam_with_validation(exam_id)
    static_resource_manager.deactivate_exam()

    # TODO: insert remaining exam completions
    # TODO: collect results for all students
    # TODO: collect them into an xlsx file
    raise HogwartsException('Not implemented', 501)


@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f'An error occurred: {error}')
    if isinstance(error, HogwartsException):
        return {'error': error.message}, error.status

    return {'error': 'Internal Server Error'}, 500


def bad_request(message):
    return error_response(message, 400)


def unauthorized(message='Unauthorized'):
    return error_response(message, 401)


def forbidden(message):
    return error_response(message, 403)


def not_found(message):
    return error_response(message, 404)


def conflict(message):
    return error_response(message, 409)


def error_response(message, status_code):
    return jsonify({'error': message}), status_code


if __name__ == "__main__":
    with app.app_context() as context:
        db.create_all()
    app.run()

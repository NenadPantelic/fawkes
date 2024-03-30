from time import sleep

from requests import post, get

from exception import HogwartsException
from util.logging import logger

CLIENT_ERROR_STATUS_CODES = [400, 401, 403, 409]
RETRYABLE_STATUS_CODES = [502, 503, 429]


class MinervaClient:
    def __init__(self, url, user_header, max_retry):
        self._url = url
        self._user_header = user_header
        self._max_retry = max_retry

    def submit(self, assignment_id, assignment_name, environment, exam_id, content, user_id):
        headers = {self._user_header: user_id}
        payload = {
            'assignmentId': assignment_id,
            'assignmentName': assignment_name,
            'environment': environment,
            'examId': exam_id,
            'content': content,
        }
        url = f'{self._url}/api/v1/submissions'

        return self._post(url, headers, payload, 202)

    def list_my_submissions(self, exam_id, page, size, user_id):
        headers = {self._user_header: user_id}
        url = f'{self._url}/api/v1/submissions?examId={exam_id}&page={page}&size={size}'
        return self._get(url, headers, 200)

    def list_all_submissions(self, page, size, user_id):
        headers = {self._user_header: user_id}
        url = f'{self._url}/api/v1/submissions/_all?page={page}&size={size}'
        return self._get(url, headers, 200)

    def get_submission(self, submission_id, user_id):
        headers = {self._user_header: user_id}
        url = f'{self._url}/api/v1/submissions/{submission_id}'
        return self._get(url, headers, 200)

    def get_allowance(self, assignment_id, user_id):
        headers = {self._user_header: user_id}
        url = f'{self._url}/api/v1/submissions/allowance?assignmentId={assignment_id}'
        return self._get(url, headers, 200)

    def get_exam_results(self, exam_id, user_id):
        # TODO
        pass

    def _post(self, url, headers, payload, expected_status_code=200):
        return self._execute_with_retry(lambda _: post(url, payload, headers=headers), expected_status_code)

    def _get(self, url, headers, expected_status_code=200):
        return self._execute_with_retry(lambda _: get(url, headers=headers), expected_status_code)

    def _execute_with_retry(self, exec, expected_status_code):
        attempt_count = 0

        while attempt_count < self._max_retry:
            attempt_count += 1
            response = exec()

            response_status_code = response.status_code
            logger.warning(f'Minerva responded with: status = {response_status_code}, body = {response.text}')

            if response_status_code == expected_status_code:
                return response.json()

            if response_status_code in CLIENT_ERROR_STATUS_CODES:
                raise HogwartsException(response.text, response_status_code)

            if response_status_code == 500:
                raise HogwartsException('Internal server error.', 500)

            if response_status_code in RETRYABLE_STATUS_CODES:
                sleep(2 ** attempt_count)

        raise HogwartsException('Grading service is currently unavailable', 503)

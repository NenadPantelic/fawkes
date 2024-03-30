from dataclasses import dataclass
from datetime import datetime, timedelta

from uuid import uuid4
from base64 import b64encode, b64decode

from json import loads, dumps

from exception import UNAUTHORIZED


def get_time_with_offset_in_minutes(offset_in_minutes):
    return datetime.isoformat(datetime.utcnow() + timedelta(minutes=offset_in_minutes))


class AuthManager:
    def __init__(self, token_expiration_offset_in_minutes):
        self._token_expiration_offset_in_minutes = token_expiration_offset_in_minutes
        self._credentials = {}

    def create_token(self, user):
        payload = dumps({
            'id': user.id,
            'email': user.email,
            'role': user.role.value,
            'exp': get_time_with_offset_in_minutes(self._token_expiration_offset_in_minutes),
            'salt': str(uuid4())
        }).encode('utf-8')

        token = b64encode(payload).decode('utf-8')
        self._credentials[token] = UserContext(user.id, user.email, user.role)
        return token

    def get_user(self, token):
        user = self._credentials.get(token)
        if not user:
            raise UNAUTHORIZED

        # TODO: going without exp check at the moment
        # decoded_token = self._decode_token(token)
        # exp = decoded_token.get("exp")
        # if self._is_token_expired(exp):
        #     self._credentials.pop(token, None)
        #     raise UNAUTHORIZED

        return user

    def invalidate_token(self, token):
        self._credentials.pop(token, None)

    def _decode_token(self, token):
        if not token:
            raise ValueError('Missing token')

        decoded_token = loads(b64decode(token).decode("utf-8"))
        decoded_token["exp"] = datetime.fromisoformat(decoded_token["exp"])
        return decoded_token

    def _is_token_expired(self, expiration_time):
        return datetime.utcnow() >= expiration_time


@dataclass
class UserContext:
    id: str
    email: str
    role: str

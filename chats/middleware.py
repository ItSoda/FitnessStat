import os
from datetime import datetime

import django
import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

from users.models import User

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blackkk.settings")
django.setup()

ALGORITHM = "HS256"


@database_sync_to_async
def get_user(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=ALGORITHM)
    except Exception:
        return AnonymousUser()

    token_exp = datetime.fromtimestamp(payload["exp"])
    if token_exp < datetime.utcnow():
        return AnonymousUser()

    try:
        user = User.objects.get(id=payload["user_id"])
    except User.DoesNotExist:
        return AnonymousUser()

    return user


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            query_string = scope["query_string"].decode("utf-8")
            token_key = query_string.split("&")[0].split("token=")[-1]
        except ValueError:
            token_key = None

        scope["user"] = await get_user(token_key)
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)

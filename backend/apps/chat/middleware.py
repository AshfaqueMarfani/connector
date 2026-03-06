"""
JWT-based WebSocket authentication middleware for Django Channels.

Extracts the JWT access token from the query string (?token=xxx)
and authenticates the user before the WebSocket connection is established.
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str):
    """
    Validate a JWT access token and return the corresponding user.
    Returns AnonymousUser if the token is invalid or the user doesn't exist.
    """
    try:
        token = AccessToken(token_str)
        user_id = token.get("user_id")
        user = User.objects.get(id=user_id, is_active=True)
        return user
    except (InvalidToken, TokenError) as e:
        logger.warning(f"WebSocket auth failed – invalid token: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning("WebSocket auth failed \u2013 user not found for token")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"WebSocket auth unexpected error: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that authenticates WebSocket connections using JWT.

    Usage in ASGI config:
        JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    The client connects with:
        ws://host/ws/v1/chat/<room_id>/?token=<jwt_access_token>
    """

    async def __call__(self, scope, receive, send):
        # Parse the query string for the token
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_list = query_params.get("token", [])

        if token_list:
            scope["user"] = await get_user_from_token(token_list[0])
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

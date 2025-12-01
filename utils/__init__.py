"""
Utils package for MI Chatbot Portal.
"""

from .access_control import (
    get_sheet_client,
    normalize_role,
    normalize_bot_type,
    find_code_row,
    mark_row_used,
    get_service_account_email,
    VALID_BOT_TYPES,
    VALID_ROLES,
    ROLE_INSTRUCTOR,
    ROLE_DEVELOPER,
    ROLE_STUDENT,
    SheetClientError,
    MissingSecretsError,
    MalformedSecretsError,
    PermissionDeniedError,
)

__all__ = [
    'get_sheet_client',
    'normalize_role',
    'normalize_bot_type',
    'find_code_row',
    'mark_row_used',
    'get_service_account_email',
    'VALID_BOT_TYPES',
    'VALID_ROLES',
    'ROLE_INSTRUCTOR',
    'ROLE_DEVELOPER',
    'ROLE_STUDENT',
    'SheetClientError',
    'MissingSecretsError',
    'MalformedSecretsError',
    'PermissionDeniedError',
]

#Perform general validation on inputs
#This does not include database lookups
from __future__ import absolute_import
import re
from functools import wraps


VALIDATION_ERROR_EMPTY = 1

VALIDATION_ERROR_SHORT = 2

VALIDATION_ERROR_LONG = 3

VALIDATION_ERROR_INVALID = 4

VALIDATION_ERROR_HIGH = 5

VALIDATION_ERROR_LOW = 6

VALIDATION_ERROR_MATCH = 7

EMAIL_MIN_LENGTH = None

EMAIL_MAX_LENGTH = 128
        
PASSWORD_MIN_LENGTH = 6

PASSWORD_MAX_LENGTH = 4096

USERNAME_MIN_LENGTH = 2

USERNAME_MAX_LENGTH = 128


def _format_error_message(item_name, error_codes, 
                          min_length=None, max_length=None,
                          low_value=None, high_value=None):
    limit_text = ''
    
    if error_codes is None:
        return None
    
    errors = []
    
    if VALIDATION_ERROR_EMPTY in error_codes:
        errors.append('{} is required.'.format(item_name))
    
    else:
        if VALIDATION_ERROR_EXISTS in error_codes:
            errors.append('{} is already in use.'.format(item_name))
            
        if VALIDATION_ERROR_SHORT in error_codes:
            if min_length is not None:
                limit_text = ' (needs to be over {} character{})'.format(min_length, '' if min_length == 1 else 's')
            errors.append('{} is too short{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_LONG in error_codes:
            if max_length is not None:
                limit_text = ' (needs to be under {} character{})'.format(max_length, '' if max_length == 1 else 's')
            errors.append('{} is too long{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_INVALID in error_codes:
            errors.append('{} is invalid.'.format(item_name))
            
        if VALIDATION_ERROR_HIGH in error_codes:
            if high_value is not None:
                limit_text = ' (must be less than {})'.format(high_value)
            errors.append('{} is too high{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_LOW in error_codes:
            if low_value is not None:
                limit_text = ' (must be more than {})'.format(low_value)
            errors.append('{} is too low{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_MATCH in error_codes:
            errors.append('{}s don\'t match.'.format(item_name))

    return errors
    
    
def validate_length(min_length=None, max_length=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value_len = len(args[0])
            allow_empty = kwargs.get('empty', False)
            if not value_len and not allow_empty:
                kwargs['_error_ids'].append(VALIDATION_ERROR_EMPTY)
            elif min_length is not None and 0 < value_len < min_length:
                kwargs['_error_ids'].append(VALIDATION_ERROR_SHORT)
            elif max_length is not None and value_len > max_length:
                kwargs['_error_ids'].append(VALIDATION_ERROR_LONG)
            return func(*args, **kwargs)
        return wrapper
    return decorator

    
def validate_range(min_value=None, max_value=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if min_value is not None and args[0] < min_value:
                kwargs['_error_ids'].append(VALIDATION_ERROR_LOW)
            elif max_value is not None and args[0] > max_value:
                kwargs['_error_ids'].append(VALIDATION_ERROR_HIGH)
            return func(*args, **kwargs)
        return wrapper
    return decorator

    
def validate_regex(regex):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not re.match(regex, args[0]):
                kwargs['_error_ids'].append(VALIDATION_ERROR_INVALID)
            return func(*args, **kwargs)
        return wrapper
    return decorator

    
def validate_match(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0] == args[1]:
            return func(*args, **kwargs)
        return VALIDATION_ERROR_MATCH
    return wrapper


def validate_prepare(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['_error_ids'] = []
        return func(*args, **kwargs)
    return wrapper


def validate_finalize(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            del kwargs['empty']
        except KeyError:
            pass
        return func(*args, **kwargs)
    return wrapper


@validate_prepare
@validate_length(EMAIL_MIN_LENGTH, EMAIL_MAX_LENGTH)
@validate_regex('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
@validate_finalize
def validate_email(email, _error_ids=None):
    return _format_error_message('Email address', _error_ids,
                                 min_length=EMAIL_MIN_LENGTH,
                                 max_length=EMAIL_MAX_LENGTH)


@validate_prepare
@validate_length(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)
@validate_match
@validate_finalize
def validate_password(password, confirm=None, _error_ids=None):
    return _format_error_message('Password', _error_ids,
                                 min_length=PASSWORD_MIN_LENGTH,
                                 max_length=PASSWORD_MAX_LENGTH)

    
@validate_prepare
@validate_length(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH)
@validate_regex('^[a-zA-Z0-9_.-]*$')
@validate_finalize
def validate_username(username, _error_ids=None):
    return _format_error_message('Username', _error_id,
                                 min_length=USERNAME_MIN_LENGTH,
                                 max_length=USERNAME_MAX_LENGTH)

#Perform general validation on inputs
#This does not include database lookups
from __future__ import absolute_import
import re
from functools import wraps


VALIDATION_ERROR_EXISTS = 0

VALIDATION_ERROR_EMPTY = 1

VALIDATION_ERROR_SHORT = 2

VALIDATION_ERROR_LONG = 3

VALIDATION_ERROR_INVALID = 4

VALIDATION_ERROR_HIGH = 5

VALIDATION_ERROR_LOW = 6

VALIDATION_ERROR_MATCH = 7

VALIDATION_ERROR_COMMON = 8

VALIDATION_ERROR_UNIQUE = 10

EMAIL_MIN_LENGTH = None

EMAIL_MAX_LENGTH = 128

PASSWORD_MIN_LENGTH = 6

PASSWORD_MAX_LENGTH = 4096

PASSWORD_REQUIRED_UNIQUE = 4

USERNAME_MIN_LENGTH = 3

USERNAME_MAX_LENGTH = 128


def format_error_message(item_name, error_codes, unique_characters=None,
                          min_length=None, max_length=None,
                          low_value=None, high_value=None):
    
    errors = []
    
    if VALIDATION_ERROR_EMPTY in error_codes:
        errors.append('{} is required.'.format(item_name))
    
    else:
        if VALIDATION_ERROR_EXISTS in error_codes:
            errors.append('{} is already in use.'.format(item_name))
            
        if VALIDATION_ERROR_SHORT in error_codes:
            limit_text = ''
            if min_length is not None:
                limit_text = ' (needs to be over {} character{})'.format(min_length, '' if min_length == 1 else 's')
            errors.append('{} is too short{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_LONG in error_codes:
            limit_text = ''
            if max_length is not None:
                limit_text = ' (needs to be under {} character{})'.format(max_length, '' if max_length == 1 else 's')
            errors.append('{} is too long{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_INVALID in error_codes:
            errors.append('{} is invalid.'.format(item_name))
            
        if VALIDATION_ERROR_HIGH in error_codes:
            limit_text = ''
            if high_value is not None:
                limit_text = ' (must be less than {})'.format(high_value)
            errors.append('{} is too high{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_LOW in error_codes:
            limit_text = ''
            if low_value is not None:
                limit_text = ' (must be more than {})'.format(low_value)
            errors.append('{} is too low{}.'.format(item_name, limit_text))
            
        if VALIDATION_ERROR_MATCH in error_codes:
            errors.append('{}s don\'t match.'.format(item_name))

        if VALIDATION_ERROR_COMMON in error_codes:
            errors.append('{} is very unsafe due to being too widely used.'.format(item_name))
            
        if VALIDATION_ERROR_UNIQUE in error_codes:
            limit_text = ''
            if unique_characters is not None:
                limit_text = ' (must have at least {})'.format(unique_characters)
            errors.append('{} has too few unique characters{}.'.format(item_name, limit_text))
            
    return errors
    
    
def validate_length(min_length=None, max_length=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value_len = len(args[0])
            if not value_len and not kwargs.get('empty', False):
                kwargs['_error_ids'].append(VALIDATION_ERROR_EMPTY)
            elif min_length is not None and value_len < min_length and not kwargs.get('ignore_short', False):
                kwargs['_error_ids'].append(VALIDATION_ERROR_SHORT)
            elif max_length is not None and value_len > max_length and not kwargs.get('ignore_long', False):
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
        if args[0] != args[1]:
            kwargs['_error_ids'].append(VALIDATION_ERROR_MATCH)
        return func(*args, **kwargs)
    return wrapper

    
def validate_unique(unique_characters=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if unique_characters is not None:
                if len(set(args[0])) < unique_characters:
                    kwargs['_error_ids'].append(VALIDATION_ERROR_UNIQUE)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_prepare(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['_error_ids'] = []
        return func(*args, **kwargs)
    return wrapper


def validate_finalize(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        remove_kwargs = ['empty', 'ignore_short', 'ignore_long']
        for i in remove_kwargs:
            try:
                del kwargs[i]
            except KeyError:
                pass
        return func(*args, **kwargs)
    return wrapper


@validate_prepare
@validate_length(EMAIL_MIN_LENGTH, EMAIL_MAX_LENGTH)
@validate_regex('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
@validate_finalize
def validate_email(email, _error_ids):
    return format_error_message('Email address', _error_ids,
                                min_length=EMAIL_MIN_LENGTH,
                                max_length=EMAIL_MAX_LENGTH)


with open('static/used_passwords.txt', 'r') as f:
    COMMON_PASSWORDS = set(f.read().split('\n'))


@validate_prepare
@validate_length(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)
@validate_match
@validate_unique(PASSWORD_REQUIRED_UNIQUE)
@validate_finalize
def validate_password(password, confirm, _error_ids):
    if VALIDATION_ERROR_SHORT not in _error_ids and password in COMMON_PASSWORDS:
        _error_ids.append(VALIDATION_ERROR_COMMON)
    return format_error_message('Password', _error_ids,
                                min_length=PASSWORD_MIN_LENGTH,
                                max_length=PASSWORD_MAX_LENGTH,
                                unique_characters=PASSWORD_REQUIRED_UNIQUE)

    
@validate_prepare
@validate_length(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH)
@validate_regex('^[a-zA-Z0-9_.-]*$')
@validate_finalize
def validate_username(username, _error_ids):
    return format_error_message('Username', _error_ids,
                                min_length=USERNAME_MIN_LENGTH,
                                max_length=USERNAME_MAX_LENGTH)

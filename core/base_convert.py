from __future__ import absolute_import, division
import math
import random
import string


_ALL_CHARACTERS = [chr(i) for i in range(32, 256)]

_BASE64_ORDER = string.digits + string.ascii_letters + '+/='

_DISALLOW = '\0\'\"\b\n\r\t\\'

DEFAULT_CHARACTERS = _BASE64_ORDER + ''.join(i for i in _ALL_CHARACTERS if i not in _BASE64_ORDER + _DISALLOW)

ASCII_CHARACTERS = _BASE64_ORDER + ''.join(i for i in string.punctuation if i not in _BASE64_ORDER + _DISALLOW)


def base_convert(string, start_base=None, end_base=None, 
                 padding=False, strip_padding=True,
                 seed_input=None, seed_output=None, 
                 allowed_characters=None, ascii_only=False):
    """Convert text from one base to another.
    Note that negative numbers, decimals, and case-insensitive strings
    are not supported (eg. "abc" is valid for base 16, "ABC" is not).
    
    >>> base_convert(255, 10, 16)
    'ff'
    >>> base_convert('ff', 16, 10)
    '255'
    >>> base_convert('ff', 16, 2)
    '11111111'
    >>> base_convert('531fac3a92', 16, 43)
    '1dkmoofz'
    >>> base_convert('1dkmoofz', 43, 16)
    '531fac3a92'
    
    Padding can be applied if the result should always be a set length.
    For example, uuid4.hex to base 64 will result in a length of 20-22,
    this will ensure the length is always 22.
    Similar to how base64 pads with '=', the next character in the 
    sequence will be used for padding, and will be automatically 
    stripped when converted back again (or if "strip_padding" is
    disabled, a ValueError will instead be raised).
    
    >>> base_convert('082f0b911a', 16, 64)
    'wL2V4q'
    >>> base_convert('082f0b911a', 16, 64, padding=True)
    'wL2V4q='
    
    A separate seed is required for input and output, as the input
    generally needs the unmodified character sequence to work.
    The output seed is required for encoding, and input for decoding.

    For the purpose of transferring text that has been given a seed, 
    "ascii_only" can be set which will avoid using any characters
    that could cause encoding issues.
    This reduces the highest base from 221 to 94.
    
    >>> base_convert('abcdef0123456789', 16, 64, seed_output='secret', ascii_only=True)
    'pNlW,>Etk^s'
    >>> base_convert('pNlW,>Etk^s', 64, 16, seed_input='secret', ascii_only=True)
    'abcdef0123456789'
    """
    
    #Define the character set if not set (or strip characters)
    if allowed_characters is None:
        if ascii_only:
            allowed_characters = ASCII_CHARACTERS
        else:
            allowed_characters = DEFAULT_CHARACTERS
    elif ascii_only:
        allowed_characters = ''.join(i for i in allowed_characters if i in ASCII_CHARACTERS)
    char_input = list(allowed_characters)
    
    #Define the bases if not set
    if start_base is None:
        start_base = len(char_input) - 1
    else:
        start_base = int(start_base)
    if end_base is None:
        end_base = len(char_input) - 1
    else:
        end_base = int(end_base)
    
    #Shuffle list if any seeds are set
    if seed_input is not None or seed_output is not None:
        char_output = list(char_input)
        if seed_input is not None:
            random.seed(seed_input)
            random.shuffle(char_input)
        if seed_output is not None:
            random.seed(seed_output)
            random.shuffle(char_output)
    else:
        char_output = char_input
        
    #Limit the characters that can be used
    input_padding = char_input[start_base]
    output_padding = char_output[end_base]
    char_input = char_input[:start_base]
    char_output = char_output[:-1]
    
    #Make sure bases are valid
    len_input = len(char_input)
    len_output = len(char_output)
    if start_base > len_input or end_base > len_output:
        raise ValueError('base is too high')
    elif min(start_base, end_base) < 2:
        raise ValueError('base is too low')
    
    string = str(string)
    if strip_padding:
        string = string.rstrip(input_padding)
    
    #Convert to integer (manually do it if too large for the inbuilt conversion)
    try:
        remaining = int(string, start_base)
    except ValueError:
        lookup = {v: i for i, v in enumerate(char_input)}
        remaining = 0
        for i, v in enumerate(string[::-1]):
            try:
                remaining += lookup[v] * start_base ** i
            except KeyError:
                raise ValueError(u'string "{}" not valid for base {}'.format(string, start_base))
    
    #Get the characters in reverse order (remainder from dividing the integer by the base)
    result = []
    while remaining:
        remaining, remainder = divmod(remaining, end_base)
        result.append(char_output[remainder])
    
    #Fill the end characters to pad it out
    if padding:
        expected_length = int(math.ceil(len(string) / math.log(end_base, start_base)))
        extra_characters = expected_length - len(result)
        if extra_characters:
            result = [output_padding] * extra_characters + result
    
    return ''.join(result[::-1])
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()
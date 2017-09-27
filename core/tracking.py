from flask import request


def ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)
    
    
def user_agent():
    return request.user_agent.string
    
    
def browser():
    return request.user_agent.browser
    
    
def platform():
    return request.user_agent.platform
    
    
def language():
    return request.accept_languages[0][0]

from flask import request
from core.hash import quick_hash


def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)
    
    
def get_user_agent():
    return request.user_agent.string
    
    
def get_browser():
    return request.user_agent.browser
    
    
def get_platform():
    return request.user_agent.platform
    
    
def get_language():
    return request.accept_languages[0][0]

    
def get_url():
    if request.query_string:
        return '{}?{}'.format(request.path, request.query_string)
    return request.path
    
    
def get_ip_id(sql_exec):
    ip_address = get_ip()
    result = sql_exec('SELECT id FROM ip_addresses WHERE ip_address = %s', ip_address)
    if result:
        id = result[0][0]
        sql_exec('UPDATE ip_addresses SET last_visit = UNIX_TIMESTAMP(NOW()), total_visits = total_visits + 1 WHERE id = %s', id)
    else:
        id = sql_exec('INSERT INTO ip_addresses (ip_address, first_visit, last_visit, total_visits) VALUES (%s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), 1)', ip_address)
    return id
    
    
def get_ua_id(sql_exec):
    user_agent = get_user_agent()
    hash = quick_hash(user_agent)
    result = sql_exec('SELECT id FROM user_agents WHERE agent_hash = %s', hash)
    if result:
        id = result[0][0]
        sql_exec('UPDATE user_agents SET last_visit = UNIX_TIMESTAMP(NOW()), total_visits = total_visits + 1 WHERE id = %s', id)
    else:
        id = sql_exec('INSERT INTO user_agents (agent_string, agent_hash, first_visit, last_visit, total_visits) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), 1)', user_agent, hash)
    return id
    
    
def get_browser_id(sql_exec):
    browser_name = get_browser()
    hash = quick_hash(browser_name)
    result = sql_exec('SELECT id FROM browsers WHERE browser_hash = %s', hash)
    if result:
        id = result[0][0]
        sql_exec('UPDATE browsers SET last_visit = UNIX_TIMESTAMP(NOW()), total_visits = total_visits + 1 WHERE id = %s', id)
    else:
        id = sql_exec('INSERT INTO browsers (browser_name, browser_hash, first_visit, last_visit, total_visits) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), 1)', browser_name, hash)
    return id
    
    
def get_platform_id(sql_exec):
    platform_name = get_platform()
    hash = quick_hash(platform_name)
    result = sql_exec('SELECT id FROM platforms WHERE platform_hash = %s', hash)
    if result:
        id = result[0][0]
        sql_exec('UPDATE platforms SET last_visit = UNIX_TIMESTAMP(NOW()), total_visits = total_visits + 1 WHERE id = %s', id)
    else:
        id = sql_exec('INSERT INTO platforms (platform_name, platform_hash, first_visit, last_visit, total_visits) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), 1)', platform_name, hash)
    return id
    
    
def get_language_id(sql_exec):
    language = get_language()
    result = sql_exec('SELECT id FROM languages WHERE language = %s', language)
    if result:
        id = result[0][0]
        sql_exec('UPDATE languages SET last_visit = UNIX_TIMESTAMP(NOW()), total_visits = total_visits + 1 WHERE id = %s', id)
    else:
        id = sql_exec('INSERT INTO languages (language, first_visit, last_visit, total_visits) VALUES (%s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), 1)', language)
    return id

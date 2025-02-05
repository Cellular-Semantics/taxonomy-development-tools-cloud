import os
import json
import jwt
from typing import Any, Dict

from hkdf import Hkdf
from jose.jwe import decrypt, encrypt


DEFAULT_USER = "visitor"

def get_session_info(rqst):
    user = DEFAULT_USER
    email = None
    repo_org = None

    if rqst.args.get('token'):
        token = rqst.args.get('token')
        email, repo_org, user = decode_simple_token(token, os.getenv('TOKEN_SECRET'))
    elif rqst.cookies and 'tdtAuthToken' in rqst.cookies:
        token = rqst.cookies.get('tdtAuthToken')
        email, repo_org, user = decode_simple_token(token, os.getenv('TOKEN_SECRET'))
    # elif rqst.cookies and 'authjs.session-token' in rqst.cookies:
    #     token = rqst.cookies.get('authjs.session-token')
    #     email, repo_org, user = decode_encrypted_token(token, os.getenv('NEXTAUTH_SECRET'))
    # elif rqst.cookies and '__Secure-authjs.session-token' in rqst.cookies:
    #     token = rqst.cookies.get('__Secure-authjs.session-token')
    #     email, repo_org, user = decode_encrypted_token(token, os.getenv('NEXTAUTH_SECRET'))
    return user, email, repo_org


def decode_simple_token(token: str, secret):
    decoded = jwt.decode(token, secret, algorithms=['HS256'])
    user = decoded.get('name')
    email = decoded.get('email')
    repo_org = decoded.get('repoOrg')
    return email, repo_org, user


def __encryption_key(secret: str):
    return Hkdf(bytes("authjs.session-token","utf-8"), bytes(secret, "utf-8")).expand(b"Auth.js Generated Encryption Key (authjs.session-token)", 64)


def encode_jwe(payload: Dict[str, Any], secret: str):
    data = bytes(json.dumps(payload), "utf-8")
    key = __encryption_key(secret)
    return bytes.decode(encrypt(data, key), "utf-8")


def decode_encrypted_token(token: str, secret: str):
    e_key=  __encryption_key(secret)
    decrypted = decrypt(token,e_key)

    if decrypted:
        token_content = json.loads(bytes.decode(decrypted, "utf-8"))
        user_name = None
        if token_content.get('user'):
            user_name = token_content.get('user').get('username')
        return token_content.get('email'), None, user_name
    else:
        return None, None, None
import os
import dotenv
import bottle
import re
import pytz
import subprocess
import re
import hashlib
import base64
import json
import datetime


dotenv.load_dotenv(dotenv.find_dotenv())

bottle.TEMPLATE_PATH.append('./gokart')
bottle.debug(True)
bottle.BaseRequest.MEMFILE_MAX = 20 * 1024 * 1024

BASE_PATH = os.path.dirname(__file__)
BASE_DIST_PATH = os.path.join(os.path.dirname(BASE_PATH),"dist")
ENV_TYPE = (os.environ.get("ENV_TYPE") or "prod").lower()

STATIC_SERVICE=os.environ.get("STATIC_SERVICE") or "https://static.dbca.wa.gov.au"

PERTH_TIMEZONE = datetime.datetime.now(pytz.timezone('Australia/Perth')).tzinfo

class Setting(object):
    @staticmethod
    def getBool(name,defaultValue=None):
        value = os.environ.get(name)
        if value is None:
            return defaultValue
        else:
            return True if value.lower() in ("true","yes","t","y") else False

    @staticmethod
    def getString(name,defaultValue=None):
        return os.environ.get(name,defaultValue)

session_key_header = "X-Session-Key"
sso_cookie_name = os.environ.get("SSO_COOKIE_NAME") or "dbca_wa_gov_au_sessionid"
def get_session_cookie():
    """ 
    Get the session cookie from user request for sso
    if not found, return None
    """
    try:
        #import ipdb;ipdb.set_trace()
        session_key = bottle.request.get_header(session_key_header)
        if session_key:
            return session_key
        else:
            raise bottle.HTTPError(status=401)
    except:
        raise bottle.HTTPError(status=401)

def get_file_md5(f):
    get_md5 = subprocess.Popen(["md5sum",f], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    get_md5_output = get_md5.communicate()

    if get_md5.returncode != 0:
        raise bottle.HTTPError(status=500,body="Generate file md5 failed.{}".format(get_md5_output[1]))

    return get_md5_output[0].split()[0]


def getMd5(data):
    m = hashlib.md5()
    m.update(data)
    data = base64.urlsafe_b64encode(m.digest())
    if data[-3:] == "===":
        return data[0:-3]
    elif data[-2:] == "==":
        return data[0:-2]
    elif data[-1:] == "=":
        return data[0:-1]
    else:
        return data


#get type name from url
typename_re = re.compile("typenames?=\s*(?P<name>[a-zA-Z0-9_\-\:\%]+)\s*",re.DOTALL)
def typename(url):
    m = typename_re.search(url.lower())
    return m.group('name').replace("%3a",":") if m else None



def datetime_encoder(self,o):
    if isinstance(o,datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    else:
        raise TypeError("Unknown type {}".format(type(o)))
json.JSONEncoder.default = datetime_encoder

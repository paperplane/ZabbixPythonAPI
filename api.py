#! /usr/bin/env python2.7

__version__ = '1.0.0'
__author__='paperplane'

'''
Python Client SDK For Zabbix API
'''


import json 
import urllib2
import logging
import pprint

urllib2.socket.setdefaulttimeout(10)

#============LOG SECTION==============#
class Singleton(object):
    def __new__(cls,*args,**kwargs):
        if '_inst' not in vars(cls):
            cls._inst = super(Singleton,cls).__new__(cls,*args,**kwargs)
        return cls._inst

class Logger(Singleton):
    '''
    logging is wired, so make sure do that only once.
    '''
    _no_handlers = True
    def __init__(self,logfilepath='/var/log/zabbix.log'):
        self._setup_logging()
        if self._no_handlers:
            self._setup_handlers(logfilepath=logfilepath)

    def _setup_logging(self):
        self.logger = logging.getLogger('Zabbix API')

    def _setup_handlers(self,logfilepath='/var/log/zabbix.log'):
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(logfilepath,'a')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self._no_handlers = False

#============CALL SECTION=============#
def checkparams(func):
    '''
    check parameter conflicts.
    '''
    def wrapper(client,operation,method,*args,**kw):
        if args and kw:
            message = 'parameters error! both list and dict params in the same method'
            Logger().logger.error(message)
            raise ZabbixAPIException(message)
        return func(client,operation,method,*args,**kw)
    return wrapper

def checkauth(func):
    def wrapper(client,operation,method,*args,**kw):
        if not client.auth:
            message = 'auth error! please login'
            Logger().logger.error(message)
            raise ZabbixAPIException(message)
        return func(client,operation,method,*args,**kw)
    return wrapper

@checkparams
@checkauth
def do_post(client,operation,method,*args,**kw):
    '''
    do http_post for zabbix api method.
    '''
    headers = {"Content-Type": "application/json"}
    params = None
    if args:
        params = args
    else:
        params = kw
    print params
    request = urllib2.Request(client.url,client.json_obj(method+'.'+operation,params),headers)
    try:
        result = urllib2.urlopen(request)
    except urllib2.URLError:
        message = 'URLError! API calls failed'
        Logger.logger.error(message)
        raise ZabbixAPIException()
    else:
        result = json.loads(result.read())
        if 'error' in result:
            message = result['error']
            Logger().logger.error(message)
            raise ZabbixAPIException(message)
        Logger().logger.info('API calls succeed with resource: %s, action: %s'%(method,operation))
        return result['result']

#============EXCEPTION SECTION=============#
class ZabbixAPIException(Exception):
    '''
    raise APIError with Error Message.
    '''
    def __init__(self,message):
        self.message = message
    
    def __str__(self):
        return repr(self.message)


#=============API OBJECT SECTION=============#
class APIClient(object):
    '''
    API Client For Zabbix.
    '''
    def __init__(self,domain,username,password):
        self.url = domain.rstrip('/')+'/api_jsonrpc.php'
        self.username = username
        self.password = password
        self.auth = ''
        self.logger = Logger().logger
        self.object_list =  ['user','host','item','template','action']
        self.id = 0

    def login(self):
        '''
        user login
        '''
        user_info = {'user':self.username,
            'password':self.password
        }
        obj = self.json_obj('user.login',user_info)

        response = self.do_request(obj)
        if 'error' in response:
            message = response['error']
            self.logger.error(message)
            raise ZabbixAPIException(message)
        self.auth = response['result']
        self.logger.info('zabbix login with user: %s, version: %s' % (self.username,self.version()))

    def version(self):
        '''
        return api version.
        '''
        version_obj = self.json_obj('apiinfo.version',[])
        return self.do_request(version_obj)['result']

    def json_obj(self,method,params):
        '''
        request json object in zabbix api.
        '''
        obj = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth":self.auth,
            "id": self.id
        }
        return json.dumps(obj)

    def do_request(self,json_obj):
        '''
        use for login and get version.
        '''
        headers = {"Content-Type": "application/json"}
        request = urllib2.Request(self.url,json_obj,headers)
        try:
            result = urllib2.urlopen(request)
        except urllib2.URLError:
            message = 'URLError error! login fails'
            self.logger.error(message)
            raise ZabbixAPIException(message)
        else:
            return json.loads(result.read())

    def __getattr__(self,attr):
        if '__'in attr:
            return getattr(self.get,attr)
        return _Callable(self,attr)


class _Callable(object):
    def __init__(self,client,method):
        self.client = client
        self.method = method
    def __getattr__(self,attr):
        operations = ['create','delete','exists','get','getobjects','isreadable','iswritable','massadd','massremove','massupdate','update']
        if attr in operations:
            return _Executable(self.client,attr,self.method)
        method = '%s.%s'%(self.method,attr)
        return _Callable(self.client,method)
    def __str__(self):
        return '%s'%(self.method)

class _Executable(object):
    def __init__(self,client,operation,method):
        self.client = client
        self.operation = operation
        self.method = method
    def __call__(self,*args,**kw):
        return do_post(self.client,self.operation,self.method,*args,**kw)
    def __str__(self):
        return '%s %s'%(self.operation,self.method)

#=================TEST SECTION=================#
def main():
    api = APIClient(domain='http://monitor.example.com',username='api',password='api')
    api.login()
    res = api.host.get(output=['available','maintenance_type','maintenances','ipmi_username', 'snmp_disable_until'],filter={"host": ['caijingDBslave179','CMPP-16','CMPP-09']})
    pprint.pprint(res,width=60) 
if __name__ == '__main__':
    main()

#! /usr/bin/env python2.7

'''
simple cli tools for zabbix api
it is in development
more function to be added
better realization of the method remains to be found
'''

import argparse
import api
import sys
from getpass import getpass

def auth_opt():
    parser = argparse.ArgumentParser(add_help=False)

    group = parser.add_argument_group('authentication')
    group.add_argument('-s','--server',action='store',default='http://monitor.example.com',help='zabbix server url')
    group.add_argument('-u','--user',action='store',default='api',help='zabbix user name')
    group.add_argument('-p','--password',action='store',default='api',help='zabbix user password')
    return parser

def get_options():
    '''
    commad line options
    '''
    parser = argparse.ArgumentParser(prog='zabbix',parents=[auth_opt()],)

    subparsers = parser.add_subparsers(help='method support currently',dest='method')

    create_parser = subparsers.add_parser('create',help='Create zabbix object')
    create_parser.add_argument('object',action='store',choices=('user','host'),help='zabbix object to create')
    create_parser.add_argument('--passwd',action='store',help='new user password')
    create_parser.add_argument('--usrgrps',action='store',help='group that user belong to')
    create_parser.add_argument('--groups',action='store',help='host groups to add the host to')
    create_parser.add_argument('--interfaces',action='store',help='interfaces to be created for the host')

    delete_parser = subparsers.add_parser('delete', help='Remove zabbix object')
    delete_parser.add_argument('object', action='store',choices=('user',),help='The zabbix object to remove')
    delete_parser.add_argument('--userid',action='store',help='id of the user to remove')

    get_parser = subparsers.add_parser('get', help='Get zabbix object information')
    get_parser.add_argument('object', action='store',choices=('user','host','item'),help='Zabbix object to get')
    get_parser.add_argument('--output',action='store',help='choose attribute of the object to display')
    
    parser.add_argument('--version', action='version',version = '%(prog)s 1.0')
    return parser

def show_help(parser):
    parser.print_help()
    sys.exit(1)

def main():
    options = get_options().parse_args()

    print options
    if not options.server:
        show_help(get_options())

    if not options.user:
        options.user = raw_input('username:')
    
    if not options.password:
        options.password = getpass()

    zapi = api.APIClient(options.server,options.user,options.password)
    method = options.method
    object = options.object
    zapi.login()
    try:
        obj = getattr(zapi,object)
    except:
        print >> sys.stderr, 'object not support'
        sys.exit(1)
    try:
        func = getattr(obj,method)
    except:
        print >> sys.stderr, 'method not support'
        sys.exit(1)
   
    if method == 'get':
        print func(output=options.output)
    elif method == 'delete':
        print func(userid=options.userid) 
    else:
        func(passwd=options.passwd,usrgrps=options.usrgrps,groups=options.groups,interfaces=options.interfaces)

if __name__ == '__main__':
    main()

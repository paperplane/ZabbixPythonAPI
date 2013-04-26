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
    create_parser.add_argument('--passwd',action='store',type=str,help='new user password')
    create_parser.add_argument('--usrgrps',action='append',type=eval,help='group that user belong to')
    create_parser.add_argument('--groups',action='append',type=eval,help='host groups to add the host to')
    create_parser.add_argument('--interfaces',action='append',type=eval,help='interfaces of the host to be created')
    create_parser.add_argument('--applications',action='append',type=str,help='applaications of the item to be created')

    delete_parser = subparsers.add_parser('delete', help='Remove zabbix object')
    delete_parser.add_argument('object', action='store',choices=('user','host','item'),help='The zabbix object to remove')
    delete_parser.add_argument('--userid',action='append',type=eval,help='ids of the user to remove')
    delete_parser.add_argument('--hostid',action='append',type=eval,help='ids of the host to remove')
    delete_parser.add_argument('--itemid',action='append',type=str,help='ids of the item to remove')

    get_parser = subparsers.add_parser('get', help='Get zabbix object information')
    get_parser.add_argument('object', action='store',choices=('user','host','item'),help='Zabbix object to get')
    get_parser.add_argument('-o','--output',action='append',dest='output',help='choose attribute of the object to display')
    get_parser.add_argument('-f','--filter',type=eval,dest='filter',help='filter for zabbix object in dict type')
    
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
        print func(output=options.output,filter=options.filter)
    elif method == 'delete':
        print func(userid=options.userid,hostid=options.hostid,itemid=options.itemid) 
    else:
        func(passwd=options.passwd,usrgrps=options.usrgrps,groups=options.groups,interfaces=options.interfaces,applications=options.applications)

if __name__ == '__main__':
    main()

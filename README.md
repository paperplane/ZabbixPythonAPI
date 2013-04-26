ZabbixPythonAPI
===============

Zabbix SDK and CLI Tools use Zabbix API. At present this API provides:

+ Zabbix Python SDK
+ Zabbix CommandLine Tools Based on this SDK

Developed and mantained by Junqi Lee(paperplane). Please feel free to report bugs and your suggestions.

***

##API Usage##

First, refer to API document. Use <strong>host.get</strong> as an example.

    API:
    integer/array host.get(object parameters)

    Request Method:
    POST

    Request Parameters:
    {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": "extend",
            "filter": {
                "host": [
                    "Zabbix server",
                    "Linux server"
                ]
            }
        },
        "auth": "038e1d7b1735c6a5436ee9eae095879e",
        "id": 1
    }


Then,we will call this api in the way api.host.get(). but how to call this api:

+ Initilize the api client

    api = 

+ Login to get authid

    api.login()

+ Call the api

    api.host.get()

Notice: Json Format Request Params translate to key=value parameters.

***

##Command Line Tools Usage##

Currently support cli:

    create user
    create host
    create itme
    get    user
    get    host
    get    item
    delete user
    delete host
    delete item

Every method has an example to show how to use. For detailed information,use --help/-h.




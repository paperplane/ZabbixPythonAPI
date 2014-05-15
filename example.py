from zbxadmin.api import APIClient, ZabbixAPIException, Logger
import re, subprocess

class ScreenCreate():
    def __init__(self,  hostgroup, hostlist, proclist, itemlist, itemalias):
        self.api = APIClient(domain='http://localhost',username='Admin',password='Zabbix')
        self.api.login()
        self.itemvalue = {'test1':3,'test2':1} #item key => value unit
        self.hostgroup = hostgroup
        self.hostlist = hostlist
        self.proclist = proclist
        self.itemlist = itemlist
        self.aliasdict = dict(zip(itemlist,itemalias)) #itemalias is the item list display on ui

    def host_create_or_update(self, hostgroup, hostlist):
        """
        create group and host
        """
        api = self.api
        hostdict = {} #host name => host id
        interface = {} #host name => host interface

        #create zabbix group then return groupid. if this group exist then return groupid directly.
        groupid = api.hostgroup.get(filter={"name": self.hostgroup]})
        if groupid:
            groupid = groupid[0]['groupid']
            Logger().logger.info('Update Exists Group: %s'% self.hostgroup)
        else:
            groupid = api.hostgroup.create(name=self.hostgroup)['groupids'][0] #temp added. future will be deleted
            Logger().logger.info("Create New Group, %s " % self.hostgroup)

        for hostname in self.hostlist:
            #Every Zabbix Hosts Will be the same. If this zabbix hosts not on the server, 'ip' parameter will be diffenence.
            hostid = api.host.get(output="hostid", filter={"host":[hostname], "groupids": [groupid]})
            if hostid:
                hostdict[hostname] = hostid[0]['hostid']
                Logger().logger.info('Update Exist Host: %s'% hostname)
            else:
                hostdict[hostname] = api.host.create(host=hostname,interfaces=[{"type": 1,"main": 1,"useip": 1,"ip": "127.0.0.1","dns": "","port": "10050"}],groups=[{"groupid":groupid}])['hostids'][0]
                Logger().logger.info('Create New Host: %s'% hostname)

            interface[hostname] = api.hostinterface.get(hostids=hostdict[hostname],output="interfaceid")[0]['interfaceid']
        return (hostdict, interface)

        
    def create_bulk_proc(self, hostdict, interface):
        """
        multi proc one graph
        """
        api = self.api
        itemdict = {} #item name<-->display name

        screenitemdict = {} #screen item objects list
        for itemname in self.itemlist:
            x = 0 #screen item X-location
            y = 0 #screen item y-location
            procid = filter(lambda ch: ch not in '0123456789', self.proclist[0])
            for hostname in self.hostlist:
                gitemlist = []
                itemidlist = []
                colorlist = ['0000BB','00BB00','BB0000','00BBBB','BB00BB','BBBB00','888888','000033','003300','330000','003333','330033','333300','000000']
                for procname,color in zip(self.proclist,colorlist):
                    #itemname display on frontweb
                    itemdict[itemname] = "%s %s %s" % (hostname, procname, aliasdict.get(itemname, itemname))
                    #keyname store in zabbix database
                    item_key = self.hostgroup + '.' + procname + '.' + itemname

                    #create new item. query it if exist. then return item id. first check self.itemvalue if exists. 
                    valuetype = self.itemvalue.get(itemname, 0)
           
                    item = api.item.get(hostids=hostdict[hostname], search={"key_": item_key}, output=["itemid","name"])
                    if item:
                        itemid = item[0]["itemid"]
                        name = item[0]["name"]
                        if name != itemdict[itemname]: 
                            api.item.update(itemid=itemid, name=itemdict[itemname])
                            Logger().logger.info('Update Item Name: %s ' % itemname )
                    else:
                        itemid = api.item.create(name=itemdict[itemname],hostid=hostdict[hostname],key_=item_key,type=2,value_type=valuetype,interfaceid=interface[hostname],delay=60,history=14)['itemids'][0]
                        Logger().logger.info('Create New Item: %s ' % itemname )
                    gitemlist.append({"itemid": itemid, "color": color}) 
                    itemidlist.append(itemid)

                #create graph. one item with one graph. query it if exist. then return item id.
                graphname = "%s %s %s" % (hostname, procid, aliasdict.get(itemname, itemname))
                graph = api.graph.get(hostids=hostdict[hostname], itemids=itemidlist, output=["graphid","name"])
                if graph:
                    graphid = graph[0]['graphid']
                    name = graph[0]['name']
                    if name != graphname:
                        api.graph.update(graphid=graphid, name=graphname)
                        Logger().logger.info('Update Graph Name: %s ' % itemname )
                else:
                    graphid = api.graph.create(name=graphname, width=900, height=200, gitems=gitemlist)['graphids'][0]
                    Logger().logger.info("Create New Graph: %s " % itemname)
                    
                screenitemdict.setdefault(procid + '::' + itemname, []).append({"resourcetype": 0, "resourceid": graphid, "width": "500", "rowspan": 0, "colspan": 0, "heigth": "100", "x": str(x), "y": str(y)})
                y += 1 # one row so alway x == 0
        return self.screen_create_or_update(screenitemdict)

    def screen_create_or_update(self, screenitemdict):
        for itemgraph, screenitemlist in screenitemdict.iteritems():
            #create zabbix screen object
            procname, itemname = itemgraph.split('::')
            screenname = "%s %s %s" % self.hostgroup, procname, self.aliasdict.get(itemname, itemname))
            screenid = api.screen.get(filter={"name":[screenname]})
            if screenid:
                screenid = screenid[0]['screenid']
                api.screen.update(screenid=screenid, name=screenname, screenitems=screenitemlist)
                Logger().logger.info('Update Exists Screen: %s' % screenname)
            else:
                screenid = api.screen.create(name=screenname, vsize=len(self.hostlist), hsize=1, screenitems=screenitemlist)
                Logger().logger.info('Create New Screen: %s' % screenname)
        return "Success! Update Success!"


    def create_single_proc(self, hostdict, interface):
        """
        one proc name one graph
        """
        api = self.api
        itemdict = {} #item name => display name

        screenitemdict = {} #screen item objects list
        for itemname in self.itemlist:
            for procname in self.proclist:
                x = 0 #screen item X-location
                y = 0 #screen item y-location
                for hostname in self.hostlist:
                    #itemname display on frontweb
                    itemdict[itemname] = "%s %s %s" % (hostname, procname, aliasdict.get(itemname, itemname))
                    #keyname store in zabbix database
                    item_key = self.hostgroup + '.' + procname + '.' + itemname

                    #create new item. query it if exist. then return item id. first check self.itemvalue if exists. 
                    valuetype = self.itemvalue.get(itemname, 0)
                    #itemid = api.item.get(hostids=hostdict[hostname], groupids=groupid, search={"name": itemdict[itemname] }, output="itemid")
                    item = api.item.get(hostids=hostdict[hostname], search={"key_": item_key}, output=["itemid","name"])
                    if item:
                        itemid = item[0]["itemid"]
                        name = item[0]["name"]
                        if name != itemdict[itemname]: 
                            api.item.update(itemid=itemid, name=itemdict[itemname])
                            Logger().logger.info('Update Item Name: %s ' % itemname )
                    else:
                        itemid = api.item.create(name=itemdict[itemname],hostid=hostdict[hostname],key_=item_key,type=2,value_type=valuetype,interfaceid=interface[hostname],delay=60,history=14)['itemids'][0]
                        Logger().logger.info('Create New Item: %s ' % itemname )

                    #create graph. one item with one graph. query it if exist. then return item id.
                    graph = api.graph.get(hostids=hostdict[hostname], itemids=itemid, output=["graphid","name"])
                    if graph:
                        graphid = graph[0]['graphid']
                        graphname = graph[0]['name']
                        if graphname != itemdict[itemname]:
                            api.graph.update(graphid=graphid, name=itemdict[itemname])
                            Logger().logger.info('Update Graph Name: %s ' % itemname )
                    else:
                        graphid = api.graph.create(name=itemdict[itemname], width=900,height=200,gitems=[{"itemid": itemid, "color": "00AA00"}])['graphids'][0]
                        Logger().logger.info("Create New Graph: %s " % itemname)
                    
                    screenitemdict.setdefault(procname + '::' + itemname, []).append({"resourcetype": 0, "resourceid": graphid, "width": "500", "rowspan": 0, "colspan": 0, "heigth": "100", "x": str(x), "y": str(y)})
                    y += 1 # one row so alway x == 0
        return self.screen_create_or_update(screenitemdict)

class DeleteScreen():
    '''support two types, two modes'''
    def __init__(self, hostgroup, hostlist, hostflag='host', hostname=''):
        self.api = APIClient(domain='http://localhost',username='Admin',password='zabbix@sogou-inc.com')
        self.api.login()
        self.hostgroup = hostgroup
        self.hostlist = hostlist
        self.hostflag = hostflag
        self.hostname = hostname
        
    def delete_single(self):
        api = self.api
        groupid = api.hostgroup.get(filter={"name":[self.hostgroup]})
        if groupid:
            groupid = groupid[0]['groupid']
        else:
            Logger().logger.error("Delete Error: %s group not found!" % self.hostgroup)
            return "Delete Failed: %s group not found!" % self.hostgroup

        if self.hostflag == 'host' :
            if not self.hostname:
                Logger().logger.error('Delete Host Failed: HostGroup %s Hostname Need Provide.' %s self.hostgroup)
                return 'Delete Host Failed: HostGroup %s Hostname Need Provide.' %s self.hostgroup
            hostid = api.host.get(output="hostid", filter={"host":[self.hostname], "groupids": [groupid]})
            if hostid:
                hostid = hostid[0]['hostid']
                api.host.delete(hostid)
                Logger().logger.info("Delete Hosts Success: %s %s" % (self.hostgroup, self.hostname))
            else:
                Logger().logger.error("Delete Hosts Error: %s %s Not Found Host" % (self.hostgroup, self.hostname))
                return "Delete Hosts Failed: %s %s Not Found Host" % (self.hostgroup, self.hostname)
            if not self.hostlist:
                api.hostgroup.delete(groupid)
                Logger().logger.info("Delete Group Success: %s %s" % (self.hostgroup, self.hostname))
        else:
            for hostname in self.hostlist:
                hostid = api.host.get(output="hostid", filter={"host":[hostname], "groupids": [groupid]})
                if hostid:
                    hostid = hostid[0]['hostid']
                    api.host.delete(hostid)
                    Logger().logger.info("Delete Hosts Success: %s %s" % (self.hostgroup, hostname))
                else:
                    Logger().logger.error("Delete Failed: %s %s Not Found Host" % (self.hostgroup, hostname))
                    return "Delete Hosts Failed: %s %s Not Found Host" % (self.hostgroup, hostname)
            api.hostgroup.delete(groupid)
            Logger().logger.info("Delete Group Success: %s %s" % (self.hostgroup, self.hostname))

        #returnstr = update_screen_list(hostgroup, hostlist, proclist, itemlist)
        #if "Failed" in returnstr:
        #    Logger().logger.error("Failed! Delete %s Then Update %s Failed!" % (hostname, hostgroup))
        #    return "Failed! Delete Then Update Failed!"
        #Logger().logger.info("Success! Delete %s Then Update %s Success!" % (hostname, hostgroup))
        return "Success! Delete Then Update Success!"

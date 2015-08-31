# -*- coding: utf-8 -*-
"""
codac.archiveadd
==========
@authors: timo.schroeder@ipp-hgw.mpg.de
data rooturl database view    project strgrp stream idx    channel
lev  0       1        2       3       4      5      6      7
"""
from re import compile
from .support import error,setTIME
from .base import Path
from .classes import browser
re = compile('[A-Z]+[0-9]+')
import sys
if sys.version_info.major==3:
    xrange=range
    long=int

def addW7X(treename='test',shotnumber=-1,time=['2015/07/01-12:00:00.000000000','2015/07/01-12:30:00.000000000']):
    from MDSplus import Tree
    name = "raw"
    path = Path("/ArchiveDB/raw/W7X").url()
    with Tree(treename,shotnumber,'New') as tree:
        try:
            timeNode=tree.addNode('TIMING','NUMERIC')
            timeNode.addTag('TIME')
            tree.write()
        except:
            pass
        setTIME(time) # [\T_START,\T_END]
        try:
            tree.deleteNode(name)
        except:
            pass
        addProject(tree,name,'',path)
        tree.write()
        tree.close


def addProject(node,nname,name='',url=[]):
    from re import compile
    cap = compile('[^A-Z]')
    if name!='':
        node = node.addNode(nname,'STRUCTURE')
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    if  url==[]: url = codac_url(node)
    urlNode = node.addNode('$URL','TEXT');urlNode.putData(url)
    url = str(urlNode.data())
    b = browser(url)
    streamgroups = b.list_streamgroups()
    for s in streamgroups:
        cnname = s.split('.')
        cnname[0] = cap.sub('',cnname[0])
        addStreamgroup(node,''.join(cnname),s)

def addStreamgroup(node,nname,name='',url=[]):
    from re import compile
    cap = compile('[^A-Z]')
    if name!='':
        node = node.addNode(nname,'STRUCTURE')
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    if  url==[]: url = codac_url(node)
    urlNode = node.addNode('$URL','TEXT');urlNode.putData(url)
    node.addNode('$CFGLOG','ANY').putData(codac_cfglog(node))
    url = str(urlNode.data())
    b = browser(url)
    streams,contents = b.list_streams()
    for stream,content in zip(streams,contents):
        cnname = stream.split('.')
        cnname[0] = cap.sub('',cnname[0])
        cnname = ''.join(cnname)
        if 'DATASTREAM' in content:
            addStream(node,cnname,stream)
        elif 'PARLOG' in content:
            plogNode = node.addNode(cnname,'STRUCTURE')
            if re.match(cnname) is not None:
                print(cnname)
                try:
                    plogNode.addTag(cnname)
                except:
                    print(cnname)
            plogNode.addNode('$URL','TEXT').putData(codac_url(plogNode))
            plogNode.addNode('$NAME','TEXT').putData(stream)
            addParlog(plogNode)


def addStream(node,nname,name='',url=[]):
    if name!='':
        node = node.addNode(nname,'SIGNAL')
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    node.putData(codac_stream(node))
    if  url==[]: url = codac_url(node)
    node.addNode('$URL','TEXT').putData(url)
    chanDescs = addParlog(node)
    for i in xrange(len(chanDescs)):
        addChannel(node,'CH'+str(i),i,chanDescs[i])
        
def addParlog(node):
    from interface import read_parlog
    from support import fixname12
    try:
        time = node.getNode('\TIME')
        url = str(node.getNode('$URL').data())
        dist = read_parlog(url,time)
    except:
        print(error())
        node.addNode('$PARLOG','ANY').putData(codac_parlog(node))
        return []
    if dist.has_key('chanDescs'): chanDescs = dist['chanDescs']; del(dist['chanDescs'])
    else: chanDescs=[]
    if len(dist):
        parNode = node.addNode('$PARLOG','STRUCTURE')
        for k,v in dist.items():
            try:
                k = fixname12(k)
                if isinstance(v,(str)):
                    parNode.addNode(k,'TEXT').putData(v)
                elif isinstance(v,(int, float)):
                    parNode.addNode(k,'NUMERIC').putData(v)
                elif isinstance(v,(list)) and isinstance(v[0],(int, float)):
                    parNode.addNode(k,'NUMERIC').putData(v)
                elif isinstance(v,(unicode)):
                    parNode.addNode(k,'TEXT').putData(v.encode('CP1252','backslashreplace'))
            except:
                print(node.MinPath)
                print(k)
                print(v)
    return chanDescs

def addChannel(node,nname,idx,chan={},url=[]):
    from support import fixname12
    node = node.addNode(nname,'SIGNAL')
    node.putData(codac_channel(node))
    if url==[]: url = codac_url(node)
    node.addNode('$URL','TEXT').putData(url)
    nameNode = node.addNode('$NAME','TEXT');
    node.addNode('$IDX','NUMERIC').putData(idx)
    for k,v in chan.items():
        try:
            if k=='physicalQuantity':
                pass
            elif k=='active':
                v = int(v)
                node.setOn(v!=0)
            elif k=='name':
                try:
                    if isinstance(v,(unicode)):
                        v = v.encode('CP1252','backslashreplace')
                except:
                    pass               
                nameNode.putData(v)
            else:
                k = fixname12(k)
                if isinstance(v,(str)):
                    node.addNode(k,'TEXT').putData(v)
                elif isinstance(v,(int, float, list)):
                    node.addNode(k,'NUMERIC').putData(v)
                elif isinstance(v,(unicode)):
                    node.addNode(k,'TEXT').putData(v.encode('CP1252','backslashreplace'))
        except:
            print(k)
            print(v)
            error()

from MDSplus import TdiCompile
def codac_url(node):
    return TdiCompile('codac_url($)',(node,))
def codac_channel(channelNode):
    return TdiCompile('codac_signal($)',(channelNode,))
def codac_stream(streamNode):
    return TdiCompile('codac_signal($)',(streamNode,))
def codac_parlog(streamNode):
    return TdiCompile('codac_parlog($)',(streamNode,))
def codac_cfglog(streamgroupNode):
    return TdiCompile('codac_cfglog($)',(streamgroupNode,))
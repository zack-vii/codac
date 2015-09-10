"""
archive.archivebuild
==========
@authors: timo.schroeder@ipp-hgw.mpg.de
data rooturl database view    project strgrp stream idx    channel
lev  0       1        2       3       4      5      6      7
"""
from archive.classes import browser
import archive.version as _ver
    
def build(treename='test',shotnumber=-1,time=['2015/07/01-12:00:00.000000000','2015/07/01-12:30:00.000000000']):
    from archive.base import Path
    from archive.support import setTIME
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
    re  = compile('[A-Z]+[0-9]+')
    cap = compile('[^A-Z]')
    if name!='':
        node = node.addNode(nname,'STRUCTURE')
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    if  url==[]: url = archive_url(node)
    urlNode = node.addNode('$URL','TEXT');urlNode.putData(url)
    url = urlNode.data().tostring()
    if not isinstance(url,(str,)):
        url = url.decode()
    b = browser(url)
    streamgroups = b.list_streamgroups()
    for s in streamgroups:
        cnname    = s.split('.')
        cnname[0] = cap.sub('',cnname[0])
        addStreamgroup(node,''.join(cnname),s)

def addStreamgroup(node,nname,name='',url=[]):
    from re import compile
    re  = compile('[A-Z]+[0-9]+')
    cap = compile('[^A-Z]')
    if name!='':
        node = node.addNode(nname,'STRUCTURE')
        # node is stream group
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    if  url==[]: url = archive_url(node)
    urlNode = node.addNode('$URL','TEXT');urlNode.putData(url)
    node.addNode('$CFGLOG','ANY').putData(archive_cfglog(node))
    url = urlNode.data().tostring()
    if not isinstance(url,(str,)):
        url = url.decode()
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
            plogNode.addNode('$URL','TEXT').putData(archive_url(plogNode))
            plogNode.addNode('$NAME','TEXT').putData(stream)
            addParlog(plogNode)

def addStream(node,nname,name='',url=[]):
    from re import compile
    re  = compile('[A-Z]+[0-9]+')
    if name!='':
        node = node.addNode(nname,'SIGNAL')
        if re.match(nname) is not None:
            print(nname)
            node.addTag(nname)
        node.addNode('$NAME','TEXT').putData(name)
    node.putData(archive_stream(node))
    if url==[]: url = archive_url(node)
    node.addNode('$URL','TEXT').putData(url)
    chanDescs = addParlog(node)
    for i in _ver.xrange(len(chanDescs)):
        addChannel(node,'CH'+str(i),i,chanDescs[i])

def addParlog(node):
    from archive.interface import read_parlog
    from archive.support import error,fixname12
    try:
#        time = node.getNode('\TIME')
        url = node.getNode('$URL').data().tostring()
        if not isinstance(url,(str,)):
            url = url.decode()
        dist = read_parlog(url,[-1,-1])
    except:
        print(error())
        node.addNode('$PARLOG','ANY').putData(archive_parlog(node))
        return []
    if 'chanDescs' in dist.keys(): chanDescs = dist['chanDescs']; del(dist['chanDescs'])
    else: chanDescs=[]
    if len(dist):
        parNode = node.addNode('$PARLOG','STRUCTURE')
        for k,v in dist.items():
            if v is None:
                continue
            try:
                k = fixname12(k)
                if isinstance(v,(str,)):
                    parNode.addNode(k,'TEXT').putData(v)
                elif isinstance(v,(int, float)):
                    parNode.addNode(k,'NUMERIC').putData(v)
                elif isinstance(v,(list,)) and isinstance(v[0],(int, float)):
                    parNode.addNode(k,'NUMERIC').putData(v)
                elif isinstance(v,(dict,)):
                    pn = parNode.addNode(k,'ANY')
                    if not '['+str(len(v)-1)+']' in v.keys():
                        pn.putData(v.__str__())
                    else:
                        v = [v['['+str(i)+']'] for i in _ver.xrange(len(v))]
                        try:
                            pn.putData(v)
                        except:
                            pn.putData([i.__str__() for i in v])
                elif isinstance(v,(_ver.unicode,)):
                    parNode.addNode(k,'TEXT').putData(v.encode('CP1252','backslashreplace'))
            except:
                print(node.MinPath)
                print(k)
                print(v)
                print(error(1))
    return chanDescs

def addChannel(node,nname,idx,chan={},url=[]):
    from archive.support import error,fixname12
    node = node.addNode(nname,'SIGNAL')
    node.putData(archive_channel(node))
    if url==[]: url = archive_url(node)
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
                if _ver.has_unicode and isinstance(v,(_ver.unicode)):
                        v = v.encode('CP1252','backslashreplace')        
                nameNode.putData(v)
            else:
                k = fixname12(k)
                if isinstance(v,(str,)):
                    node.addNode(k,'TEXT').putData(v)
                elif isinstance(v,(int, float, list)):
                    node.addNode(k,'NUMERIC').putData(v)
                elif _ver.has_bytes and isinstance(v,(_ver.bytes,)):
                        node.addNode(k,'TEXT').putData(v.decode())
                elif _ver.has_unicode and isinstance(v,(_ver.unicode,)):
                        node.addNode(k,'TEXT').putData(v.encode('CP1252','backslashreplace'))
        except:
            print(k)
            print(v)
            error()

def archive_url(node):
    from MDSplus import TdiCompile
    return TdiCompile('archive_url($)',(node,))
def archive_channel(channelNode):
    from MDSplus import TdiCompile
    return TdiCompile('archive_signal($,IF_ERROR(_time,*))',(channelNode,))
def archive_stream(streamNode):
    from MDSplus import TdiCompile
    return TdiCompile('archive_signal($,IF_ERROR(_time,*))',(streamNode,))
def archive_parlog(streamNode):
    from MDSplus import TdiCompile
    return TdiCompile('archive_parlog($,IF_ERROR(_time,*))',(streamNode,))
def archive_cfglog(streamgroupNode):
    from MDSplus import TdiCompile
    return TdiCompile('archive_cfglog($,IF_ERROR(_time,*))',(streamgroupNode,))
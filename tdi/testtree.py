import sys
if sys.version_info.major==3:
    xrange = range

def testtree(node):
    try:
        print("python call: testtree("+str(node)+")")
        return getSignal(node.getNodeName())
    except:#return debug information
        import traceback
        trace = 'python error:\n'+traceback.format_exc()
        for line in trace.split('\n'):
            print(line)
        return(trace)
"""
SEGMENT
ntype = "ARR", "SEG"
ndims = N 1,2,3
dtype = 8,16,32,64,F,D
name  = ntype+ndims+"D"+dtype
""" 
def getSignal(name,data=False):
    from MDSplus.mdsscalar import Int8,Int16,Int32,Int64,Float32,Float64,String
    if name=='TEXT':
        return String('Wooppp!!')
    from MDSplus._tdishr  import TdiCompile
    from MDSplus.mdsarray import Int8Array,Int16Array,Int32Array,Int64Array,Float32Array,Float64Array
    if name=='IMAGE':
        if data:
            return TdiCompile('DATA:ARR1D32')
        else:
            name='ARR1D32'
    if name=='IMAGES':
        if data:
            return TdiCompile('DATA:ARR2D32')
        else:
            name='ARR2D32'

    from re import findall as parse
    shapes=((10000,), (600,800), (64,64,64), (32,32,32,32), (16,16,16,16,16))
    dtypes= {"8"  : (Int8,       Int8Array,      'BYTE'     , 0x100),
             "16" : (Int16,      Int16Array,     'WORD'     , 0x100),
             "32" : (Int32,      Int32Array,     'LONG'     , 0x100),
             "64" : (Int64,      Int64Array,     'QUADWORD' , 0x10000),
             "F"  : (Float32,    Float32Array,   'FLOAT'    , 1.1),
             "D"  : (Float64,    Float64Array,   'D_FLOAT'  , 1.01)}
  
    m = parse("(ARR|SEG|NUM)(?:([0-9]*)D|)([0-9FD]+)(?:_([0-9]+))?",name.upper())[0]
    ntype = m[0]
    ndims = int(m[1]) if not m[1]=='' else 1
    dtype = m[2]
    shape = shapes[ndims] if ndims<5 else (4,)*ndims
    pysfun = dtypes[dtype][0]
    pyafun = dtypes[dtype][1]
    tdifun = dtypes[dtype][2]
    factor = dtypes[dtype][3]
    from MDSplus.compound import Range,Signal
    from numpy import pi,cos,array
    
    if ntype=='NUM':
        return pysfun(pi)

    def fun(x):
        return((cos(2*pi*x)+1.)/2.)
    def time(N):
        return Range(0., 1., 1./(N-1)).setUnits("time")
    def axis(N,idx):
        return Range(0., 1., 1./(N-1)).setUnits("dim_of("+str(idx)+")")

    data  = TdiCompile(tdifun+'($VALUE)').setUnits('V')

    dims = [[]]*(ndims+1)
    dims[0] = time(shape[0])
    raw = pysfun(0).data()
    tfac = 1;
    for i in xrange(ndims):
        dims[ndims-i] = X = axis(shape[ndims-i],ndims-i)
        raw = array([raw*factor+round(x*0x7F) for x in X.data()])
        tfac*= factor
    raw = array([raw+round(fun(x)*0x7F)*tfac for x in dims[0].data()])
    raw = pyafun(raw).setUnits('data')
    return Signal(data,raw,*dims).setHelp('this is the help text')

            
def createTestTree(path=None):
    import MDSplus,os
    def populate(node):
        def py(n):
            n.putData(MDSplus.TdiCompile('testtree('+n.getPath()+')'))
        ntypes=["ARR","SEG","NUM"]
        dtypes=["8","16","32","64","F","D"]
        ndims =range(3)
        py(node.addNode('IMAGE','SIGNAL'))
        py(node.addNode('IMAGES','SIGNAL'))
        py(node.addNode('TEXT','TEXT'))
        for nt in ntypes:
            for dt in dtypes:
                if nt=="NUM":
                    py(node.addNode(nt+dt,'NUMERIC'))
                else:
                    for nd in ndims:
                        py(node.addNode(nt+str(nd)+"D"+dt,'SIGNAL'))
    def evaluate(node):
        segszs=(1000, 100)
        for n in node.getMembers():
            if n.getNodeName().startswith("SEG"):
                sig = getSignal(n.getNodeName(),True)
                data= sig.data()
                segsz = segszs[data.ndim] if data.ndim<2 else 1
                for i in xrange(data.shape[0]/segsz):
                    ft  = (i*segsz,(i+1)*segsz)
                    dim = MDSplus.Dimension(sig.dim_of()[ft[0]:ft[1]]).setUnits(sig.dim_of().units)
                    img = data[ft[0]:ft[1]]
                    n.makeSegment(0,0,dim,img)
                n.setHelp(sig.getHelp())
            else:
                n.putData(getSignal(n.getNodeName(),True))

    isunix = os.name=='posix';
    if isunix:
        path = "/tmp"
    else:
        path = os.getenv('TEMP')
        os.environ["test_path"] = path
        with MDSplus.Tree('test',-1,'new') as tree:
            datanode = tree.addNode('DATA','STRUCTURE')
            pynode   = tree.addNode('PYTHON','STRUCTURE')
            populate(pynode)
            populate(datanode)
            tree.write()
            evaluate(datanode)
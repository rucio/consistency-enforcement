from .part import PartitionedList

def cmp3(a, r, b):
    """
    Performs the 3-way consistency comparison between 3 lists:
        
        a - database dump after the scan
        r - site scan results
        b - database dump before the scan
    
    Produces 2 lists:
    
        missing items - items present in both ``a`` and ``b`` but not in ``r``
        "dark" items - items present in ``r`` bit not in ``a`` nor ``b``
    
    Notice that results are symmetric with respect to swapping ``a`` and ``b``

    Parameters
    ----------
    a : iterable
    b : iterable
    r : iterable
    
    Returns
    -------
    tuple (d, m)
        d and m are dark list and missing list respectively
    """
    
    #
    # produces 2 lists:
    #
    #       D = R-A-B = (R-A)-B
    #       M = A*B-R = (A-R)*B
    #
    a_r = set(a)    # this will be A-R
    r_a = set()     # this will be R-A
    for x in r:
            try:    a_r.remove(x)
            except KeyError:
                    r_a.add(x)
    d = r_a
    m = set()
    for x in b:
            try:    d.remove(x)
            except KeyError:    pass
            if x in a_r:
                    m.add(x)
    #print("memory utilization at the end of cmp3, MB:", getMemory())
    return list(d), list(m)
    
def cmp3_missing(a, r, b):
    #       M = A*B-R
    m = set()    
    a_set = set(a)    
    for x in b:
        if x in a_set:
            m.add(x)
    del a_set                   # release memory
    for x in r:
        if x in m:
            m.remove(x)
    return list(m)
    
def cmp3_dark(a, r, b):
    #       D = R-A-B = (R-A)-B
    d = set(r)     
    for x in a:
        try:    d.remove(x)
        except KeyError: pass
    for x in b:
        try:    d.remove(x)
        except KeyError: pass
    return list(d)
            
def lines(f):
    l = f.readline()
    while l:
        yield l
        l = f.readline()

def cmp3_lists(a_list, r_list, b_list):
    assert a_list.NParts == r_list.NParts and r_list.NParts == b_list.NParts, "Inconsistent number of parts: B:%d, R:%d, A:%d" % (
        b_list.NParts, r_list.NParts, a_list.NParts)

    d_list, m_list = [], []
    for i, (ap, rp, bp) in enumerate(zip(a_list.partitions, r_list.partitions, b_list.partitions)):
            #print("Comparing %s %s %s..." % (an, rn, bn))
            d, m = cmp3(lines(af), lines(rf), lines(bf))
            d_list += d
            m_list += m
            print("Partition %d compared: dark:%d missing:%d" % (i, len(d), len(m))) 
    return d_list, m_list

def cmp3_generator(a_list, r_list, b_list, stream=None):
    """
    Performs the 3-way consistency comparison between 3 partitoined lists:
        
        a_list - database dump after the scan
        r_list - site scan results
        b_list - database dump before the scan
    
    Produces:
    
        missing items - items present in both ``a`` and ``b`` but not in ``r``
        "dark" items - items present in ``r`` bit not in ``a`` nor ``b``
    
    Notice that results are symmetric with respect to swapping ``a`` and ``b``

    Parameters
    ----------
    a : ParitionedList object
    b : ParitionedList object
    r : ParitionedList object
    stream : str or None
        output stream selection, "d" or "m" or None
    
    Returns
    -------
    geretator of tuples (<stream>, <item>)
       ``stream`` is eirher "d" or "m" or None. "d" will select only "dark" items, "m" will select only missing items and
        None will return all
    
    Notes
    -----
    The order in which items are retruned is not specified and may change depending on the implementation details.
    
    Number of partitions in all 3 lists must be the same.
    """

    assert a_list.NParts == r_list.NParts and r_list.NParts == b_list.NParts, "Inconsistent number of parts: B:%d, R:%d, A:%d" % (
        b_list.NParts, r_list.NParts, a_list.NParts)

    d_list, m_list = [], []
    for i, (ap, rp, bp) in enumerate(zip(a_list.partitions, r_list.partitions, b_list.partitions)):
            #print("Comparing %s %s %s..." % (an, rn, bn))
            if stream is None:
                d, m = cmp3(ap, rp, bp)
                yield from (('d',f) for f in d)
                yield from (('m',f) for f in m)
            elif stream == 'd':
                yield from cmp3_dark(ap, rp, bp)
            elif stream == 'm':
                yield from cmp3_missing(ap, rp, bp)

def cmp3_parts(a_prefix, r_prefix, b_prefix):
    a_list = PartitionedList.open(a_prefix)
    r_list = PartitionedList.open(r_prefix)
    b_list = PartitionedList.open(b_prefix)
    return cmp3_lists(a_list, r_list, b_list)

import time

class Tracer(object):

    def __init__(self, path="", tzero=0.0, calibrate=False):
        self.Path = path
        self.Points = {}
        self.TZero = tzero
        if calibrate:   self.calibrate()

    def __getitem__(self, name):
        point = self.Points.get(name)
        if point is None:
            path = name if not self.Path else self.Path + '/' + name
            point = self.Points[name] = TracePoint(name, path, self.TZero)
        return point

    def stats(self):
        out = []
        for n, p in self.Points.items():
            out += p.stats()
        return sorted(out)

    def format(self, as_list=False):
        stats = self.stats()
        maxp = 4
        for t in stats:
            path = t[0]
            maxp = max(len(path), maxp)
        headfmt = f"%-{maxp}s %8s %8s %8s"
        datafmt = f"%-{maxp}s %8d %8.3f %8.3f"
        div = "-"*maxp + " -------- -------- --------"
        out = [
            headfmt % ("Point", "Count", "Total", "Average"),
            div
        ] + [datafmt % tup for tup in self.stats()] + [div]
        if as_list:
            return out
        else:
            return "\n".join(out)
            
    def print_stats(self, headline=None, file=None):
        out = self.format()
        if headline:
            out = headline + "\n" + out
        if file is not None:
            print(out, file=file)
        else:
            print(out)
        
    def reset(self):
        self.Points = {}     
        
    def calibrate(self):
        # not really working
        t = Tracer()
        N = 100
        d = 0.001
        tx = t["x"]
        ty = tx["y"]
        n = 0
        for _ in range(N):   
            with tx:
                with ty:
                    n += 1
        self.TZero = (tx.Time - ty.Time)/N
        return n

class TracePoint(Tracer):
    def __init__(self, name, path, tzero):
        Tracer.__init__(self, path, tzero)
        self.Name = name
        self.TZero = tzero
        self.reset()
        self.T0 = time.time()
        
    def reset(self):
        self.Count = 0
        self.Time = 0.0

    def begin(self):
        self.T0 = time.time()
        return self
        
    def end(self):
        self.Count += 1
        self.Time += time.time() - self.T0
        return self
        
    def stats(self):
        avg = None
        if self.Count > 0:  avg = self.Time/self.Count - self.TZero
        return [(self.Path, self.Count, self.Time - self.TZero*self.Count, avg)] + Tracer.stats(self)

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, et, ev, tb):
        self.end()

class DummyTracer(Tracer):
    
    def __init__(self, *params, **args):
        pass
        
    def __getitem__(self, name):
        return DummyTracePoint()
        
    def stats(self):
        return []
        
    def print_stats(self, headline=None, file=None):
        pass

class DummyTracePoint(DummyTracer):
    
    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        pass

    
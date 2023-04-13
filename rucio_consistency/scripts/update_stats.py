import json, os.path, traceback, copy
from rucio_consistency import Stats

Usage = """
python [-k <key>] [-u <update JSON file>] [-j "<inline JSON expression>"] [-t] <stats JSON file to update>
"""

def main():
    import sys, getopt
    
    opts, args = getopt.getopt(sys.argv[1:], "k:u:j:t")
    opts = dict(opts)
    
    if not args:
        print(Usage)
        sys.exit(2)
    stats_file = args[0]
    key = opts.get("-k")
    if "-u" in opts:
        update = json.loads(open(opts["-u"], "r").read())
    elif "-j" in opts:
        update = json.loads(opts["-j"])
    elif "-t" in opts:
        update = sys.stdin.read()           # treat the input as text value
    else:
        update = json.loads(sys.stdin.read())

    s = Stats(stats_file)
    if key:
        path = key.split("/")
        path, last = path[:-1], path[-1]
        d = s
        for p in path:
            d = d.setdefault(p, {})            
            print(p, d, s.Data)
        d[last] = update
        s.save()
    else:
        s.update(update)

if __name__ == "__main__":
    main()
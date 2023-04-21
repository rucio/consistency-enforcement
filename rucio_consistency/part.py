from zlib import adler32
import gzip, glob
from .py3 import to_bytes, PY3


def part(nparts, path):
        if nparts <= 1: return 0
        if PY3:    path = to_bytes(path)
        #print("part(", nparts, path,"): adler:", adler32(path))
        return adler32(path) % nparts
        
class _Partition(object):
    
    def __init__(self, f, path):
        self.F = f
        self.Path = path
        
    def __iter__(self):
        return self
        
    def __next__(self):
        l = self.F.readline()
        if not l:
            raise StopIteration
        return l.strip()
        
    def rewind(self):
        self.F.seek(0,0)
        
class PartitionedList(object):
    
    def __init__(self, mode, filenames, compressed=False):
        """Initializes the PartitionedList object.
        
        Parameters
        ----------
        mode : str
            "w" for write and "r" for read-only
        filenames : list
            Ordered list of file paths for the partition
        compressed : boolean
            Whether the files will be compressed with gzip. Used with "w" only. Existing files will be opened as gzip-compressed if they have the
            .gz extension
        
        Notes
        -----
            It is recommended to use ``open`` and ``create`` static methods instead of the constructor
        """
        self.Mode = mode
        self.FileNames = filenames
        self.Files = []
        self.NParts = len(filenames)
        self.Compressed = compressed
        
        if mode == "w":
            self.Files = [open(fn, "w") if not compressed else gzip.open(fn, "wt") for fn in self.FileNames]
        else:
            self.Files = [open(fn, "r") if not fn.endswith(".gz") else gzip.open(fn, "rt") for fn in self.FileNames]
            
        self.NWritten = 0
            
    @staticmethod
    def open(prefix=None, files=None):
        """Static method to open an existing partitioned list
        
        Parameters
        ----------
        prefix : str
            Open files matching pattern: <prefix>*
        files : list
            Ordered list of file paths for the partition
        """
        # open existing set
        if files is None:
            files = sorted(glob.glob(f"{prefix}.*"))
        return PartitionedList("r", files)
        
    @staticmethod
    def create(nparts, prefix, compressed=False):
        """Static method to create a new partitioned list
        
        Parameters
        ----------
        nparts : int
            Number of partitions to create. Each partition will be stored in a separate file.
        prefix : str
            Files will be created as <prefix>.00000, <prefix>.00001, ...
        compressed : boolean
            Whether to compress the partition files
        """
        # create new set
        gz = ".gz" if compressed else ""
        files = ["%s.%05d%s" % (prefix, i, gz) for i in range(nparts)]
        return PartitionedList("w", files, compressed)
        
    @staticmethod
    def create_file(path, compressed=False):
        # create a single file set
        if compressed and not path.endswith(".gz"):
            path = path + ".gz"
        return PartitionedList("w", [path], compressed)
        
    def add(self, item):
        """Adds an item to the partitioned list by appending it to corresponding partition file. The partition file is chosen by computing
        Adler32 checksum as an unsigned (positive) integer on the item and then taking modulo by the number of partitions in the list of the 
        integer result.
        
        Parameters
        ----------
        item : str or bytes
            The item to add to the list
        """
        if self.Mode != "w":    raise ValueError("The list is not open for writing")
        item = item.strip()
        i = part(self.NParts, item)
        #print(item, "%", self.NParts, "->", i)
        item = item+"\n"
        self.Files[i].write(item)
        self.NWritten += 1
        
    def files(self):
        """Returns ordered list of paths for the partition files
        """
        return self.Files
        
    @property
    def partitions(self):
        """Returns list of Partition objects for the list. Each partition can be iterated to get the list of items:
        
            for part in the_list.partitions:
                for item in part:
                    ...

        """
        return [_Partition(f, path) for f, path in zip(self.Files, self.FileNames)]
        
    def items(self):
        """Generator yielding all the items in the list.
        """
        assert self.Mode == "r"
        for f in self.Files:
            l = f.readline()
            while l:
                yield l.strip()
                l = f.readline()
                
    def __iter__(self):
        """Iterator for the list. This allows the PartitionedList object to be used as:
        
            for item in the_list:
                ...

        """
        return self.items()

    def close(self):
        """Closes the list. It is important to call this method for a list open for writing.
        """
        [f.close() for f in self.Files]

    def __del__(self):
        """The destructor will call close()
        """
        self.close()

if __name__ == "__main__":
    import sys, glob
    prefix = sys.argv[1]
    lst = PartitionedList.open(prefix=prefix)
    for f in lst:
        print (f)

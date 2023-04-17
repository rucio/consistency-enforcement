Consistenty Enforcement Tools
=============================

XRootD Scanner
--------------

.. code-block:: shell

    $ rce_scan [options] <RSE>
    
    Options:
    -c <config.yaml>|-c rucio   - required - read config either from a YAML file or from Rucio
    -o <output file prefix>     - output will be sent to <output>.00000, <output>.00001, ...
    -e <path>                   - output file for the list of empty directories
    -t <timeout>                - xrdfs ls operation timeout (default 30 seconds)
    -m <max workers>            - default 5
    -R <recursion depth>        - start using -R at or below this depth (dfault 3)
    -n <nparts>
    -k                          - do not treat individual directories scan errors as overall scan failure
    -q                          - quiet - only print summary
    -x                          - do not use metadata (ls -l), do not include file sizes
    -M <max_files>              - stop scanning the root after so many files were found
    -s <stats_file>             - write final statistics to JSON file
    -r <root count file>        - JSON file with file counds by root
    
List Partitioning and Comparison
--------------------------------

This set of tools is created to compare very large (~100 million entries) sets of file paths or names or text strings of any other kind so that
the time spent comparing the lists grows lineary with the set size. One of the operations used in the Rucio Consistency Enforcement is synchronous
comparison of 3 separate sets of file paths or LFNs to produce the list of missing and "dark" files. In order to perform this function
so that it takes O(set size) time, the tool kit partitions each of the 3 lists into subsets using a simple and efficient hashing function
(specifically, Adler32) so that the same path always gets into the same partition number given constant number of partitions.
Once each of the 3 lists is partitioned (which takes O(set size) time), then 3-way comparison is performed on each triplet of corresponding
partitions from each of the 3 sets. The triplet comparison is performed in memory and it also takes O(set size) time. Then the comparison
results from all the triplets are merged into combined "dark" and missing list. Partition size is chosen so that it is not too small
and yet it can fit into the virtual memory of a single process without causing memory swapping inefficiency.

Set Partitioning
----------------

Python module
.............

Command line tool
.................

.. code-block:: shell

    $ rce_partition -o <output prefix> <file> ...

    Options:    
    -q - quiet
    -c <config file>
    -r <rse> - RSE name - to use RSE-specific configuration, ignored if -c is not used
    -n <nparts> - override the value from the <config file>
    -z - use gzip compression for output


Set Comparison Tools
--------------------

cmp5
....


.. code-block:: shell

    $ rce_cmp5 [-z] [-s <stats file> [-S <stats key>]] <b m prefix> <b d prefix> <r prefix> <a m prefix> <a d prefix> <dark output> <missing output>

cmp3
....

.. code-block:: shell

    $ rce_cmp3 [-z] [-s <stats file> [-S <stats key>]] <b prefix> <r prefix> <a prefix> <dark output> <missing output>


cmp2
....

.. code-block:: shell

    $ rce_cmp2 [-z] [-s <stats file> [-S <stats key>]]    (join|minus|xor|or) <A prefix> <B prefix> <output prefix>
    $ rce_cmp2 [-z] [-s <stats file> [-S <stats key>]] -f (join|minus|xor|or) <A file> <B file> <output file>


Rucio Replicas Dump
-------------------

.. code-block:: shell

    $ rce_db_dump [options] -c <config.yaml> <rse_name>
    
    Options:
    -c <config file> -- required
    -d <db config file> -- required - uses rucio.cfg format. Must contain "default" and "schema" under [databse]
    -v -- verbose
    -n <nparts>
    -f <state>:<prefix> -- filter files with given state to the files set with prefix
        state can be either combination of capital letters or "*" 
        can be repeated  ( -f A:/path1 -f CD:/path2 )
        use "*" for state to send all the files to the output set ( -f *:/path )
    -l -- include more columns, otherwise physical path only, automatically on if -a is used
    -z -- produce gzipped output
    -s <stats file> -- write stats into JSON file
       -S <key> -- add dump stats to stats under the key
    -r <file>   -- file counts per root and store in the file as JSON structure with file counts
    -m <N files> -- stop after N files

Configuration File
------------------
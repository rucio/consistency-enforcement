Consistenty Enforcement Toolkit
===============================

Introduction
------------

The objective of the Consistency Enforcement (CE) process is to keep the Rucio database and actual contents of an RSE in sync. Namely, the goal
is to make sure the set of active file replicas in the Rucio database matches the set of files actually found in the RSE.
The process runs periodically for each RSE and consists of the following steps:

1.  Inconsistencies detection

    a.  Dump Rucio replicas table contents. This dump produces 2 lists of LFNs:
    
        * List of Active replicas found in the RSE (active list or BA)
        * List of all replicas found in the RSE (complete list or BC)
        
    b.  Scan the RSE. This is done by running recursive xrootd scanner of the RSE and produces the list of LFNs for files found in the RSE (site list or R)
    c.  Repeat the database dump in exactly the same way at (1). This step produces active the list (AA) and the complete list (AC)
    d.  Compute list of "dark" replicas as the list of replicas found in (R) but not in (BC) or (AC) - replicas which are not supposed to be the the RSE:
    
        D = R - BC - AC
        
    e.  Compute list of "missing" replicas as the list of replicas in both (BA) and (AA) but not (R):
    
        M = (BA*AA) - R
        
2.  Consistency Enforcement actions

    a. Declare relicas on the "missing" list (M) as "bad" to Rucio using Rucio client API
    b. Quarantine replicas on the "dark" list (D) using Rucio client API
    
The action tools are not included in the toolkit because they include some CMS policies and may be too CMS specific.

Installation
------------

The easiest way to install the package is to use ``pip``:

.. code-block:: shell

    $ pip install rucio-consistency
    
    or 
    
    $ pip install rucio-consistency --user
    $ export PATH=...     # make sure that the place where pip puts the executables is in your PATH
    

Another way is to download the package from the GitHub repository and then install it:

.. code-block:: shell

    $ git clone https://github.com/rucio/consistency-enforcement.git
    $ cd consistency-enforcement
    $ python setup.py install

    or 

    $ python setup.py install --user
    $ export PATH=...     # make sure that the place where pip puts the executables is in your PATH
    

Rucio Databse Replicas Table Dump
---------------------------------

Censistency Enforcement Toolkit compares contents of the Rucio replicas table to actual state of the RSE.
The ``rce_db_dump`` tool is used to produce a list of replica LFNs in selected state(s) from the ``repplicas``
table. It accesses the Rucio databse directly fot that. The output of ``rce_db_dump`` is a partitioned list
of replica LFNs.

.. code-block:: shell

    rce_db_dump [options] -c <config.yaml> <rse_name>
        -c <config file> -- required
        -d <db config file> -- required - uses rucio.cfg format. Must contain "default" and "schema" under [databse]
        -v -- verbose
        -n <nparts>
        -f <state>:<prefix> -- filter replicas with given state to the files set with prefix
            state can be either combination of capital letters or "*" 
            can be repeated  ( -f A:/path1 -f CD:/path2 )
            use "*" for state to send all the replicas to the output set ( -f *:/path )
        -l -- include more columns, otherwise physical path only, automatically on if -a is used
        -z -- produce gzipped output
        -s <stats file> -- write stats into JSON file
           -S <key> -- add dump stats to stats under the key
        -r <file>   -- file counts per root and store in the file as JSON structure with file counts
        -m <N files> -- stop after N replicas

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
    
To use the scanner:

1. "pip install --user rucio-consistency" or "pip3 install --user rucio-consistency"
2. You may need to add ~/.local/bin" to your PATH
3. Create or download the CE configuration file. CMS CE configuration is available at: https://cmsweb.cern.ch/rucioconmon/ce/ce_config/ce_config.yaml
4. Make sure you have valid X.509 proxy, define environment variable X509_USER_PROXY=<file with your proxy>
5. Run the scanner: "rce_scan -z -c config.yaml -o /output_dir/site_scan T1_DE_KIT_Disk". This will create partitioned list of
   replicas "/output_dir/site_scan.*.gz"

    
Set Partitioning and Comparison
-------------------------------

These tools can be used to compare very large (~100 million entries) sets of file paths or names or text strings of any other kind so that
the time spent comparing the lists grows lineary with the set size. One of the operations used in the Rucio Consistency Enforcement is synchronous
comparison of 3 separate sets of file paths or LFNs to produce the lists of missing and "dark" files. In order to perform this function
so that it takes O(set size) time, the toolkit first partitions each of the 3 lists into subsets using a simple and efficient hashing function
(specifically, Adler32) so that the same path always gets into the same partition given constant number of partitions.
Once each of the 3 lists is partitioned (which takes O(set size) time), then 3-way comparison is performed on each triplet of corresponding
partitions from each of the 3 sets. The triplet comparison is performed in memory and it also takes O(set size) time. Then the comparison
results from all the triplets are merged into combined "dark" and missing list. Partition size is chosen so that it is not too small
and yet it can fit into the virtual memory of a single process without causing memory swapping inefficiency.

Set partitioning
................

This tool can be used to create a partitioned list of items. It assumes that each item is represented as a line in each
of the input text files.

.. code-block:: shell

    $ rce_partition -o <output prefix> <file> ...

    Options:    
    -q - quiet
    -c <config file>
    -r <rse> - RSE name - to use RSE-specific configuration, ignored if -c is not used
    -n <nparts> - override the value from the <config file> for the RSE
    -z - use gzip compression for the output

rce_cmp3
........

.. code-block:: shell

    $ rce_cmp3 [-z] [-s <stats file> [-S <stats key>]] <b prefix> <r prefix> <a prefix> <dark output> <missing output>

``rce_cmp3`` command peforrms "naive" consistency comparison between 3 sets of items stored in corresponding partitioned item lists:

    * Database dump after the site scan
    * Site scan results
    * Database dump before the site scan
    
It produces 2 files with the output lists:

    * "Dark" items - items present in the site scan but not in any of the 2 database dumps
    * Missing items - items present in both database dumps but not in the site scan

rce_cmp5
........


.. code-block:: shell

    $ rce_cmp5 [-z] [-s <stats file> [-S <stats key>]] <b m prefix> <b d prefix> <r prefix> <a m prefix> <a d prefix> <dark output> <missing output>

        <b m prefix> - Prefix for the partitioned list with the DB dump before the site scan used to produce the missing list
        <b d prefix> - Prefix for the partitioned list with the DB dump before the site scan used to produce the "dark" list
        <r prefix> - Prefix for the partitioned list with the site scan results
        <a m prefix> - Prefix for the partitioned list with the DB dump after the site scan used to produce the missing list
        <a d prefix> - Prefix for the partitioned list with the DB dump after the site scan used to produce the "dark" list

        <dark output> <missing output> - output files

This is more "conservative" version of ``rce_cmp3`` script. The difference between ``rce_cmp5`` and ``rce_cmp3`` 
is that ``rce_cmp5`` takes 2 different pairs of the database dumps. One of the pair includes all RSE replicas
from Rucio, regardless of the replica status and is used to produce the "dark" items list. The other pair of database dumps includes only
active (``A``) replicas, and this pair is used to produce the list of missing items. As you can see, the "dark" and missing lists produced by ``rce_cmp5``
are never supersets of those produced by ``rce_cmp3``. Hence, they are generally more conservative.

rce_cmp2
........

.. code-block:: shell

    $ rce_cmp2 [-z] [-s <stats file> [-S <stats key>]]    (join|minus|xor|or) <A prefix> <B prefix> <output prefix>
    $ rce_cmp2 [-z] [-s <stats file> [-S <stats key>]] -f (join|minus|xor|or) <A file> <B file> <output file>

General purpose tool to compare 2 partitioned lists. Requires that both lists have the same number of partitions.

Rucio Replicas Dump
-------------------

This tool is used to produce a list of replicas for an RSE from the Rucio database replicas table. The output is a
partitioned list of LFNs.

.. code-block:: shell

    $ rce_db_dump [options] -c <config.yaml> <rse_name>
    
    Options:
    -c <config file> -- required
    -d <db config file> -- required - uses rucio.cfg format. Must contain "default" and "schema" under [databse]
    -v -- verbose
    -n <nparts>
    -f <state>:<prefix> -- filter replicas with given state to the files set with prefix
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

Consistency Enforcement tools use common configuration file used to configure various components on per-RSE basis. Here is a sample of 
a configuration file in YAML format:

.. code-block::

    database:		# optional. rucio.cfg can be used instead 
            host:           host.cern.ch
            port:           10121
            service:        host.cern.ch
            schema:         THE_SCHEMA
            user:           database_reader
            password:       "password"

    rses:
      "*": # default values for all RSEs
        include_sizes: no
        partitions:     5
        ignore_list:
            - /store/backfill
            - /store/test
            - /store/unmerged
            - /store/temp
            - /store/mc/SAM
            - /store/mc/HC
            - /store/accounting
            - /store/express/tier0_harvest
        scanner:
          recursion:      1
          nworkers:        8
          timeout:        300
          server_root: /
          remove_prefix: /
          add_prefix: /
          roots:
          - path: /store/express
          - path: /store/mc
          - path: /store/data
          - path: /store/generator
          - path: /store/results
          - path: /store/hidata
          - path: /store/himc
          - path: /store/relval
        dbdump:
          path_root:   /


      T0_CH_CERN_Disk:
        scanner:
          include_sizes: no
          server: eoscms.cern.ch
          server_root: /eos/cms/tier0/store/
      T1_DE_KIT_Disk:
        scanner:
          server: cmsxrootd-kit.gridka.de:1094

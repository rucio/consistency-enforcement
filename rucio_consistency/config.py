import re, os, json, yaml, pprint
from configparser import ConfigParser


class DBConfig:

	# class to read relevant parameters from rucio.cfg

    def __init__(self, schema, dburl):
        self.DBURL = dburl
        self.Schema = schema
    
    @staticmethod
    def from_cfg(path):
        cfg = ConfigParser()
        cfg.read(path)
        dbparams = dict(cfg.items("database"))
        return DBConfig(dbparams.get("schema"), dbparams["default"])
        
    @staticmethod
    def from_yaml(path_or_dict):
        if isinstance(path_or_dict, str):
            cfg = yaml.load(open(path_or_dict, "r"), Loader=yaml.SafeLoader)["database"]
        else:
            cfg = path_or_dict

        user = cfg["user"]
        password = cfg["password"]
        schema = cfg["schema"]
        conn_str = None
        if "connstr" in cfg:
            conn_str = cfg["connstr"]
            dburl = "oracle+cx_oracle://%s:%s@%s" % (user, password, conn_str)
        else:
            host = cfg["host"]
            port = cfg["port"]
            service = cfg["service"]
            dburl = "oracle+cx_oracle://%s:%s@%s:%s/?service_name=%s" % (
                                    user, password, host, port, service)
        return DBConfig(schema, dburl)


class RSEConfiguration(object):

    def __init__(self, rse, cfg):
        self.RSE = rse
        self.Config = cfg
        self.ScanerConfig = cfg.get("scanner", {})
        self.NPartitions = cfg.get("npartitions", 8)
        self.IgnoreList = cfg.get("ignore_list", [])
        roots = self.ScanerConfig.get("roots", [])
        self.RootList = [d["path"] for d in roots]
        #
        # scanner configuration
        #
        self.Server = self.ScanerConfig["server"]
        self.ServerRoot = self.ScanerConfig.get("server_root", "/")           # prefix up to, but not including /store/
        self.ScannerTimeout = self.ScanerConfig.get("timeout", 300)
        self.RemovePrefix = self.ScanerConfig.get("remove_prefix", "")        # to be applied after site root is removed
        self.AddPrefix = self.ScanerConfig.get("add_prefix", "")              # to be applied after site root is removed
        self.NWorkers = self.ScanerConfig.get("nworkers", 8)
        self.IncludeSizes = self.ScanerConfig.get("include_sizes", True)
        self.RecursionThreshold = self.ScanerConfig.get("recursion", 1)
        self.ServerIsRedirector = self.ScanerConfig.get("is_redirector", True)

        #
        # DB dump configuration
        #
        self.DBDumpPathRoot = self.Config.get("dbdump", {}).get("path_root", "/")
        
    def get(self, name, default=None):
        return self.Config.get(name, default)


class CEConfiguration(object):

    def __init__(self, config_file):
        if isinstance(config_file, str):
            config_file = open(config_file, "r")

        config = yaml.load(config_file, Loader=yaml.SafeLoader)
        self.ConfigByRSE = {}
        defaults = config.get("rses", {}).get("*", {})
        for rse, rse_config in config.get("rses", []).items():
            if rse != "*":
                self.ConfigByRSE[rse] = self.merge(defaults, rse_config)

    def merge(self, defaults, overrides):
        out = defaults.copy()
        for key, value in overrides.items():
            if isinstance(value, dict):
                out[key] = self.merge(defaults.get(key, {}), value)
            else:
                out[key] = value
        return out

    def rse_config(self, rse):
        return RSEConfiguration(rse, self.ConfigByRSE[rse])

    __getitem__ = rse_config

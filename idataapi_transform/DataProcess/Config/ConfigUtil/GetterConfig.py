import asyncio
import inspect
import aioredis

try:
    import aiomysql
except Exception as e:
    pass

try:
    import motor.motor_asyncio
except Exception as e:
    pass

from .BaseConfig import BaseGetterConfig

from ..ESConfig import get_es_client
from ..DefaultValue import DefaultVal
from ..ConnectorConfig import session_manger, main_config


class RAPIConfig(BaseGetterConfig):
    def __init__(self, source, per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit,
                 max_retry=DefaultVal.max_retry, random_min_sleep=DefaultVal.random_min_sleep,
                 random_max_sleep=DefaultVal.random_max_sleep, session=None, filter_=None, return_fail=False,
                 tag=None, **kwargs):
        """
        will request until no more next_page to get, or get "max_limit" items

        :param source: API to get, i.e. "http://..."
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param max_retry: if request fail, retry max_retry times
        :param random_min_sleep: if request fail, random sleep at least random_min_sleep seconds before request again
        :param random_max_sleep: if request fail, random sleep at most random_min_sleep seconds before request again
        :param session: aiohttp session to perform request
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param return_fail: if set to True, for each iteration, will return a tuple,
            api_getter = ProcessFactory.create_getter(RAPIConfig("http://..."))
            async for items, bad_objects in getter:
                A = bad_objects[0]
                A.response: -> json object: '{"appCode": "weixinpro", "dataType": "post", "message": "param error", "retcode": "100005"}', if fail in request, response will be None
                A.tag: -> tag you pass to RAPIConfig
                A.source: -> source you pass to RAPIConfig

        :param args:
        :param kwargs:

        Example:
            api_config = RAPIConfig("http://...")
            api_getter = ProcessFactory.create_getter(api_config)
            async for items in api_getter:
                print(items)
        """
        super().__init__()
        self.source = source
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.max_retry = max_retry
        self.random_min_sleep = random_min_sleep
        self.random_max_sleep = random_max_sleep
        self.session = session_manger.get_session() if not session else session
        self.filter = filter_
        self.return_fail = return_fail
        self.tag = tag


class RCSVConfig(BaseGetterConfig):
    def __init__(self, filename, mode=DefaultVal.default_file_mode_r, encoding=DefaultVal.default_encoding,
                 per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit, filter_=None, **kwargs):
        """
        :param filename: filename to read
        :param mode: file open mode, i.e "r"
        :param encoding: file encoding i.e "utf8"
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param kwargs:

        Example:
            csv_config = RJsonConfig("./result.csv", encoding="gbk")
            csv_getter = ProcessFactory.create_getter(csv_config)
            async for items in csv_getter:
                print(items)

            # both async generator and generator implemented
            for items in csv_getter:
                print(items)
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.filter = filter_


class RESConfig(BaseGetterConfig):
    def __init__(self, indices, doc_type, per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit,
                 scroll="1m", query_body=None, return_source=True, max_retry=DefaultVal.max_retry,
                 random_min_sleep=DefaultVal.random_min_sleep, random_max_sleep=DefaultVal.random_max_sleep,
                 filter_=None, **kwargs):
        """
        :param indices: elasticsearch indices
        :param doc_type: elasticsearch doc_type
        :param per_limit: how many items to get per request
        :param max_limit: get at most max_limit items, if not set, get all
        :param scroll: default is "1m"
        :param query_body: default is '{"size": "per_limit", "query": {"match_all": {}}}'
        :param return_source: if set to True, will return [item , ..., itemN], item is the "_source" object
                              if set to False, will return whatever elasticsearch return, i.e {"hits": {"total": ...}}
        :param max_retry: if request fail, retry max_retry times
        :param random_min_sleep: if request fail, random sleep at least random_min_sleep seconds before request again
        :param random_max_sleep: if request fail, random sleep at most random_min_sleep seconds before request again
        :param filter_: run "transform --help" to see command line interface explanation for detail,
            only work if return_source is False
        :param kwargs:

        Example:
            body = {
                "size": 100,
                "_source": {
                    "includes": ["likeCount", "id", "title"]
                    }
            }
            es_config = RESConfig("post20170630", "news", max_limit=1000, query_body=body)
            es_getter = ProcessFactory.create_getter(es_config)
            async for items in es_getter:
                print(item)
        """
        super().__init__()
        if not main_config.has_es_configured:
            raise ValueError("You must config es_hosts before using Elasticsearch, Please edit configure file: %s" % (main_config.ini_path, ))

        if not query_body:
            query_body = {
                "size": per_limit,
                "query": {
                    "match_all": {}
                }
            }
        self.query_body = query_body
        self.indices = indices
        self.doc_type = doc_type
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.scroll = scroll
        self.es_client = get_es_client()
        self.return_source = return_source
        self.max_retry = max_retry
        self.random_min_sleep = random_min_sleep
        self.random_max_sleep = random_max_sleep
        self.filter = filter_


class RJsonConfig(BaseGetterConfig):
    def __init__(self, filename, mode=DefaultVal.default_file_mode_r, encoding=DefaultVal.default_encoding,
                 per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit, filter_=None, **kwargs):
        """
        :param filename: line by line json file to read
        :param mode: file open mode, i.e "r"
        :param encoding: file encoding i.e "utf8"
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param kwargs:

        Example:
            json_config = RJsonConfig("./result.json")
            json_getter = ProcessFactory.create_getter(json_config)
            async for items in json_getter:
                print(items)

            # both async generator and generator implemented
            for items in json_getter:
                print(items)
        """
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.filter = filter_


class RXLSXConfig(BaseGetterConfig):
    def __init__(self, filename, per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit, sheet_index=0,
                 filter_=None, **kwargs):
        """
        :param filename: filename to read
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param sheet_index: which sheet to get, 0 means 0th sheet
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param kwargs:

        Example:
            xlsx_config = RXLSXConfig("./result.xlsx")
            xlsx_getter = ProcessFactory.create_getter(xlsx_config)
            async for items in xlsx_getter:
                print(items)

            # both async generator and generator implemented
            for items in xlsx_getter:
                print(items)

        """
        super().__init__()
        self.filename = filename
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.sheet_index = sheet_index
        self.filter = filter_


class RAPIBulkConfig(BaseGetterConfig):
    def __init__(self, sources, interval=DefaultVal.interval, concurrency=main_config["main"].getint("concurrency"),
                 filter_=None, return_fail=False, **kwargs):
        """
        :param sources: an iterable object, each item must be "url" or instance of RAPIConfig
        :param interval: integer or float, each time you call async generator, you will wait for "interval" seconds
                         and get all items fetch during this "interval"
        :param concurrency: how many concurrency task run, default read from config file, if concurrency set,
                            only string(url) in "sources" will work with this concurrency level, RAPIConfig instance won't
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param return_fail: if set to True, for each iteration, will return a tuple,
            api_getter = ProcessFactory.create_getter(RAPIBulkConfig([...]))
            async for items, bad_objects in getter:
                A = bad_objects[0]
                A.response: -> json object: '{"appCode": "weixinpro", "dataType": "post", "message": "param error", "retcode": "100005"}', if fail in request, response will be None
                A.tag: -> tag you pass to RAPIConfig
                A.source: -> source you pass to RAPIConfig

        :param kwargs:

        Example:
            sources = ["http://....", "http://....", "http://....", RAPIConfig("http://....")]
            bulk_config = RAPUBulkConfig(sources)
            bulk_getter = ProcessFactory.create_getter(bulk_config)
            async for items in bulk_getter:
                print(items)

        """
        super().__init__()
        self.configs = (self.to_config(i) for i in sources)
        self.interval = interval
        self.concurrency = concurrency
        self.session = session_manger._generate_session(concurrency_limit=concurrency)
        self.filter = filter_
        self.return_fail = return_fail

    def to_config(self, item):
        if isinstance(item, RAPIConfig):
            return item
        else:
            return RAPIConfig(item, session=self.session, filter_=self.filter, return_fail=self.return_fail)

    def __del__(self):
        if inspect.iscoroutinefunction(self.session.close):
            asyncio.ensure_future(self.session.close())
        else:
            self.session.close()


class RRedisConfig(BaseGetterConfig):
    def __init__(self, key, key_type="LIST", per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit,
                 filter_=None, max_retry=DefaultVal.max_retry, random_min_sleep=DefaultVal.random_min_sleep,
                 random_max_sleep=DefaultVal.random_max_sleep, host=main_config["redis"].get("host"),
                 port=main_config["redis"].getint("port"), db=main_config["redis"].getint("db"),
                 password=main_config["redis"].get("password"), timeout=main_config["redis"].getint("timeout"),
                 encoding=main_config["redis"].get("encoding"), need_del=main_config["redis"].getboolean("need_del"),
                 direction=main_config["redis"].get("direction"), compress=main_config["redis"].getboolean("compress"),
                 **kwargs):
        """
        :param key: redis key to get data
        :param key_type: redis data type to operate, current only support LIST, HASH
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param max_retry: if request fail, retry max_retry times
        :param random_min_sleep: if request fail, random sleep at least random_min_sleep seconds before request again
        :param random_max_sleep: if request fail, random sleep at most random_min_sleep seconds before request again
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param host: redis host -> str
        :param port: redis port -> int
        :param db: redis database number -> int
        :param password: redis password -> int
        :param timeout: timeout per redis connection -> float
        :param encoding: redis object encoding -> str
        :param need_del:  whether need to del the key after get object from redis -> boolean
        :param direction: "L" or "R", left to right or roght to left
        :param compress: whether compress data use zlib before write to redis -> boolean
        :param kwargs:

        Example:
            redis_config = RRedisConfig("my_key")
            redis_getter = ProcessFactory.create_getter(redis_config)
            async for items in redis_getter:
                print(items)
        """
        super().__init__()
        if not main_config.has_redis_configured and port <= 0:
            raise ValueError("You must config redis before using Redis, Please edit configure file: %s" % (main_config.ini_path, ))

        if key_type not in ("LIST", "HASH"):
            raise ValueError("key_type must be one of (%s)" % (str(("LIST", "HASH")), ))
        if not encoding:
            raise ValueError("You must specific encoding, since I am going to load each object in json format, "
                             "and treat it as dictionary in python")
        if not password:
            password = None

        self.redis_pool_cli = None
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.encoding = encoding
        self.timeout = timeout

        self.key_type = key_type
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.filter = filter_
        self.max_retry = max_retry
        self.random_min_sleep = random_min_sleep
        self.random_max_sleep = random_max_sleep
        self.need_del = need_del

        self.name = "%s_%s->%s" % (str(host), str(port), str(key))

        self.redis_read_method = self.redis_len_method = self.redis_del_method = None
        self.direction = direction
        self.compress = compress

        if key_type == "LIST":
            self.is_range = True
        else:
            self.is_range = False

    async def get_redis_pool_cli(self):
        """
        :return: an async redis client
        """
        if self.redis_pool_cli is None:
            kwargs = {
                "db": self.db,
                "password": self.password,
                "encoding": self.encoding,
                "timeout": self.timeout,
                "minsize": 1,
                "maxsize": 3
            }
            if self.compress:
                del kwargs["encoding"]
            self.redis_pool_cli = await aioredis.create_redis_pool((self.host, self.port), **kwargs)
            if self.key_type == "LIST":
                self.redis_read_method = self.redis_pool_cli.lrange
                self.redis_len_method = self.redis_pool_cli.llen
                self.redis_del_method = self.redis_pool_cli.ltrim
            else:
                self.redis_read_method = self.redis_pool_cli.hgetall
                self.redis_len_method = self.redis_pool_cli.hlen
                self.redis_del_method = self.redis_pool_cli.delete

        return self.redis_pool_cli


class RMySQLConfig(BaseGetterConfig):
    def __init__(self, table, per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit,
                 filter_=None, max_retry=DefaultVal.max_retry, random_min_sleep=DefaultVal.random_min_sleep,
                 random_max_sleep=DefaultVal.random_max_sleep, host=main_config["mysql"].get("host"),
                 port=main_config["mysql"].getint("port"), user=main_config["mysql"].get("user"),
                 password=main_config["mysql"].get("password"), database=main_config["mysql"].get("database"),
                 encoding=main_config["mysql"].get("encoding"), loop=None, **kwargs):
        """
        :param table: mysql table
        :param per_limit: how many items to get per time
        :param max_limit: get at most max_limit items, if not set, get all
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param max_retry: if request fail, retry max_retry times
        :param random_min_sleep: if request fail, random sleep at least random_min_sleep seconds before request again
        :param random_max_sleep: if request fail, random sleep at most random_min_sleep seconds before request again
        :param host: mysql host -> str
        :param port: mysql port -> int
        :param user: mysql user -> str
        :param password: mysql password -> str
        :param database: mysql database -> str
        :param charset: default utf8 -> str
        :param loop: async loop instance
        :param kwargs:

        Example:
            mysql_config = RRedisConfig("my_table")
            redis_getter = ProcessFactory.create_getter(mysql_config)
            async for items in redis_getter:
                print(items)
        """
        super().__init__()
        if not main_config.has_mysql_configured and port <= 0:
            raise ValueError("You must config mysql before using MySQL, Please edit configure file: %s" % (main_config.ini_path, ))
        if "aiomysql" not in globals():
            raise ValueError("module mysql disabled, please reinstall "
                             "requirements with python version higher than 3.5.3 to enable it")

        self.table = table
        self.database = database

        self.max_limit = max_limit
        self.per_limit = per_limit
        self.max_retry = max_retry
        self.random_min_sleep = random_min_sleep
        self.random_max_sleep = random_max_sleep
        self.filter = filter_

        self.name = "%s->%s" % (self.table, self.database)

        self.host = host
        self.port = port
        self.user = user
        if not password:
            password = ''
        self.password = password
        self.database = database
        self.encoding = encoding

        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.mysql_pool_cli = self.connection = self.cursor = None

    async def get_mysql_pool_cli(self):
        """
        :return: an async mysql client
        """
        if self.mysql_pool_cli is None:
            self.mysql_pool_cli = await aiomysql.create_pool(host=self.host, port=self.port, user=self.user,
                                                             password=self.password, db=self.database, loop=self.loop,
                                                             minsize=1, maxsize=3, charset=self.encoding)
            self.connection = await self.mysql_pool_cli.acquire()
            self.cursor = await self.connection.cursor()
        return self.mysql_pool_cli

    def free_resource(self):
        if self.mysql_pool_cli is not None:
            self.mysql_pool_cli.release(self.connection)
            self.mysql_pool_cli.close()
            self.loop.create_task(self.mysql_pool_cli.wait_closed())
            self.mysql_pool_cli = self.connection = self.cursor = None


class RMongoConfig(BaseGetterConfig):
    def __init__(self, collection, per_limit=DefaultVal.per_limit, max_limit=DefaultVal.max_limit,
                 query_body=None, max_retry=DefaultVal.max_retry,
                 random_min_sleep=DefaultVal.random_min_sleep, random_max_sleep=DefaultVal.random_max_sleep,
                 filter_=None, host=main_config["mongo"].get("host"), port=main_config["mongo"].getint("port"),
                 username=main_config["mongo"].get("username"), password=main_config["mongo"].get("password"),
                 database=main_config["mongo"].get("database"), **kwargs):
        """
        :param collection: collection name
        :param per_limit: how many items to get per request
        :param max_limit: get at most max_limit items, if not set, get all
        :param query_body: search query, default None, i.e: {'i': {'$lt': 5}}
        :param return_source: if set to True, will return [item , ..., itemN], item is the "_source" object
                              if set to False, will return whatever elasticsearch return, i.e {"hits": {"total": ...}}
        :param max_retry: if request fail, retry max_retry times
        :param random_min_sleep: if request fail, random sleep at least random_min_sleep seconds before request again
        :param random_max_sleep: if request fail, random sleep at most random_min_sleep seconds before request again
        :param filter_: run "transform --help" to see command line interface explanation for detail
        :param kwargs:

        Example:
            mongo_config = RMongoConfig("my_coll")
            mongo_getter = ProcessFactory.create_getter(mongo_config)
            async for items in mongo_getter:
                print(item)
        """
        super().__init__()
        if not main_config.has_mongo_configured:
            raise ValueError("You must config MongoDB before using MongoDB, Please edit configure file: %s" % (main_config.ini_path, ))
        if "motor" not in globals():
            raise ValueError("module motor disabled, please reinstall "
                             "requirements in linux")

        self.collection = collection
        self.query_body = query_body
        self.per_limit = per_limit
        self.max_limit = max_limit
        self.max_retry = max_retry
        self.random_min_sleep = random_min_sleep
        self.random_max_sleep = random_max_sleep
        self.filter = filter_
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.name = "%s->%s" % (self.database, self.collection)

        self.client = self.cursor = None

    def get_mongo_cli(self):
        if self.client is None:
            kwargs = {
                "host": self.host,
                "port": self.port
            }
            if self.username:
                kwargs["username"] = self.username
            if self.password:
                kwargs["password"] = self.password
            self.client = motor.motor_asyncio.AsyncIOMotorClient(**kwargs)
            if self.query_body:
                self.cursor = self.client[self.database][self.collection].find(self.query_body)
            else:
                self.cursor = self.client[self.database][self.collection].find(self.query_body)
        return self.client

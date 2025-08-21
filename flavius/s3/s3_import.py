import re
import uuid
import time
import os
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple, TypedDict
from collections import defaultdict

import flavius
import neo4j
import abc

# ========== 日志 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_INFO", "INFO").upper())


# ========== 配置 ==========
class AWSConfig(TypedDict):
    access_key_id: str
    secret_access_key: str
    region: str
    endpoint: str
    bucket_name: str


class DatabaseConfig(TypedDict):
    namespace: str
    graph: str
    flavius_url: str


class LoaderConfig:
    def __init__(self, args: argparse.Namespace):
        self.sf = args.scale_factor
        self.csv_dir = args.csv_dir
        self.ddl_file = Path(args.ddl_file_path)
        self.max_workers = args.max_workers
        self.output_dir = Path(f"output/output-sf{self.sf}")

        self.db_config = DatabaseConfig(
            namespace=args.ns, graph=args.graph, flavius_url=args.flavius_url
        )

        self.aws_config = AWSConfig(
            access_key_id=self._get_env("AWS_ACCESS_KEY_ID"),
            secret_access_key=self._get_env("AWS_SECRET_ACCESS_KEY"),
            region=self._get_env("AWS_DEFAULT_REGION"),
            endpoint=self._get_env("AWS_ENDPOINT_URL", False),
            bucket_name=self._get_env("BUCKET_NAME"),
        )

    def _get_env(self, var: str, required: bool = True) -> str:
        value = os.getenv(var)
        if required and not value:
            raise ValueError(f"Environment variable {var} is required")
        return value


# ========== Driver 抽象 ==========
class BaseDriverAdapter(metaclass=abc.ABCMeta):
    name = "Base"

    @abc.abstractmethod
    def execute_query(self, query: str, namespace: str, graph: str) -> any:
        pass

    @abc.abstractmethod
    def drop_namespace(self, ns: str):
        pass

    @abc.abstractmethod
    def create_namespace(self, ns: str):
        pass

    @abc.abstractmethod
    def create_graph(self, graph: str, ns: str):
        pass

    @abc.abstractmethod
    def close(self):
        pass


class FlaviusDriverAdapter(BaseDriverAdapter):
    name = "Flavius"

    def __init__(self, url: str, user: str, password: str, timeout: int = 2400):
        self.driver = flavius.GraphDatabase.driver(url, username=user, password=password, timeout=timeout)
        self.driver.verify_connectivity()

    def execute_query(self, query: str, namespace: str, graph: str):
        logger.debug("Executing %s query: %s, namespace: %s, graph: %s", self.name, query, namespace, graph)
        return self.driver.execute_query(query, namespace=namespace, graph=graph)

    def drop_namespace(self, ns: str):
        logger.debug("Executing drop namespace: %s", ns)
        self.driver.drop_namespace(ns)

    def create_namespace(self, ns: str):
        logger.debug("Creating namespace: %s", ns)
        self.driver.create_namespace(ns)

    def create_graph(self, graph: str, ns: str):
        logger.debug("Creating graph: %s in namespace: %s", graph, ns)
        self.driver.create_graph(graph, ns)

    def close(self):
        self.driver.close()


class Neo4jDriverAdapter(BaseDriverAdapter):
    name = "Neo4j"

    def __init__(self, url: str, user: str, password: str, **params):
        uri = f"{url}?namespace={params.get('ns', '')}&graph={params.get('graph', '')}"
        uri += "&timezone=UTC&timeout=2400"
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password), keep_alive=True)
        logger.info("Connected to Neo4j at %s", url)

    def execute_query(self, query: str, namespace: str, graph: str):
        logger.debug("Executing %s query: %s", self.name, query)
        try:
            with self.driver.session() as session:
                return session.run(query, metadata={"namespace": namespace, "graph": graph})
        except Exception as e:
            logger.exception("Query execution failed: %s", e)
            raise

    def drop_namespace(self, ns: str):
        with self.driver.session() as session:
            return session.run(f"drop namespace {ns}", metadata={"namespace": ns})

    def create_namespace(self, ns: str):
        with self.driver.session() as session:
            return session.run(f"create namespace {ns}")

    def create_graph(self, graph: str, ns: str):
        with self.driver.session() as session:
            return session.run(f"create graph {graph}", metadata={"namespace": ns})

    def close(self):
        self.driver.close()


def create_driver_adapter(args: argparse.Namespace) -> BaseDriverAdapter:
    url = args.flavius_url
    if url.startswith("neo4j://"):
        return Neo4jDriverAdapter(
            url, user=args.user, password=args.password, ns=args.ns, graph=args.graph
        )
    else:
        return FlaviusDriverAdapter(url, user=args.user, password=args.password)


# ========== Template ==========
class TemplateProcessor:
    @staticmethod
    def replace_variables(input_str: str, variables: Dict[str, str]) -> str:
        escape_token = f"__ESCAPED_DOLLAR_{uuid.uuid4().hex}__"
        escaped = input_str.replace(r"\$", escape_token)
        for name, value in variables.items():
            pattern = re.escape(f"${{{name}}}")
            escaped = re.sub(pattern, value, escaped)
        return escaped.replace(escape_token, "$")


# ========== Writer ==========
class BatchWriter:
    def __init__(self, adapter: BaseDriverAdapter, config: LoaderConfig):
        self.adapter = adapter
        self.config = config
        self.query_cache: Dict[str, str] = {}

    def _load_query(self, entity: str) -> str:
        if entity not in self.query_cache:
            query_file = Path(f"dml/ins-{entity}.cypher")
            self.query_cache[entity] = query_file.read_text()
        return self.query_cache[entity]

    def _prepare_query(self, entity: str, csv_path: str) -> str:
        template = self._load_query(entity)
        return TemplateProcessor.replace_variables(
            template,
            {"csv_file": csv_path, **self.config.aws_config, "has_header": "false"},
        )

    def execute_update(self, entity: str, csv_path: str) -> int:
        query = self._prepare_query(entity, csv_path)
        result = self.adapter.execute_query(
            query,
            namespace=self.config.db_config["namespace"],
            graph=self.config.db_config["graph"],
        )
        return 0 if result is None else 1  # Neo4j session.run 不直接返回 count

    def batch_execute(self, entities: List[Tuple[str, str]], executor: ThreadPoolExecutor) -> float:
        start_time = time.time()
        futures = []
        for entity, rel_path in entities:
            csv_path = f"s3://{self.config.aws_config['bucket_name']}/{self.config.csv_dir}/{rel_path}/"
            futures.append(executor.submit(self.execute_update, entity, csv_path))

        total_changes = 0
        for future in as_completed(futures):
            try:
                total_changes += future.result()
            except Exception as e:
                logger.error("Task failed: %s", e)

        duration = time.time() - start_time
        logger.info(
            "Processed %d entities. Total changes: %d. Duration: %.2fs",
            len(entities), total_changes, duration,
        )
        return duration


# ========== Schema ==========
class SchemaManager:
    def __init__(self, adapter: BaseDriverAdapter, config: LoaderConfig):
        self.adapter = adapter
        self.config = config

    def setup_namespace(self) -> float:
        ns = self.config.db_config["namespace"]
        try:
            self.adapter.drop_namespace(ns)
        except Exception as e:
            logger.warning("Namespace drop failed: %s", e)

        start_time = time.time()
        self.adapter.create_namespace(ns)
        self.adapter.create_graph(self.config.db_config["graph"], ns)
        duration = time.time() - start_time
        logger.info("Schema setup completed in %.2fs", duration)
        return duration

    def execute_ddl(self) -> float:
        start_time = time.time()
        with open(self.config.ddl_file) as f:
            for line in f:
                stmt = line.strip()
                if stmt and not stmt.startswith("#"):
                    self.adapter.execute_query(
                        stmt,
                        namespace=self.config.db_config["namespace"],
                        graph=self.config.db_config["graph"],
                    )
        duration = time.time() - start_time
        logger.info("DDL execution completed in %.2fs", duration)
        return duration


# ========== Recorder ==========
class ResultRecorder:
    def __init__(self, config: LoaderConfig, adapter: BaseDriverAdapter):
        self.config = config
        self.output_dir = config.output_dir
        self.adapter = adapter
        self._prepare_output()

    def _prepare_output(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "timings.csv").write_text("tool|sf|q|time\n")
        (self.output_dir / "benchmark.csv").write_text("time\n")

    def record_timing(self, phase: str, duration: float):
        with open(self.output_dir / "timings.csv", "a") as f:
            f.write(f"{self.adapter.name}|{self.config.sf}|{phase}|{duration:.6f}\n")

    def record_benchmark(self, total_duration: float):
        with open(self.output_dir / "benchmark.csv", "a") as f:
            f.write(f"{total_duration:.6f}\n")


# 定义数据模型
NODES = [
    ("Place", "initial_snapshot/static/Place"),
    ("Organisation", "initial_snapshot/static/Organisation"),
    ("TagClass", "initial_snapshot/static/TagClass"),
    ("Tag", "initial_snapshot/static/Tag"),
    ("Forum", "initial_snapshot/dynamic/Forum"),
    ("Person", "initial_snapshot/dynamic/Person"),
    ("Comment", "initial_snapshot/dynamic/Comment"),
    ("Post", "initial_snapshot/dynamic/Post"),
]

RELATIONSHIPS = [
    ("Place_isPartOf_Place", "initial_snapshot/static/Place_isPartOf_Place"),
    (
        "TagClass_isSubclassOf_TagClass",
        "initial_snapshot/static/TagClass_isSubclassOf_TagClass",
    ),
    (
        "Organisation_isLocatedIn_Place",
        "initial_snapshot/static/Organisation_isLocatedIn_Place",
    ),
    (
        "Tag_hasType_TagClass",
        "initial_snapshot/static/Tag_hasType_TagClass",
    ),
    (
        "Comment_hasCreator_Person",
        "initial_snapshot/dynamic/Comment_hasCreator_Person",
    ),
    (
        "Comment_isLocatedIn_Country",
        "initial_snapshot/dynamic/Comment_isLocatedIn_Country",
    ),
    (
        "Comment_replyOf_Comment",
        "initial_snapshot/dynamic/Comment_replyOf_Comment",
    ),
    (
        "Comment_replyOf_Post",
        "initial_snapshot/dynamic/Comment_replyOf_Post",
    ),
    (
        "Forum_containerOf_Post",
        "initial_snapshot/dynamic/Forum_containerOf_Post",
    ),
    (
        "Forum_hasMember_Person",
        "initial_snapshot/dynamic/Forum_hasMember_Person",
    ),
    (
        "Forum_hasModerator_Person",
        "initial_snapshot/dynamic/Forum_hasModerator_Person",
    ),
    (
        "Forum_hasTag_Tag",
        "initial_snapshot/dynamic/Forum_hasTag_Tag",
    ),
    (
        "Person_hasInterest_Tag",
        "initial_snapshot/dynamic/Person_hasInterest_Tag",
    ),
    (
        "Person_isLocatedIn_City",
        "initial_snapshot/dynamic/Person_isLocatedIn_City",
    ),
    (
        "Person_knows_Person",
        "initial_snapshot/dynamic/Person_knows_Person",
    ),
    (
        "Person_likes_Comment",
        "initial_snapshot/dynamic/Person_likes_Comment",
    ),
    (
        "Person_likes_Post",
        "initial_snapshot/dynamic/Person_likes_Post",
    ),
    (
        "Post_hasCreator_Person",
        "initial_snapshot/dynamic/Post_hasCreator_Person",
    ),
    (
        "Comment_hasTag_Tag",
        "initial_snapshot/dynamic/Comment_hasTag_Tag",
    ),
    (
        "Post_hasTag_Tag",
        "initial_snapshot/dynamic/Post_hasTag_Tag",
    ),
    (
        "Post_isLocatedIn_Country",
        "initial_snapshot/dynamic/Post_isLocatedIn_Country",
    ),
    (
        "Person_studyAt_University",
        "initial_snapshot/dynamic/Person_studyAt_University",
    ),
    (
        "Person_workAt_Company",
        "initial_snapshot/dynamic/Person_workAt_Company",
    ),
]


def main():
    parser = argparse.ArgumentParser(description="LDBC数据加载器")
    parser.add_argument("--scale-factor", required=True)
    parser.add_argument("--csv-dir", required=True)
    parser.add_argument("--ddl-file-path", required=True)
    parser.add_argument("--ns", default="ldbc")
    parser.add_argument("--graph", default="graph")
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--flavius-url", default="neo4j://fe-0:7687")
    parser.add_argument("--user", default="fvadmin")
    parser.add_argument("--password", default="fvadmin123")

    args = parser.parse_args()
    config = LoaderConfig(args)
    adapter = create_driver_adapter(args)
    recorder = ResultRecorder(config, adapter)
    schema_mgr = SchemaManager(adapter, config)
    writer = BatchWriter(adapter, config)

    try:
        ns_duration = schema_mgr.setup_namespace()
        recorder.record_timing("ns", ns_duration)

        total_start = time.time()
        ddl_duration = schema_mgr.execute_ddl()
        recorder.record_timing("ddl", ddl_duration)

        with ThreadPoolExecutor(config.max_workers) as executor:
            nodes_duration = writer.batch_execute(NODES, executor)
            recorder.record_timing("write_nodes", nodes_duration)
            edges_duration = writer.batch_execute(RELATIONSHIPS, executor)
            recorder.record_timing("write_edges", edges_duration)

        total_duration = time.time() - total_start
        recorder.record_benchmark(total_duration)
        logger.info("Total benchmark duration: %.2f seconds", total_duration)

    except Exception as e:
        logger.critical("Main process failed: %s", e, exc_info=True)
        raise
    finally:
        adapter.close()


if __name__ == "__main__":
    main()

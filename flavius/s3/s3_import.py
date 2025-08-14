import re
import uuid
import time
import os
import logging
import flavius
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple, TypedDict

# 配置日志系统

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("loader.log")
    ],
)
logger = logging.getLogger(__name__)

logger.setLevel(os.getenv("LOG_INFO", "INFO").upper())


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


class TemplateProcessor:
    @staticmethod
    def replace_variables(input_str: str, variables: Dict[str, str]) -> str:
        """安全替换模板变量，保留转义字符"""
        escape_token = f"__ESCAPED_DOLLAR_{uuid.uuid4().hex}__"
        escaped = input_str.replace(r"\$", escape_token)

        for name, value in variables.items():
            pattern = re.escape(f"${{{name}}}")
            escaped = re.sub(pattern, value, escaped)

        return escaped.replace(escape_token, "$")


class BatchWriter:
    def __init__(self, driver, config: LoaderConfig):
        self.driver = driver
        self.config = config
        self.query_cache: Dict[str, str] = {}

    def _load_query(self, entity: str) -> str:
        """加载Cypher查询模板"""
        if entity not in self.query_cache:
            query_file = Path(f"dml/ins-{entity}.cypher")
            self.query_cache[entity] = query_file.read_text()
        return self.query_cache[entity]

    def _prepare_query(self, entity: str, csv_path: str) -> str:
        """准备Cypher查询语句"""
        template = self._load_query(entity)
        return TemplateProcessor.replace_variables(
            template,
            {"csv_file": csv_path, **self.config.aws_config, "has_header": "false"},
        )

    def execute_update(self, entity: str, csv_path: str) -> int:
        """执行单个更新操作"""
        query = self._prepare_query(entity, csv_path)
        logger.debug("Executing query: %s", query)

        result = self.driver.execute_query(
            query,
            namespace=self.config.db_config["namespace"],
            graph=self.config.db_config["graph"],
        )
        return result[0] if result else 0

    def batch_execute(
        self, entities: List[Tuple[str, str]], executor: ThreadPoolExecutor
    ) -> float:
        """批量执行更新操作"""
        start_time = time.time()
        futures = []

        for entity, rel_path in entities:
            csv_path = (
                f"s3://{self.config.aws_config['bucket_name']}/"
                f"{self.config.csv_dir}/{rel_path}/"
            )
            futures.append(executor.submit(self.execute_update, entity, csv_path))

        # 处理结果和异常
        total_changes = 0
        for future in as_completed(futures):
            try:
                total_changes += future.result()
            except Exception as e:
                logger.error("Task failed: %s", e)

        duration = time.time() - start_time
        logger.info(
            "Processed %d entities. Total changes: %d. Duration: %.2fs",
            len(entities),
            total_changes,
            duration,
        )
        return duration


class SchemaManager:
    def __init__(self, driver, config: LoaderConfig):
        self.driver = driver
        self.config = config

    def setup_namespace(self) -> float:
        """初始化命名空间"""
        ns = self.config.db_config["namespace"]

        try:
            self.driver.drop_namespace(ns)
            logger.info("Dropped namespace %s", ns)
        except Exception as e:
            logger.warning("Namespace drop failed: %s", e)

        start_time = time.time()

        self.driver.create_namespace(ns)
        self.driver.create_graph(self.config.db_config["graph"], ns)

        duration = time.time() - start_time
        logger.info(
            "Created namespace %s with graph %s completed in %.2fs",
            ns,
            self.config.db_config["graph"],
            duration,
        )

        return duration

    def execute_ddl(self) -> float:
        """执行DDL脚本"""
        start_time = time.time()

        with open(self.config.ddl_file) as f:
            for line in f:
                stmt = line.strip()
                if stmt and not stmt.startswith("#"):
                    logger.debug("Executing DDL: %s", stmt)
                    self.driver.execute_query(
                        stmt,
                        namespace=self.config.db_config["namespace"],
                        graph=self.config.db_config["graph"],
                    )

        duration = time.time() - start_time
        logger.info("DDL execution completed in %.2fs", duration)
        return duration


class ResultRecorder:
    def __init__(self, config: LoaderConfig):
        self.config = config
        self.output_dir = config.output_dir
        self._prepare_output()

    def _prepare_output(self):
        """准备输出目录和文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "results.csv").touch()
        (self.output_dir / "timings.csv").write_text("tool|sf|q|time\n")
        (self.output_dir / "benchmark.csv").write_text("time\n")

    def record_timing(self, phase: str, duration: float):
        """记录时间指标"""
        with open(self.output_dir / "timings.csv", "a") as f:
            f.write(f"Flavius|{self.config.sf}|{phase}||{duration:.6f}\n")

    def record_benchmark(self, total_duration: float):
        """记录总耗时"""
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
    # 配置解析
    parser = argparse.ArgumentParser(description="LDBC数据加载器")
    parser.add_argument("--scale-factor", required=True, help="数据规模因子")
    parser.add_argument("--csv-dir", required=True, help="CSV文件目录路径")
    parser.add_argument("--ddl-file-path", required=True, help="DDL文件路径")
    parser.add_argument("--ns", default="ldbc", help="命名空间")
    parser.add_argument("--graph", default="graph", help="图名称")
    parser.add_argument("--max-workers", type=int, default=16, help="最大工作线程数")
    parser.add_argument(
        "--flavius-url", default="http://fe-0:30000", help="Flavius服务地址"
    )

    args = parser.parse_args()
    config = LoaderConfig(args)

    # 初始化组件
    driver = flavius.GraphDatabase.driver(config.db_config["flavius_url"], timeout=240)
    driver.verify_connectivity()

    recorder = ResultRecorder(config)
    schema_mgr = SchemaManager(driver, config)
    writer = BatchWriter(driver, config)

    try:
        # 基准测试流程

        # 模式初始化
        ns_duration = schema_mgr.setup_namespace()
        recorder.record_timing("ns", ns_duration)
        total_start = time.time()
        ddl_duration = schema_mgr.execute_ddl()
        recorder.record_timing("ddl", ddl_duration)

        with ThreadPoolExecutor(config.max_workers) as executor:
            # 节点导入
            nodes_duration = writer.batch_execute(NODES, executor)
            recorder.record_timing("write_nodes", nodes_duration)
            # 关系导入
            edges_duration = writer.batch_execute(RELATIONSHIPS, executor)
            recorder.record_timing("write_edges", edges_duration)

        # 结果记录
        total_duration = time.time() - total_start
        recorder.record_benchmark(total_duration)
        logger.info("Total benchmark duration: %.2f seconds", total_duration)

    except Exception as e:
        logger.critical("Main process failed: %s", e, exc_info=True)
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()

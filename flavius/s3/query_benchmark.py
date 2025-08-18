#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import argparse
import logging
import abc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Optional
import flavius
import neo4j
from collections import defaultdict

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_INFO", "INFO").upper())


class QueryConfig:
    def __init__(self, args: argparse.Namespace, loop_index: int = 0):
        self.sf = args.scale_factor
        self.query_dir = Path(args.query_dir)
        self.max_workers = args.max_workers
        # 为每次循环创建独立的输出目录
        self.output_dir = Path(f"output/query-sf{self.sf}/run_{loop_index}")
        self.parallel = args.parallel
        self.default_repeat = args.repeat
        self.loop_index = loop_index  # 保存当前循环索引

        self.db_config = {
            "namespace": args.ns,
            "graph": args.graph,
            "flavius_url": args.flavius_url,
            "user": args.user,
            "password": args.password,
        }


class ResultRecorder:
    def __init__(self, config: QueryConfig):
        self.config = config
        self.output_dir = config.output_dir
        self._prepare_output()
        # 存储每个 query 的所有耗时
        self.query_times = defaultdict(list)

    def _prepare_output(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "timings.csv").write_text("tool|sf|q|time\n")
        (self.output_dir / "benchmark.csv").write_text("time\n")
        (self.output_dir / "stats.csv").write_text(
            "q|repeat|avg_time|max_time|min_time\n"
        )

    def record_timing(self, query_name: str, duration: float):
        self.query_times[query_name].append(duration)
        with open(self.output_dir / "timings.csv", "a") as f:
            f.write(f"Flavius|{self.config.sf}|{query_name}|{duration:.6f}\n")

    def log_timing(self):
        logger.info("Timings result written to %s", self.output_dir / "timings.csv")

    def record_benchmark(self, total_duration: float):
        with open(self.output_dir / "benchmark.csv", "a") as f:
            f.write(f"{total_duration:.6f}\n")
        logger.info("Benchmark result written to %s", self.output_dir / "benchmark.csv")

    def write_stats(self):
        """输出每个 query 的统计信息"""
        with open(self.output_dir / "stats.csv", "a") as f:
            for q, times in self.query_times.items():
                avg_t = sum(times) / len(times)
                max_t = max(times)
                min_t = min(times)
                f.write(f"{q}|{len(times)}|{avg_t:.6f}|{max_t:.6f}|{min_t:.6f}\n")
        logger.info("Per-query stats written to %s", self.output_dir / "stats.csv")


class BaseDriverAdapter(metaclass=abc.ABCMeta):
    """驱动适配器抽象基类"""
    @abc.abstractmethod
    def execute_query(
        self, query: str, namespace: str, graph: str, query_name: str = None
    ) -> float:
        """执行查询并返回耗时（秒）"""
        pass

    @abc.abstractmethod
    def close(self):
        """关闭驱动连接"""
        pass


class FlaviusDriverAdapter(BaseDriverAdapter):
    """Flavius 驱动适配器"""
    def __init__(self, url: str, timeout: int = 2400):
        self.driver = flavius.GraphDatabase.driver(url, timeout=timeout)
        self.driver.verify_connectivity()

    def execute_query(
        self, query: str, namespace: str, graph: str, query_name: str = None
    ) -> float:
        start_time = time.time()
        self.driver.execute_query(query, namespace=namespace, graph=graph)
        return time.time() - start_time

    def close(self):
        self.driver.close()


class Neo4jDriverAdapter(BaseDriverAdapter):
    """Neo4j 驱动适配器"""
    def __init__(self, url: str, user: str, password: str, **params):
        # 确保包含必要的连接参数
        uri = f"{url}?namespace={params.get('ns', '')}&graph={params.get('graph', '')}"
        uri += "&timezone=UTC&timeout=2400&max_parallelism=4&chunk_size=1000"
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password), keep_alive=True)
        logger.info("Connected to Neo4j at %s", url)

    def execute_query(
        self, query: str, namespace: str, graph: str, query_name: str = None
    ) -> float:
        start_time = time.time()
        with self.driver.session() as session:
            session.run(
                query,
                metadata={
                    "namespace": namespace,
                    "graph": graph,
                },
            )
        return time.time() - start_time

    def close(self):
        self.driver.close()


class QueryRunner:
    def __init__(self, adapter: BaseDriverAdapter, config: QueryConfig, recorder: ResultRecorder):
        self.adapter = adapter
        self.config = config
        self.recorder = recorder
        self.repeat_map = self._load_repeat_config()

    def _load_repeat_config(self) -> Dict[str, int]:
        """读取 repeat.conf 配置（可选）"""
        repeat_conf = self.config.query_dir / "repeat.conf"
        repeat_map = {}
        if repeat_conf.exists():
            for line in repeat_conf.read_text().splitlines():
                if "=" in line:
                    name, count = line.split("=", 1)
                    repeat_map[name.strip()] = int(count.strip())
        return repeat_map

    def _load_queries(self) -> List[Tuple[str, str, int]]:
        """扫描 query_dir 下的非 _ 开头文件，读取查询语句和执行次数"""
        queries = []
        for file_path in sorted(self.config.query_dir.glob("*")):
            if (
                file_path.is_file()
                and not file_path.name.startswith("_")
                and file_path.suffix
            ):
                query_str = file_path.read_text().strip()
                if query_str:
                    repeat_count = self.repeat_map.get(
                        file_path.name, self.config.default_repeat
                    )
                    queries.append((file_path.name, query_str, repeat_count))
        return queries

    def _execute_single_query(self, query_name: str, query_str: str) -> float:
        """执行单个查询并记录结果"""
        try:
            start_time = time.time()
            self.adapter.execute_query(
                query_str,
                namespace=self.config.db_config["namespace"],
                graph=self.config.db_config["graph"],
                query_name=query_name,
            )
            duration = time.time() - start_time
            logger.info("Query %s executed in %.2fs", query_name, duration)
            self.recorder.record_timing(query_name, duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.exception("Failed to execute query %s in %.2fs: %s", query_name, duration, e)
        return duration

    def run_all(self):
        queries = self._load_queries()
        logger.info("Loaded %d queries from %s", len(queries), self.config.query_dir)

        start_total = time.time()

        if self.config.parallel:
            with ThreadPoolExecutor(self.config.max_workers) as executor:
                futures = []
                for name, query, repeat_count in queries:
                    for i in range(repeat_count):
                        futures.append(
                            executor.submit(self._execute_single_query, name, query)
                        )
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error("Query failed: %s", e, exc_info=True)
        else:
            for name, query, repeat_count in queries:
                for i in range(repeat_count):
                    self._execute_single_query(name, query)

        total_duration = time.time() - start_total
        logger.info("All queries completed in %.2fs", total_duration)
        self.recorder.log_timing()
        self.recorder.record_benchmark(total_duration)
        self.recorder.write_stats()


def create_driver_adapter(args: argparse.Namespace) -> BaseDriverAdapter:
    """根据URL协议创建对应的驱动适配器"""
    url = args.flavius_url
    if url.startswith("neo4j://"):
        return Neo4jDriverAdapter(
            url,
            user=args.user,
            password=args.password,
            ns=args.ns,
            graph=args.graph
        )
    else:
        return FlaviusDriverAdapter(url)


def main():
    parser = argparse.ArgumentParser(description="Graph Query Benchmark")
    parser.add_argument("--scale-factor", required=True, help="数据规模因子")
    parser.add_argument("--query-dir", required=True, help="查询文件目录路径")
    parser.add_argument("--ns", default="ldbc", help="命名空间")
    parser.add_argument("--graph", default="graph", help="图名称")
    parser.add_argument("--max-workers", type=int, default=4, help="最大并发线程数")
    parser.add_argument(
        "--flavius-url", default="http://fe-0:30000", help="Flavius服务地址"
    )
    parser.add_argument("--user", default="fvadmin", help="用户名")
    parser.add_argument("--password", default="fvadmin123", help="密码")
    parser.add_argument("--repeat", type=int, default=1, help="默认每个 query 执行次数")
    parser.add_argument("--parallel", action="store_true", help="是否并行执行")
    # 添加循环次数参数
    parser.add_argument("--loop", type=int, default=1, help="整个测试集的循环执行次数")

    args = parser.parse_args()

    try:
        # 执行指定次数的循环
        for loop_index in range(args.loop):
            logger.info("===== Starting benchmark run %d/%d =====", 
                       loop_index + 1, args.loop)
            
            # 每次循环使用独立的配置和记录器
            config = QueryConfig(args, loop_index)
            adapter = create_driver_adapter(args)
            recorder = ResultRecorder(config)
            runner = QueryRunner(adapter, config, recorder)
            
            try:
                runner.run_all()
            except Exception as e:
                logger.error("Run %d failed: %s", loop_index + 1, e, exc_info=True)
            finally:
                adapter.close()
            
            logger.info("===== Completed benchmark run %d/%d =====", 
                       loop_index + 1, args.loop)
            
            # 如果不是最后一次循环，等待1秒避免资源冲突
            # if loop_index < args.loop - 1:
            #     time.sleep(1)
                
    except Exception as e:
        logger.critical("Benchmark failed: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
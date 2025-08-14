#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict
import flavius  # 依赖和导入脚本一致
import neo4j  # 依赖和导入脚本一致
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
    def __init__(self, args: argparse.Namespace):
        self.sf = args.scale_factor
        self.query_dir = Path(args.query_dir)
        self.max_workers = args.max_workers
        self.output_dir = Path(f"output/query-sf{self.sf}")
        self.parallel = args.parallel
        self.default_repeat = args.repeat

        self.db_config = {
            "namespace": args.ns,
            "graph": args.graph,
            "flavius_url": args.flavius_url,
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


class QueryRunner:
    def __init__(self, driver, config: QueryConfig, recorder: ResultRecorder):
        self.driver = driver
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

    def _execute_query_once(self, query_name: str, query_str: str) -> float:
        """执行单次查询并返回耗时"""
        start_time = time.time()
        self.driver.execute_query(
            query_str,
            namespace=self.config.db_config["namespace"],
            graph=self.config.db_config["graph"],
        )
        duration = time.time() - start_time
        logger.info("Query %s executed in %.2fs", query_name, duration)
        self.recorder.record_timing(query_name, duration)
        return duration

    def _execute_query_once_in_session(
        self, session, query_name: str, query_str: str
    ) -> float:
        """执行单次查询并返回耗时"""
        start_time = time.time()
        session.run(
            query_str,
            metadata={
                "namespace": self.config.db_config["namespace"],
                "graph": self.config.db_config["graph"],
            },
        )
        duration = time.time() - start_time
        logger.info("Query %s executed in %.2fs", query_name, duration)
        self.recorder.record_timing(query_name, duration)
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
                            executor.submit(self._execute_query_once, name, query)
                        )
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error("Query failed: %s", e)
        else:
            with self.driver.session() as session:
                for name, query, repeat_count in queries:
                    for i in range(repeat_count):
                        try:
                            self._execute_query_once_in_session(session, name, query)
                            # self._execute_query_once(name, query)
                        except Exception as e:
                            logger.exception("Query %s failed: %s", query, e)

        total_duration = time.time() - start_total
        logger.info("All queries completed in %.2fs", total_duration)
        self.recorder.log_timing()
        self.recorder.record_benchmark(total_duration)
        self.recorder.write_stats()


def main():
    parser = argparse.ArgumentParser(description="Flavius Query Benchmark")
    parser.add_argument("--scale-factor", required=True, help="数据规模因子")
    parser.add_argument("--query-dir", required=True, help="查询文件目录路径")
    parser.add_argument("--ns", default="ldbc", help="命名空间")
    parser.add_argument("--graph", default="graph", help="图名称")
    parser.add_argument("--max-workers", type=int, default=4, help="最大并发线程数")
    parser.add_argument(
        "--flavius-url", default="http://fe-0:30000", help="Flavius服务地址"
    )
    parser.add_argument("--user", default="neo4j", help="用户名")
    parser.add_argument("--password", default="includ123", help="密码")
    parser.add_argument("--repeat", type=int, default=1, help="默认每个 query 执行次数")
    parser.add_argument("--parallel", action="store_true", help="是否并行执行")

    args = parser.parse_args()
    config = QueryConfig(args)

    if args.flavius_url.startswith("neo4j://"):
        URI = f"{config.db_config['flavius_url']}?namespace={args.ns}&graph={args.graph}&timezone=UTC&timeout=2400&max_parallelism=4&chunk_size=1000"
        AUTH = (args.user, args.password)
        logger.info("Connecting to Neo4j at %s with auth %s", URI, AUTH[0])
        with neo4j.GraphDatabase.driver(
            URI,
            auth=AUTH,
            max_connection_lifetime=60,  # 秒，避免连接被 ELB/NAT 提前干掉
            keep_alive=True,
        ) as driver:
            recorder = ResultRecorder(config)
            runner = QueryRunner(driver, config, recorder)
            try:
                runner.run_all()
            except Exception as e:
                logger.critical("Benchmark failed: %s", e, exc_info=True)
                raise
    else:
        driver = flavius.GraphDatabase.driver(
            config.db_config["flavius_url"], timeout=2400
        )
        driver.verify_connectivity()

        recorder = ResultRecorder(config)
        runner = QueryRunner(driver, config, recorder)

        try:
            runner.run_all()
        except Exception as e:
            logger.critical("Benchmark failed: %s", e, exc_info=True)
            raise
        finally:
            driver.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import argparse
import os
import shutil
import sys
import subprocess
from pathlib import Path
from utils import list_csv_files


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Neo4j数据导入工具",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--neo4j-data-dir", help="Neo4j数据存储目录")
    parser.add_argument("--neo4j-header-dir", required=True, help="CSV头文件目录")
    parser.add_argument(
        "--neo4j-csv-dir",
        required=True,
        help="原始CSV数据目录, 目录下包含 deletes/, initial_snapshot/ 和 inserts/",
    )
    parser.add_argument(
        "--neo4j-ddl-dir", required=True, help="DDL文件目录,用于创建索引(必需参数)"
    )
    parser.add_argument("--neo4j-version", default="4.4", help="Neo4j版本号")
    parser.add_argument("--neo4j-env-vars", default="", help="额外的Docker环境变量")

    return parser.parse_args()


# 解析命令行参数
args = parse_arguments()

# 初始化配置参数
NEO4J_DATA_DIR = Path(args.neo4j_data_dir)
NEO4J_HEADER_DIR = Path(args.neo4j_header_dir)
NEO4J_CSV_DIR = args.neo4j_csv_dir
NEO4J_DDL_DIR = Path(args.neo4j_ddl_dir)
NEO4J_VERSION = args.neo4j_version
NEO4J_ENV_VARS = args.neo4j_env_vars

# 清理并重建数据目录
if NEO4J_DATA_DIR.exists():
    shutil.rmtree(NEO4J_DATA_DIR)
NEO4J_DATA_DIR.mkdir(parents=True)


# 节点配置列表（类型，头文件相对路径，CSV目录相对路径）
NODES = [
    ("Place", "static/Place", "initial_snapshot/static/Place"),
    ("Organisation", "static/Organisation", "initial_snapshot/static/Organisation"),
    ("TagClass", "static/TagClass", "initial_snapshot/static/TagClass"),
    ("Tag", "static/Tag", "initial_snapshot/static/Tag"),
    ("Forum", "dynamic/Forum", "initial_snapshot/dynamic/Forum"),
    ("Person", "dynamic/Person", "initial_snapshot/dynamic/Person"),
    ("Message:Comment", "dynamic/Comment", "initial_snapshot/dynamic/Comment"),
    ("Message:Post", "dynamic/Post", "initial_snapshot/dynamic/Post"),
]

# 关系配置列表（类型，头文件相对路径，CSV目录相对路径）
RELATIONSHIPS = [
    (
        "IS_PART_OF",
        "static/Place_isPartOf_Place",
        "initial_snapshot/static/Place_isPartOf_Place",
    ),
    (
        "IS_SUBCLASS_OF",
        "static/TagClass_isSubclassOf_TagClass",
        "initial_snapshot/static/TagClass_isSubclassOf_TagClass",
    ),
    (
        "IS_LOCATED_IN",
        "static/Organisation_isLocatedIn_Place",
        "initial_snapshot/static/Organisation_isLocatedIn_Place",
    ),
    (
        "HAS_TYPE",
        "static/Tag_hasType_TagClass",
        "initial_snapshot/static/Tag_hasType_TagClass",
    ),
    (
        "HAS_CREATOR",
        "dynamic/Comment_hasCreator_Person",
        "initial_snapshot/dynamic/Comment_hasCreator_Person",
    ),
    (
        "IS_LOCATED_IN",
        "dynamic/Comment_isLocatedIn_Country",
        "initial_snapshot/dynamic/Comment_isLocatedIn_Country",
    ),
    (
        "REPLY_OF",
        "dynamic/Comment_replyOf_Comment",
        "initial_snapshot/dynamic/Comment_replyOf_Comment",
    ),
    (
        "REPLY_OF",
        "dynamic/Comment_replyOf_Post",
        "initial_snapshot/dynamic/Comment_replyOf_Post",
    ),
    (
        "CONTAINER_OF",
        "dynamic/Forum_containerOf_Post",
        "initial_snapshot/dynamic/Forum_containerOf_Post",
    ),
    (
        "HAS_MEMBER",
        "dynamic/Forum_hasMember_Person",
        "initial_snapshot/dynamic/Forum_hasMember_Person",
    ),
    (
        "HAS_MODERATOR",
        "dynamic/Forum_hasModerator_Person",
        "initial_snapshot/dynamic/Forum_hasModerator_Person",
    ),
    (
        "HAS_TAG",
        "dynamic/Forum_hasTag_Tag",
        "initial_snapshot/dynamic/Forum_hasTag_Tag",
    ),
    (
        "HAS_INTEREST",
        "dynamic/Person_hasInterest_Tag",
        "initial_snapshot/dynamic/Person_hasInterest_Tag",
    ),
    (
        "IS_LOCATED_IN",
        "dynamic/Person_isLocatedIn_City",
        "initial_snapshot/dynamic/Person_isLocatedIn_City",
    ),
    (
        "KNOWS",
        "dynamic/Person_knows_Person",
        "initial_snapshot/dynamic/Person_knows_Person",
    ),
    (
        "LIKES",
        "dynamic/Person_likes_Comment",
        "initial_snapshot/dynamic/Person_likes_Comment",
    ),
    (
        "LIKES",
        "dynamic/Person_likes_Post",
        "initial_snapshot/dynamic/Person_likes_Post",
    ),
    (
        "HAS_CREATOR",
        "dynamic/Post_hasCreator_Person",
        "initial_snapshot/dynamic/Post_hasCreator_Person",
    ),
    (
        "HAS_TAG",
        "dynamic/Comment_hasTag_Tag",
        "initial_snapshot/dynamic/Comment_hasTag_Tag",
    ),
    ("HAS_TAG", "dynamic/Post_hasTag_Tag", "initial_snapshot/dynamic/Post_hasTag_Tag"),
    (
        "IS_LOCATED_IN",
        "dynamic/Post_isLocatedIn_Country",
        "initial_snapshot/dynamic/Post_isLocatedIn_Country",
    ),
    (
        "STUDY_AT",
        "dynamic/Person_studyAt_University",
        "initial_snapshot/dynamic/Person_studyAt_University",
    ),
    (
        "WORK_AT",
        "dynamic/Person_workAt_Company",
        "initial_snapshot/dynamic/Person_workAt_Company",
    ),
]


# 自定义 find 函数实现
def find_files(
    prefix,
) -> list:
    # 设置 AWS 凭证
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    BUCKET_NAME = os.getenv("BUCKET_NAME")

    result = list_csv_files(
        access_key_id=AWS_ACCESS_KEY_ID,
        access_key_secret=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
        bucket_name=BUCKET_NAME,
        prefix=prefix,
    )

    print("find_files result:", result)

    return result


# 构建 Docker 命令
docker_cmd = [
    "docker",
    "run",
    "--rm",
    "--user",
    f"{os.getuid()}:{os.getgid()}",
    "--volume",
    f"{NEO4J_DATA_DIR.absolute()}:/data",
    "--volume",
    f"{NEO4J_DDL_DIR.absolute()}:/ddl",
    "--volume",
    f"{NEO4J_HEADER_DIR.absolute()}:/headers",
]

# 添加环境变量
if NEO4J_ENV_VARS:
    docker_cmd.extend(NEO4J_ENV_VARS.split())

# Neo4j 主体命令
docker_cmd += [
    f"neo4j:{NEO4J_VERSION}",
    "neo4j-admin",
    "database",
    "import",
    "full",
    "--id-type=INTEGER",
    "--ignore-empty-strings=true",
    "--bad-tolerance=0",
    "--schema=/ddl/indices.cypher",
]


def build_entity_args(
    neo4j_csv_dir,
    find_files,
    docker_cmd,
    header_rel_path,
    csv_rel_path,
    entity_type,
    entity,
):
    header_path = f"/headers/{header_rel_path}.csv"
    csv_full_path = f"{neo4j_csv_dir}/{csv_rel_path}"
    files = find_files(str(csv_full_path))
    files_str = "," + ",".join(files) if len(files) != 0 else ""
    docker_cmd.append(f"--{entity_type}={entity}={header_path}{files_str}")


# 添加节点参数
for entity_type, header_rel_path, csv_rel_path in NODES:
    build_entity_args(
        NEO4J_CSV_DIR,
        find_files,
        docker_cmd,
        header_rel_path,
        csv_rel_path,
        "nodes",
        entity_type,
    )

# 添加关系参数
for rel_type, header_rel_path, csv_rel_path in RELATIONSHIPS:
    build_entity_args(
        NEO4J_CSV_DIR,
        find_files,
        docker_cmd,
        header_rel_path,
        csv_rel_path,
        "relationships",
        rel_type,
    )

# 添加分隔符参数
docker_cmd.append("--delimiter=|")
docker_cmd.append("--verbose")

# 执行命令
print("Executing:", " ".join(docker_cmd))
result = subprocess.run(docker_cmd, check=True)

# 检查执行结果
if result.returncode != 0:
    print("Docker command failed with code:", result.returncode)
    sys.exit(result.returncode)

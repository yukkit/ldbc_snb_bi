import argparse
import json
import os
from pathlib import Path


def get_file_urls(local_base_dir, table_names=set()):
    """
    生成指定目录下所有文件的本地文件 URL
    :param table_names: 需要生成 URL 的表名列表（可选）
    :return: 包含 { "<表名>" : { "<batch_id>": [文件 URLs...] } 的字典
    :raises ValueError: 如果本地基础目录不存在
    """
    # 获取本地基础目录
    table_base_dir = os.path.join(local_base_dir, "inserts", "dynamic")

    if not os.path.isdir(table_base_dir):
        raise ValueError(f"本地表数据目录 {table_base_dir} 不存在")

    signed_url_dict = {}

    print(f"正在扫描本地目录 {table_base_dir}...")

    # 遍历一级目录（表名目录）
    for table_entry in os.listdir(table_base_dir):
        table_dir = os.path.join(table_base_dir, table_entry)

        # 跳过非目录文件
        if not os.path.isdir(table_dir):
            continue

        # 过滤表名
        table_name = table_entry
        if table_names and table_name not in table_names:
            print(f"跳过表 {table_name}")
            continue

        signed_url_dict[table_name] = {}

        # 遍历二级目录（batch_id目录）
        for batch_entry in os.listdir(table_dir):
            batch_dir = os.path.join(table_dir, batch_entry)

            # 跳过非目录文件
            if not os.path.isdir(batch_dir):
                continue

            batch_id = batch_entry  # 保留完整目录名作为 key
            signed_url_dict[table_name][batch_id] = []

            # 遍历三级文件
            for file_entry in os.listdir(batch_dir):
                file_path = os.path.join(batch_dir, file_entry)

                if os.path.isfile(file_path) and (
                    file_path.endswith(".csv") or file_path.endswith(".csv.gz")
                ):
                    # 转换为标准 file:// URL
                    absolute_file_url = Path(file_path).resolve().as_uri()

                    # 删除路径中的 `local_base_dir`，因为我们会将数据文件挂在到 neo4j 容器中
                    file_url = absolute_file_url.replace(
                        Path(local_base_dir).resolve().as_uri(), "file://"
                    )

                    signed_url_dict[table_name][batch_id].append(file_url)
                    print(f"找到文件: {absolute_file_url}, 转换为: {file_url}")

        print(f"完成处理表 {table_name}")

    print("本地文件扫描完成")
    return signed_url_dict


if __name__ == "__main__":
    LOCAL_BASE_DIR = os.getenv("NEO4J_CSV_DIR", "/default/path")

    parser = argparse.ArgumentParser(description="生成本地文件URL列表")
    # 为了保持接口兼容性保留 timeout 参数（实际不使用）
    parser.add_argument(
        "--timeout", type=int, default=3600, help="兼容性参数（不再生效）"
    )
    args = parser.parse_args()

    result = get_file_urls(local_base_dir=LOCAL_BASE_DIR)
    print("\n最终文件URL列表:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

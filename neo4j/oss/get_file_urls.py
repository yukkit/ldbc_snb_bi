import argparse
import json
import oss2
import os


def get_file_urls(
    oss_access_key_id,
    oss_access_key_secret,
    oss_endpoint,
    oss_bucket_name,
    oss_prefix,
    timeout=60,
    table_names=set(),
):
    """
    生成指定目录下所有文件的签名 URL
    :param table_names: 需要生成签名 URL 的表名列表（可选）
    :param timeout: URL有效期(秒), 默认3600秒
    :return: 包含 { "<表名>" : { "<batch_id>": [文件签名 URLs...] } 的字典
    :raises ValueError: 如果环境变量未设置
    :raises Exception: 如果发生错误
    """

    # 创建认证对象
    auth = oss2.Auth(oss_access_key_id, oss_access_key_secret)

    # 创建 Bucket 对象
    bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket_name)

    print(f"正在生成 {oss_bucket_name}/{oss_prefix} 下所有文件的签名 URL...")

    signed_url_dict = {}
    try:
        # 遍历所有对象（自动处理分页）
        for name_dir in oss2.ObjectIterator(bucket, prefix=oss_prefix, delimiter="/"):
            # 排除目录对象
            print(f"正在处理对象: {name_dir.key}")
            if name_dir.key.endswith("/"):
                # ldbc_snb_bi_sf1_raw/Comment/
                name = name_dir.key[len(oss_prefix) : -1]
                print(f"对象名称: {name}")
                # 忽略不在 table_names 中的对象
                if table_names and name not in table_names:
                    print(f"跳过对象: {name}")
                    continue

                if name not in signed_url_dict:
                    signed_url_dict[name] = {}

                for batch_dir in oss2.ObjectIterator(
                    bucket, prefix=name_dir.key, delimiter="/"
                ):
                    if batch_dir.key.endswith("/"):
                        # ldbc_snb_bi_sf1_raw/Comment/batch_id=2012-11-29/
                        batch = batch_dir.key[len(name_dir.key) : -1]
                        print(f"batch 名称: {batch}")

                        if batch not in signed_url_dict[name]:
                            signed_url_dict[name][batch] = []

                        for file in oss2.ObjectIterator(bucket, prefix=batch_dir.key):
                            # ldbc_snb_bi_sf1_raw/Comment/batch_id=2012-11-29/part-00000-0e50c5ac-8cdf-4099-b745-2e5c0c1e6913.c000.csv
                            print(f"文件名称: {file.key}")
                            # 忽略目录对象
                            if not file.key.endswith("/"):
                                # 生成签名 URL
                                url = bucket.sign_url("GET", file.key, timeout)
                                print(f"生成的签名 URL: {url}")
                                # 往 signed_url_dict[name][batch] 列表中添加 已签名的 url
                                signed_url_dict[name][batch].append(url)
            print(f"对象 {name_dir.key} 处理完成\n")
            print(f"当前已生成 {len(signed_url_dict)} 个对象的签名 URL")
            print("==========================")
        print("所有对象的签名 URL 生成完成")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        raise e

    return signed_url_dict


if __name__ == "__main__":
    ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "your-access-key-id")
    ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "your-access-key-secret")
    ENDPOINT = os.getenv("OSS_ENDPOINT", "https://oss-cn-hangzhou.aliyuncs.com")
    BUCKET_NAME = os.getenv("OSS_BUCKET_NAME", "kasma-fileio-ci")
    PREFIX = os.getenv("OSS_PREFIX", "ldbc_snb_bi_sf1_raw/")

    # 配置命令行参数解析
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--timeout", type=int, default=3600, help="URL有效期(秒，默认 3600)"
    )
    args = parser.parse_args()

    # 执行并输出结果
    result = get_file_urls(
        oss_access_key_id=ACCESS_KEY_ID,
        oss_access_key_secret=ACCESS_KEY_SECRET,
        oss_endpoint=ENDPOINT,
        oss_bucket_name=BUCKET_NAME,
        oss_prefix=PREFIX,
        timeout=args.timeout,
    )
    print("Generated URLs:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

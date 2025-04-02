import os
import boto3


def list_csv_files(
    access_key_id,
    access_key_secret,
    region_name,
    bucket_name,
    prefix,
):
    """
    列出指定 S3 存储桶和目录下的所有 CSV 文件
    :param bucket_name: S3 存储桶名称
    :param prefix: 目录前缀 (例如: myfolder/)
    """
    s3 = boto3.client(
        "s3",
        region_name=region_name,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=access_key_secret,
    )

    # 打印参数列表
    print(
        f"access_key_id: {access_key_id}, access_key_secret: {access_key_secret}, region_name: {region_name}, bucket_name: {bucket_name}, prefix: {prefix}"
    )

    # 确保目录前缀以斜杠结尾（避免匹配到其他前缀相同的文件）
    if not prefix.endswith("/"):
        prefix += "/"

    # 使用分页器处理超过 1000 个文件的情况
    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    csv_files = []
    for page in page_iterator:
        if "Contents" in page:
            for obj in page["Contents"]:
                key = obj["Key"]
                # 过滤 CSV 文件并排除目录对象
                if key.endswith(".csv") and not key.endswith("/"):
                    print(f"========{obj}")
                    size = obj["Size"]
                    if size == 0:
                        print(f"Skipping empty file: {key}")
                        continue
                    # 构造 s3:// 路径
                    s3_uri = f"s3://{bucket_name}/{key}"
                    csv_files.append(s3_uri)

    return csv_files


if __name__ == "__main__":
    """
    export AWS_ACCESS_KEY_ID=xxx
    export AWS_SECRET_ACCESS_KEY=xxx
    export AWS_DEFAULT_REGION=ap-east-1
    export BUCKET_NAME=kasma-fileio-ci
    export PREFIX=ldbc_snb_bi_sf1_raw/initial_snapshot/static/Place/
    """
    ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key-id")
    ACCESS_KEY_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "your-access-key-secret")
    REGION = os.getenv("AWS_DEFAULT_REGION", "your-region")
    BUCKET_NAME = os.getenv("BUCKET_NAME", "your-bucket-name")
    PREFIX = os.getenv("PREFIX", "ldbc_snb_bi_sf1_raw/")

    # 执行并输出结果
    result = list_csv_files(
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET,
        region_name=REGION,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
    )
    print(",".join(result))

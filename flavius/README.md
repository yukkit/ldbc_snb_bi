# LDBC SNB BI Flavius/Cypher implementation

## Prerequisites

- Docker
- Docker Compose
- AWS CLI
- Python
- Python packages:
  - `flavius`

```
pip install -i https://test.pypi.org/simple/ flavius
```

## Generating the data set

```bash
export SF=0.003
export OUTPUT_DATA_DIR="$(pwd)"/out_sf${SF}_bi
rm -rf ${OUTPUT_DATA_DIR}
mkdir -p ${OUTPUT_DATA_DIR}   # create output directory
docker run \
    --rm \
    -v ${OUTPUT_DATA_DIR}:/out \
    ldbc/datagen-standalone:0.5.1-2.12_spark3.2 \
    --parallelism $(nproc) \
    -- \
    --format csv \
    --scale-factor ${SF} \
    --explode-edges \
    --mode bi \
    --output-dir out \
    --format-options header=false,quoteAll=true
```

## upload the data to S3

```bash
# 上传csv文件
export CSV_DIR=ldbc_snb_bi_sf${SF}_raw
export BUCKET_NAME=kasma-fileio-ci

aws s3 cp ${OUTPUT_DATA_DIR}/graphs/csv/bi/composite-projected-fk/ s3://${BUCKET_NAME}/${CSV_DIR}/ \
--recursive \
--include "*.csv"

# aws s3 cp 的时候 --include "*.csv" 貌似不好用，所以在删除掉多余文件
aws s3 rm s3://${BUCKET_NAME}/${CSV_DIR}/ \
--recursive \
--exclude "*.csv" 
```

## start flavius

```bash
# TODO
````

## Loading the data

```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=ap-east-1
export AWS_ENDPOINT_URL=
export BUCKET_NAME=${BUCKET_NAME:-"kasma-fileio-ci"}

env LOG_INFO=debug python3 s3/s3_import.py \
--flavius-url http://fe-0:30000 \
--scale_factor ${SF} \
--csv-dir ${CSV_DIR:-"ldbc_snb_bi_sf${SF}_raw"} \
--ddl-file-path "$(pwd)"/ddl/ddl_ldbc.slt \
--max_workers 16
```

## Microbatches

Test loading the microbatches:

在 queries 目录下

# LDBC SNB BI Flavius/Cypher implementation

## Prerequisites

- Docker
- Docker Compose
- AWS CLI
- Python
- Python packages:
  - `flavius`
  - `neo4j`
  - `matplotlib`
  - `seaborn`

```
pip3 install -r requirements.txt
# https://github.com/Kasma-Inc/Flavius_SDK/tree/main/python
pip3 install -i https://test.pypi.org/simple/ flavius-py310
# 按需
pip3 install --upgrade requests
```



## Generating the data set

```bash
export SF=1
export OUTPUT_DATA_DIR=/data03/dataset/out_sf${SF}_bi
rm -rf ${OUTPUT_DATA_DIR}
mkdir -p ${OUTPUT_DATA_DIR}   # create output directory
docker run \
    --rm \
    -v ${OUTPUT_DATA_DIR}:/out \
    ldbc/datagen-standalone:0.5.1-2.12_spark3.2 \
    --parallelism $(nproc) \
    --memory 40g \
    -- \
    --format csv \
    --scale-factor ${SF} \
    --explode-edges \
    --mode bi \
    --output-dir out \
    --format-options header=false,quoteAll=true
```
fvadmin
## upload the data to S3

```bash
# 上传csv文件
export CSV_DIR=ldbc_snb_bi_sf${SF}_raw
export BUCKET_NAME=kasma-fileio-ci

aws s3 cp ${OUTPUT_DATA_DIR}/graphs/csv/bi/composite-projected-fk/ s3://${BUCKET_NAME}/${CSV_DIR}/ \
--recursive \
--exclude "*" \
--include "*.csv"
```

## start flavius

```bash
# TODO
````

## Loading the data

```bash
export NS=ldbc
export GRAPH=graph
export FLAVIUS_URL="http://localhost:39999"

export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=ap-east-1
export AWS_ENDPOINT_URL=
export BUCKET_NAME=${BUCKET_NAME:-"kasma-fileio-ci"}

env LOG_INFO=debug python3 s3/s3_import.py \
--flavius-url ${FLAVIUS_URL} \
--ns ${NS} \
--graph ${GRAPH} \
--scale-factor ${SF} \
--csv-dir ${CSV_DIR:-"ldbc_snb_bi_sf${SF}_raw"} \
--ddl-file-path "$(pwd)"/ddl/ddl_ldbc.slt \
--max_workers 16
```

## Microbatches

### 执行benchmark

```bash
# 会在 output/query-sf${SF} 目录下生成结果
# 包括 timings.csv、benchmark.csv 和 stats.csv
env LOG_INFO=debug python3 s3/query_benchmark.py \
--flavius-url ${FLAVIUS_URL} \
--ns ${NS} \
--graph ${GRAPH} \
--scale-factor ${SF} \
--query-dir "$(pwd)"/queries/ \
--repeat 3
```

### 绘制结果

```bash
env LOG_INFO=debug python3 s3/plot_benchmark_result.py \
--timings output/query-sf${SF}/timings.csv \
--scale-factor ${SF}
```
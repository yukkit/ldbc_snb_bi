# LDBC SNB BI Neo4j/Cypher implementation

## Generating the data set

同 Flavius


## Loading the data

```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=ap-east-1
export BUCKET_NAME=kasma-fileio-ci

export NEO4J_ENV_VARS="--cpus 16 --memory 64GB --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes --env AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} --env AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} --env AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} --env NEO4J_dbms_memory_pagecache_size=20G --env NEO4J_dbms_memory_heap_max__size=44G"

export LOCAL_DATA_DIR="/home/yjzhang/neo4j/data"

python3 s3/s3_import.py \
--neo4j-data-dir ${LOCAL_DATA_DIR} \
--neo4j-header-dir /home/yjzhang/workspace/ldbc_snb_bi/neo4j/headers \
--neo4j-ddl-dir /home/yjzhang/workspace/ldbc_snb_bi/neo4j/ddl \
--neo4j-csv-dir ldbc_snb_bi_sf10_raw \
--neo4j-version 2025.03.0-enterprise \
--neo4j-env-vars "${NEO4J_ENV_VARS}"
```

## 启动 neo4j

```bash
docker run \
    --rm \
    --cpus 16 \
    --memory 48G \
    --network yukkit_cluster \
    --network-alias neo4j \
    --volume ${LOCAL_DATA_DIR}:/data \
    --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    --env NEO4J_db_logs_query_enabled=VERBOSE \
    --env NEO4J_server_logs_debug_enabled=true \
    --env NEO4J_dbms_logs_http_enabled=true \
    --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
    --env NEO4J_AUTH=none \
    --env NEO4J_dbms_security_allow__csv__import__from__file__urls=true \
    --env NEO4J_server_directories_import='/import' \
    --env NEO4J_server_memory_pagecache_size=20G \
    --env NEO4J_server_memory_heap_max__size=28G \
    --name yukkit_neo4j \
    neo4j:2025.03.0-enterprise
```

## Microbatches

在 queries 目录下

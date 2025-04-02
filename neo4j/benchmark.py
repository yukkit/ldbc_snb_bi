from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import os
import csv
import datetime
import neo4j
from queries import run_queries, run_precomputations
from pathlib import Path
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor
import argparse


def write_batch_fun(tx, query_spec, csv_file):
    result = tx.run(query_spec, csv_file=csv_file)
    return result.value()


def run_update(session, query_spec, csv_file):
    result = session.execute_write(write_batch_fun, query_spec, csv_file)
    num_changes = result[0]
    return num_changes


def run_update_entity(driver, insert_queries, signed_url_dict, entity, batch_dir):
    with driver.session() as session:
        # check if the entity is in the signed_url_dict
        if entity not in signed_url_dict:
            print(f"Entity {entity} not found in signed_url_dict")
            return
        # get the signed URL for the entity
        batch_2_signed_urls = signed_url_dict[entity]
        # check if the batch_dir is in the signed_url_dict
        if batch_dir not in batch_2_signed_urls:
            print(f"Batch {batch_dir} not found in signed_url_dict for entity {entity}")
            return
        # get the signed URL for the batch_dir
        signed_urls = batch_2_signed_urls[batch_dir]

        print(f"Starting {entity}:")
        for csv_file in signed_urls:
            print(f"- Loading: {csv_file}")
            run_update(session, insert_queries[entity], csv_file)
        print(f"End {entity}:")


def run_batch_updates(
    driver,
    session,
    data_dir,
    signed_url_dict,
    batch_date,
    batch_type,
    insert_nodes,
    insert_edges,
    delete_entities,
    insert_queries,
    delete_queries,
    max_workers,
):
    start = time.time()

    batch_id = batch_date.strftime("%Y-%m-%d")
    batch_dir = f"batch_id={batch_id}"
    print(f"#################### {batch_dir} ####################")

    print("## Insert Nodes")
    with ThreadPoolExecutor(max_workers) as pool:
        for entity in insert_nodes:
            pool.submit(
                run_update_entity,
                driver=driver,
                insert_queries=insert_queries,
                signed_url_dict=signed_url_dict,
                entity=entity,
                batch_dir=batch_dir,
            )
    print("## Insert Edges")
    with ThreadPoolExecutor(max_workers) as pool:
        for entity in insert_edges:
            pool.submit(
                run_update_entity,
                driver=driver,
                insert_queries=insert_queries,
                signed_url_dict=signed_url_dict,
                entity=entity,
                batch_dir=batch_dir,
            )

            # # check if the entity is in the signed_url_dict
            # if entity not in signed_url_dict:
            #     print(f"Entity {entity} not found in signed_url_dict")
            #     continue
            # # get the signed URL for the entity
            # batch_2_signed_urls = signed_url_dict[entity]
            # # check if the batch_dir is in the signed_url_dict
            # if batch_dir not in batch_2_signed_urls:
            #     print(
            #         f"Batch {batch_dir} not found in signed_url_dict for entity {entity}"
            #     )
            #     continue
            # # get the signed URL for the batch_dir
            # signed_urls = batch_2_signed_urls[batch_dir]

            # print(f"{entity}:")
            # for csv_file in signed_urls:
            #     print(f"- Loading: {csv_file}")
            #     run_update(session, insert_queries[entity], csv_file)

    # print("## Deletes")
    # for entity in delete_entities:
    #     batch_path = f"{data_dir}/deletes/dynamic/{entity}/{batch_dir}"
    #     if not os.path.exists(batch_path):
    #         continue

    #     print(f"{entity}:")
    #     for csv_file in [
    #         f
    #         for f in os.listdir(batch_path)
    #         if f.endswith(".csv") or f.endswith(".csv.gz")
    #     ]:
    #         print(f"- {entity}/{batch_dir}/{csv_file}")
    #         run_update(session, delete_queries[entity], batch_dir, csv_file)
    return time.time() - start


if __name__ == "__main__":
    query_variants = [
        "1",
        "2a",
        "2b",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8a",
        "8b",
        "9",
        "10a",
        "10b",
        "11",
        "12",
        "13",
        "14a",
        "14b",
        "15a",
        "15b",
        "16a",
        "16b",
        "17",
        "18",
        "19a",
        "19b",
        "20a",
        "20b",
    ]

    driver = neo4j.GraphDatabase.driver("bolt://neo4j:7687")
    session = driver.session()

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale_factor", type=str, help="Scale factor", required=True)
    parser.add_argument(
        "--data_dir",
        type=str,
        help="Directory with the initial_snapshot, insert, and delete directories",
        required=False,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test execution: 1 query/batch",
        required=False,
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validation mode", required=False
    )
    parser.add_argument(
        "--pgtuning",
        action="store_true",
        help="Paramgen tuning execution: 100 queries/batch",
        required=False,
    )
    parser.add_argument(
        "--queries", action="store_true", help="Only run queries", required=False
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=16,
        help="Number of threads to use for batch updates",
        required=False,
    )
    args = parser.parse_args()
    sf = args.scale_factor
    test = args.test
    pgtuning = args.pgtuning
    data_dir = args.data_dir
    queries_only = args.queries
    validate = args.validate
    max_workers = args.max_workers

    ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "your-access-key-id")
    ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "your-access-key-secret")
    ENDPOINT = os.getenv("OSS_ENDPOINT", "https://oss-cn-hangzhou.aliyuncs.com")
    BUCKET_NAME = os.getenv("OSS_BUCKET_NAME", "kasma-fileio-ci")
    PREFIX = os.getenv("OSS_PREFIX", "ldbc_snb_bi_sf1_raw/")

    if data_dir:
        data_dir = os.path.abspath(data_dir)
        print(f"Using local data directory: {data_dir}")
        from local import get_file_urls

        signed_url_dict = get_file_urls.get_file_urls(local_base_dir=data_dir)
    else:
        if not all([ACCESS_KEY_ID, ACCESS_KEY_SECRET, ENDPOINT, BUCKET_NAME, PREFIX]):
            raise ValueError("Please ensure all environment variables are set")
        print(
            f"Using OSS data directory: {BUCKET_NAME}/{PREFIX} with endpoint {ENDPOINT}"
        )
        from oss import get_file_urls

        print(f"Generating signed URLs for {BUCKET_NAME}/{PREFIX}...")

        signed_url_dict = get_file_urls.get_file_urls(
            oss_access_key_id=ACCESS_KEY_ID,
            oss_access_key_secret=ACCESS_KEY_SECRET,
            oss_endpoint=ENDPOINT,
            oss_bucket_name=BUCKET_NAME,
            oss_prefix=PREFIX,
            timeout=3600,
        )

    print(f"- Input data files: {signed_url_dict}")

    parameter_csvs = {}
    for query_variant in query_variants:
        # wrap parameters into infinite loop iterator
        parameter_csvs[query_variant] = cycle(
            csv.DictReader(
                open(f"../parameters/parameters-sf{sf}/bi-{query_variant}.csv"),
                delimiter="|",
            )
        )

    # to ensure that all inserted edges have their endpoints at the time of their insertion, we insert nodes first and edges second
    insert_nodes = ["Comment", "Forum", "Person", "Post"]
    insert_edges = [
        "Comment_hasCreator_Person",
        "Comment_hasTag_Tag",
        "Comment_isLocatedIn_Country",
        "Comment_replyOf_Comment",
        "Comment_replyOf_Post",
        "Forum_containerOf_Post",
        "Forum_hasMember_Person",
        "Forum_hasModerator_Person",
        "Forum_hasTag_Tag",
        "Person_hasInterest_Tag",
        "Person_isLocatedIn_City",
        "Person_knows_Person",
        "Person_likes_Comment",
        "Person_likes_Post",
        "Person_studyAt_University",
        "Person_workAt_Company",
        "Post_hasCreator_Person",
        "Post_hasTag_Tag",
        "Post_isLocatedIn_Country",
    ]
    insert_entities = insert_nodes + insert_edges

    # set the order of deletions to reflect the dependencies between node labels (:Comment)-[:REPLY_OF]->(:Post)<-[:CONTAINER_OF]-(:Forum)-[:HAS_MODERATOR]->(:Person)
    delete_nodes = ["Comment", "Post", "Forum", "Person"]
    delete_edges = [
        "Forum_hasMember_Person",
        "Person_knows_Person",
        "Person_likes_Comment",
        "Person_likes_Post",
    ]
    delete_entities = delete_nodes + delete_edges

    insert_queries = {}
    for entity in insert_entities:
        with open(f"dml/ins-{entity}.cypher", "r") as insert_query_file:
            insert_queries[entity] = insert_query_file.read()

    delete_queries = {}
    for entity in delete_entities:
        with open(f"dml/del-{entity}.cypher", "r") as delete_query_file:
            delete_queries[entity] = delete_query_file.read()

    output = Path(f"output/output-sf{sf}")
    output.mkdir(parents=True, exist_ok=True)
    open(f"output/output-sf{sf}/results.csv", "w").close()
    open(f"output/output-sf{sf}/timings.csv", "w").close()

    results_file = open(f"output/output-sf{sf}/results.csv", "a")
    timings_file = open(f"output/output-sf{sf}/timings.csv", "a")
    timings_file.write(f"tool|sf|day|batch_type|q|parameters|time\n")

    network_start_date = datetime.date(2012, 11, 29)
    network_end_date = datetime.date(2013, 1, 1)
    test_end_date = datetime.date(2012, 12, 2)
    batch_size = relativedelta(days=1)
    batch_date = network_start_date

    benchmark_start = time.time()

    if queries_only:
        batch_type = "power"
        run_precomputations(
            sf, query_variants, session, batch_date, batch_type, timings_file
        )
        reads_time = run_queries(
            query_variants,
            parameter_csvs,
            session,
            sf,
            batch_date,
            batch_type,
            test,
            pgtuning,
            timings_file,
            results_file,
        )
    else:
        # Run alternating write-read blocks.
        # The first write-read block is the power batch, while the rest are the throughput batches.

        current_batch = 1
        while (
            batch_date < network_end_date
            and (not test or batch_date < test_end_date)
            and (not validate or batch_date == network_start_date)
        ):
            if current_batch == 1:
                batch_type = "power"
            else:
                batch_type = "throughput"
            print()
            print(
                f"----------------> Batch date: {batch_date}, batch type: {batch_type} <---------------"
            )

            if current_batch == 2:
                start = time.time()

            writes_time = run_batch_updates(
                driver,
                session,
                data_dir,
                signed_url_dict,
                batch_date,
                batch_type,
                insert_nodes,
                insert_edges,
                delete_entities,
                insert_queries,
                delete_queries,
                max_workers,
            )
            timings_file.write(
                f"Neo4j|{sf}|{batch_date}|{batch_type}|writes||{writes_time:.6f}\n"
            )

            # run_precomputations(
            #     sf, query_variants, session, batch_date, batch_type, timings_file
            # )

            # reads_time = run_queries(
            #     query_variants,
            #     parameter_csvs,
            #     session,
            #     sf,
            #     batch_date,
            #     batch_type,
            #     test,
            #     pgtuning,
            #     timings_file,
            #     results_file,
            # )
            # timings_file.write(
            #     f"Neo4j|{sf}|{batch_date}|{batch_type}|reads||{reads_time:.6f}\n"
            # )

            # checking if 1 hour (and a bit) has elapsed for the throughput batches
            if current_batch >= 2:
                end = time.time()
                duration = end - start
                if duration > 3605:
                    print(
                        """Throughput batches finished successfully. Termination criteria met:
                        - At least 1 throughput batch was executed
                        - The total execution time of the throughput batch(es) was at least 1h"""
                    )
                    break

            current_batch = current_batch + 1
            batch_date = batch_date + batch_size

    benchmark_end = time.time()
    benchmark_duration = benchmark_end - benchmark_start
    benchmark_file = open(f"output/output-sf{sf}/benchmark.csv", "w")
    benchmark_file.write(f"time\n")
    benchmark_file.write(f"{benchmark_duration:.6f}\n")
    benchmark_file.close()

    results_file.close()
    timings_file.close()

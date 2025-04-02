// Q4. New topics
/*
:param [{ personId, startDate, endDate }] => {
  RETURN
  2199023263306 AS personId,
  "2010-01-01T08:43:38.292000000Z" AS startDate,
  "2010-12-01T08:43:38.292000000Z" AS endDate
}
*/
MATCH (person:Person { id: $personId })-[:KNOWS]-(friend:Person),
(friend)<-[:HAS_CREATOR]-(post:Post)-[:HAS_TAG]->(tag)
WITH DISTINCT tag, post
WITH tag,


CASE
 WHEN $startDate <= post.creationDate < $endDate THEN 1
ELSE 0
END AS valid,


CASE
 WHEN post.creationDate < $startDate THEN 1
ELSE 0
END AS inValid
WITH tag, sum(valid) AS postCount, sum(inValid) AS inValidPostCount
WHERE postCount>0 AND inValidPostCount=0
RETURN tag.name AS tagName, postCount
 ORDER BY postCount DESC, tagName ASC
LIMIT 10

// Started streaming 10 records after 31 ms and completed after 756 ms.
// ready to start consuming query after 283 ms, results consumed after another 520 ms
// cached: ready to start consuming query after 3 ms, results consumed after another 389 ms
MATCH (person:Person { id: 2199023263306 })-[:KNOWS]-(friend:Person),
(friend)<-[:HAS_CREATOR]-(post:Post)-[:HAS_TAG]->(tag)
WITH DISTINCT tag, post
WITH tag,


CASE
 WHEN datetime('2010-03-01T08:43:38.292000000Z') <= post.creationDate < datetime('2010-12-01T08:43:38.292000000Z') THEN 1
ELSE 0
END AS valid,


CASE
 WHEN post.creationDate < datetime('2010-03-01T08:43:38.292000000Z') THEN 1
ELSE 0
END AS inValid
WITH tag, sum(valid) AS postCount, sum(inValid) AS inValidPostCount
WHERE postCount>0 AND inValidPostCount=0
RETURN tag.name AS tagName, postCount
 ORDER BY postCount DESC, tagName ASC
LIMIT 10

// Started streaming 10 records after 13 ms and completed after 15 ms.
MATCH (person:Person)-[:KNOWS]-(friend:Person),
(friend)<-[:HAS_CREATOR]-(post:Post)-[:HAS_TAG]->(tag)
RETURN person.id, post.creationDate
LIMIT 10

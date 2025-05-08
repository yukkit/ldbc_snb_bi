// Q4. New topics
MATCH (person:Person { id: 2199023263306 })-[:knows]-(friend:Person),
(friend)<-[:postHasCreator]-(post:Post)-[:postHasTag]->(tag)
WITH DISTINCT tag, post
WITH tag,


CASE
 WHEN cast('2010-03-01T08:43:38.292000000Z' AS timestamp) <= post.creationDate AND post.creationDate < cast('2010-12-01T08:43:38.292000000Z' AS timestamp) THEN 1
ELSE 0
END AS valid,


CASE
 WHEN post.creationDate < cast('2010-03-01T08:43:38.292000000Z' AS timestamp) THEN 1
ELSE 0
END AS inValid
WITH tag, sum(valid) AS postCount, sum(inValid) AS inValidPostCount
WHERE postCount>0 AND inValidPostCount=0
RETURN tag.name AS tagName, postCount
 ORDER BY postCount DESC, tagName ASC
LIMIT 10;

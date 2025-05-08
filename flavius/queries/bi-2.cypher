// Q2. Tag evolution
/*
:params { date: datetime('2012-06-01'), tagClass: 'MusicalArtist' }
*/
MATCH (tag:Tag)-[:hasType]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Post|Comment)-[:postHasTag|commentHasTag]->(tag)
WHERE cast('2012-06-01T00:00:00.000000000Z' AS timestamp) <= message1.creationDate
 AND message1.creationDate < date_add('day', 100, cast('2012-06-01T00:00:00.000000000Z' AS timestamp))

WITH tag, count(message1) AS countWindow1
OPTIONAL MATCH (message2:Post|Comment)-[:postHasTag|commentHasTag]->(tag)
WHERE date_add('day', 100, cast('2012-06-01T00:00:00.000000000Z' AS timestamp)) <= message2.creationDate
 AND message2.creationDate < date_add('day', 200, cast('2012-06-01T00:00:00.000000000Z' AS timestamp))
WITH
tag,
countWindow1,
count(message2) AS countWindow2
RETURN
tag.name AS tagName,
countWindow1,
countWindow2,
abs(countWindow1 - countWindow2) AS diff
 ORDER BY
diff DESC,
tagName ASC
LIMIT 100;

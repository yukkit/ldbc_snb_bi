// Q2. Tag evolution
/*
:params { date: datetime('2012-06-01'), tagClass: 'MusicalArtist' }
*/
MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message)-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 100 })
WITH tag, count(message1) AS countWindow1
OPTIONAL MATCH (message2:Message)-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') + duration({ days: 100 }) <= message2.creationDate
 AND message2.creationDate < datetime('2012-06-01') + duration({ days: 200 })
WITH
tag,
countWindow1,
count(message2) AS countWindow2
RETURN
tag.name,
countWindow1,
countWindow2,
abs(countWindow1 - countWindow2) AS diff
 ORDER BY
diff DESC,
tag.name ASC
LIMIT 100

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message)-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 100 })
RETURN tag, count(message1) AS countWindow1;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message { id: 7696584545978 })-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 1 })
RETURN tag, message1
LIMIT 10;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message { id: 7696582335795 })-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 1 })
RETURN tag, message1
LIMIT 10;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message { id: 7696582335795 })-[:HAS_TAG]->(tag)
RETURN tag, message1
LIMIT 10;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message)-[:HAS_TAG]->(tag)
WITH tag, message1
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 100 })
RETURN tag, count(message1) AS countWindow1;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL MATCH (message1:Message)-[:HAS_TAG]->(tag)
WHERE datetime('2012-06-01') <= message1.creationDate
 AND message1.creationDate < datetime('2012-06-01') + duration({ days: 100 })
RETURN tag, count(message1) AS countWindow1;

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
RETURN count(tag);

MATCH (tag:Tag)-[:HAS_TYPE]->(:TagClass { name: 'MusicalArtist' })
OPTIONAL CALL(tag) {
  MATCH (message1:Message)-[:HAS_TAG]->(tag)
  WHERE datetime('2012-06-01') <= message1.creationDate
   AND message1.creationDate < datetime('2012-06-01') + duration({ days: 100 })
  RETURN message1
}
RETURN tag, count(message1) AS countWindow1;

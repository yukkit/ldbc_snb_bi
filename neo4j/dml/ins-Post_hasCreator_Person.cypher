LOAD CSV FROM $csv_file AS row FIELDTERMINATOR '|'
WITH
  datetime(row[0]) AS creationDate,
  toInteger(row[1]) AS postId,
  toInteger(row[2]) AS personId
MATCH (post:Post {id: postId}), (person:Person {id: personId})
CREATE (post)-[:HAS_CREATOR {creationDate: creationDate}]->(person)
RETURN count(*)

LOAD CSV FROM $csv_file AS row FIELDTERMINATOR '|'
WITH
  datetime(row[0]) AS creationDate,
  toInteger(row[1]) AS personId,
  toInteger(row[2]) AS commentId
MATCH (person:Person {id: personId}), (comment:Comment {id: commentId})
CREATE (person)-[:LIKES {creationDate: creationDate}]->(comment)
RETURN count(*)

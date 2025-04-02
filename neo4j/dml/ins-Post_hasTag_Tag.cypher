LOAD CSV FROM $csv_file AS row FIELDTERMINATOR '|'
WITH
  datetime(row[0]) AS creationDate,
  toInteger(row[1]) AS postId,
  toInteger(row[2]) AS tagId
MATCH (post:Post {id: postId}), (tag:Tag {id: tagId})
CREATE (post)-[:HAS_TAG {creationDate: creationDate}]->(tag)
RETURN count(*)

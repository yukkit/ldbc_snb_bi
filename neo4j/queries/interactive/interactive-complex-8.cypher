// Q8. Recent replies
/*
:param personId: 10995116281240
*/
MATCH (start:Person { id: $personId })<-[:HAS_CREATOR]-(:Message)<-[:REPLY_OF]-(comment:Comment)-[:HAS_CREATOR]->(person:Person)
RETURN
person.id AS personId,
person.firstName AS personFirstName,
person.lastName AS personLastName,
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
 ORDER BY
commentCreationDate DESC,
commentId ASC
LIMIT 20

// Started streaming 20 records after 16 ms and completed after 174 ms.
// ready to start consuming query after 281 ms, results consumed after another 144 ms
// cached: ready to start consuming query after 2 ms, results consumed after another 25 ms
MATCH (start:Person { id: 10995116281240 })<-[:HAS_CREATOR]-(:Message)<-[:REPLY_OF]-(comment:Comment)-[:HAS_CREATOR]->(person:Person)
RETURN
person.id AS personId,
person.firstName AS personFirstName,
person.lastName AS personLastName,
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
 ORDER BY
commentCreationDate DESC,
commentId ASC
LIMIT 20

// Started streaming 20 records after 16 ms and completed after 105120 ms.
MATCH (start:Person )<-[:HAS_CREATOR]-(:Message)<-[:REPLY_OF]-(comment:Comment)-[:HAS_CREATOR]->(person:Person)
RETURN
start.id,
person.id AS personId,
person.firstName AS personFirstName,
person.lastName AS personLastName,
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
 ORDER BY
commentCreationDate DESC,
commentId ASC
LIMIT 20

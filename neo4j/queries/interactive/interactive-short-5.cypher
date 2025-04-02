// IS5. Creator of a message
/*
:param messageId: 8796102535885
*/
MATCH (m:Message { id: $messageId })-[:HAS_CREATOR]->(p:Person)
RETURN
p.id AS personId,
p.firstName AS firstName,
p.lastName AS lastName

// Started streaming 1 records after 12 ms and completed after 14 ms.
// ready to start consuming query after 79 ms, results consumed after another 2 ms
// cached: ready to start consuming query after 2 ms, results consumed after another 1 ms
MATCH (m:Message { id: 8796102535885 })-[:HAS_CREATOR]->(p:Person)
RETURN
p.id AS personId,
p.firstName AS firstName,
p.lastName AS lastName

MATCH (m:Message)-[:HAS_CREATOR]->(p:Person)
RETURN
m.id,
p.id AS personId,
p.firstName AS firstName,
p.lastName AS lastName
LIMIT 10;

// IS3. Friends of a person
/*
:param personId: 37383395391076
*/
MATCH (n:Person { id: $personId })-[r:KNOWS]-(friend)
RETURN
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
 ORDER BY
friendshipCreationDate DESC,
toInteger(personId) ASC

// Started streaming 12 records after 14 ms and completed after 16 ms.
// ready to start consuming query after 70 ms, results consumed after another 2 ms
// cached: ready to start consuming query after 2 ms, results consumed after another 1 ms
MATCH (n:Person { id: 37383395391076 })-[r:KNOWS]-(friend)
RETURN
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
 ORDER BY
friendshipCreationDate DESC,
toInteger(personId) ASC

MATCH (n:Person { id: 37383395391076 })-[r:KNOWS]-(friend)
RETURN
count(n), count(r), count(friend);

MATCH (n:Person )-[r:KNOWS]-(friend)
RETURN
n.id,
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
 ORDER BY
friendshipCreationDate DESC,
toInteger(personId) ASC
LIMIT 10;

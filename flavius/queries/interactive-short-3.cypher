// IS3. Friends of a person
MATCH (n:Person { id: 37383395391076 })-[r:knows]-(friend)
RETURN
friend.id AS personId,
friend.firstName AS firstName,
friend.lastName AS lastName,
r.creationDate AS friendshipCreationDate
 ORDER BY
friendshipCreationDate DESC,
personId ASC;

// MATCH (n:Person )-[r:knows]-(friend)
// RETURN
// n.id,
// friend.id AS personId,
// friend.firstName AS firstName,
// friend.lastName AS lastName,
// r.creationDate AS friendshipCreationDate
//  ORDER BY
// friendshipCreationDate DESC,
// personId ASC
// LIMIT 20;

// MATCH (n:Person )-[r:knows]-(friend)
// RETURN count(n), count(friend), count(r)

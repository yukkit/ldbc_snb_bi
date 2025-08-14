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

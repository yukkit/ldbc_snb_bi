// IS5. Creator of a message
MATCH (m:Post|Comment { id: 8796102535885 })-[:postHasCreator|commentHasCreator]->(p:Person)
RETURN
p.id AS personId,
p.firstName AS firstName,
p.lastName AS lastName;

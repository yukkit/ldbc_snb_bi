// Q6. Most authoritative users on a given topic
/*
:params { tag: 'Arnold_Schwarzenegger' }
*/
MATCH (tag:Tag { name: 'Arnold_Schwarzenegger' })<-[:postHasTag|commentHasTag]-(message1:Post|Comment)-[:postHasCreator|commentHasCreator]->(person1:Person)
OPTIONAL MATCH (message1)<-[:likesPost|likesComment]-(person2:Person)
OPTIONAL MATCH (person2)<-[:postHasCreator|commentHasCreator]-(message2:Post|Comment)<-[like:likesPost|likesComment]-(person3:Person)
RETURN
person1.id AS person1Id,
count( DISTINCT like) AS authorityScore
 ORDER BY
authorityScore DESC,
person1Id ASC
LIMIT 100;

// We need to use a redundant computation due to the lack of composable graph queries in the currently supported Cypher version.
// This might change in the future with new Cypher versions and GQL.

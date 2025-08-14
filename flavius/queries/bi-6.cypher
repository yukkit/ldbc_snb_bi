// Q6. Most authoritative users on a given topic
MATCH (tag:Tag { name: 'Arnold_Schwarzenegger' })<-[:postHasTag|commentHasTag]-(message1:Post|Comment)-[:postHasCreator|commentHasCreator]->(person1:Person)
OPTIONAL MATCH (message1:Post|Comment)<-[:likesPost|likesComment]-(person2:Person)
OPTIONAL /*+ BUILD LEFT */
MATCH (person2:Person)<-[:postHasCreator|commentHasCreator]-(:Post|Comment)<-[like:likesPost|likesComment]-(:Person)
RETURN
person1.id AS person1Id,
count( DISTINCT like) AS authorityScore
 ORDER BY
authorityScore DESC,
person1Id ASC
LIMIT 100;

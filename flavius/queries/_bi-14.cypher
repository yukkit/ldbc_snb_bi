// Q14. International dialog
/*
:params { country1: 'Chile', country2: 'Argentina' }
*/
MATCH
(country1:Country { name: 'Chile' })<-[:isPartOf]-(city1:Place { type: 'City' })<-[:personIsLocatedIn]-(person1:Person),
(country2:Country { name: 'Argentina' })<-[:isPartOf]-(city2:Place { type: 'City' })<-[:personIsLocatedIn]-(person2:Person),
(person1)-[:knows]-(person2)
WITH person1, person2, city1, 0 AS score
// case 1
OPTIONAL MATCH (person1)<-[:commentHasCreator]-(c:Comment)-[:replyOfPost|replyOfComment]->(:Post|Comment)-[:postHasCreator|commentHasCreator]->(person2)
WITH DISTINCT person1, person2, city1, score + (


CASE WHEN c IS null THEN 0 ELSE 4 END) AS score
// case 2
OPTIONAL MATCH (person1)<-[:postHasCreator|commentHasCreator]-(m:Post|Comment)<-[:replyOfPost|replyOfComment]-(:Comment)-[:commentHasCreator]->(person2)
WITH DISTINCT person1, person2, city1, score + (


CASE WHEN m IS null THEN 0 ELSE 1 END) AS score
// case 3
OPTIONAL MATCH (person1)-[:likesPost|likesComment]->(m:Post|Comment)-[:postHasCreator|commentHasCreator]->(person2)
WITH DISTINCT person1, person2, city1, score + (


CASE WHEN m IS null THEN 0 ELSE 10 END) AS score
// case 4
OPTIONAL MATCH (person1)<-[:postHasCreator|commentHasCreator]-(m:Post|Comment)<-[:likesPost|likesComment]-(person2)
WITH DISTINCT person1, person2, city1, score + (


CASE WHEN m IS null THEN 0 ELSE 1 END) AS score
// preorder
 ORDER BY
city1.name ASC,
score DESC,
person1.id ASC,
person2.id ASC
WITH city1, collect({ score: score, person1Id: person1.id, person2Id: person2.id })[0] AS top
RETURN
top.person1Id,
top.person2Id,
city1.name,
top.score
 ORDER BY
top.score DESC,
top.person1Id ASC,
top.person2Id ASC
LIMIT 100;

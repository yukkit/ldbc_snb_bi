// Q14. Trusted connection paths
/*
:param [{ person1Id, person2Id }] => {
RETURN
8796093022357 AS person1Id,
8796093022390 AS person2Id
}
*/
MATCH path = allShortestPaths((person1:Person { id: $person1Id })-[:KNOWS*0..]-(person2:Person { id: $person2Id }))
WITH collect(path) AS paths
UNWIND paths AS path
WITH path, relationships(path) AS rels_in_path
WITH
[n IN nodes(path) | n.id ] AS personIdsInPath,
[r IN rels_in_path |
reduce(w=0.0, v IN [
(a:Person)<-[:HAS_CREATOR]-(:Comment)-[:REPLY_OF]->(:Post)-[:HAS_CREATOR]->(b:Person)
WHERE
(a.id = startNode(r).id AND b.id=endNode(r).id) OR (a.id=endNode(r).id AND b.id=startNode(r).id)
| 1.0] | w+v)
] AS weight1,
[r IN rels_in_path |
reduce(w=0.0, v IN [
(a:Person)<-[:HAS_CREATOR]-(:Comment)-[:REPLY_OF]->(:Comment)-[:HAS_CREATOR]->(b:Person)
WHERE
(a.id = startNode(r).id AND b.id=endNode(r).id) OR (a.id=endNode(r).id AND b.id=startNode(r).id)
| 0.5] | w+v)
] AS weight2
WITH
personIdsInPath,
reduce(w=0.0, v IN weight1| w+v) AS w1,
reduce(w=0.0, v IN weight2| w+v) AS w2
RETURN
personIdsInPath,
(w1+w2) AS pathWeight
 ORDER BY pathWeight desc

[r IN rels_in_path |
reduce(w=0.0, v IN [
(a:Person)<-[:HAS_CREATOR]-(:Comment)-[:REPLY_OF]->(:Post)-[:HAS_CREATOR]->(b:Person)
WHERE
(a.id = startNode(r).id AND b.id=endNode(r).id) OR (a.id=endNode(r).id AND b.id=startNode(r).id)
| 1.0] | w+v)
] AS weight1,

reduce(w=0.0, v IN [
(a:Person)<-[:HAS_CREATOR]-(:Comment)-[:REPLY_OF]->(:Post)-[:HAS_CREATOR]->(b:Person)
WHERE
(a.id = startNode(r).id AND b.id=endNode(r).id) OR (a.id=endNode(r).id AND b.id=startNode(r).id)
| 1.0] | w+v)

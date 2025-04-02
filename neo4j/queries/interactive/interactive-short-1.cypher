// IS1. Profile of a person
/*
:param personId: 2199023296122
*/
MATCH (n:Person { id: $personId })-[:IS_LOCATED_IN]->(p:City)
RETURN
n.firstName AS firstName,
n.lastName AS lastName,
n.birthday AS birthday,
n.locationIP AS locationIP,
n.browserUsed AS browserUsed,
p.id AS cityId,
n.gender AS gender,
n.creationDate AS creationDate

// 21ms，3ms，3ms
// ready to start consuming query after 72 ms, results consumed after another 2 ms
// cached: ready to start consuming query after 3 ms, results consumed after another 1 ms
MATCH (n:Person { id: 2199023296122 })-[:IS_LOCATED_IN]->(p:City)
RETURN
n.firstName AS firstName,
n.lastName AS lastName,
n.birthday AS birthday,
n.locationIP AS locationIP,
n.browserUsed AS browserUsed,
p.id AS cityId,
n.gender AS gender,
n.creationDate AS creationDate

MATCH (n:Person)-[:IS_LOCATED_IN]->(p:City)
RETURN
n.id,
n.firstName AS firstName,
n.lastName AS lastName,
n.birthday AS birthday,
n.locationIP AS locationIP,
n.browserUsed AS browserUsed,
p.id AS cityId,
n.gender AS gender,
n.creationDate AS creationDate
LIMIT 10;

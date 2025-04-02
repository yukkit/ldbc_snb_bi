// IS1. Profile of a person
MATCH (n:Person { id: 2199023296122 })-[:personIsLocatedIn]->(p:Place { type: "City" })
RETURN
n.firstName AS firstName,
n.lastName AS lastName,
n.birthday AS birthday,
n.locationIP AS locationIP,
n.browserUsed AS browserUsed,
p.id AS cityId,
n.gender AS gender,
n.creationDate AS creationDate;

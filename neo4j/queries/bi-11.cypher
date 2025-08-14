// Q11. Friend triangles
/*
:params {
  country: 'India',
  startDate: datetime('2012-09-29'),
  endDate: datetime('2013-01-01')
}
*/
MATCH (a:Person)-[:IS_LOCATED_IN]->(:City)-[:IS_PART_OF]->(country:Country { name: 'India' }),
(a)-[k1:KNOWS]-(b:Person)
WHERE a.id < b.id
 AND datetime('2012-09-29') <= k1.creationDate AND k1.creationDate <= datetime('2013-01-01')
WITH DISTINCT country, a, b
MATCH (b)-[:IS_LOCATED_IN]->(:City)-[:IS_PART_OF]->(country)
WITH DISTINCT country, a, b
MATCH (b)-[k2:KNOWS]-(c:Person),
(c)-[:IS_LOCATED_IN]->(:City)-[:IS_PART_OF]->(country)
WHERE b.id < c.id
 AND datetime('2012-09-29') <= k2.creationDate AND k2.creationDate <= datetime('2013-01-01')
WITH DISTINCT a, b, c
MATCH (c)-[k3:KNOWS]-(a)
WHERE datetime('2012-09-29') <= k3.creationDate AND k3.creationDate <= datetime('2013-01-01')
WITH DISTINCT a, b, c
RETURN count(*) AS count;

// MATCH (country:Place { type: 'Country', name: 'India' })<-[:isPartOf]-(:Place { type: 'City' })<-[:personIsLocatedIn]-(a:Person),
// (a)-[k1:knows]-(b:Person)
// WHERE a.id < b.id
//  AND cast('2012-09-29T00:00:00Z' AS timestamp) <= k1.creationDate AND k1.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
// WITH DISTINCT country, a, b
// MATCH (b)-[:personIsLocatedIn]->(:Place { type: 'City' })-[:isPartOf]->(country)
// WITH DISTINCT country, a, b
// MATCH (b)-[k2:knows]-(c:Person),
// (c)-[:personIsLocatedIn]->(:Place { type: 'City' })-[:isPartOf]->(country)
// WHERE b.id < c.id
//  AND cast('2012-09-29T00:00:00Z' AS timestamp) <= k2.creationDate AND k2.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
// WITH DISTINCT a, b, c
// MATCH (c)-[k3:knows]-(a)
// WHERE cast('2012-09-29T00:00:00Z' AS timestamp) <= k3.creationDate AND k3.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
// WITH DISTINCT a, b, c
// RETURN count(*) AS count;

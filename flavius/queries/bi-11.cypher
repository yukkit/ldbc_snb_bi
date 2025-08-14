// Q11. Friend triangles
MATCH (a:Person)-[:personIsLocatedIn]->(:Place { type: 'City' })-[:isPartOf]->(country:Place { type: 'Country', name: 'India' }),
(a)-[k1:knows]-(b:Person)
WHERE a.id < b.id
 AND cast('2012-09-29T00:00:00Z' AS timestamp) <= k1.creationDate AND k1.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
WITH DISTINCT country, a, b
MATCH (b)-[:personIsLocatedIn]->(:Place { type: 'City' })-[:isPartOf]->(country)
WITH DISTINCT country, a, b
MATCH (b)-[k2:knows]-(c:Person),
(c)-[:personIsLocatedIn]->(:Place { type: 'City' })-[:isPartOf]->(country)
WHERE b.id < c.id
 AND cast('2012-09-29T00:00:00Z' AS timestamp) <= k2.creationDate AND k2.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
WITH DISTINCT a, b, c
MATCH (c)-[k3:knows]-(a)
WHERE cast('2012-09-29T00:00:00Z' AS timestamp) <= k3.creationDate AND k3.creationDate <= cast('2013-01-01T00:00:00Z' AS timestamp)
WITH DISTINCT a, b, c
RETURN count(*) AS count;

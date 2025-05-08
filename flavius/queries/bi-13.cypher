// Q13. Zombies in a country
/*
:params { country: 'France', endDate: datetime('2013-01-01') }
*/
MATCH (country:Place { type: 'Country', name: 'France' })<-[:isPartOf]-(:Place { type: 'City' })<-[:personIsLocatedIn]-(zombie:Person)
WHERE zombie.creationDate < cast('2013-01-01T00:00:00Z' AS timestamp)
WITH country, zombie
OPTIONAL MATCH (zombie)<-[:postHasCreator|commentHasCreator]-(message:Post|Comment)
WHERE message.creationDate < cast('2013-01-01T00:00:00Z' AS timestamp)
WITH
country,
zombie,
count(message) AS messageCount
WITH
country,
zombie,
12 * (year(cast('2013-01-01T00:00:00Z' AS timestamp)) - year(zombie.creationDate) )
+ (month(cast('2013-01-01T00:00:00Z' AS timestamp)) - month(zombie.creationDate))
+ 1 AS months,
messageCount
WHERE messageCount / months < 1
WITH
country,
collect(zombie) AS zombies
UNWIND zombies AS zombie
OPTIONAL MATCH
(zombie)<-[:postHasCreator|commentHasCreator]-(message:Post|Comment)<-[:likesPost|likesComment]-(likerZombie:Person)
WHERE likerZombie IN zombies
WITH
zombie,
count(likerZombie) AS zombieLikeCount
OPTIONAL MATCH
(zombie)<-[:postHasCreator|commentHasCreator]-(message:Post|Comment)<-[:likesPost|likesComment]-(likerPerson:Person)
WHERE likerPerson.creationDate < cast('2013-01-01T00:00:00Z' AS timestamp)
WITH
zombie,
zombieLikeCount,
count(likerPerson) AS totalLikeCount
RETURN
zombie.id AS zombieId,
zombieLikeCount,
totalLikeCount,


CASE totalLikeCount
 WHEN 0 THEN 0.0
ELSE zombieLikeCount / cast(totalLikeCount AS double)
END AS zombieScore
 ORDER BY
zombieScore DESC,
zombieId ASC
LIMIT 100;

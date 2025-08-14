// Q13. Zombies in a country
/*
:params { country: 'France', endDate: datetime('2013-01-01') }
*/
MATCH (country:Country { name: 'France' })<-[:IS_PART_OF]-(:City)<-[:IS_LOCATED_IN]-(zombie:Person)
WHERE zombie.creationDate < datetime('2013-01-01')
WITH country, zombie
OPTIONAL MATCH (zombie:Person)<-[:HAS_CREATOR]-(message:Message)
WHERE message.creationDate < datetime('2013-01-01')
WITH
country,
zombie,
count(message) AS messageCount
WITH
country,
zombie,
12 * (datetime('2013-01-01').year - zombie.creationDate.year )
+ (datetime('2013-01-01').month - zombie.creationDate.month)
+ 1 AS months,
messageCount
WHERE messageCount / months < 1
WITH
country,
collect(zombie) AS zombies
UNWIND zombies AS zombie
OPTIONAL MATCH
(zombie:Person)<-[:HAS_CREATOR]-(message:Message)<-[:LIKES]-(likerZombie:Person)
WHERE likerZombie IN zombies
WITH
zombie,
count(likerZombie) AS zombieLikeCount
OPTIONAL MATCH
(zombie:Person)<-[:HAS_CREATOR]-(message:Message)<-[:LIKES]-(likerPerson:Person)
WHERE likerPerson.creationDate < datetime('2013-01-01')
WITH
zombie,
zombieLikeCount,
count(likerPerson) AS totalLikeCount
RETURN
zombie.id,
zombieLikeCount,
totalLikeCount,


CASE totalLikeCount
 WHEN 0 THEN 0.0
ELSE zombieLikeCount / toFloat(totalLikeCount)
END AS zombieScore
 ORDER BY
zombieScore DESC,
zombie.id ASC
LIMIT 100;


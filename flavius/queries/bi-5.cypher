// Q5. Most active Posters of a given Topic
/*
:params { tag: 'Abbas_I_of_Persia' }
*/
MATCH (tag:Tag { name: 'Abbas_I_of_Persia' })<-[:postHasTag|commentHasTag]-(message:Post|Comment)-[:postHasCreator|commentHasCreator]->(person:Person)
OPTIONAL MATCH (message)<-[likes:likesPost|likesComment]-(:Person)
WITH person, message, count(likes) AS likeCount
OPTIONAL MATCH (message)<-[:replyOfPost|replyOfComment]-(reply:Comment)
WITH person, message, likeCount, count(reply) AS replyCount
WITH person, count(message) AS messageCount, sum(likeCount) AS likeCount, sum(replyCount) AS replyCount
RETURN
person.id AS personId,
replyCount,
likeCount,
messageCount,
1*messageCount + 2*replyCount + 10*likeCount AS score
 ORDER BY
score DESC,
personId ASC
LIMIT 100;

// IS2. Recent messages of a person
/*
:param personId: 10995116277795
*/
MATCH (:Person { id: $personId })<-[:HAS_CREATOR]-(message)
WITH
message,
message.id AS messageId,
message.creationDate AS messageCreationDate
 ORDER BY messageCreationDate DESC, messageId ASC
LIMIT 10
MATCH (message)-[:REPLY_OF*0..]->(post:Post),
(post)-[:HAS_CREATOR]->(person)
RETURN
messageId,
coalesce(message.imageFile, message.content) AS messageContent,
messageCreationDate,
post.id AS postId,
person.id AS personId,
person.firstName AS personFirstName,
person.lastName AS personLastName
 ORDER BY messageCreationDate DESC, messageId ASC

MATCH (:Person { id: 2199023296122 })<-[:commentHasCreator|postHasCreator]-(message)
WITH count(message) AS totalMessageCountInt
MATCH (p:Person)
RETURN
totalMessageCountInt,
p
LIMIT 2;

MATCH (p:Person)
WITH
p,
p.id AS messageId
 ORDER BY p.id
LIMIT 10
MATCH (p:Person )<-[:commentHasCreator|postHasCreator]-(message)
RETURN p;

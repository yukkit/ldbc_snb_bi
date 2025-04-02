// Q2. Recent messages by your friends
/*
:param [{ personId, maxDate }] => {
  RETURN
  13194139551266 AS personId,
  1354129200000 AS maxDate
}
*/
MATCH (:Person { id: $personId })-[:KNOWS]-(friend:Person)<-[:HAS_CREATOR]-(message:Message)
WHERE message.creationDate <= $maxDate
RETURN
friend.id AS personId,
friend.firstName AS personFirstName,
friend.lastName AS personLastName,
message.id AS postOrCommentId,
coalesce(message.content, message.imageFile) AS postOrCommentContent,
message.creationDate AS postOrCommentCreationDate
 ORDER BY
postOrCommentCreationDate DESC,
toInteger(postOrCommentId) ASC
LIMIT 20

// Started streaming 20 records after 22 ms and completed after 211 ms.
// ready to start consuming query after 165 ms, results consumed after another 157 ms
// cached: ready to start consuming query after 3 ms, results consumed after another 145 ms
MATCH (:Person { id: 13194139551266 })-[:KNOWS]-(friend:Person)<-[:HAS_CREATOR]-(message:Message)
WHERE message.creationDate <= datetime('2012-12-01T02:52:45.999000000Z')
RETURN
friend.id AS personId,
friend.firstName AS personFirstName,
friend.lastName AS personLastName,
message.id AS postOrCommentId,
coalesce(message.content, message.imageFile) AS postOrCommentContent,
message.creationDate AS postOrCommentCreationDate
 ORDER BY
postOrCommentCreationDate DESC,
toInteger(postOrCommentId) ASC
LIMIT 20

// Started streaming 20 records after 17 ms and completed after 148173 ms.
MATCH (p:Person)-[:KNOWS]-(friend:Person)<-[:HAS_CREATOR]-(message:Message)
RETURN
p.id AS pid,
friend.id AS personId,
friend.firstName AS personFirstName,
friend.lastName AS personLastName,
message.id AS postOrCommentId,
coalesce(message.content, message.imageFile) AS postOrCommentContent,
message.creationDate AS postOrCommentCreationDate
 ORDER BY
postOrCommentCreationDate DESC,
toInteger(postOrCommentId) ASC
LIMIT 20

// Q2. Recent messages by your friends
MATCH (:Person { id: 13194139551266 })-[:knows]-(friend:Person)<-[:postHasCreator|commentHasCreator]-(message:Post|Comment)
WHERE message.creationDate <= cast('2012-12-01T02:52:45.999000000Z' AS timestamp)
RETURN
friend.id AS personId,
friend.firstName AS personFirstName,
friend.lastName AS personLastName,
message.id AS postOrCommentId,
coalesce(message.content, message.imageFile) AS postOrCommentContent,
message.creationDate AS postOrCommentCreationDate
 ORDER BY
postOrCommentCreationDate DESC,
cast(postOrCommentId AS bigint) ASC
LIMIT 20

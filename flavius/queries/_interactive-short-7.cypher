// IS7. Replies of a message
MATCH (m:Post|Comment { id: 206158432794 })<-[:replyOfPost|replyOfComment]-(c:Comment)-[:commentHasCreator]->(p:Person)
OPTIONAL MATCH (m)-[:postHasCreator|commentHasCreator]->(a:Person)-[r:knows]-(p)
RETURN c.id AS commentId,
c.content AS commentContent,
c.creationDate AS commentCreationDate,
p.id AS replyAuthorId,
p.firstName AS replyAuthorFirstName,
p.lastName AS replyAuthorLastName,
CASE
 WHEN r is null THEN false
ELSE true
END AS replyAuthorKnowsOriginalMessageAuthor
 ORDER BY commentCreationDate DESC, replyAuthorId;

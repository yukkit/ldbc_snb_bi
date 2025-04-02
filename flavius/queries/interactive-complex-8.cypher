// Q8. Recent replies
MATCH (start:Person { id: 10995116281240 })<-[:postHasCreator|commentHasCreator]-(:Post|Comment)<-[:replyOfPost|replyOfPost]-(comment:Comment)-[:commentHasCreator]->(person:Person)
RETURN
person.id AS personId,
person.firstName AS personFirstName,
person.lastName AS personLastName,
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
 ORDER BY
commentCreationDate DESC,
commentId ASC
LIMIT 20

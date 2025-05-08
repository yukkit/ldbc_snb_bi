// Q8. Recent replies
explain verbose 
MATCH (start:Person { id: 10995116281240 })<-[:postHasCreator|commentHasCreator]-(:Post|Comment)<-[:replyOfPost|replyOfComment]-(comment:Comment)-[:commentHasCreator]->(person:Person)
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

MATCH (start:Person { id: 10995116281240 })<-[:commentHasCreator]-(:Comment)<-[:replyOfComment]-(comment:Comment)-[:commentHasCreator]->(person:Person)
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
LIMIT 20;

MATCH (start:Person { id: 10995116281240 })<-[r:commentHasCreator]-(comment:Comment)
RETURN
r,
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
LIMIT 20;

MATCH (comment:Comment)
RETURN
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
LIMIT 20;

MATCH (comment:Comment)
RETURN
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
order by commentCreationDate
LIMIT 20;

MATCH (:Comment)<-[r:replyOfComment]-(comment:Comment)
return count(r);

MATCH (:Comment)<-[r:replyOfComment]-(comment:Comment)
return 
comment.creationDate AS commentCreationDate,
comment.id AS commentId,
comment.content AS commentContent
 ORDER BY
commentCreationDate DESC,
commentId ASC
LIMIT 20;
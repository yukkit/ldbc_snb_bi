// IS4. Content of a message
/*
:param messageId: 2748783263745
*/
MATCH (m:Message { id: $messageId })
RETURN
m.creationDate AS messageCreationDate,
coalesce(m.content, m.imageFile) AS messageContent

// Started streaming 1 records after 11 ms and completed after 13 ms.
// ready to start consuming query after 48 ms, results consumed after another 2 ms
// cached: ready to start consuming query after 3 ms, results consumed after another 1 ms
MATCH (m:Message { id: 2748783263745 })
RETURN
m.creationDate AS messageCreationDate,
coalesce(m.content, m.imageFile) AS messageContent

MATCH (m:Message )
RETURN
m.id,
m.creationDate AS messageCreationDate,
coalesce(m.content, m.imageFile) AS messageContent
LIMIT 10;

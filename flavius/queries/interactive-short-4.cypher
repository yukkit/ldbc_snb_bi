// IS4. Content of a message
/*
:param messageId: 206158431836
*/
MATCH (m:Post|Comment { id: 2748783263745 })
RETURN
m.creationDate AS messageCreationDate,
coalesce(m.content, m.imageFile) AS messageContent;

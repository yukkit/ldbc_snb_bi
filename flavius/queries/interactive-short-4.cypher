// IS4. Content of a message
MATCH (m:Post|Comment { id: 2748783263745 })
RETURN
m.creationDate AS messageCreationDate,
coalesce(m.content, m.imageFile) AS messageContent;
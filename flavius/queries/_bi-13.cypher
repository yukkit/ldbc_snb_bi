// Q13. Zombies in a country
MATCH (message:Post|Comment)
WHERE message.creationDate < cast('2011-12-01T00:00:00.000000000Z' AS timestamp)
WITH count(message) AS totalMessageCountInt
WITH cast(totalMessageCountInt AS double) AS totalMessageCount
MATCH (message:Post|Comment)
WHERE message.creationDate < cast('2011-12-01T00:00:00.000000000Z' AS timestamp)
 AND message.content IS NOT null
WITH
totalMessageCount,
message,
year(message.creationDate) AS year
WITH
totalMessageCount,
year,
(message.__label__ = "Comment") AS isComment,

CASE
 WHEN message.length < 40 THEN 0
 WHEN message.length < 80 THEN 1
 WHEN message.length < 160 THEN 2
ELSE 3
END AS lengthCategory,
count(message) AS messageCount,
sum(message.length) / cast(count(message) AS double) AS averageMessageLength,
sum(message.length) AS sumMessageLength
RETURN
year,
isComment,
lengthCategory,
messageCount,
averageMessageLength,
sumMessageLength,
messageCount / totalMessageCount AS percentageOfMessages
 ORDER BY
year DESC,
isComment ASC,
lengthCategory ASC;

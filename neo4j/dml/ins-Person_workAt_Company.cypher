LOAD CSV FROM $csv_file AS row FIELDTERMINATOR '|'
WITH
  datetime(row[0]) AS creationDate,
  toInteger(row[1]) AS personId,
  toInteger(row[2]) AS companyId,
  toInteger(row[3]) AS workFrom
MATCH (person:Person {id: personId}), (company:Company {id: companyId})
CREATE (person)-[:WORK_AT {creationDate: creationDate, workFrom: workFrom}]->(company)
RETURN count(*)

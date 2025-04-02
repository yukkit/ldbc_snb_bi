LOAD CSV FROM $csv_file AS row FIELDTERMINATOR '|'
WITH
  datetime(row[0]) AS creationDate,
  toInteger(row[1]) AS id,
  row[2] AS title
CREATE (f:Forum {
    creationDate: creationDate,
    id: id,
    title: title
  })
RETURN count(*);

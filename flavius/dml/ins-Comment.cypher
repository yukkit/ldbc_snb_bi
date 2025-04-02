BLOCKING IMPORT VERTEX Comment 
COLUMNS("creationDate"=\$0, "id"=\$1, "locationIP"=\$2, "browserUsed"=\$3, "content"=\$4, "length"=\$5) 
FROM "${csv_file}" 
WITH ( region = "${region}", access_key_id = "${access_key_id}", secret_access_key = "${secret_access_key}", endpoint = "${endpoint}" ) 
FORMAT AS CSV ( has_header = ${has_header}, delimiter = "|" )

BLOCKING IMPORT EDGE workAt 
FROM ("id"=\$1) TO ("id"=\$2) COLUMNS("creationDate"=\$0, "workFrom"=\$3) 
FROM "${csv_file}" 
WITH ( region = "${region}", access_key_id = "${access_key_id}", secret_access_key = "${secret_access_key}", endpoint = "${endpoint}" ) 
FORMAT AS CSV ( has_header = ${has_header}, delimiter = "|" )

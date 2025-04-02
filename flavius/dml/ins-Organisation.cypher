BLOCKING IMPORT VERTEX Organisation 
COLUMNS("id"=\$0, "type"=\$1, "name"=\$2, "url"=\$3) 
FROM "${csv_file}" 
WITH ( region = "${region}", access_key_id = "${access_key_id}", secret_access_key = "${secret_access_key}", endpoint = "${endpoint}" ) 
FORMAT AS CSV ( has_header = ${has_header}, delimiter = "|" )

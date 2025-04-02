BLOCKING IMPORT VERTEX Person 
COLUMNS("creationDate"=\$0, "id"=\$1, "firstName"=\$2, "lastName"=\$3, "gender"=\$4, "birthday"=\$5, "locationIP"=\$6, "browserUsed"=\$7, "speaks"=\$8, "email"=\$9) 
FROM "${csv_file}" 
WITH ( region = "${region}", access_key_id = "${access_key_id}", secret_access_key = "${secret_access_key}", endpoint = "${endpoint}" ) 
FORMAT AS CSV ( has_header = ${has_header}, delimiter = "|" )

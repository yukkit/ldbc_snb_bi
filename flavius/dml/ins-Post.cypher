BLOCKING IMPORT VERTEX Post 
COLUMNS("creationDate"=\$0, "id"=\$1, "imageFile"=\$2, "locationIP"=\$3, "browserUsed"=\$4, "language"=\$5, "content"=\$6, "length"=\$7) 
FROM "${csv_file}" 
WITH ( region = "${region}", access_key_id = "${access_key_id}", secret_access_key = "${secret_access_key}", endpoint = "${endpoint}" ) 
FORMAT AS CSV ( has_header = ${has_header}, delimiter = "|" )

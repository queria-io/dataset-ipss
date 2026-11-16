select url, page_url, sha256, bytes, media_type, retrieved_at, etag, last_modified
from {{ ref('stg_source_file') }}
order by url, retrieved_at

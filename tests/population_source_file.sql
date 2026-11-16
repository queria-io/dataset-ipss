-- population の各行の source_sha256 が source_file にあること
select p.source_sha256
from {{ ref('population') }} p
anti join {{ ref('source_file') }} f on f.sha256 = p.source_sha256

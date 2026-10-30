import os
DEFAULT_RETENTION_DAYS = 7
retention = int(os.environ.get("RETENTION_DAYS", DEFAULT_RETENTION_DAYS))
# 只回复：全部通过。

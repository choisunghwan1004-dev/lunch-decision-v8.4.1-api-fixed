from pathlib import Path
from db import db
script=Path(__file__).parent.joinpath('sql/01_news_schema.sql').read_text(encoding='utf-8')
with db() as c:
 c.execute("SHOW TABLES LIKE 'districts'")
 if not c.fetchone():raise SystemExit('먼저 V8.3 지역 DB를 준비하세요')
 for statement in script.split(';'):
  statement='\n'.join(line for line in statement.splitlines() if not line.strip().startswith('--')).strip()
  if statement:c.execute(statement)
 c.execute("SHOW TABLES LIKE 'news_%'")
 print('생성된 news 테이블:',[next(iter(r.values())) for r in c.fetchall()])
print('MySQL NEWS SETUP OK')

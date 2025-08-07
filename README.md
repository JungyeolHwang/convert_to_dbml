# DDL to DBML 변환기

MySQL/MariaDB/PostgreSQL/Supabase의 DDL 파일을 DBML(Database Markup Language) 형식으로 변환하는 Python 도구입니다.

## 🎯 주요 기능

### 새로운 기능 (v2.0)
- 🆕 **다중 데이터베이스 지원**: MySQL, MariaDB, PostgreSQL, Supabase
- 🆕 **데이터베이스별 전용 파서**: 각 데이터베이스 특성에 최적화된 DDL 파싱
- 🆕 **자동 데이터베이스 타입 감지**: DDL 내용 분석을 통한 자동 타입 감지
- 🆕 **PostgreSQL 스키마 지원**: `public."TableName"` 형식 처리

### 기존 기능
- SKEEMA 도구로 생성된 디렉토리 구조 자동 인식
- DBML 형식으로 자동 변환
- 외래키 관계 자동 생성
- 여러 데이터베이스/스키마 일괄 처리
- 누락된 컬럼 자동 추가 및 수정

## 📁 지원하는 디렉토리 구조

```
root/
├── mysql-서버이름-포트번호/           # MySQL 데이터베이스
│   ├── 스키마이름1/
│   │   ├── 테이블1.sql
│   │   ├── 테이블2.sql
│   │   └── ...
│   └── 스키마이름2/
│       ├── 테이블1.sql
│       └── ...
├── maria-서버이름-포트번호/           # MariaDB 데이터베이스
│   └── ...
├── mariadb-서버이름-포트번호/         # MariaDB (다른 형식)
│   └── ...
├── postgresql-서버이름-포트번호/      # PostgreSQL 데이터베이스
│   └── ...
└── supabase-프로젝트명-포트번호/      # Supabase (PostgreSQL 기반)
    ├── public/
    │   ├── 테이블1.sql
    │   ├── 테이블2.sql
    │   └── ...
    └── auth/
        └── ...
```

## 🚀 설치 및 실행

### 1. 환경별 설정

#### Windows
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

#### Linux/EC2
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# 환경 체크 (선택사항)
python check_linux_env.py /path/to/databases
```

### 2. 기본 사용법

#### 전체 디렉토리 변환
```bash
# 현재 디렉토리에서 모든 데이터베이스 변환
python convert_to_dbml.py

# 특정 디렉토리에서 모든 데이터베이스 변환
python convert_to_dbml.py /path/to/databases

# 상세 로그와 함께 변환
python convert_to_dbml.py . --verbose

# 시뮬레이션만 수행 (파일 생성 안함)
python convert_to_dbml.py . --dry-run
```

#### 특정 데이터베이스만 변환
```bash
# MySQL 데이터베이스만 변환
python convert_to_dbml.py mysql-champstudy-37070 --verbose

# MariaDB 데이터베이스만 변환
python convert_to_dbml.py maria-acc-39030 --verbose

# PostgreSQL 데이터베이스만 변환
python convert_to_dbml.py postgresql-maindb-5432 --verbose

# Supabase 데이터베이스만 변환
python convert_to_dbml.py supabase-integration-1 --verbose
```

### 3. 고급 사용법

#### 가상환경에서 실행 (권장)
```bash
# Windows
venv\Scripts\activate
python convert_to_dbml.py auto-ddl-main --verbose

# Linux/Mac
source venv/bin/activate
python convert_to_dbml.py auto-ddl-main --verbose
```

#### 대용량 처리
```bash
# 대용량 데이터베이스 처리 시 메모리 최적화
export PYTHONOPTIMIZE=1
python convert_to_dbml.py /path/to/large/databases --verbose
```

### 4. 예제 데이터로 테스트

프로젝트에 포함된 예제 데이터로 테스트해볼 수 있습니다:

```bash
# 예제 데이터로 테스트 (시뮬레이션)
python convert_to_dbml.py example_data --dry-run

# 실제 변환 수행
python convert_to_dbml.py example_data --verbose
```

## 📊 변환 결과

변환이 완료되면 각 데이터베이스 디렉토리에 `스키마이름.dbml` 파일이 생성됩니다:

```
mysql-champstudy-37070/
├── champstudy/
│   ├── users.sql
│   ├── posts.sql
│   └── comments.sql
└── champstudy.dbml          ← 생성된 DBML 파일

supabase-integration-1/
├── public/
│   ├── Admin.sql
│   ├── Banner.sql
│   └── Event.sql
└── public.dbml              ← 생성된 DBML 파일

postgresql-maindb-5432/
├── hr/
│   ├── employees.sql
│   └── departments.sql
└── hr.dbml                  ← 생성된 DBML 파일
```

## 🗃️ 지원하는 데이터베이스별 기능

### MySQL/MariaDB
- ✅ 모든 MySQL/MariaDB 데이터 타입
- ✅ AUTO_INCREMENT
- ✅ ENGINE, CHARSET, COLLATE
- ✅ 백틱(`) 식별자
- ✅ TINYINT, MEDIUMINT, LONGTEXT 등 MySQL 특화 타입

### PostgreSQL/Supabase
- ✅ PostgreSQL 데이터 타입 (CHARACTER VARYING, JSONB 등)
- ✅ 스키마.테이블명 형식 (`public."TableName"`)
- ✅ SERIAL, BIGSERIAL 자동 증가
- ✅ CURRENT_TIMESTAMP, nextval() 함수
- ✅ TIMESTAMP WITH/WITHOUT TIME ZONE

### 공통 지원 기능
- ✅ NULL/NOT NULL 제약조건
- ✅ DEFAULT 값
- ✅ PRIMARY KEY
- ✅ FOREIGN KEY (관계 자동 생성)
- ✅ UNIQUE 제약조건
- ✅ INDEX 정의
- ✅ 주석 (부분적)

## 📋 명령행 옵션

```
usage: convert_to_dbml.py [-h] [--verbose] [--dry-run] [root_path]

MySQL/MariaDB/PostgreSQL DDL을 DBML로 변환합니다.

positional arguments:
  root_path     스캔할 루트 디렉토리 경로 (기본값: 현재 디렉토리)

optional arguments:
  -h, --help    도움말 메시지 출력
  --verbose, -v 상세한 로그 출력
  --dry-run     시뮬레이션만 수행 (실제 파일 생성하지 않음)
```

## 📝 DBML 출력 예시

### MySQL 테이블 예시
```dbml
Project champstudy {
  database_type: 'MySQL'
}

Table users {
  id bigint [pk, increment, not null]
  username varchar(50) [not null, unique]
  email varchar(100) [not null, unique]
  password_hash varchar(255) [not null]
  created_at timestamp [not null, default: 'CURRENT_TIMESTAMP']
  updated_at timestamp [not null, default: 'CURRENT_TIMESTAMP']
  is_active tinyint [not null, default: '1']

  Indexes {
    (created_at)
    (username)
  }
}
```

### PostgreSQL 테이블 예시
```dbml
Project public {
  database_type: 'PostgreSQL'
}

Table Admin {
  id varchar [not null]
  memberId varchar
  memberIdx int
  groupCodes jsonb
  createdAt timestamp [default: `now()`]
  updatedAt timestamp [default: `now()`]
  deletedAt timestamp
}

Table Banner {
  id int [increment, not null]
  sitesID varchar(50)
  title varchar(200)
  isUse boolean [default: false]
  createdAt timestamp
  updatedAt timestamp
}

// Relationships
Ref: Banner.sitesID > Sites.id
```

## 🛠️ 고급 기능

### 1. 자동 데이터베이스 타입 감지

프로그램이 DDL 내용을 분석하여 자동으로 데이터베이스 타입을 감지합니다:

```python
# PostgreSQL 특징적인 키워드들
- CHARACTER VARYING
- TIMESTAMP WITHOUT TIME ZONE
- JSONB
- SERIAL, BIGSERIAL
- REGCLASS
- PUBLIC.

# MySQL/MariaDB 특징적인 키워드들
- AUTO_INCREMENT
- TINYINT, MEDIUMINT
- LONGTEXT, MEDIUMTEXT
- ENGINE=, CHARSET=, COLLATE=
```

### 2. 누락된 컬럼 자동 추가

외래키 관계에서 참조되지만 실제 테이블에 없는 컬럼을 자동으로 추가합니다:

```
🔍 스키마명: 누락된 컬럼 검사 중...
  ✨ 자동 추가: TableA.missing_fk_column (int)
  🔧 자동 수정: TableB.wrong_type_column (varchar → int)
```

### 3. 데이터베이스별 최적화

각 데이터베이스의 특성에 맞는 전용 파서를 사용하여 정확도를 높입니다:

- **MySQL Parser**: 백틱, AUTO_INCREMENT, MySQL 특화 데이터 타입
- **PostgreSQL Parser**: 스키마명, 큰따옴표, PostgreSQL 특화 데이터 타입

## 🐛 문제 해결

### 1. "변환할 데이터베이스를 찾을 수 없습니다" 오류

#### 원인과 해결법:
- **디렉토리 구조**: `mysql-`, `maria-`, `mariadb-`, `postgresql-`, `supabase-`로 시작하는 디렉토리가 있는지 확인
- **권한 문제**: 디렉토리 읽기 권한 확인
- **경로 문제**: 절대경로 사용 또는 따옴표로 경로 감싸기

```bash
# 디렉토리 구조 확인
ls -la /path/to/databases

# 권한 확인 및 부여 (Linux/Mac)
chmod -R 755 /path/to/databases
sudo chown -R $USER:$USER /path/to/databases

# 절대경로 사용
python convert_to_dbml.py /absolute/path/to/databases --verbose
```

### 2. 파일 인코딩 오류

DDL 파일의 인코딩 문제가 있을 때:
```bash
# UTF-8로 파일 변환 (Linux/Mac)
find /path/to/databases -name "*.sql" -exec file {} \; | grep -v UTF-8

# 파일을 UTF-8로 변환
iconv -f ISO-8859-1 -t UTF-8 file.sql > file_utf8.sql
```

### 3. PostgreSQL 특수 구문 오류

PostgreSQL DDL에서 파싱 오류가 발생할 때:
```bash
# verbose 모드로 상세 로그 확인
python convert_to_dbml.py supabase-project --verbose

# 특정 파일만 테스트
python -c "
from postgresql_ddl_parser import PostgreSQLDDLParser
parser = PostgreSQLDDLParser()
result = parser.parse_file('문제파일.sql')
print(result)
"
```

### 4. 메모리 부족 (대용량 데이터베이스)

```bash
# 메모리 최적화 옵션
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# 한 번에 하나의 데이터베이스만 처리
python convert_to_dbml.py mysql-large-db-3306 --verbose
```

## 🔍 DBML 뷰어 및 활용

생성된 DBML 파일은 다음 도구들로 시각화할 수 있습니다:

### 온라인 도구
- **[dbdiagram.io](https://dbdiagram.io/)** - 가장 인기 있는 온라인 ERD 뷰어
  - 생성된 `.dbml` 파일 내용을 복사해서 붙여넣기
  - 실시간 ERD 생성 및 편집
  - PNG, PDF, SQL 등으로 내보내기

### VS Code 확장
- **[DBML extension](https://marketplace.visualstudio.com/items?itemName=matt-meyers.vscode-dbml)** - VS Code에서 DBML 파일 편집
- **[ERD Editor](https://marketplace.visualstudio.com/items?itemName=dineug.vuerd-vscode)** - ERD 시각화

### CLI 도구
```bash
# dbml-renderer 설치 및 사용
npm install -g dbml-renderer
dbml-renderer -i schema.dbml -o schema.svg
```

## 📈 성능 최적화

### 대용량 데이터베이스 처리
```bash
# 메모리 사용량 모니터링
python -m memory_profiler convert_to_dbml.py large-database

# 병렬 처리 (여러 데이터베이스)
for db in mysql-* maria-* postgresql-*; do
  python convert_to_dbml.py "$db" --verbose &
done
wait
```

### 처리 속도 개선
- SSD 사용 권장
- 가상환경에서 실행
- 불필요한 파일 제외 (`.gitignore` 활용)

## 🔄 업데이트 및 마이그레이션

### v1.x에서 v2.x로 업그레이드

v2.x에서는 데이터베이스별 전용 파서가 도입되어 더욱 정확한 변환이 가능합니다:

```bash
# 기존 DBML 파일 백업
mkdir backup_dbml
find . -name "*.dbml" -exec cp {} backup_dbml/ \;

# 새 버전으로 재변환
python convert_to_dbml.py . --verbose

# 결과 비교
diff -r backup_dbml/ current_dbml/
```

## 🤝 기여하기

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!

### 개발 환경 설정
```bash
# 저장소 클론
git clone https://github.com/your-repo/ddl-to-dbml-converter.git
cd ddl-to-dbml-converter

# 개발용 가상환경 설정
python -m venv dev-env
source dev-env/bin/activate  # Linux/Mac
# dev-env\Scripts\activate   # Windows

# 개발 의존성 설치
pip install -r requirements-dev.txt

# 테스트 실행
python -m pytest tests/
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면:
1. GitHub Issues에 등록
2. 문서를 먼저 확인
3. `--verbose` 옵션으로 상세 로그 확인
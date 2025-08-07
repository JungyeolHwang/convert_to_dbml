# DDL to DBML 변환기

MySQL/MariaDB/PostgreSQL의 DDL 파일을 DBML(Database Markup Language) 형식으로 변환하는 Python 도구입니다.

## 🎯 주요 기능

- SKEEMA 도구로 생성된 디렉토리 구조 자동 인식
- MySQL/MariaDB DDL 파싱
- DBML 형식으로 자동 변환
- 외래키 관계 자동 생성
- 여러 데이터베이스/스키마 일괄 처리

## 📁 지원하는 디렉토리 구조

```
root/
├── mysql-서버이름-포트번호/
│   ├── 스키마이름1/
│   │   ├── 테이블1.sql
│   │   ├── 테이블2.sql
│   │   └── ...
│   └── 스키마이름2/
│       ├── 테이블1.sql
│       └── ...
├── maria-서버이름-포트번호/     # 또는 mariadb-*
│   └── ...
└── postgresql-서버이름-포트번호/
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

```bash
# 현재 디렉토리에서 변환
python convert_to_dbml.py

# 특정 디렉토리에서 변환
python convert_to_dbml.py /path/to/databases

# 상세 로그와 함께 변환
python convert_to_dbml.py . --verbose

# 시뮬레이션만 수행 (파일 생성 안함)
python convert_to_dbml.py . --dry-run
```

### 3. 예제 데이터로 테스트

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
mysql-champstudy-3306/
├── champ/
│   ├── users.sql
│   ├── posts.sql
│   └── comments.sql
└── champ.dbml          ← 생성된 DBML 파일

mysql-acc-3306/
├── calc/
│   ├── accounts.sql
│   └── transactions.sql
└── calc.dbml           ← 생성된 DBML 파일
```

## 🔧 지원하는 DDL 기능

### 테이블 정의
- ✅ 모든 MySQL/MariaDB 데이터 타입
- ✅ NULL/NOT NULL 제약조건
- ✅ DEFAULT 값
- ✅ AUTO_INCREMENT
- ✅ 주석 (부분적)

### 제약조건
- ✅ PRIMARY KEY
- ✅ FOREIGN KEY (관계 자동 생성)
- ✅ UNIQUE 제약조건
- ✅ INDEX 정의

### DBML 출력 예시

```dbml
Project champ {
  database_type: 'MySQL'
}

Table users {
  id bigint [pk, increment, not null]
  username varchar(50) [not null, unique]
  email varchar(100) [not null, unique]
  password_hash varchar(255) [not null]
  first_name varchar(50)
  last_name varchar(50)
  created_at timestamp [not null, default: 'CURRENT_TIMESTAMP']
  updated_at timestamp [not null, default: 'CURRENT_TIMESTAMP']
  is_active tinyint [not null, default: '1']

  Indexes {
    (created_at)
  }
}

Table posts {
  id bigint [pk, increment, not null]
  user_id bigint [not null]
  title varchar(200) [not null]
  content text [not null]
  status enum [not null, default: 'draft']
  view_count int [not null, default: '0']
  created_at timestamp [not null, default: 'CURRENT_TIMESTAMP']
  updated_at timestamp [not null, default: 'CURRENT_TIMESTAMP']

  Indexes {
    (user_id)
    (status)
    (created_at)
  }
}

// Relationships
Ref: posts.user_id > users.id
```

## 📋 명령행 옵션

```
usage: convert_to_dbml.py [-h] [--verbose] [--dry-run] [root_path]

MySQL/MariaDB DDL을 DBML로 변환합니다.

positional arguments:
  root_path     스캔할 루트 디렉토리 경로 (기본값: 현재 디렉토리)

optional arguments:
  -h, --help    도움말 메시지 출력
  --verbose, -v 상세한 로그 출력
  --dry-run     시뮬레이션만 수행 (실제 파일 생성하지 않음)
```

## 🐛 문제 해결

### 1. "변환할 데이터베이스를 찾을 수 없습니다" 오류

#### 원인과 해결법:
- **디렉토리 구조**: `mysql-`, `maria-`, `mariadb-`, `postgresql-`로 시작하는 디렉토리가 있는지 확인
- **권한 문제**: 디렉토리 읽기 권한 확인 (`chmod -R 755 /path/to/databases`)
- **경로 문제**: 절대경로 사용 또는 따옴표로 경로 감싸기

#### 리눅스/EC2 환경:
```bash
# 환경 체크
python check_linux_env.py /path/to/databases

# 권한 부여
chmod -R 755 /path/to/databases
sudo chown -R $USER:$USER /path/to/databases

# 절대경로 사용
python convert_to_dbml.py /absolute/path/to/databases --verbose
```

### 2. 파일 인코딩 오류
- DDL 파일이 UTF-8이 아닌 경우 자동으로 다른 인코딩을 시도합니다
- 여전히 문제가 있으면 파일을 UTF-8로 저장해주세요

### 3. 복잡한 DDL 구문
- 현재 기본적인 CREATE TABLE 문을 지원합니다
- 복잡한 제약조건이나 MySQL 특화 기능은 부분적으로 지원됩니다

## 🔍 DBML 뷰어

생성된 DBML 파일은 다음 도구들로 시각화할 수 있습니다:

- [dbdiagram.io](https://dbdiagram.io/) - 온라인 ERD 뷰어
- [VS Code DBML extension](https://marketplace.visualstudio.com/items?itemName=matt-meyers.vscode-dbml) - VS Code 확장
- [dbml-renderer](https://github.com/softwaretechnik-berlin/dbml-renderer) - CLI 도구

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
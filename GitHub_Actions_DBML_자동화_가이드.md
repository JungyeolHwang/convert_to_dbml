# GitHub Actions를 활용한 DDL to DBML 자동 변환 시스템

## 📋 개요

회사의 DDL 반영 프로세스에서 `auto-ddl` 레포지토리의 변경사항을 자동으로 감지하여 DBML 파일을 생성하고 동기화하는 시스템입니다.

## 🔄 현재 DDL 반영 프로세스

1. **개발자 요청**: CURSOR IDE를 통해 테이블 수정/생성 요청
2. **MCP 처리**: 내부 MCP가 auto-ddl 레포지토리에 접근하여 SQL 파일 직접 수정
3. **AI 서버**: 회사 AI 서버가 ALTER, CREATE 구문 자동 생성
4. **PR 생성**: 생성된 DDL 구문을 PR 리뷰에 첨부하여 요청
5. **DBA 승인**: DBA가 PR 검토 후 MERGE 수행
6. **자동 배포**: GitHub Actions → Lambda → 운영 DB DDL 실행

## 🎯 해결하고자 하는 문제

### 주요 이슈
- **동기화 문제**: auto-ddl 변경 시 DBML도 업데이트되어야 함
- **접근성 문제**: MCP가 내부적으로 처리하여 개발자 로컬에 auto-ddl이 없음
- **실시간성**: DDL 변경과 DBML 변환 간의 시간차 발생

### 기존 고려사항
- **실시간 자동 동기화** vs **수동 실행** 방식 검토
- **인프라 복잡성** vs **사용자 편의성** 트레이드오프

## 💡 제안하는 해결 방안

### GitHub Actions 기반 자동 동기화

auto-ddl 레포지토리에 DDL to DBML 변환기를 직접 통합하여 완전 자동화 구현

## 🏗️ 시스템 아키텍처

### 1. 디렉토리 구조

```
auto-ddl/
├── .github/
│   └── workflows/
│       └── generate-dbml.yml        ← 자동화 워크플로우
├── tools/                           ← DDL to DBML 변환기
│   ├── convert_to_dbml.py
│   ├── dbml_converter.py
│   ├── mysql_ddl_parser.py
│   ├── postgresql_ddl_parser.py
│   ├── base_ddl_parser.py
│   ├── ddl_parser.py
│   ├── directory_scanner.py
│   ├── fix_missing_columns.py
│   ├── requirements.txt
│   └── README.md
├── mysql-서버이름-포트번호/           ← 실제 DDL 파일들
│   └── 스키마이름/
│       ├── 테이블1.sql
│       └── 테이블2.sql
├── supabase-프로젝트명-포트번호/
│   └── public/
│       ├── Admin.sql
│       └── Banner.sql
└── maria-서버이름-포트번호/
    └── 스키마이름/
        └── 테이블.sql
```

### 2. 자동화 워크플로우

#### GitHub Actions 구성 (.github/workflows/generate-dbml.yml)

```yaml
name: Generate DBML Files

on:
  push:
    paths: ['**/*.sql']  # SQL 파일 변경 시에만 실행
  workflow_dispatch:     # 수동 실행 지원

jobs:
  generate-dbml:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 2  # 변경사항 비교를 위해

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install sqlparse>=0.4.4

    - name: Detect changed directories
      id: detect-changes
      run: |
        # 변경된 SQL 파일들의 디렉토리 찾기
        CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD | grep '\.sql$' || true)
        
        if [ -z "$CHANGED_FILES" ]; then
          echo "No SQL files changed"
          echo "changed_dirs=" >> $GITHUB_OUTPUT
          exit 0
        fi
        
        # 변경된 파일들이 속한 데이터베이스 디렉토리들 추출
        CHANGED_DIRS=""
        for file in $CHANGED_FILES; do
          DB_DIR=$(echo $file | grep -E '^(mysql|maria|mariadb|postgresql|supabase)-[^/]+/' | head -1 | cut -d'/' -f1)
          if [ ! -z "$DB_DIR" ]; then
            if [[ ! $CHANGED_DIRS =~ $DB_DIR ]]; then
              CHANGED_DIRS="$CHANGED_DIRS $DB_DIR"
            fi
          fi
        done
        
        echo "Changed directories: $CHANGED_DIRS"
        echo "changed_dirs=$CHANGED_DIRS" >> $GITHUB_OUTPUT

    - name: Generate DBML for changed directories
      if: steps.detect-changes.outputs.changed_dirs != ''
      run: |
        for DIR in ${{ steps.detect-changes.outputs.changed_dirs }}; do
          echo "🔄 Processing directory: $DIR"
          python tools/convert_to_dbml.py "$DIR" --verbose
        done

    - name: Commit DBML files
      if: steps.detect-changes.outputs.changed_dirs != ''
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add *.dbml
        
        if ! git diff --staged --quiet; then
          DIRS="${{ steps.detect-changes.outputs.changed_dirs }}"
          git commit -m "🤖 Auto-generate DBML files for: $DIRS"
          git push
          echo "✅ DBML files updated for: $DIRS"
        else
          echo "ℹ️ No DBML changes detected"
        fi
```

## 🚀 동작 시나리오

### 시나리오 1: 단일 데이터베이스 수정

```bash
# 개발자가 수정한 파일
mysql-champstudy-3306/champstudy/users.sql

# GitHub Actions 실행 과정
1. SQL 파일 변경 감지
2. mysql-champstudy-3306 디렉토리 식별
3. 해당 디렉토리만 DBML 변환 실행
4. champstudy.dbml 파일 생성/업데이트
5. 자동 커밋 및 푸시

# 결과
✅ DBML files updated for: mysql-champstudy-3306
```

### 시나리오 2: 다중 데이터베이스 수정

```bash
# 개발자가 수정한 파일들
mysql-champstudy-3306/champstudy/users.sql
supabase-integration-1/public/Admin.sql
maria-hisbilling-37041/his_resume/tables.sql

# GitHub Actions 실행 과정
1. 모든 변경된 SQL 파일 감지
2. 3개 데이터베이스 디렉토리 식별
3. 각 디렉토리별로 DBML 변환 실행
4. 3개 DBML 파일 생성/업데이트
5. 일괄 커밋 및 푸시

# 결과
✅ DBML files updated for: mysql-champstudy-3306 supabase-integration-1 maria-hisbilling-37041
```

## ⚡ 성능 및 효율성

### 최적화 기능
- **선별적 처리**: 변경된 디렉토리만 처리하여 실행 시간 단축
- **정확한 감지**: git diff로 정확한 변경 사항 파악
- **불필요한 실행 방지**: SQL 파일 변경이 없으면 실행하지 않음
- **캐시 활용**: pip 패키지 캐시로 의존성 설치 시간 단축

### 예상 실행 시간
- **VM 시작**: ~30초
- **Python 설정**: ~20초
- **의존성 설치**: ~10초 (캐시 사용 시)
- **DBML 변환**: ~1-5초 (데이터베이스 크기에 따라)
- **커밋 & 푸시**: ~5초

**총 소요시간: 약 1-2분**

## 🔧 구현 단계

### Phase 1: 기본 구현
1. **tools/ 디렉토리 생성**: auto-ddl 레포지토리에 변환기 파일들 복사
2. **GitHub Actions 워크플로우 추가**: generate-dbml.yml 파일 생성
3. **테스트**: 샘플 SQL 파일 수정하여 동작 확인

### Phase 2: 고도화
1. **에러 핸들링**: 변환 실패 시 알림 및 롤백 기능
2. **리포팅**: 변환 결과 요약 및 슬랙 알림
3. **성능 최적화**: 병렬 처리 및 캐시 전략 개선

## 📋 요구사항 및 전제조건

### 기술적 요구사항
- **GitHub 레포지토리**: auto-ddl 레포지토리에 대한 쓰기 권한
- **GitHub Actions**: 공개 레포지토리는 무료, 프라이빗은 사용량에 따라 과금
- **Python 환경**: 3.9 이상 (GitHub Actions 기본 제공)
- **의존성**: sqlparse>=0.4.4 (매우 가벼운 의존성)

### 보안 고려사항
- **토큰 권한**: GITHUB_TOKEN의 repository 권한 필요
- **브랜치 보호**: main 브랜치 보호 규칙과의 호환성 확인
- **코드 리뷰**: 자동 생성된 DBML 파일에 대한 리뷰 정책

## ✅ 장점

### 사용자 관점
- **완전 자동화**: 개발자 개입 없이 DBML 생성
- **실시간 동기화**: DDL 변경 즉시 DBML 반영
- **선별적 처리**: 변경된 부분만 처리하여 효율적

### 운영 관점
- **일관성 보장**: 항상 DDL과 DBML이 동기화됨
- **비용 효율성**: GitHub Actions 무료 한도 내에서 충분히 사용 가능
- **유지보수 용이**: 단순한 구조로 관리 부담 최소화

### 기술적 관점
- **안정성**: 격리된 환경에서 매번 깨끗하게 실행
- **확장성**: 새로운 데이터베이스 타입 추가 용이
- **모니터링**: GitHub Actions 로그로 실행 상태 추적 가능

## 🚨 주의사항

### 제한사항
- **GitHub Actions 실행 시간**: 최대 6시간 (일반적으로 1-2분 소요)
- **동시 실행**: 같은 워크플로우는 큐에서 순차 처리
- **브랜치 제한**: main 브랜치에 직접 푸시 (브랜치 보호 규칙 고려 필요)

### 모니터링 포인트
- **실행 실패**: 네트워크 오류, 파싱 오류 등
- **커밋 충돌**: 동시 수정 시 발생 가능한 충돌
- **용량 제한**: 생성되는 DBML 파일 크기 (일반적으로 문제없음)

## 📞 지원 및 문의

### 문제 해결
1. **GitHub Actions 로그 확인**: 실행 상세 로그 분석
2. **로컬 테스트**: tools/ 디렉토리에서 수동 실행으로 디버깅
3. **이슈 등록**: 변환기 레포지토리에 이슈 보고

### 개선 요청
- 새로운 데이터베이스 타입 지원
- 추가 기능 요청
- 성능 최적화 제안

---

*이 문서는 회사의 DDL 반영 프로세스를 개선하기 위한 기술 제안서입니다. 구현 전 보안 정책 및 인프라 제약사항을 확인해주시기 바랍니다.*

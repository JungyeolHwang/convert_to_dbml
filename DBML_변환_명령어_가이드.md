# DBML 변환 명령어 가이드

## 🚀 빠른 시작

### 1. 가상환경 활성화
```powershell
venv\Scripts\activate
```

### 2. 개별 디렉토리 변환

#### Maria DB 스키마들
```powershell

python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-acc-39030

# maria-bidding-39040
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-bidding-39040

# maria-BOOKSAPI-34023
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-BOOKSAPI-34023

# maria-BSCM-39041
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-BSCM-39041

# maria-champstudyB2B-37222
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-champstudyB2B-37222

# maria-closingbanner-37030
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-closingbanner-37030

# maria-gosi-regi-37083
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-gosi-regi-37083

# maria-hacademia-38024
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-hacademia-38024

# maria-hisbilling-37041
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-hisbilling-37041

# maria-hismember-37040
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-hismember-37040

# maria-jrjump-36010
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-jrjump-36010

# maria-jrjump-regi-38028
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-jrjump-regi-38028

# maria-LIVETV-38048
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-LIVETV-38048

# maria-LOG-39043
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-LOG-39043

# maria-ORDER-38046
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-ORDER-38046

# maria-RECRUIT-39020
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-RECRUIT-39020

# maria-regi-38025
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-regi-38025

# maria-regica-37154
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-regica-37154

# maria-SAP-39010
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-SAP-39010

# maria-totalcalc-39031
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/maria-totalcalc-39031
```

#### MySQL 스키마들
```powershell
# mysql-autokeyword-38045
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-autokeyword-38045

# mysql-BIGPLE-37130
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-BIGPLE-37130

# mysql-campus-38047
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-campus-38047

# mysql-champstudy-37070
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-champstudy-37070

# mysql-common-realname-37140
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-common-realname-37140

# mysql-dokhaksa-35010
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-dokhaksa-35010

# mysql-finance-37100
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-finance-37100

# mysql-frontend-37052
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-frontend-37052

# mysql-fullservice-37221
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-fullservice-37221

# mysql-gohackers-38010
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-gohackers-38010

# mysql-gosi-37080
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-gosi-37080

# mysql-grammer-gateway-37210
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-grammer-gateway-37210

# mysql-hackersbook-34021
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hackersbook-34021

# mysql-hackersjob-37110
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hackersjob-37110

# mysql-hackerstest-37120
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hackerstest-37120

# mysql-hackersuhak-38020
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hackersuhak-38020

# mysql-hisapp-37042
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hisapp-37042

# mysql-hissurvey-37043
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-hissurvey-37043

# mysql-japan-firststep-37190
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-japan-firststep-37190

# mysql-land-37090
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-land-37090

# mysql-mockexam-37200
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-mockexam-37200

# mysql-onlyoffice-39100
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-onlyoffice-39100

# mysql-shorturl-37180
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-shorturl-37180

# mysql-teacher-37060
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-teacher-37060

# mysql-toeicvoca-37150
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-toeicvoca-37150

# mysql-toeicvocauser-37151
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-toeicvocauser-37151

# mysql-voca-37170
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-voca-37170

# mysql-voca-mid-high-37152
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-voca-mid-high-37152

# mysql-voca4800-37160
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/mysql-voca4800-37160
```

#### 기타 스키마들
```powershell
# supabase-integration-1
python convert_to_dbml.py auto-ddl-main/auto-ddl-main/supabase-integration-1
```

## 🔄 일괄 변환 스크립트 (PowerShell)

### 전체 자동 변환
```powershell
# 모든 디렉토리를 자동으로 변환하는 스크립트
$directories = @(
    "maria-bidding-39040",
    "maria-BOOKSAPI-34023", 
    "maria-BSCM-39041",
    "maria-champstudyB2B-37222",
    "maria-closingbanner-37030",
    "maria-gosi-regi-37083",
    "maria-hacademia-38024",
    "maria-hisbilling-37041",
    "maria-hismember-37040",
    "maria-jrjump-36010",
    "maria-jrjump-regi-38028",
    "maria-LIVETV-38048",
    "maria-ORDER-38046",
    "maria-RECRUIT-39020",
    "maria-regi-38025",
    "maria-regica-37154",
    "maria-SAP-39010",
    "maria-totalcalc-39031",
    "mysql-autokeyword-38045",
    "mysql-BIGPLE-37130",
    "mysql-campus-38047",
    "mysql-champstudy-37070",
    "mysql-common-realname-37140",
    "mysql-dokhaksa-35010",
    "mysql-finance-37100",
    "mysql-frontend-37052",
    "mysql-fullservice-37221",
    "mysql-gohackers-38010",
    "mysql-gosi-37080",
    "mysql-grammer-gateway-37210",
    "mysql-hackersbook-34021",
    "mysql-hackersjob-37110",
    "mysql-hackerstest-37120",
    "mysql-hackersuhak-38020",
    "mysql-hisapp-37042",
    "mysql-hissurvey-37043",
    "mysql-japan-firststep-37190",
    "mysql-land-37090",
    "mysql-mockexam-37200",
    "mysql-onlyoffice-39100",
    "mysql-shorturl-37180",
    "mysql-teacher-37060",
    "mysql-toeicvoca-37150",
    "mysql-toeicvocauser-37151",
    "mysql-voca-37170",
    "mysql-voca-mid-high-37152",
    "mysql-voca4800-37160",
    "supabase-integration-1"
)

foreach ($dir in $directories) {
    Write-Host "🔄 Converting: $dir" -ForegroundColor Yellow
    python convert_to_dbml.py "auto-ddl-main/auto-ddl-main/$dir"
    Write-Host "✅ Completed: $dir" -ForegroundColor Green
    Write-Host "-----------------------------------"
}

Write-Host "🎉 모든 변환이 완료되었습니다!" -ForegroundColor Cyan
```

## 📋 사용 방법

### 1. 개별 변환
- 위의 개별 명령어 중 원하는 스키마 선택해서 실행

### 2. 일괄 변환
- PowerShell에서 위의 전체 자동 변환 스크립트 복사해서 실행
- 모든 디렉토리가 순차적으로 자동 변환됨

### 3. 변환 결과 확인
```powershell
# 생성된 DBML 파일 확인
Get-ChildItem -Path "auto-ddl-main" -Filter "*.dbml" -Recurse
```

## ⚠️ 주의사항

1. **가상환경 활성화 필수**: 변환 전 반드시 `venv\Scripts\activate` 실행
2. **경로 확인**: `auto-ddl-main/auto-ddl-main/` 경로가 정확한지 확인
3. **오류 발생 시**: 개별 디렉토리별로 실행해서 문제 디렉토리 식별
4. **대용량 스키마**: `maria-SAP-39010`, `mysql-gosi-37080` 등은 시간이 오래 걸릴 수 있음

## 🎯 예상 결과

- **총 48개 디렉토리** 변환 예정
- **수천 개의 테이블** DBML 변환
- **완벽한 dbdiagram.io 호환** DBML 생성

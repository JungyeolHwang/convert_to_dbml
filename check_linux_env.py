#!/usr/bin/env python3
"""
리눅스 환경에서 DDL to DBML 변환기 실행 전 환경 체크 스크립트
"""

import os
import sys
import pwd
import grp
import stat
import locale
from pathlib import Path

def check_python_environment():
    """Python 환경 체크"""
    print("🐍 Python 환경 체크")
    print(f"  Python 버전: {sys.version}")
    print(f"  Python 실행 파일: {sys.executable}")
    
    # 가상환경 체크
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("  ✅ 가상환경 활성화됨")
    else:
        print("  ⚠️  가상환경이 활성화되지 않음")
    
    # 필수 모듈 체크
    try:
        import sqlparse
        print(f"  ✅ sqlparse 버전: {sqlparse.__version__}")
    except ImportError:
        print("  ❌ sqlparse가 설치되지 않음 (pip install sqlparse)")
    
    print()

def check_system_info():
    """시스템 정보 체크"""
    print("🖥️  시스템 정보")
    
    # OS 정보
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    os_name = line.split('=')[1].strip().strip('"')
                    print(f"  OS: {os_name}")
                    break
    
    # 사용자 정보
    user = pwd.getpwuid(os.getuid())
    print(f"  사용자: {user.pw_name} (UID: {user.pw_uid})")
    
    # 그룹 정보
    groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
    print(f"  그룹: {', '.join(groups)}")
    
    # 로케일 정보
    try:
        current_locale = locale.getlocale()
        print(f"  로케일: {current_locale}")
        
        # UTF-8 체크
        encoding = locale.getpreferredencoding()
        print(f"  인코딩: {encoding}")
        if 'utf' not in encoding.lower():
            print("  ⚠️  UTF-8이 아닌 인코딩이 설정됨")
    except Exception as e:
        print(f"  ❌ 로케일 정보 가져오기 실패: {e}")
    
    print()

def check_directory_access(path_str):
    """디렉토리 접근 권한 체크"""
    print(f"📁 디렉토리 체크: {path_str}")
    
    try:
        path = Path(path_str).resolve()
        print(f"  절대 경로: {path}")
        
        # 존재 여부
        if not path.exists():
            print(f"  ❌ 경로가 존재하지 않음")
            return False
        
        if not path.is_dir():
            print(f"  ❌ 디렉토리가 아님")
            return False
        
        print(f"  ✅ 경로 존재함")
        
        # 권한 체크
        stat_info = path.stat()
        permissions = oct(stat_info.st_mode)[-3:]
        print(f"  권한: {permissions}")
        
        # 소유자 정보
        try:
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            group = grp.getgrgid(stat_info.st_gid).gr_name
            print(f"  소유자: {owner}:{group}")
        except KeyError:
            print(f"  소유자: UID {stat_info.st_uid}, GID {stat_info.st_gid}")
        
        # 읽기 권한 테스트
        if os.access(path, os.R_OK):
            print("  ✅ 읽기 권한 있음")
        else:
            print("  ❌ 읽기 권한 없음")
            return False
        
        # 실행 권한 테스트 (디렉토리 탐색용)
        if os.access(path, os.X_OK):
            print("  ✅ 실행 권한 있음")
        else:
            print("  ❌ 실행 권한 없음")
            return False
        
        # 하위 디렉토리 나열 테스트
        try:
            items = list(path.iterdir())
            print(f"  ✅ 하위 항목: {len(items)}개")
            
            # mysql-*, mariadb-*, postgresql- 패턴 체크
            db_dirs = []
            for item in items:
                if item.is_dir():
                    name = item.name
                    if (name.startswith('mysql-') or 
                        name.startswith('mariadb-') or 
                        name.startswith('postgresql-')):
                        db_dirs.append(name)
            
            if db_dirs:
                print(f"  ✅ 데이터베이스 디렉토리 발견: {len(db_dirs)}개")
                for db_dir in db_dirs:
                    print(f"    📁 {db_dir}")
                    
                    # 각 DB 디렉토리의 스키마 체크
                    db_path = path / db_dir
                    try:
                        schema_dirs = [item.name for item in db_path.iterdir() if item.is_dir()]
                        if schema_dirs:
                            print(f"      스키마: {', '.join(schema_dirs)}")
                            
                            # 첫 번째 스키마의 SQL 파일 체크
                            first_schema = db_path / schema_dirs[0]
                            sql_files = list(first_schema.glob('*.sql'))
                            print(f"      SQL 파일: {len(sql_files)}개")
                        else:
                            print(f"      ❌ 스키마 디렉토리 없음")
                    except PermissionError:
                        print(f"      ❌ {db_dir} 읽기 권한 없음")
            else:
                print("  ⚠️  mysql-*, mariadb-*, postgresql- 패턴의 디렉토리 없음")
                
        except PermissionError as e:
            print(f"  ❌ 디렉토리 나열 권한 없음: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ 디렉토리 체크 실패: {e}")
        return False
    
    finally:
        print()

def main():
    """메인 함수"""
    print("🔍 DDL to DBML 변환기 리눅스 환경 체크")
    print("=" * 50)
    print()
    
    # Python 환경 체크
    check_python_environment()
    
    # 시스템 정보 체크
    check_system_info()
    
    # 디렉토리 체크
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
        success = check_directory_access(directory_path)
        
        print("📋 결과 요약")
        if success:
            print("✅ 모든 체크 통과! 변환을 실행할 수 있습니다.")
            print()
            print("🚀 권장 실행 명령:")
            print(f"python convert_to_dbml.py '{directory_path}' --verbose")
        else:
            print("❌ 문제가 발견되었습니다. 위 메시지를 참고하여 해결해주세요.")
            print()
            print("💡 일반적인 해결 방법:")
            print("1. 권한 문제: chmod -R 755 <directory>")
            print("2. 소유자 문제: sudo chown -R $USER:$USER <directory>")
            print("3. 경로 문제: 절대경로 사용 또는 따옴표로 감싸기")
    else:
        print("사용법: python check_linux_env.py <database_directory_path>")
        print("예시: python check_linux_env.py /home/ubuntu/databases")

if __name__ == "__main__":
    main()
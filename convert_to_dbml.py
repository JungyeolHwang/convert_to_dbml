#!/usr/bin/env python3
"""
MySQL/MariaDB DDL을 DBML로 변환하는 메인 스크립트

사용법:
    python convert_to_dbml.py [루트_디렉토리_경로] [옵션]

예시:
    python convert_to_dbml.py /path/to/databases
    python convert_to_dbml.py . --verbose
    python convert_to_dbml.py /databases --dry-run
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List

from ddl_parser import DDLParser
from dbml_converter import DBMLConverter
from directory_scanner import DirectoryScanner


class DDLToDBMLConverter:
    """DDL을 DBML로 변환하는 메인 클래스"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.ddl_parser = DDLParser()
        self.dbml_converter = DBMLConverter()
        self.stats = {
            'databases_processed': 0,
            'schemas_processed': 0,
            'tables_processed': 0,
            'files_created': 0,
            'errors': []
        }
    
    def convert_all(self, root_path: str, dry_run: bool = False) -> bool:
        """
        루트 디렉토리의 모든 데이터베이스를 DBML로 변환
        
        Args:
            root_path: 스캔할 루트 디렉토리
            dry_run: True이면 실제 파일을 생성하지 않고 시뮬레이션만 수행
            
        Returns:
            성공 여부
        """
        try:
            # 디렉토리 스캔
            scanner = DirectoryScanner(root_path)
            database_structure = scanner.scan_databases()
            
            if not database_structure:
                print("⚠️  변환할 데이터베이스를 찾을 수 없습니다.")
                print(f"루트 디렉토리: {os.path.abspath(root_path)}")
                print()
                print("🔍 문제 해결 방법:")
                print("1. 디렉토리 경로가 올바른지 확인")
                print("2. mysql-*, maria-*, mariadb-*, postgresql-* 형태의 디렉토리가 있는지 확인")
                print("3. 디렉토리에 읽기 권한이 있는지 확인")
                print()
                print("📁 현재 디렉토리 내용:")
                try:
                    from pathlib import Path
                    import stat
                    path_obj = Path(root_path)
                    if path_obj.exists() and path_obj.is_dir():
                        items_found = False
                        for item in path_obj.iterdir():
                            items_found = True
                            # 권한 정보 추가
                            permissions = oct(item.stat().st_mode)[-3:]
                            if item.is_dir():
                                print(f"  📁 {item.name} (권한: {permissions})")
                            else:
                                print(f"  📄 {item.name} (권한: {permissions})")
                        
                        if not items_found:
                            print("  (빈 디렉토리)")
                        
                        # 디렉토리 권한도 체크
                        dir_permissions = oct(path_obj.stat().st_mode)[-3:]
                        print(f"  🔐 디렉토리 권한: {dir_permissions}")
                        
                    else:
                        print(f"  ❌ 경로가 존재하지 않거나 디렉토리가 아닙니다.")
                        print(f"  경로 상태: exists={path_obj.exists()}, is_dir={path_obj.is_dir() if path_obj.exists() else 'N/A'}")
                except PermissionError as e:
                    print(f"  ❌ 권한 오류: {e}")
                    print("  💡 sudo 권한이나 디렉토리 소유자 권한이 필요할 수 있습니다.")
                except Exception as e:
                    print(f"  ❌ 디렉토리 읽기 오류: {e}")
                return False
            
            # 스캔 결과 출력
            if self.verbose:
                scanner.print_scan_summary(database_structure)
            else:
                print(f"📊 발견된 데이터베이스: {len(database_structure)}개")
                total_schemas = sum(len(schemas) for schemas in database_structure.values())
                print(f"📊 총 스키마: {total_schemas}개")
            
            # 각 데이터베이스/스키마별로 변환 수행
            for db_name, schemas in database_structure.items():
                self._convert_database(scanner, db_name, schemas, dry_run)
            
            # 결과 요약 출력
            self._print_conversion_summary()
            
            return len(self.stats['errors']) == 0
            
        except Exception as e:
            print(f"❌ 변환 중 오류 발생: {e}")
            return False
    
    def _convert_database(self, scanner: DirectoryScanner, db_name: str, 
                         schemas: Dict[str, List[str]], dry_run: bool):
        """단일 데이터베이스의 모든 스키마를 변환"""
        db_info = scanner.get_database_info(db_name)
        
        print(f"\n🔄 처리 중: {db_name} ({db_info['db_type']} - {db_info['server_name']}:{db_info['port']})")
        
        for schema_name, ddl_files in schemas.items():
            try:
                self._convert_schema(scanner, db_name, schema_name, ddl_files, dry_run)
                self.stats['schemas_processed'] += 1
            except Exception as e:
                error_msg = f"{db_name}/{schema_name}: {e}"
                self.stats['errors'].append(error_msg)
                print(f"  ❌ {schema_name}: {e}")
        
        self.stats['databases_processed'] += 1
    
    def _convert_schema(self, scanner: DirectoryScanner, db_name: str, 
                       schema_name: str, ddl_files: List[str], dry_run: bool):
        """단일 스키마의 모든 테이블을 DBML로 변환"""
        if self.verbose:
            print(f"  📁 스키마: {schema_name} ({len(ddl_files)}개 테이블)")
        
        # 모든 DDL 파일을 파싱
        all_tables = {}
        table_count = 0
        
        for ddl_file in ddl_files:
            try:
                tables_data = self.ddl_parser.parse_file(ddl_file)
                all_tables.update(tables_data)
                table_count += len(tables_data)
                
                if self.verbose:
                    table_names = list(tables_data.keys())
                    if table_names:
                        print(f"    ✅ {Path(ddl_file).name}: {', '.join(table_names)}")
                    else:
                        print(f"    ⚠️  {Path(ddl_file).name}: 테이블을 찾을 수 없음")
                        
            except Exception as e:
                error_msg = f"파일 파싱 실패 {ddl_file}: {e}"
                self.stats['errors'].append(error_msg)
                if self.verbose:
                    print(f"    ❌ {Path(ddl_file).name}: {e}")
        
        if not all_tables:
            print(f"  ⚠️  {schema_name}: 변환할 테이블이 없습니다.")
            return
        
        # DBML로 변환
        dbml_content = self.dbml_converter.convert_tables_to_dbml(all_tables, schema_name)
        
        # 누락된 컬럼 감지 및 수정
        schema_dir = Path(ddl_files[0]).parent if ddl_files else None
        if schema_dir and schema_dir.exists():
            print(f"  🔍 {schema_name}: 누락된 컬럼 검사 중...")
            dbml_content = self.dbml_converter.validate_and_fix_missing_columns(dbml_content, str(schema_dir))
        
        # 출력 파일 경로 생성
        output_path = scanner.generate_output_path(db_name, schema_name)
        
        if dry_run:
            print(f"  🔍 [DRY-RUN] 생성될 파일: {output_path} ({table_count}개 테이블)")
        else:
            # DBML 파일 저장
            self.dbml_converter.save_dbml_file(dbml_content, output_path)
            print(f"  ✅ {schema_name}: {output_path} ({table_count}개 테이블)")
            self.stats['files_created'] += 1
        
        self.stats['tables_processed'] += table_count
    
    def _print_conversion_summary(self):
        """변환 결과 요약 출력"""
        print("\n" + "="*50)
        print("📊 변환 완료 요약")
        print("="*50)
        print(f"처리된 데이터베이스: {self.stats['databases_processed']}개")
        print(f"처리된 스키마: {self.stats['schemas_processed']}개")
        print(f"처리된 테이블: {self.stats['tables_processed']}개")
        print(f"생성된 DBML 파일: {self.stats['files_created']}개")
        
        if self.stats['errors']:
            print(f"\n⚠️  오류: {len(self.stats['errors'])}개")
            for error in self.stats['errors']:
                print(f"  - {error}")
        else:
            print("\n🎉 모든 변환이 성공적으로 완료되었습니다!")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="MySQL/MariaDB DDL을 DBML로 변환합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python convert_to_dbml.py .                    # 현재 디렉토리에서 변환
  python convert_to_dbml.py /path/to/databases   # 특정 경로에서 변환
  python convert_to_dbml.py . --verbose          # 상세 로그와 함께 변환
  python convert_to_dbml.py . --dry-run          # 시뮬레이션만 수행 (파일 생성 안함)
        """
    )
    
    parser.add_argument(
        'root_path',
        nargs='?',
        default='.',
        help='스캔할 루트 디렉토리 경로 (기본값: 현재 디렉토리)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세한 로그 출력'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='시뮬레이션만 수행 (실제 파일 생성하지 않음)'
    )
    
    args = parser.parse_args()
    
    # 루트 디렉토리 존재 확인
    if not os.path.exists(args.root_path):
        print(f"❌ 디렉토리가 존재하지 않습니다: {args.root_path}")
        sys.exit(1)
    
    print("🚀 DDL to DBML 변환기")
    print(f"📁 루트 디렉토리: {os.path.abspath(args.root_path)}")
    
    if args.dry_run:
        print("🔍 DRY-RUN 모드: 파일을 생성하지 않고 시뮬레이션만 수행합니다.")
    
    print()
    
    # 변환 실행
    converter = DDLToDBMLConverter(verbose=args.verbose)
    success = converter.convert_all(args.root_path, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
"""
디렉토리 구조를 스캔하여 DDL 파일들을 찾고 처리하는 모듈
"""

import os
import glob
from typing import Dict, List, Tuple
from pathlib import Path


class DirectoryScanner:
    """SKEEMA 구조의 디렉토리를 스캔하여 DDL 파일들을 찾는 클래스"""
    
    def __init__(self, root_path: str):
        """
        Args:
            root_path: 스캔할 루트 디렉토리 경로
        """
        self.root_path = Path(root_path)
        
    def scan_databases(self) -> Dict[str, Dict[str, List[str]]]:
        """
        디렉토리 구조를 스캔하여 데이터베이스별로 스키마와 DDL 파일들을 매핑
        
        Returns:
            Dict[database_name, Dict[schema_name, List[ddl_files]]]
            예: {
                'mysql-champstudy-3306': {
                    'champ': ['table1.sql', 'table2.sql']
                },
                'mysql-acc-3306': {
                    'calc': ['table1.sql', 'table2.sql']
                }
            }
        """
        database_structure = {}
        
        # 현재 디렉토리가 직접 데이터베이스 디렉토리인지 확인
        if self._is_database_directory(self.root_path):
            db_name = self.root_path.name
            schema_structure = self._scan_schemas_in_database(self.root_path)
            if schema_structure:
                database_structure[db_name] = schema_structure
                return database_structure
        
        # 루트 디렉토리에서 mysql-* 또는 mariadb-* 형태의 디렉토리 찾기
        for db_dir in self.root_path.iterdir():
            if not db_dir.is_dir():
                continue
                
            db_name = db_dir.name
            
            # mysql-*, maria-*, mariadb-*, postgresql-*, supabase-* 패턴 확인
            if not (db_name.startswith('mysql-') or db_name.startswith('maria-') or db_name.startswith('mariadb-') or db_name.startswith('postgresql-') or db_name.startswith('supabase-')):
                continue
            
            schema_structure = self._scan_schemas_in_database(db_dir)
            if schema_structure:
                database_structure[db_name] = schema_structure
        
        return database_structure
    
    def _is_database_directory(self, path: Path) -> bool:
        """
        주어진 경로가 데이터베이스 디렉토리인지 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            데이터베이스 디렉토리 여부
        """
        # 디렉토리 이름이 mysql-*, maria-*, mariadb-*, postgresql-*, supabase-* 패턴인지 확인
        dir_name = path.name
        if not (dir_name.startswith('mysql-') or dir_name.startswith('maria-') or dir_name.startswith('mariadb-') or dir_name.startswith('postgresql-') or dir_name.startswith('supabase-')):
            return False
        
        # 하위에 스키마로 보이는 디렉토리들이 있는지 확인
        try:
            schema_dirs = [item for item in path.iterdir() if item.is_dir()]
            if not schema_dirs:
                return False
            
            # 각 스키마 디렉토리에 .sql 파일이 있는지 확인
            for schema_dir in schema_dirs:
                sql_files = list(schema_dir.glob('*.sql'))
                if sql_files:
                    return True  # 최소 하나의 스키마에 SQL 파일이 있으면 DB 디렉토리로 판단
            
            return False
        except (PermissionError, OSError):
            return False
    
    def _scan_schemas_in_database(self, db_dir: Path) -> Dict[str, List[str]]:
        """
        데이터베이스 디렉토리 내의 스키마들을 스캔
        
        Args:
            db_dir: 데이터베이스 디렉토리 경로
            
        Returns:
            Dict[schema_name, List[ddl_files]]
        """
        schema_structure = {}
        
        for schema_dir in db_dir.iterdir():
            if not schema_dir.is_dir():
                continue
                
            schema_name = schema_dir.name
            ddl_files = self._find_ddl_files(schema_dir)
            
            if ddl_files:
                schema_structure[schema_name] = ddl_files
        
        return schema_structure
    
    def _find_ddl_files(self, schema_dir: Path) -> List[str]:
        """
        스키마 디렉토리에서 .sql 파일들을 찾기
        
        Args:
            schema_dir: 스키마 디렉토리 경로
            
        Returns:
            DDL 파일 경로들의 리스트
        """
        ddl_files = []
        
        # .sql 파일들을 찾기
        for sql_file in schema_dir.glob('*.sql'):
            if sql_file.is_file():
                ddl_files.append(str(sql_file))
        
        return sorted(ddl_files)
    
    def get_database_info(self, db_name: str) -> Dict[str, str]:
        """
        데이터베이스 이름에서 정보 추출
        
        Args:
            db_name: 데이터베이스 디렉토리 이름 (예: mysql-champstudy-3306, maria-mydb-3307)
            
        Returns:
            Dict containing db_type, server_name, port
        """
        parts = db_name.split('-')
        
        if len(parts) >= 3:
            db_type = parts[0]  # mysql, maria, mariadb, postgresql, supabase
            # maria는 mariadb로 표시
            if db_type == 'maria':
                db_type = 'mariadb'
            server_name = '-'.join(parts[1:-1])  # 중간 부분들을 합침 (서버명에 하이픈이 있을 수 있음)
            port = parts[-1]  # 마지막 부분은 포트
        else:
            db_type = parts[0] if parts else 'unknown'
            if db_type == 'maria':
                db_type = 'mariadb'
            server_name = '-'.join(parts[1:]) if len(parts) > 1 else 'unknown'
            port = 'unknown'
        
        return {
            'db_type': db_type,
            'server_name': server_name,
            'port': port
        }
    
    def generate_output_path(self, db_name: str, schema_name: str) -> str:
        """
        출력 DBML 파일 경로 생성
        
        Args:
            db_name: 데이터베이스 이름
            schema_name: 스키마 이름
            
        Returns:
            DBML 파일 경로
        """
        # 현재 경로가 이미 데이터베이스 디렉토리인 경우
        if self._is_database_directory(self.root_path):
            return str(self.root_path / f"{schema_name}.dbml")
        else:
            # 일반적인 경우 (상위 디렉토리에서 스캔)
            db_dir = self.root_path / db_name
            return str(db_dir / f"{schema_name}.dbml")
    
    def print_scan_summary(self, database_structure: Dict[str, Dict[str, List[str]]]):
        """스캔 결과 요약을 출력"""
        print("=== 디렉토리 스캔 결과 ===")
        print(f"루트 디렉토리: {self.root_path}")
        print(f"발견된 데이터베이스: {len(database_structure)}개\n")
        
        for db_name, schemas in database_structure.items():
            db_info = self.get_database_info(db_name)
            print(f"📁 {db_name}")
            print(f"   타입: {db_info['db_type']}")
            print(f"   서버: {db_info['server_name']}")
            print(f"   포트: {db_info['port']}")
            print(f"   스키마: {len(schemas)}개")
            
            for schema_name, ddl_files in schemas.items():
                print(f"   └── {schema_name}: {len(ddl_files)}개 테이블")
                for ddl_file in ddl_files[:3]:  # 처음 3개만 표시
                    table_name = Path(ddl_file).stem
                    print(f"       - {table_name}")
                if len(ddl_files) > 3:
                    print(f"       ... 그 외 {len(ddl_files) - 3}개")
            print()


if __name__ == "__main__":
    # 테스트 코드
    import sys
    
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = "."
    
    scanner = DirectoryScanner(root_path)
    structure = scanner.scan_databases()
    scanner.print_scan_summary(structure)
    
    # 샘플 출력 경로 생성 테스트
    for db_name, schemas in structure.items():
        for schema_name in schemas.keys():
            output_path = scanner.generate_output_path(db_name, schema_name)
            print(f"출력 경로: {output_path}")
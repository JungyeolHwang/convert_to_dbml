"""
통합 DDL 파서
데이터베이스 타입에 따라 적절한 파서를 선택하여 CREATE TABLE 문을 파싱합니다.
"""

from typing import Dict
from mysql_ddl_parser import MySQLDDLParser
from postgresql_ddl_parser import PostgreSQLDDLParser


class DDLParser:
    """DDL 파일을 파싱하여 테이블 구조 정보를 추출하는 통합 파서"""
    
    def __init__(self, db_type: str = 'mysql'):
        """
        Args:
            db_type: 데이터베이스 타입 ('mysql', 'mariadb', 'postgresql', 'supabase')
        """
        self.db_type = db_type.lower()
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """데이터베이스 타입에 따라 적절한 파서 생성"""
        if self.db_type in ['mysql', 'mariadb']:
            return MySQLDDLParser()
        elif self.db_type in ['postgresql', 'supabase']:
            return PostgreSQLDDLParser()
        else:
            # 기본값으로 MySQL 파서 사용
            return MySQLDDLParser()
    
    def parse_file(self, file_path: str) -> Dict:
        """DDL 파일을 파싱하여 테이블 정보를 반환"""
        return self.parser.parse_file(file_path)
    
    def parse_ddl_content(self, content: str) -> Dict:
        """DDL 내용을 파싱하여 테이블 정보를 반환"""
        return self.parser.parse_ddl_content(content)
    
    @staticmethod
    def detect_database_type(content: str) -> str:
        """DDL 내용을 분석하여 데이터베이스 타입을 추정"""
        content_upper = content.upper()
        
        # PostgreSQL 특징적인 키워드들
        postgresql_indicators = [
            'CHARACTER VARYING',
            'TIMESTAMP WITHOUT TIME ZONE',
            'TIMESTAMP WITH TIME ZONE',
            'JSONB',
            'SERIAL',
            'BIGSERIAL',
            'NEXTVAL(',
            'REGCLASS',
            'PUBLIC.'
        ]
        
        # MySQL/MariaDB 특징적인 키워드들
        mysql_indicators = [
            'AUTO_INCREMENT',
            'TINYINT',
            'MEDIUMINT',
            'LONGTEXT',
            'MEDIUMTEXT',
            'TINYTEXT',
            'LONGBLOB',
            'MEDIUMBLOB',
            'TINYBLOB',
            'ENGINE=',
            'CHARSET=',
            'COLLATE='
        ]
        
        postgresql_score = sum(1 for indicator in postgresql_indicators if indicator in content_upper)
        mysql_score = sum(1 for indicator in mysql_indicators if indicator in content_upper)
        
        if postgresql_score > mysql_score:
            return 'postgresql'
        else:
            return 'mysql'
"""
기본 DDL 파서 인터페이스
각 데이터베이스별 파서가 구현해야 할 공통 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class BaseDDLParser(ABC):
    """모든 DDL 파서가 구현해야 할 기본 인터페이스"""
    
    def __init__(self):
        self.tables = {}
    
    def parse_file(self, file_path: str) -> Dict:
        """DDL 파일을 파싱하여 테이블 정보를 반환"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패 시 다른 인코딩 시도
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        return self.parse_ddl_content(content)
    
    @abstractmethod
    def parse_ddl_content(self, content: str) -> Dict:
        """DDL 내용을 파싱하여 테이블 정보를 반환"""
        pass
    
    @abstractmethod
    def _parse_create_table(self, statement) -> Optional[Dict]:
        """CREATE TABLE 문을 파싱"""
        pass
    
    @abstractmethod
    def _clean_identifier(self, identifier: str) -> str:
        """식별자에서 특수문자 제거"""
        pass
    
    @abstractmethod
    def _parse_column_definition(self, tokens: List) -> Optional[Dict]:
        """컬럼 정의를 파싱"""
        pass
    
    @abstractmethod
    def _parse_constraint(self, tokens: List) -> Optional[Dict]:
        """제약조건을 파싱"""
        pass

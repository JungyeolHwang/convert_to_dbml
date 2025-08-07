"""
PostgreSQL DDL 파서
CREATE TABLE 문을 파싱하여 테이블 정보를 추출합니다.
"""

import re
import sqlparse
from sqlparse.sql import Statement, Token, TokenList
from sqlparse.tokens import Keyword, Name, Literal, Punctuation
from typing import Dict, List, Optional, Tuple
from base_ddl_parser import BaseDDLParser


class PostgreSQLDDLParser(BaseDDLParser):
    """PostgreSQL DDL 파일을 파싱하여 테이블 구조 정보를 추출하는 클래스"""
    
    def __init__(self):
        super().__init__()
        # PostgreSQL 데이터 타입 매핑
        self.postgresql_type_mapping = {
            'character varying': 'VARCHAR',
            'character': 'CHAR',
            'varchar': 'VARCHAR',
            'char': 'CHAR',
            'text': 'TEXT',
            'integer': 'INT',
            'int': 'INT',
            'int4': 'INT',
            'bigint': 'BIGINT',
            'int8': 'BIGINT',
            'smallint': 'SMALLINT',
            'int2': 'SMALLINT',
            'decimal': 'DECIMAL',
            'numeric': 'DECIMAL',
            'real': 'REAL',
            'float4': 'REAL',
            'double precision': 'DOUBLE',
            'float8': 'DOUBLE',
            'serial': 'SERIAL',
            'bigserial': 'BIGSERIAL',
            'smallserial': 'SMALLSERIAL',
            'boolean': 'BOOLEAN',
            'bool': 'BOOLEAN',
            'date': 'DATE',
            'time': 'TIME',
            'time without time zone': 'TIME',
            'time with time zone': 'TIMETZ',
            'timestamp': 'TIMESTAMP',
            'timestamp without time zone': 'TIMESTAMP',
            'timestamp with time zone': 'TIMESTAMPTZ',
            'interval': 'INTERVAL',
            'uuid': 'UUID',
            'json': 'JSON',
            'jsonb': 'JSONB',
            'xml': 'XML',
            'bytea': 'BYTEA',
            'inet': 'INET',
            'cidr': 'CIDR',
            'macaddr': 'MACADDR',
            'point': 'POINT',
            'line': 'LINE',
            'lseg': 'LSEG',
            'box': 'BOX',
            'path': 'PATH',
            'polygon': 'POLYGON',
            'circle': 'CIRCLE',
            'money': 'MONEY',
            'regclass': 'REGCLASS'
        }
    
    def parse_ddl_content(self, content: str) -> Dict:
        """DDL 내용을 파싱하여 테이블 정보를 반환"""
        # PostgreSQL CREATE TABLE 문들을 찾아서 파싱
        table_info = {}
        
        # CREATE TABLE 문을 정규식으로 찾기 (PostgreSQL 스키마.테이블명 형식 지원)
        create_table_pattern = r'CREATE\s+TABLE\s+(?:(\w+)\.)?(?:")?(\w+)(?:")?\s*\((.*?)\);'
        matches = re.finditer(create_table_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            schema_name = match.group(1)  # 스키마명 (예: public)
            table_name = match.group(2)   # 테이블명
            table_content = match.group(3)  # 테이블 정의 내용
            
            # 테이블명 정리
            clean_table_name = self._clean_identifier(table_name)
            
            # 컬럼과 제약조건 파싱
            columns, constraints = self._parse_postgresql_table_content(table_content)
            
            if columns:  # 컬럼이 있는 경우만 추가
                table_info[clean_table_name] = {
                    'name': clean_table_name,
                    'schema': schema_name,
                    'columns': columns,
                    'constraints': constraints
                }
        
        return table_info
    
    def _parse_create_table(self, statement: Statement) -> Optional[Dict]:
        """CREATE TABLE 문을 파싱 (fallback 용도)"""
        # PostgreSQL의 경우 문자열 기반 파싱을 주로 사용
        content = str(statement)
        table_info = self.parse_ddl_content(content)
        
        if table_info:
            # 첫 번째 테이블 반환
            return list(table_info.values())[0]
        
        return None
    
    def _clean_identifier(self, identifier: str) -> str:
        """식별자에서 따옴표 등 특수문자 제거"""
        # PostgreSQL의 큰따옴표 제거
        cleaned = identifier.strip('"\'`')
        
        # 스키마.테이블명에서 테이블명만 추출
        if '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) == 2:
                cleaned = parts[1].strip('"\'`')
        
        return cleaned
    
    def _parse_postgresql_table_content(self, content: str) -> Tuple[List[Dict], List[Dict]]:
        """PostgreSQL 테이블 정의 내용을 파싱"""
        columns = []
        constraints = []
        
        # 컬럼 정의들을 콤마로 분리 (단, 괄호 안의 콤마는 무시)
        items = self._split_table_items(content)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 제약조건인지 확인
            constraint = self._parse_postgresql_constraint(item)
            if constraint:
                constraints.append(constraint)
            else:
                # 컬럼 정의 파싱
                column = self._parse_postgresql_column(item)
                if column:
                    columns.append(column)
        
        return columns, constraints
    
    def _split_table_items(self, content: str) -> List[str]:
        """테이블 정의를 콤마로 분리 (괄호 안의 콤마는 무시)"""
        items = []
        current_item = ""
        paren_depth = 0
        quote_char = None
        
        i = 0
        while i < len(content):
            char = content[i]
            
            # 따옴표 처리
            if char in ['"', "'"] and (i == 0 or content[i-1] != '\\'):
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None
                current_item += char
            
            # 괄호 처리 (따옴표 안이 아닐 때만)
            elif quote_char is None:
                if char == '(':
                    paren_depth += 1
                    current_item += char
                elif char == ')':
                    paren_depth -= 1
                    current_item += char
                elif char == ',' and paren_depth == 0:
                    # 최상위 레벨의 콤마
                    if current_item.strip():
                        items.append(current_item.strip())
                    current_item = ""
                else:
                    current_item += char
            else:
                current_item += char
            
            i += 1
        
        # 마지막 아이템 추가
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def _parse_postgresql_column(self, item: str) -> Optional[Dict]:
        """PostgreSQL 컬럼 정의를 파싱"""
        # 기본 컬럼 패턴: "컬럼명" 데이터타입 [제약조건들]
        item = item.strip()
        
        # 컬럼명과 데이터 타입 추출
        parts = item.split()
        if len(parts) < 2:
            return None
        
        column_name = self._clean_identifier(parts[0])
        
        # 데이터 타입 추출 (여러 단어로 구성될 수 있음)
        data_type = ""
        type_end_idx = 1
        
        # PostgreSQL의 복합 데이터 타입 처리 (예: "character varying", "timestamp without time zone")
        for i in range(1, len(parts)):
            part = parts[i].upper()
            if part in ['NOT', 'NULL', 'DEFAULT', 'PRIMARY', 'UNIQUE', 'REFERENCES', 'CHECK']:
                break
            if data_type:
                data_type += " "
            data_type += parts[i]
            type_end_idx = i + 1
        
        # 데이터 타입 정규화
        data_type_clean = self._normalize_postgresql_type(data_type)
        
        # 속성들 파싱
        attributes = []
        default_value = None
        
        remaining_parts = parts[type_end_idx:]
        remaining_text = " ".join(remaining_parts).upper()
        
        if 'NOT NULL' in remaining_text:
            attributes.append('not null')
        
        if 'PRIMARY KEY' in remaining_text:
            attributes.append('pk')
        
        if 'UNIQUE' in remaining_text:
            attributes.append('unique')
        
        # DEFAULT 값 추출
        default_match = re.search(r'DEFAULT\s+([^,\s]+(?:\([^)]*\))?)', item, re.IGNORECASE)
        if default_match:
            default_value = default_match.group(1)
            # PostgreSQL 특수 DEFAULT 값 처리
            if default_value.upper() == 'CURRENT_TIMESTAMP':
                default_value = 'CURRENT_TIMESTAMP'
            elif 'nextval(' in default_value.lower():
                # SERIAL 타입의 시퀀스 DEFAULT는 자동 증가로 처리
                attributes.append('increment')
                default_value = None
        
        return {
            'name': column_name,
            'type': data_type_clean,
            'attributes': attributes,
            'default': default_value,
            'comment': None
        }
    
    def _normalize_postgresql_type(self, data_type: str) -> str:
        """PostgreSQL 데이터 타입을 정규화"""
        data_type_lower = data_type.lower().strip()
        
        # 괄호가 있는 타입 처리 (예: character varying(255))
        type_match = re.match(r'^([^(]+)(\(.+\))?$', data_type_lower)
        if type_match:
            base_type = type_match.group(1).strip()
            size_info = type_match.group(2) if type_match.group(2) else ""
            
            # 매핑된 타입 찾기
            if base_type in self.postgresql_type_mapping:
                return self.postgresql_type_mapping[base_type] + size_info
            else:
                return data_type  # 원본 반환
        
        # 매핑된 타입 찾기
        if data_type_lower in self.postgresql_type_mapping:
            return self.postgresql_type_mapping[data_type_lower]
        
        return data_type  # 원본 반환
    
    def _parse_postgresql_constraint(self, item: str) -> Optional[Dict]:
        """PostgreSQL 제약조건을 파싱"""
        item_upper = item.upper()
        
        # PRIMARY KEY 제약조건
        if 'PRIMARY KEY' in item_upper and 'CONSTRAINT' in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'primary_key',
                    'columns': columns
                }
        
        # FOREIGN KEY 제약조건
        if 'FOREIGN KEY' in item_upper and 'REFERENCES' in item_upper:
            return self._parse_postgresql_foreign_key(item)
        
        # UNIQUE 제약조건
        if 'UNIQUE' in item_upper and 'CONSTRAINT' in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'unique',
                    'columns': columns
                }
        
        return None
    
    def _parse_postgresql_foreign_key(self, item: str) -> Optional[Dict]:
        """PostgreSQL FOREIGN KEY 제약조건 파싱"""
        # FOREIGN KEY 패턴 매칭
        fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+(?:(\w+)\.)?(?:")?(\w+)(?:")?\s*\(([^)]+)\)'
        match = re.search(fk_pattern, item, re.IGNORECASE)
        
        if match:
            columns = [self._clean_identifier(col.strip()) for col in match.group(1).split(',')]
            ref_schema = match.group(2)  # 참조 스키마 (있을 경우)
            ref_table = self._clean_identifier(match.group(3))
            ref_columns = [self._clean_identifier(col.strip()) for col in match.group(4).split(',')]
            
            return {
                'type': 'foreign_key',
                'columns': columns,
                'ref_table': ref_table,
                'ref_columns': ref_columns,
                'ref_schema': ref_schema
            }
        
        return None
    
    def _extract_columns_from_string(self, item: str) -> List[str]:
        """문자열에서 컬럼명 추출"""
        # 괄호 안의 내용 찾기
        match = re.search(r'\(([^)]+)\)', item)
        if not match:
            return []
        
        columns_str = match.group(1)
        columns = [self._clean_identifier(col.strip()) for col in columns_str.split(',')]
        return [col for col in columns if col]
    
    def _parse_column_definition(self, tokens: List) -> Optional[Dict]:
        """컬럼 정의를 파싱 (베이스 클래스 구현)"""
        # PostgreSQL의 경우 문자열 기반 파싱을 사용하므로 이 메서드는 사용하지 않음
        return None
    
    def _parse_constraint(self, tokens: List) -> Optional[Dict]:
        """제약조건을 파싱 (베이스 클래스 구현)"""
        # PostgreSQL의 경우 문자열 기반 파싱을 사용하므로 이 메서드는 사용하지 않음
        return None

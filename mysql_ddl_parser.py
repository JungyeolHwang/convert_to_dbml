"""
MySQL/MariaDB DDL 파서
CREATE TABLE 문을 파싱하여 테이블 정보를 추출합니다.
"""

import re
import sqlparse
from sqlparse.sql import Statement, Token, TokenList
from sqlparse.tokens import Keyword, Name, Literal, Punctuation
from typing import Dict, List, Optional, Tuple
from base_ddl_parser import BaseDDLParser


class MySQLDDLParser(BaseDDLParser):
    """MySQL/MariaDB DDL 파일을 파싱하여 테이블 구조 정보를 추출하는 클래스"""
    
    def __init__(self):
        super().__init__()
        # MySQL/MariaDB 데이터 타입 매핑
        self.mysql_type_mapping = {
            'tinyint': 'TINYINT',
            'smallint': 'SMALLINT',
            'mediumint': 'MEDIUMINT',
            'int': 'INT',
            'integer': 'INT',
            'bigint': 'BIGINT',
            'decimal': 'DECIMAL',
            'numeric': 'DECIMAL',
            'float': 'FLOAT',
            'double': 'DOUBLE',
            'bit': 'BIT',
            'char': 'CHAR',
            'varchar': 'VARCHAR',
            'binary': 'BINARY',
            'varbinary': 'VARBINARY',
            'tinyblob': 'TINYBLOB',
            'blob': 'BLOB',
            'mediumblob': 'MEDIUMBLOB',
            'longblob': 'LONGBLOB',
            'tinytext': 'TINYTEXT',
            'text': 'TEXT',
            'mediumtext': 'MEDIUMTEXT',
            'longtext': 'LONGTEXT',
            'date': 'DATE',
            'time': 'TIME',
            'datetime': 'DATETIME',
            'timestamp': 'TIMESTAMP',
            'year': 'YEAR',
            'enum': 'ENUM',
            'set': 'SET',
            'json': 'JSON'
        }
    
    def parse_ddl_content(self, content: str) -> Dict:
        """DDL 내용을 파싱하여 테이블 정보를 반환"""
        # SQL 파싱
        parsed = sqlparse.parse(content)
        
        table_info = {}
        
        for statement in parsed:
            if statement.get_type() == 'CREATE':
                # CREATE TABLE만 처리하도록 필터링
                if self._is_create_table_statement(statement):
                    table_data = self._parse_create_table(statement)
                    if table_data:
                        table_info[table_data['name']] = table_data
        
        return table_info
    
    def _is_create_table_statement(self, statement) -> bool:
        """CREATE 문이 CREATE TABLE인지 확인 (PROCEDURE, FUNCTION 등 제외)"""
        tokens = list(statement.flatten())
        
        # CREATE 다음에 오는 키워드 확인
        create_found = False
        for token in tokens:
            if token.ttype in (Keyword, Keyword.DDL) and token.value.upper() == 'CREATE':
                create_found = True
                continue
            
            if create_found and token.ttype in (Keyword, Keyword.DDL):
                keyword = token.value.upper()
                # TABLE인 경우만 True 반환
                if keyword == 'TABLE':
                    return True
                # PROCEDURE, FUNCTION, VIEW 등은 False 반환
                elif keyword in ('PROCEDURE', 'FUNCTION', 'VIEW', 'INDEX', 'TRIGGER', 'EVENT'):
                    return False
        
        return False
    
    def _parse_create_table(self, statement: Statement) -> Optional[Dict]:
        """CREATE TABLE 문을 파싱"""
        tokens = list(statement.flatten())
        
        # CREATE TABLE 확인
        create_found = False
        table_found = False
        table_name = None
        
        for i, token in enumerate(tokens):
            if token.ttype in (Keyword, Keyword.DDL) and token.value.upper() == 'CREATE':
                create_found = True
            elif create_found and token.ttype is Keyword and token.value.upper() == 'TABLE':
                table_found = True
            elif table_found and token.ttype is Name:
                table_name = self._clean_identifier(token.value)
                break
            elif table_found and token.value.strip() and not token.value.isspace() and token.value not in ['(', ')', ',', ';']:
                # 백틱으로 감싸진 테이블명 등을 처리
                table_name = self._clean_identifier(token.value)
                break
        
        if not table_name:
            return None
        
        # 테이블 정의 부분 추출
        table_def_start = -1
        paren_count = 0
        table_def_tokens = []
        
        # sqlparse가 큰 토큰으로 만든 경우를 위한 대안 처리
        table_content_token = None
        for token in tokens:
            if '(' in token.value and ')' in token.value and 'COMMENT' in token.value:
                # 테이블 정의가 포함된 토큰 발견
                table_content_token = token.value
                break
        
        if table_content_token:
            # 문자열 기반으로 직접 파싱
            columns, constraints = self._parse_table_definition_from_string(table_content_token)
        else:
            # 전체 statement를 문자열로 변환해서 파싱 (ENUM 처리를 위해)
            full_statement = str(statement)
            columns, constraints = self._parse_table_definition_from_string(full_statement)
        
        return {
            'name': table_name,
            'columns': columns,
            'constraints': constraints
        }
    
    def _clean_identifier(self, identifier: str) -> str:
        """식별자에서 백틱, 따옴표, @문자 등 특수문자 제거"""
        # 백틱이나 따옴표 제거
        cleaned = identifier.strip('`"\'')
        # @문자 제거 (예: table@schema -> table)
        if '@' in cleaned:
            cleaned = cleaned.split('@')[0]
        return cleaned
    
    def _simple_comma_split(self, table_content: str) -> List[str]:
        """간단한 콤마 분리 로직 (백업용)"""
        items = []
        current_item = ""
        in_comment = False
        quote_char = None
        paren_depth = 0
        
        i = 0
        while i < len(table_content):
            char = table_content[i]
            
            # COMMENT 키워드 감지
            if not in_comment and not quote_char and table_content[i:i+7].upper() == 'COMMENT':
                if i + 7 < len(table_content) and table_content[i+7] in [' ', '\t', "'", '"']:
                    in_comment = True
                current_item += char
                i += 1
                continue
            
            # 따옴표 처리
            elif char in ["'", '"'] and (i == 0 or table_content[i-1] != '\\'):
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None
                    if in_comment:
                        in_comment = False
                current_item += char
                
            # 괄호 처리
            elif char == '(' and quote_char is None:
                paren_depth += 1
                current_item += char
                
            elif char == ')' and quote_char is None:
                paren_depth -= 1
                current_item += char
                
            # 콤마 분리
            elif char == ',' and quote_char is None and paren_depth == 0 and not in_comment:
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
                
            else:
                current_item += char
            
            i += 1
        
        # 마지막 아이템 추가
        if current_item.strip():
            items.append(current_item.strip())
        
        return items
    
    def _preprocess_table_content(self, table_content: str) -> str:
        """테이블 내용 전처리 - COMMENT 내부의 복잡한 문자를 단순화"""
        # COMMENT '복잡한내용' 을 COMMENT 'comment' 로 단순화
        processed = re.sub(r"COMMENT\s*'[^']*'", "COMMENT 'comment'", table_content, flags=re.IGNORECASE)
        # COMMENT "복잡한내용" 도 처리
        processed = re.sub(r'COMMENT\s*"[^"]*"', 'COMMENT "comment"', processed, flags=re.IGNORECASE)
        return processed
    
    def _parse_table_definition_from_string(self, content: str) -> Tuple[List[Dict], List[Dict]]:
        """문자열에서 직접 테이블 정의를 파싱"""
        # 괄호 안의 내용만 추출
        start = content.find('(')
        end = content.rfind(')')
        if start == -1 or end == -1:
            return [], []
        
        table_content = content[start+1:end]
        
        # 전처리: COMMENT 부분에서 복잡한 내용 제거하고 단순화
        table_content = self._preprocess_table_content(table_content)
        
        # 간단한 콤마 분리 사용
        items = self._simple_comma_split(table_content)
        
        columns = []
        constraints = []
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 제약조건 확인
            constraint = self._parse_constraint_from_string(item)
            if constraint:
                constraints.append(constraint)
            else:
                # 컬럼 정의
                column = self._parse_column_from_string(item)
                if column:
                    columns.append(column)
        
        return columns, constraints
    
    def _parse_table_definition(self, tokens: List[Token]) -> Tuple[List[Dict], List[Dict]]:
        """토큰 리스트에서 테이블 정의를 파싱"""
        columns = []
        constraints = []
        
        current_tokens = []
        
        for token in tokens:
            if token.value == ',':
                if current_tokens:
                    # 현재 토큰들로 컬럼이나 제약조건 파싱 시도
                    constraint = self._parse_constraint(current_tokens)
                    if constraint:
                        constraints.append(constraint)
                    else:
                        column = self._parse_column_definition(current_tokens)
                        if column:
                            columns.append(column)
                    current_tokens = []
            else:
                current_tokens.append(token)
        
        # 마지막 토큰들 처리
        if current_tokens:
            constraint = self._parse_constraint(current_tokens)
            if constraint:
                constraints.append(constraint)
            else:
                column = self._parse_column_definition(current_tokens)
                if column:
                    columns.append(column)
        
        return columns, constraints
    
    def _parse_column_definition(self, tokens: List[Token]) -> Optional[Dict]:
        """컬럼 정의를 파싱"""
        if not tokens:
            return None
        
        token_values = [t.value for t in tokens if t.value.strip()]
        if len(token_values) < 2:
            return None
        
        column_name = self._clean_identifier(token_values[0])
        data_type = token_values[1]
        
        # 나머지 속성들 파싱
        attributes = []
        default_value = None
        comment = None
        
        i = 2
        while i < len(token_values):
            token = token_values[i]
            token_upper = token.upper()
            
            if token_upper == 'NOT' and i + 1 < len(token_values) and token_values[i + 1].upper() == 'NULL':
                attributes.append('not null')
                i += 2
            elif token_upper == 'NULL':
                # NULL은 기본값이므로 특별히 저장하지 않음
                i += 1
            elif token_upper == 'AUTO_INCREMENT':
                attributes.append('increment')
                i += 1
            elif token_upper == 'PRIMARY' and i + 1 < len(token_values) and token_values[i + 1].upper() == 'KEY':
                attributes.append('pk')
                i += 2
            elif token_upper == 'UNIQUE':
                attributes.append('unique')
                i += 1
            elif token_upper == 'DEFAULT':
                if i + 1 < len(token_values):
                    default_value = token_values[i + 1]
                    i += 2
                else:
                    i += 1
            elif token_upper == 'COMMENT':
                if i + 1 < len(token_values):
                    comment = token_values[i + 1].strip("'\"")
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        return {
            'name': column_name,
            'type': data_type,
            'attributes': attributes,
            'default': default_value,
            'comment': comment
        }
    
    def _parse_constraint(self, tokens: List[Token]) -> Optional[Dict]:
        """제약조건을 파싱"""
        if not tokens:
            return None
        
        token_values = [t.value for t in tokens if t.value.strip()]
        
        # PRIMARY KEY 처리
        if any(t.upper() == 'PRIMARY' for t in token_values) and any(t.upper() == 'KEY' for t in token_values):
            # 컬럼명 추출
            columns = self._extract_columns_from_constraint(token_values)
            if columns:
                return {
                    'type': 'primary_key',
                    'columns': columns
                }
        
        # FOREIGN KEY 처리
        if any(t.upper() == 'FOREIGN' for t in token_values) and any(t.upper() == 'KEY' for t in token_values):
            return self._parse_foreign_key_constraint(token_values)
        
        # UNIQUE 처리
        if any(t.upper() == 'UNIQUE' for t in token_values):
            columns = self._extract_columns_from_constraint(token_values)
            if columns:
                return {
                    'type': 'unique',
                    'columns': columns
                }
        
        return None
    
    def _parse_column_from_string(self, item: str) -> Optional[Dict]:
        """문자열에서 컬럼 정의를 파싱"""
        # PARTITION 구문 필터링 (MySQL 파티셔닝은 DBML에서 지원하지 않음)
        item_stripped = item.strip()
        if item_stripped.upper().startswith('PARTITION '):
            return None
        
        # 컬럼명과 기본 타입 추출
        column_match = re.match(r'^\s*([`\w]+)\s+(\w+)', item_stripped)
        if not column_match:
            return None
        
        column_name = self._clean_identifier(column_match.group(1))
        base_type = column_match.group(2).upper()
        
        # ENUM이나 SET 타입의 경우 전체 문자열에서 괄호 부분을 찾기
        if base_type in ['ENUM', 'SET']:
            size_info = self._extract_enum_values(item, base_type)
            if size_info:
                data_type = f"{base_type}({size_info})"
            else:
                data_type = base_type
        else:
            # 일반 타입의 경우 원본에서 타입 부분 전체 추출
            type_pattern = rf'\b{re.escape(base_type)}\b(\([^)]*\))?'
            type_match = re.search(type_pattern, item, re.IGNORECASE)
            if type_match and type_match.group(1):
                data_type = f"{base_type}{type_match.group(1)}"
            else:
                data_type = base_type
        
        # 속성들 파싱
        attributes = []
        default_value = None
        comment = None
        
        item_upper = item.upper()
        
        if 'NOT NULL' in item_upper:
            attributes.append('not null')
        if 'AUTO_INCREMENT' in item_upper:
            attributes.append('increment')
        if 'PRIMARY KEY' in item_upper:
            attributes.append('pk')
        if 'UNIQUE' in item_upper and 'UNIQUE KEY' not in item_upper:
            attributes.append('unique')
        
        # DEFAULT 값 추출 (한글 포함)
        default_match = re.search(r"DEFAULT\s+['\"]([^'\"]*)['\"]", item, re.IGNORECASE)
        if default_match:
            default_value = f"'{default_match.group(1)}'"
        else:
            # 따옴표 없는 DEFAULT 값도 처리
            default_match = re.search(r'DEFAULT\s+([^,\s]+)', item, re.IGNORECASE)
            if default_match:
                default_value = default_match.group(1)
        
        # COMMENT 추출
        comment_match = re.search(r"COMMENT\s+['\"]([^'\"]*)['\"]", item, re.IGNORECASE)
        if comment_match:
            comment = comment_match.group(1)
        
        return {
            'name': column_name,
            'type': data_type,
            'attributes': attributes,
            'default': default_value,
            'comment': comment
        }
    
    def _extract_enum_values(self, item: str, base_type: str) -> Optional[str]:
        """ENUM/SET 타입에서 값들을 추출 (중첩된 괄호 처리)"""
        # ENUM 또는 SET 시작 위치 찾기
        type_start = item.upper().find(base_type.upper())
        if type_start == -1:
            return None
        
        # 타입명 다음의 첫 번째 '(' 찾기
        paren_start = item.find('(', type_start)
        if paren_start == -1:
            return None
        
        # 균형 잡힌 괄호 찾기
        bracket_count = 0
        quote_char = None
        i = paren_start
        
        while i < len(item):
            char = item[i]
            
            # 따옴표 처리
            if char in ("'", '"') and (i == 0 or item[i-1] != '\\'):
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None
            # 따옴표 안이 아닐 때만 괄호 카운트
            elif quote_char is None:
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # 균형 잡힌 괄호 완성
                        return item[paren_start + 1:i]
            
            i += 1
        
        return None
    
    def _parse_constraint_from_string(self, item: str) -> Optional[Dict]:
        """문자열에서 제약조건을 파싱"""
        item_upper = item.upper()
        
        # PRIMARY KEY 처리
        if 'PRIMARY KEY' in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'primary_key',
                    'columns': columns
                }
        
        # FOREIGN KEY 처리
        if 'FOREIGN KEY' in item_upper:
            return self._parse_foreign_key_from_string(item)
        
        # UNIQUE 처리 (UNIQUE KEY 또는 UNIQUE INDEX)
        if ('UNIQUE KEY' in item_upper or 'UNIQUE INDEX' in item_upper) and 'FOREIGN' not in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'unique',
                    'columns': columns
                }
        
        # FULLTEXT 처리 (FULLTEXT KEY 또는 FULLTEXT INDEX)
        if 'FULLTEXT KEY' in item_upper or 'FULLTEXT INDEX' in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'fulltext',
                    'columns': columns
                }
        
        # INDEX/KEY 처리 (일반 인덱스) - 컬럼 정의와 구분하기 위해 더 정확한 패턴 매칭
        if (item_upper.strip().startswith('KEY ') or item_upper.strip().startswith('INDEX ') or 
            ' KEY ' in item_upper or ' INDEX ' in item_upper) and 'FOREIGN' not in item_upper and 'PRIMARY' not in item_upper and 'UNIQUE' not in item_upper and 'FULLTEXT' not in item_upper:
            columns = self._extract_columns_from_string(item)
            if columns:
                return {
                    'type': 'index',
                    'columns': columns
                }
        
        return None
    
    def _extract_columns_from_constraint(self, token_values: List[str]) -> List[str]:
        """제약조건에서 컬럼명 추출"""
        # 괄호 안의 컬럼명들 찾기
        in_parens = False
        columns = []
        current_column = ""
        
        for token in token_values:
            if '(' in token:
                in_parens = True
                current_column = token.replace('(', '').replace(')', '')
                if current_column:
                    columns.append(self._clean_identifier(current_column))
                current_column = ""
            elif ')' in token:
                in_parens = False
                current_column += token.replace(')', '')
                if current_column:
                    columns.append(self._clean_identifier(current_column))
                break
            elif in_parens:
                if ',' in token:
                    parts = token.split(',')
                    current_column += parts[0]
                    if current_column:
                        columns.append(self._clean_identifier(current_column))
                    current_column = parts[1] if len(parts) > 1 else ""
                else:
                    current_column += token
        
        return columns
    
    def _extract_columns_from_string(self, item: str) -> List[str]:
        """문자열에서 컬럼명 추출 (인덱스 길이 및 정렬 순서 처리)"""
        # 중첩된 괄호를 고려한 괄호 매칭
        start_idx = item.find('(')
        if start_idx == -1:
            return []
        
        # 균형 잡힌 괄호 찾기
        paren_count = 0
        end_idx = -1
        
        for i in range(start_idx, len(item)):
            if item[i] == '(':
                paren_count += 1
            elif item[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    end_idx = i
                    break
        
        if end_idx == -1:
            return []
        
        columns_str = item[start_idx + 1:end_idx]
        
        columns = []
        
        # 단계별 처리 방식
        # 1. 괄호를 고려한 스마트 콤마 분리
        parts = self._smart_comma_split(columns_str)
        
        for part in parts:
            part = part.strip()
            
            # 함수형 인덱스 완전 제거 (스마트 분리 후에)
            if self._is_functional_index(part):
                continue
            
            # 빈 파트나 무효한 파트 건너뛰기
            if not part or part in ['', '10)', "'", '"']:
                continue
            
            # 2. 각 부분에서 컬럼명만 추출
            # `column_name`(length) -> column_name
            # column_name ASC/DESC -> column_name
            
            # (length) 부분 제거 (단순한 괄호만)
            part = re.sub(r'\(\d+\)', '', part)
            
            # ASC/DESC 제거
            part = re.sub(r'\s+(ASC|DESC)\s*$', '', part, flags=re.IGNORECASE)
            
            # 백틱 등 제거
            col_name = self._clean_identifier(part.strip())
            
            if col_name:
                columns.append(col_name)
                
        return columns
    
    def _smart_comma_split(self, text: str) -> List[str]:
        """괄호와 따옴표를 고려한 스마트 콤마 분리"""
        parts = []
        current_part = ""
        paren_depth = 0
        quote_char = None
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # 따옴표 처리
            if char in ("'", '"') and (i == 0 or text[i-1] != '\\'):
                if quote_char is None:
                    quote_char = char
                elif quote_char == char:
                    quote_char = None
            
            # 괄호 처리 (따옴표 안이 아닐 때만)
            elif quote_char is None:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ',' and paren_depth == 0:
                    # 괄호 밖의 콤마만 분리점으로 사용
                    parts.append(current_part.strip())
                    current_part = ""
                    i += 1
                    continue
            
            current_part += char
            i += 1
        
        # 마지막 부분 추가
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _is_functional_index(self, part: str) -> bool:
        """함수형 인덱스인지 확인"""
        part_lower = part.lower()
        
        # 1. 알려진 MySQL 함수들이 포함된 경우
        mysql_functions = ['replace', 'right', 'left', 'substr', 'substring', 'concat', 
                          'upper', 'lower', 'date_format', 'year', 'month', 'day']
        if any(func in part_lower for func in mysql_functions):
            return True
        
        # 2. 특수 문자 패턴 (UTF8 문자셋, 콜론 등)
        if '_utf8mb3' in part or '_utf8mb4' in part:
            return True
        
        # 3. 함수 호출 패턴 (괄호 안에 백틱이나 특수 문자)
        if '(' in part and ('`' in part or ':' in part or '%' in part):
            return True
        
        return False
    
    def _parse_foreign_key_constraint(self, token_values: List[str]) -> Optional[Dict]:
        """FOREIGN KEY 제약조건 파싱"""
        # 간단한 FOREIGN KEY 파싱 로직
        # 실제 구현에서는 더 정교한 파싱이 필요할 수 있음
        columns = []
        ref_table = None
        ref_columns = []
        
        # 이는 기본적인 구현입니다. 실제로는 더 복잡한 파싱이 필요할 수 있습니다.
        return {
            'type': 'foreign_key',
            'columns': columns,
            'ref_table': ref_table,
            'ref_columns': ref_columns
        }
    
    def _parse_foreign_key_from_string(self, item: str) -> Optional[Dict]:
        """문자열에서 FOREIGN KEY 제약조건 파싱"""
        # FOREIGN KEY 패턴 매칭
        fk_pattern = r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+([^\s(]+)\s*\(([^)]+)\)'
        match = re.search(fk_pattern, item, re.IGNORECASE)
        
        if match:
            columns = [self._clean_identifier(col.strip()) for col in match.group(1).split(',')]
            ref_table = self._clean_identifier(match.group(2))
            ref_columns = [self._clean_identifier(col.strip()) for col in match.group(3).split(',')]
            
            return {
                'type': 'foreign_key',
                'columns': columns,
                'ref_table': ref_table,
                'ref_columns': ref_columns
            }
        
        return None

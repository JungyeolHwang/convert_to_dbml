"""
MySQL/MariaDB DDL 파서
CREATE TABLE 문을 파싱하여 테이블 정보를 추출합니다.
"""

import re
import sqlparse
from sqlparse.sql import Statement, Token, TokenList
from sqlparse.tokens import Keyword, Name, Literal, Punctuation
from typing import Dict, List, Optional, Tuple


class DDLParser:
    """DDL 파일을 파싱하여 테이블 구조 정보를 추출하는 클래스"""
    
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
    
    def parse_ddl_content(self, content: str) -> Dict:
        """DDL 내용을 파싱하여 테이블 정보를 반환"""
        # SQL 파싱
        parsed = sqlparse.parse(content)
        
        table_info = {}
        
        for statement in parsed:
            if statement.get_type() == 'CREATE':
                table_data = self._parse_create_table(statement)
                if table_data:
                    table_info[table_data['name']] = table_data
        
        return table_info
    
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
            # 기존 토큰 기반 방식
            for i, token in enumerate(tokens):
                if token.value == '(' and table_def_start == -1:
                    table_def_start = i
                    paren_count = 1
                    continue
                elif table_def_start != -1:
                    if token.value == '(':
                        paren_count += 1
                    elif token.value == ')':
                        paren_count -= 1
                    
                    if paren_count == 0:
                        break
                    
                    table_def_tokens.append(token)
            
            if not table_def_tokens:
                return None
            
            # 컬럼과 제약조건 파싱
            columns, constraints = self._parse_table_definition(table_def_tokens)
        
        return {
            'name': table_name,
            'columns': columns,
            'constraints': constraints
        }
    
    def _parse_table_definition(self, tokens: List[Token]) -> Tuple[List[Dict], List[Dict]]:
        """테이블 정의 내용을 파싱하여 컬럼과 제약조건을 추출"""
        # 토큰들을 공백으로 연결하여 더 안전하게 처리
        content = ' '.join(token.value for token in tokens if token.value.strip())
        
        # 정규식으로 더 정확하게 항목 분리
        # 주석이 있는 경우도 고려하여 분리
        items = []
        
        # 괄호 내용을 찾아서 콤마로 분리 (주석 내 콤마는 무시)
        in_quotes = False
        quote_char = None
        current_item = ""
        paren_depth = 0
        
        i = 0
        while i < len(content):
            char = content[i]
            
            # 따옴표 처리
            if char in ["'", '"'] and (i == 0 or content[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            
            # 괄호 깊이 추적
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            
            # 콤마로 분리 (따옴표나 괄호 안이 아닐 때만)
            elif char == ',' and not in_quotes and paren_depth == 0:
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
                i += 1
                continue
            
            current_item += char
            i += 1
        
        # 마지막 항목 추가
        if current_item.strip():
            items.append(current_item.strip())
        
        columns = []
        constraints = []
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 주석이나 잘못된 라인 필터링
            if (item.startswith('--') or item.startswith('/*') or 
                '한글' in item or '프로토콜' in item or '해당' in item or
                not any(c.isalpha() for c in item)):  # 알파벳이 하나도 없는 라인 스킵
                continue
            
            # 제약조건 체크 (PRIMARY KEY, FOREIGN KEY, INDEX, UNIQUE 등)
            if any(keyword in item.upper() for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'INDEX', 'UNIQUE KEY', 'KEY']):
                constraint = self._parse_constraint(item)
                if constraint:
                    constraints.append(constraint)
            else:
                # 컬럼 정의로 파싱
                column = self._parse_column_definition(item)
                if column:
                    columns.append(column)
        
        return columns, constraints
    
    def _parse_table_definition_from_string(self, content: str) -> Tuple[List[Dict], List[Dict]]:
        """문자열에서 직접 테이블 정의를 파싱"""
        # 괄호 안의 내용만 추출
        start = content.find('(')
        end = content.rfind(')')
        if start == -1 or end == -1:
            return [], []
        
        table_content = content[start+1:end]
        
        # 정교한 콤마 분리 (COMMENT 내부의 콤마는 무시)
        items = []
        current_item = ""
        in_comment = False
        quote_char = None
        paren_depth = 0
        
        i = 0
        while i < len(table_content):
            char = table_content[i]
            
            # COMMENT 키워드 감지
            if not in_comment and table_content[i:i+7].upper() == 'COMMENT':
                in_comment = True
                current_item += char
                i += 1
                continue
            
            # 따옴표 처리 (COMMENT 안에서)
            elif in_comment and char in ["'", '"'] and (i == 0 or table_content[i-1] != '\\'):
                if quote_char is None:
                    quote_char = char
                elif char == quote_char:
                    quote_char = None
                    if i + 1 < len(table_content) and table_content[i + 1] not in ["'", '"']:
                        in_comment = False  # COMMENT 끝
            
            # 괄호 깊이 추적 (COMMENT 밖에서)
            elif not in_comment:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ',' and paren_depth == 0:
                    # 최상위 레벨의 콤마에서 분리
                    if current_item.strip():
                        items.append(current_item.strip())
                    current_item = ""
                    i += 1
                    continue
            
            current_item += char
            i += 1
        
        # 마지막 항목 추가
        if current_item.strip():
            items.append(current_item.strip())
        
        # 각 항목을 컬럼 또는 제약조건으로 분류
        columns = []
        constraints = []
        
        for item in items:
            item = item.strip()
            if not item:
                continue
            
            # 주석이나 잘못된 라인 필터링
            if (item.startswith('--') or item.startswith('/*') or 
                '한글' in item or '프로토콜' in item or '해당' in item or
                not any(c.isalpha() for c in item)):  # 알파벳이 하나도 없는 라인 스킵
                continue
            
            # 제약조건 체크 (PRIMARY KEY, FOREIGN KEY, INDEX, UNIQUE 등)
            if any(keyword in item.upper() for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'INDEX', 'UNIQUE KEY', 'KEY']):
                constraint = self._parse_constraint(item)
                if constraint:
                    constraints.append(constraint)
            else:
                # 컬럼 정의로 파싱
                column = self._parse_column_definition(item)
                if column:
                    columns.append(column)
        
        return columns, constraints
    
    def _parse_column_definition(self, definition: str) -> Optional[Dict]:
        """컬럼 정의를 파싱"""
        # 정규식으로 컬럼명과 타입을 더 정확하게 추출
        # 형태: `column_name` type [속성들...] [COMMENT '...']
        column_match = re.match(r'^\s*[`"]?([^`"\s]+)[`"]?\s+([A-Za-z]+(?:\([^)]*\))?)', definition.strip())
        if not column_match:
            return None
        
        column_name = self._clean_identifier(column_match.group(1))
        data_type = column_match.group(2)
        
        # 데이터 타입에서 크기 정보 추출
        type_match = re.match(r'([A-Za-z]+)(\(([^)]+)\))?', data_type)
        if type_match:
            base_type = type_match.group(1).upper()
            size_info = type_match.group(3) if type_match.group(3) else None
        else:
            base_type = data_type.upper()
            size_info = None
        
        # 컬럼 속성 파싱 - COMMENT 부분을 제외하고 파싱
        # COMMENT 구간을 찾아서 제외
        comment_match = re.search(r'COMMENT\s+[\'"].*?[\'"]', definition, re.IGNORECASE | re.DOTALL)
        if comment_match:
            # COMMENT 부분을 제외한 속성 부분만 추출
            attributes_part = definition[:comment_match.start()].upper()
        else:
            attributes_part = definition.upper()
        
        column_info = {
            'name': column_name,
            'type': base_type,
            'size': size_info,
            'nullable': 'NOT NULL' not in attributes_part,
            'auto_increment': 'AUTO_INCREMENT' in attributes_part,
            'primary_key': 'PRIMARY KEY' in attributes_part,
            'unique': 'UNIQUE' in attributes_part,
            'default': None
        }
        
        # DEFAULT 값 추출 (더 정확한 파싱)
        # sqlparse가 공백을 추가하는 경우를 고려하여 날짜/시간 형식 매칭
        default_match = re.search(r'DEFAULT\s+([\'\"].*?[\'\"]|\d{4}\s*-\s*\d{2}\s*-\s*\d{2}(?:\s+\d{2}:\d{2}:\d{2})?|\d{2}:\d{2}:\d{2}|[^\s,]+)', attributes_part, re.IGNORECASE)
        if default_match:
            default_val = default_match.group(1).strip()
            # sqlparse로 인한 공백 제거 (날짜/시간 형식에서)
            default_val = re.sub(r'\s+', '', default_val) if re.match(r'\d+\s*[-:]\s*\d+', default_val) else default_val
            # 따옴표로 감싸진 문자열 처리
            if (default_val.startswith("'") and default_val.endswith("'")) or \
               (default_val.startswith('"') and default_val.endswith('"')):
                # 따옴표 제거하고 이스케이프 문자 처리
                default_val = default_val[1:-1]
                default_val = default_val.replace("\\'", "'").replace('\\"', '"')
            column_info['default'] = default_val
        
        return column_info
    
    def _parse_constraint(self, definition: str) -> Optional[Dict]:
        """제약조건을 파싱"""
        definition_upper = definition.upper()
        
        if 'PRIMARY KEY' in definition_upper:
            # PRIMARY KEY 추출
            columns_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', definition_upper)
            if columns_match:
                columns = [col.strip().strip('`') for col in columns_match.group(1).split(',')]
                return {
                    'type': 'primary_key',
                    'columns': columns
                }
        
        elif 'FOREIGN KEY' in definition_upper:
            # FOREIGN KEY 추출 - 대소문자 보존을 위해 원본 문자열에서 추출
            fk_match = re.search(r'FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([^\s(]+)\s*\(([^)]+)\)', definition, re.IGNORECASE)
            if fk_match:
                columns = [col.strip().strip('`') for col in fk_match.group(1).split(',')]
                ref_table = fk_match.group(2).strip('`')
                ref_columns = [col.strip().strip('`') for col in fk_match.group(3).split(',')]
                
                return {
                    'type': 'foreign_key',
                    'columns': columns,
                    'ref_table': ref_table,
                    'ref_columns': ref_columns
                }
        
        elif 'UNIQUE' in definition_upper:
            # UNIQUE 제약조건 추출 - 더 정확한 파싱
            unique_match = re.search(r'UNIQUE\s+(?:KEY\s+)?(?:`[^`]*`\s+)?\(([^)]+)\)', definition_upper)
            if unique_match:
                columns_str = unique_match.group(1)
                # 컬럼명만 추출하고 크기 정보나 특수 문자 제거
                columns = []
                for col in columns_str.split(','):
                    col = col.strip().strip('`')
                    # 크기 정보 제거 (예: column_name(767) -> column_name)
                    col = re.sub(r'\(\d+\)', '', col)
                    # 특수 문자나 한글이 포함된 경우 스킵
                    if col and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                        columns.append(col)
                
                if columns:  # 유효한 컬럼이 있을 때만 반환
                    return {
                        'type': 'unique',
                        'columns': columns
                    }
        
        elif 'KEY' in definition_upper and 'PRIMARY' not in definition_upper and 'FOREIGN' not in definition_upper:
            # 일반 INDEX 추출 - 더 정확한 파싱
            # KEY `index_name` (`column`), KEY (`column`) 등 다양한 형태 지원
            key_match = re.search(r'KEY\s+(?:`[^`]*`\s+)?\(([^)]+)\)', definition_upper)
            if key_match:
                columns_str = key_match.group(1)
                # 컬럼명만 추출하고 크기 정보나 특수 문자 제거
                columns = []
                for col in columns_str.split(','):
                    col = col.strip().strip('`')
                    # 크기 정보 제거 (예: column_name(767) -> column_name)
                    col = re.sub(r'\(\d+\)', '', col)
                    # 특수 문자나 한글이 포함된 경우 스킵
                    if col and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                        columns.append(col)
                
                if columns:  # 유효한 컬럼이 있을 때만 반환
                    return {
                        'type': 'index',
                        'columns': columns
                    }
        
        return None
    
    def _clean_identifier(self, identifier: str) -> str:
        """식별자에서 백틱, 따옴표, @문자 등 특수문자 제거"""
        # 백틱이나 따옴표 제거
        cleaned = identifier.strip('`"\'')
        # @문자 제거 (예: table@schema -> table)
        if '@' in cleaned:
            cleaned = cleaned.split('@')[0]
        return cleaned


if __name__ == "__main__":
    # 테스트 코드
    parser = DDLParser()
    
    test_ddl = """
    CREATE TABLE `users` (
        `id` bigint(20) NOT NULL AUTO_INCREMENT,
        `username` varchar(50) NOT NULL,
        `email` varchar(100) UNIQUE,
        `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        UNIQUE KEY `unique_email` (`email`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    result = parser.parse_ddl_content(test_ddl)
    print("파싱 결과:")
    for table_name, table_info in result.items():
        print(f"테이블: {table_name}")
        print(f"컬럼: {table_info['columns']}")
        print(f"제약조건: {table_info['constraints']}")
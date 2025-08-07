"""
DDL 데이터를 DBML 형식으로 변환하는 컨버터
"""

from typing import Dict, List, Optional, Tuple
import re
import os
from pathlib import Path


class DBMLConverter:
    """DDL 파싱 결과를 DBML 형식으로 변환하는 클래스"""
    
    def __init__(self):
        # MySQL 타입을 DBML 타입으로 매핑
        self.type_mapping = {
            'BIGINT': 'bigint',
            'INT': 'int',
            'INTEGER': 'int',
            'SMALLINT': 'smallint',
            'TINYINT': 'tinyint',
            'DECIMAL': 'decimal',
            'NUMERIC': 'decimal',
            'FLOAT': 'float',
            'DOUBLE': 'double',
            'VARCHAR': 'varchar',
            'CHAR': 'char',
            'TEXT': 'text',
            'LONGTEXT': 'longtext',
            'MEDIUMTEXT': 'mediumtext',
            'TINYTEXT': 'tinytext',
            'DATE': 'date',
            'DATETIME': 'datetime',
            'TIMESTAMP': 'timestamp',
            'TIME': 'time',
            'YEAR': 'year',
            'BLOB': 'blob',
            'LONGBLOB': 'longblob',
            'MEDIUMBLOB': 'mediumblob',
            'TINYBLOB': 'tinyblob',
            'BINARY': 'binary',
            'VARBINARY': 'varbinary',
            'ENUM': 'enum',
            'SET': 'set',
            'JSON': 'json',
            'BOOLEAN': 'boolean',
            'BOOL': 'boolean'
        }
    
    def convert_tables_to_dbml(self, tables_data: Dict[str, Dict], schema_name: str = None) -> str:
        """테이블 데이터를 DBML 형식으로 변환"""
        dbml_content = []
        
        # 프로젝트 정보 (선택적)
        if schema_name:
            dbml_content.append(f"Project {schema_name} {{")
            dbml_content.append("  database_type: 'MySQL'")
            dbml_content.append("}\n")
        
        # 각 테이블을 DBML로 변환
        for table_name, table_info in tables_data.items():
            table_dbml = self._convert_table_to_dbml(table_name, table_info)
            dbml_content.append(table_dbml)
            dbml_content.append("")  # 테이블 간 빈 줄
        
        # 관계(References) 추가
        references = self._extract_references(tables_data)
        if references:
            dbml_content.append("// Relationships")
            for ref in references:
                dbml_content.append(ref)
        
        return "\n".join(dbml_content)
    
    def _convert_table_to_dbml(self, table_name: str, table_info: Dict) -> str:
        """단일 테이블을 DBML 형식으로 변환"""
        safe_table_name = self._escape_table_name(table_name)
        lines = [f"Table {safe_table_name} {{"]
        
        # Primary Key 정보를 제약조건에서 가져와서 컬럼에 적용
        primary_key_columns = set()
        constraints = table_info.get('constraints', [])
        for constraint in constraints:
            if constraint['type'] == 'primary_key':
                primary_key_columns.update([col.lower() for col in constraint['columns']])
        
        # 컬럼 정의
        for column in table_info.get('columns', []):
            # Primary key 정보 추가
            if column['name'].lower() in primary_key_columns:
                column['primary_key'] = True
            
            column_line = self._convert_column_to_dbml(column)
            lines.append(f"  {column_line}")
        
        # 인덱스 정의 (그룹화)
        constraints = table_info.get('constraints', [])
        index_definitions = []
        
        for constraint in constraints:
            if constraint['type'] == 'primary_key':
                # Primary key는 컬럼 레벨에서 처리되므로 여기서는 스킵
                continue
            elif constraint['type'] == 'unique':
                # 실제 컬럼명 찾기
                actual_cols = self._get_actual_column_names(table_info, constraint['columns'])
                columns_str = ', '.join(actual_cols)
                index_definitions.append(f"    ({columns_str}) [unique]")
            elif constraint['type'] == 'index':
                # 실제 컬럼명 찾기
                actual_cols = self._get_actual_column_names(table_info, constraint['columns'])
                columns_str = ', '.join(actual_cols)
                index_definitions.append(f"    ({columns_str})")
        
        # 인덱스가 있으면 하나의 Indexes 블록으로 그룹화
        if index_definitions:
            lines.append("")
            lines.append("  Indexes {")
            lines.extend(index_definitions)
            lines.append("  }")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _convert_column_to_dbml(self, column: Dict) -> str:
        """컬럼 정의를 DBML 형식으로 변환"""
        name = self._escape_table_name(column['name'])
        
        # 타입 변환
        mysql_type = column['type'].upper()
        dbml_type = self.type_mapping.get(mysql_type, mysql_type.lower())
        
        # 크기 정보 추가
        if column.get('size'):
            size_info = column['size']
            # ENUM 타입의 경우 값들을 이스케이프
            if mysql_type == 'ENUM' and size_info:
                # ENUM('value1','value2') 형태에서 각 값을 이스케이프
                size_info = self._escape_enum_values(size_info)
            
            if ',' in size_info:  # DECIMAL(10,2) 같은 경우
                dbml_type += f"({size_info})"
            else:  # VARCHAR(255) 같은 경우
                dbml_type += f"({size_info})"
        
        # 속성 수집
        attributes = []
        
        if column.get('primary_key'):
            attributes.append('pk')
        
        if column.get('auto_increment'):
            attributes.append('increment')
        
        if not column.get('nullable', True):
            attributes.append('not null')
        
        if column.get('unique') and not column.get('primary_key'):
            attributes.append('unique')
        
        if column.get('default') is not None:
            default_value = column['default']
            # DBML에서 지원하는 형식으로 변환
            if default_value.upper() == 'CURRENT_TIMESTAMP':
                default_value = '`now()`'  # 함수 표현식은 백틱으로 감싸기
            elif default_value.upper() == 'NULL':
                default_value = 'null'
            elif self._is_date_format(default_value):
                # 날짜 형식은 문자열로 처리 (0000-00-00, 0000-00-00 00:00:00 등)
                default_value = f"'{default_value}'"
            elif self._is_ip_address(default_value):
                # IP 주소는 문자열로 처리 (0.0.0.0, 192.168.1.1 등)
                default_value = f"'{default_value}'"
            elif default_value.isdigit() or (default_value.replace('.', '').isdigit() and '.' in default_value and not self._is_date_format(default_value) and not self._is_ip_address(default_value)):
                # 순수 정수 또는 소수점 숫자만 그대로 (하이픈이 포함된 값은 문자열로 처리)
                pass
            elif default_value.lower() in ['true', 'false']:
                # boolean은 그대로
                pass
            else:
                # 나머지는 문자열 리터럴로 처리 (특수문자 이스케이프)
                default_value = f"'{self._escape_string_value(default_value)}'"
            attributes.append(f'default: {default_value}')
        
        # 최종 컬럼 정의 구성
        column_def = f"{name} {dbml_type}"
        
        if attributes:
            attributes_str = ', '.join(attributes)
            column_def += f" [{attributes_str}]"
        
        return column_def
    
    def _escape_string_value(self, value: str) -> str:
        """
        DBML 문자열 값에서 특수문자를 이스케이프
        
        Args:
            value: 이스케이프할 문자열
            
        Returns:
            이스케이프된 문자열
        """
        if not isinstance(value, str):
            return str(value)
        
        # DBML에서 문제가 되는 문자들을 이스케이프
        escaped = value.replace('\\', '\\\\')  # 백슬래시
        escaped = escaped.replace('\n', '\\n')  # 줄바꿈
        escaped = escaped.replace('\r', '\\r')  # 캐리지 리턴
        escaped = escaped.replace('\t', '\\t')  # 탭
        escaped = escaped.replace("'", "\\'")   # 작은따옴표
        escaped = escaped.replace('"', '\\"')   # 큰따옴표
        
        # 제어문자 제거 (출력 가능한 ASCII 문자만 유지)
        escaped = ''.join(char if ord(char) >= 32 and ord(char) <= 126 else f'\\x{ord(char):02x}' for char in escaped)
        
        return escaped
    
    def _is_date_format(self, value: str) -> bool:
        """
        값이 날짜/시간 형식인지 확인
        
        Args:
            value: 확인할 값
            
        Returns:
            날짜/시간 형식이면 True
        """
        import re
        
        # 일반적인 MySQL 날짜/시간 형식들
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # 0000-00-00
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # 0000-00-00 00:00:00
            r'^\d{2}:\d{2}:\d{2}$',  # 00:00:00
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _is_ip_address(self, value: str) -> bool:
        """
        값이 IP 주소 형식인지 확인
        
        Args:
            value: 확인할 값
            
        Returns:
            IP 주소 형식이면 True
        """
        import re
        
        # IPv4 주소 형식 (0.0.0.0 ~ 255.255.255.255)
        ipv4_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        
        # 불완전한 IP 주소 형태도 포함 (0.0.0, 192.168.1 등)
        partial_ip_pattern = r'^\d{1,3}(\.\d{1,3}){1,3}$'
        
        if re.match(ipv4_pattern, value):
            # 완전한 IP 주소인 경우 각 옥텟이 0-255 범위인지 확인
            parts = value.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        elif re.match(partial_ip_pattern, value):
            # 불완전한 IP 주소 형태도 IP 주소로 처리
            parts = value.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        
        return False
    
    def _escape_enum_values(self, enum_str: str) -> str:
        """
        ENUM 값들에서 특수문자를 이스케이프
        
        Args:
            enum_str: ENUM 값 문자열 (예: "'value1','value2'")
            
        Returns:
            이스케이프된 ENUM 값 문자열
        """
        # ENUM 값들을 파싱하고 각각 이스케이프
        import re
        
        # 'value1','value2' 형태에서 각 값을 추출
        values = re.findall(r"'([^']*)'", enum_str)
        if not values:
            # 다른 형태일 수도 있음
            return enum_str
        
        # 각 값을 이스케이프하고 다시 조합
        escaped_values = []
        for value in values:
            escaped_value = self._escape_string_value(value)
            escaped_values.append(f"'{escaped_value}'")
        
        return ','.join(escaped_values)
    
    def _escape_table_name(self, name: str) -> str:
        """
        테이블/컬럼 이름에서 DBML에서 문제가 되는 문자 처리
        
        Args:
            name: 테이블/컬럼 이름
            
        Returns:
            안전한 이름
        """
        # 공백이나 특수문자가 포함된 경우 따옴표로 감싸기
        if ' ' in name or any(char in name for char in ['-', '.', '/', '\\', '(', ')', '[', ']']):
            return f'"{name}"'
        return name
    
    def _extract_references(self, tables_data: Dict[str, Dict]) -> List[str]:
        """Foreign Key 관계를 DBML Reference 형식으로 추출"""
        references = []
        # 중복 관계 방지를 위한 set
        seen_references = set()
        
        for table_name, table_info in tables_data.items():
            constraints = table_info.get('constraints', [])
            
            for constraint in constraints:
                if constraint['type'] == 'foreign_key':
                    # 실제 컬럼명 찾기 (대소문자 구분)
                    source_cols = self._get_actual_column_names(table_info, constraint['columns'])
                    target_table_info, actual_target_table_name = self._find_table_in_data_with_name(tables_data, constraint['ref_table'])
                    target_cols = self._get_actual_column_names(target_table_info, constraint['ref_columns']) if target_table_info else constraint['ref_columns']
                    
                    # 실제 테이블명 사용
                    target_table_name = actual_target_table_name if actual_target_table_name else constraint['ref_table']
                    
                    # 단일 컬럼 FK인 경우
                    if len(source_cols) == 1 and len(target_cols) == 1:
                        ref_line = (f"Ref: {table_name}.{source_cols[0]} "
                                  f"> {target_table_name}.{target_cols[0]}")
                        # 중복 체크 후 추가
                        if ref_line not in seen_references:
                            references.append(ref_line)
                            seen_references.add(ref_line)
                    elif len(source_cols) == len(target_cols) and len(source_cols) > 0:
                        # 복합 컬럼 FK인 경우 - 단일 컬럼 관계들로 분리
                        # dbdiagram.io에서 복합 키 관계가 제대로 인식되지 않는 경우가 있음
                        for i in range(len(source_cols)):
                            ref_line = f"Ref: {table_name}.{source_cols[i]} > {target_table_name}.{target_cols[i]}"
                            # 중복 체크 후 추가
                            if ref_line not in seen_references:
                                references.append(ref_line)
                                seen_references.add(ref_line)
        
        return references
    
    def _get_actual_column_names(self, table_info: Dict, column_names: List[str]) -> List[str]:
        """테이블 정의에서 실제 컬럼명 찾기 (대소문자 정확히 맞춤)"""
        if not table_info or 'columns' not in table_info:
            return column_names
        
        actual_columns = []
        table_columns = {col['name'].lower(): col['name'] for col in table_info['columns']}
        
        for col_name in column_names:
            # 소문자로 비교해서 실제 컬럼명 찾기
            actual_name = table_columns.get(col_name.lower(), col_name)
            actual_columns.append(actual_name)
        
        return actual_columns
    
    def _find_table_in_data(self, tables_data: Dict[str, Dict], table_name: str) -> Optional[Dict]:
        """테이블 데이터에서 특정 테이블 찾기 (대소문자 무시)"""
        for tname, tinfo in tables_data.items():
            if tname.lower() == table_name.lower():
                return tinfo
        return None
    
    def _find_table_in_data_with_name(self, tables_data: Dict[str, Dict], table_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """테이블 데이터에서 특정 테이블 찾기 (대소문자 무시) - 실제 테이블명도 반환"""
        for tname, tinfo in tables_data.items():
            if tname.lower() == table_name.lower():
                return tinfo, tname
        return None, None
    
    def save_dbml_file(self, dbml_content: str, output_path: str):
        """DBML 내용을 파일로 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
    
    def validate_and_fix_missing_columns(self, dbml_content: str, schema_dir: str) -> str:
        """DBML 파일에서 누락된 컬럼들을 찾아서 수정"""
        
        if not os.path.exists(schema_dir):
            return dbml_content
        
        # 각 테이블별로 확인
        table_pattern = r'Table\s+(\w+)\s*\{([^}]+)\}'
        tables = re.findall(table_pattern, dbml_content, re.MULTILINE | re.DOTALL)
        
        fixed_content = dbml_content
        changes_made = False
        
        for table_name, table_content in tables:
            # 해당 DDL 파일 찾기
            ddl_file = os.path.join(schema_dir, f"{table_name}.sql")
            if not os.path.exists(ddl_file):
                continue
            
            # DDL에서 실제 컬럼 목록 추출
            ddl_columns = self._extract_columns_from_ddl_file(ddl_file)
            ddl_column_names = {col['name'] for col in ddl_columns}
            
            # DBML에서 현재 컬럼 목록 추출 (더 정확한 패턴 사용)
            # 컬럼 정의 라인들만 추출 (인덱스, 제약조건 등 제외)
            lines = table_content.split('\n')
            dbml_column_names = set()
            for line in lines:
                line = line.strip()
                # 컬럼 정의 라인인지 확인 (공백으로 시작하고 식별자로 시작)
                if line and not line.startswith('Indexes') and not line.startswith('FK_') and not line.startswith('//'):
                    # 정규식으로 컬럼명 추출
                    col_match = re.match(r'^\s*(\w+)\s+', line)
                    if col_match:
                        dbml_column_names.add(col_match.group(1))
            
            # 누락된 컬럼들 찾기
            missing_columns = ddl_column_names - dbml_column_names
            
            if missing_columns:
                print(f"  🔧 테이블 {table_name}에서 누락된 컬럼 수정: {', '.join(missing_columns)}")
                
                # 누락된 컬럼들의 정의 생성
                missing_col_definitions = []
                for col in ddl_columns:
                    if col['name'] in missing_columns:
                        # DBML 형식으로 변환
                        dbml_type = self._convert_sql_type_to_dbml(col['type'])
                        attributes = []
                        
                        if not col['nullable']:
                            attributes.append('not null')
                        if col['auto_increment']:
                            attributes.append('increment')
                        if col['default']:
                            if col['default'].upper() == 'CURRENT_TIMESTAMP':
                                attributes.append('default: `now()`')
                            elif col['default'].upper() == 'NULL':
                                attributes.append('default: null')
                            elif col['default'].isdigit() or col['default'].replace('.', '').replace('-', '').isdigit():
                                attributes.append(f"default: {col['default']}")
                            elif col['default'].lower() in ['true', 'false']:
                                attributes.append(f"default: {col['default'].lower()}")
                            else:
                                # 문자열 기본값
                                escaped_default = self._escape_string_value(col['default'])
                                attributes.append(f"default: '{escaped_default}'")
                        
                        attr_str = f" [{', '.join(attributes)}]" if attributes else ""
                        # 컬럼명에서 공백 제거
                        clean_column_name = col['name'].replace(' ', '_')
                        missing_col_definitions.append(f"  {clean_column_name} {dbml_type}{attr_str}")
                
                # DBML 테이블 정의에 누락된 컬럼들 추가
                if missing_col_definitions:
                    # 기존 테이블 정의 찾기
                    old_table_def = f"Table {table_name} {{{table_content}}}"
                    
                    # 추가하기 전에 현재 테이블 내용에서 이미 존재하는 컬럼들 다시 확인
                    existing_in_table = set()
                    for line in table_content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('Indexes') and not line.startswith('FK_') and not line.startswith('//'):
                            col_match = re.match(r'^\s*(\w+)\s+', line)
                            if col_match:
                                existing_in_table.add(col_match.group(1))
                    
                    # 중복 방지: 이미 존재하는 컬럼 정의는 제외
                    filtered_definitions = []
                    for col_def in missing_col_definitions:
                        col_name_match = re.match(r'\s*(\w+)\s+', col_def)
                        if col_name_match:
                            col_name = col_name_match.group(1)
                            if col_name not in existing_in_table:
                                filtered_definitions.append(col_def)
                                existing_in_table.add(col_name)  # 추가된 컬럼도 기록
                    
                    if filtered_definitions:
                        # Indexes 섹션이 있으면 그 앞에, 없으면 테이블 끝에 추가
                        if "Indexes {" in table_content:
                            # Indexes 앞에 추가
                            indexes_pos = table_content.find("\n  Indexes {")
                            before_indexes = table_content[:indexes_pos]
                            after_indexes = table_content[indexes_pos:]
                            new_content = before_indexes + "\n" + "\n".join(filtered_definitions) + "\n" + after_indexes
                        else:
                            # 테이블 끝에 추가
                            new_content = table_content.rstrip() + "\n" + "\n".join(filtered_definitions) + "\n"
                        
                        # 인덱스에서 잘못된 컬럼명 참조 수정
                        new_content = self._fix_index_column_references(new_content, ddl_columns)
                        
                        new_table_def = f"Table {table_name} {{{new_content}}}"
                        fixed_content = fixed_content.replace(old_table_def, new_table_def)
                        changes_made = True
        
        if changes_made:
            print(f"  ✅ 누락된 컬럼들을 자동으로 수정했습니다.")
        
        return fixed_content
    
    def _fix_index_column_references(self, table_content: str, ddl_columns: List[Dict]) -> str:
        """인덱스에서 잘못된 컬럼명 참조를 수정"""
        # DDL에서 실제 컬럼명 매핑 생성 (대소문자 무관)
        column_mapping = {}
        for col in ddl_columns:
            column_mapping[col['name'].lower()] = col['name']
        
        lines = table_content.split('\n')
        fixed_lines = []
        
        in_indexes = False
        for line in lines:
            if 'Indexes {' in line:
                in_indexes = True
                fixed_lines.append(line)
            elif in_indexes and line.strip() == '}':
                in_indexes = False
                fixed_lines.append(line)
            elif in_indexes:
                # 인덱스 라인에서 컬럼명 수정
                fixed_line = line
                for col in ddl_columns:
                    actual_name = col['name']
                    # 다양한 케이스 매칭
                    patterns = [
                        actual_name.upper(),  # BEGINPIT
                        actual_name.lower(),  # beginpit
                        actual_name,          # BeginPIT
                    ]
                    
                    for pattern_name in patterns:
                        if pattern_name != actual_name:
                            # 정확한 매칭을 위해 단어 경계 사용
                            pattern = r'\b' + re.escape(pattern_name) + r'\b'
                            fixed_line = re.sub(pattern, actual_name, fixed_line)
                
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _extract_columns_from_ddl_file(self, ddl_file_path: str) -> List[Dict]:
        """DDL 파일에서 컬럼들을 직접 추출 (파서가 놓치는 컬럼들도 포함)"""
        with open(ddl_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 간단한 정규식으로 컬럼 정의 찾기
        column_pattern = r'`([^`]+)`\s+([a-zA-Z]+(?:\([^)]*\))?)\s+([^,]+?)(?=,|\n\s*(?:PRIMARY|UNIQUE|KEY|CONSTRAINT|\)))'
        matches = re.findall(column_pattern, content, re.MULTILINE | re.DOTALL)
        
        columns = []
        for match in matches:
            col_name = match[0]
            col_type = match[1] 
            attributes = match[2].strip()
            
            # 기본 속성 파싱
            nullable = 'NOT NULL' not in attributes.upper()
            auto_increment = 'AUTO_INCREMENT' in attributes.upper()
            
            # DEFAULT 값 추출
            default_match = re.search(r"DEFAULT\s+([^'\s]+|'[^']*')", attributes, re.IGNORECASE)
            default_value = default_match.group(1) if default_match else None
            if default_value and default_value.startswith("'") and default_value.endswith("'"):
                default_value = default_value[1:-1]  # 따옴표 제거
            
            columns.append({
                'name': col_name,
                'type': col_type.upper(),
                'nullable': nullable,
                'auto_increment': auto_increment,
                'default': default_value
            })
        
        return columns
    
    def _convert_sql_type_to_dbml(self, sql_type: str) -> str:
        """SQL 타입을 DBML 타입으로 변환"""
        sql_type = sql_type.upper()
        
        # 기본 타입 매핑
        type_mapping = {
            'TINYINT': 'tinyint',
            'SMALLINT': 'smallint', 
            'MEDIUMINT': 'int',
            'INT': 'int',
            'INTEGER': 'int',
            'BIGINT': 'bigint',
            'DECIMAL': 'decimal',
            'NUMERIC': 'decimal',
            'FLOAT': 'float',
            'DOUBLE': 'double',
            'BIT': 'bit',
            'CHAR': 'char',
            'VARCHAR': 'varchar',
            'BINARY': 'binary',
            'VARBINARY': 'varbinary',
            'TINYBLOB': 'blob',
            'BLOB': 'blob',
            'MEDIUMBLOB': 'blob',
            'LONGBLOB': 'blob',
            'TINYTEXT': 'text',
            'TEXT': 'text',
            'MEDIUMTEXT': 'text',
            'LONGTEXT': 'longtext',
            'ENUM': 'enum',
            'SET': 'set',
            'DATE': 'date',
            'TIME': 'time',
            'DATETIME': 'datetime',
            'TIMESTAMP': 'timestamp',
            'YEAR': 'year',
            'JSON': 'json'
        }
        
        # 크기 정보와 함께 처리
        for sql_key, dbml_value in type_mapping.items():
            if sql_type.startswith(sql_key):
                # 크기 정보나 enum 값들은 그대로 유지
                size_part = sql_type[len(sql_key):].strip()
                if size_part:
                    return f"{dbml_value}{size_part}"
                else:
                    return dbml_value
        
        # 특수 케이스 처리
        if sql_type.upper() == 'FOREIGN':
            # 외래키 컬럼은 일반적으로 정수형
            return 'int'
        
        # 매핑되지 않은 타입은 소문자로 변환
        return sql_type.lower()


if __name__ == "__main__":
    # 테스트 코드
    converter = DBMLConverter()
    
    # 샘플 데이터
    sample_data = {
        'users': {
            'columns': [
                {
                    'name': 'id',
                    'type': 'BIGINT',
                    'size': '20',
                    'nullable': False,
                    'auto_increment': True,
                    'primary_key': True,
                    'unique': False,
                    'default': None
                },
                {
                    'name': 'username',
                    'type': 'VARCHAR',
                    'size': '50',
                    'nullable': False,
                    'auto_increment': False,
                    'primary_key': False,
                    'unique': False,
                    'default': None
                },
                {
                    'name': 'email',
                    'type': 'VARCHAR',
                    'size': '100',
                    'nullable': True,
                    'auto_increment': False,
                    'primary_key': False,
                    'unique': True,
                    'default': None
                }
            ],
            'constraints': [
                {
                    'type': 'primary_key',
                    'columns': ['id']
                },
                {
                    'type': 'unique',
                    'columns': ['email']
                }
            ]
        }
    }
    
    # DBML 변환 테스트
    dbml_result = converter.convert_tables_to_dbml(sample_data, 'test_schema')
    print("DBML 변환 결과:")
    print(dbml_result)
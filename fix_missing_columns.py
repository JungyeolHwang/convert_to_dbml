#!/usr/bin/env python3
"""
누락된 컬럼들을 수정하는 스크립트
DDL 파서가 복잡한 COMMENT를 가진 컬럼들을 놓치는 경우를 수정
"""

import os
import re
from typing import Dict, List

def find_missing_columns_in_ddl(ddl_file_path: str) -> List[Dict]:
    """DDL 파일에서 파서가 놓칠 수 있는 컬럼들을 찾기"""
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
        
        columns.append({
            'name': col_name,
            'type': col_type.upper(),
            'nullable': nullable,
            'auto_increment': auto_increment,
            'default': default_value
        })
    
    return columns

def fix_dbml_missing_columns(dbml_file_path: str, schema_dir: str):
    """DBML 파일에서 누락된 컬럼들을 찾아서 수정"""
    
    print(f"🔍 검사 중: {dbml_file_path}")
    
    # DBML 파일 읽기
    with open(dbml_file_path, 'r', encoding='utf-8') as f:
        dbml_content = f.read()
    
    # 각 테이블별로 확인
    table_pattern = r'Table\s+(\w+)\s*\{([^}]+)\}'
    tables = re.findall(table_pattern, dbml_content, re.MULTILINE | re.DOTALL)
    
    changes_made = False
    
    for table_name, table_content in tables:
        # 해당 DDL 파일 찾기
        ddl_file = os.path.join(schema_dir, f"{table_name}.sql")
        if not os.path.exists(ddl_file):
            continue
        
        # DDL에서 실제 컬럼 목록 추출
        ddl_columns = find_missing_columns_in_ddl(ddl_file)
        ddl_column_names = {col['name'] for col in ddl_columns}
        
        # DBML에서 현재 컬럼 목록 추출
        dbml_column_pattern = r'(\w+)\s+[^[]+(?:\[[^\]]*\])?'
        dbml_columns = re.findall(dbml_column_pattern, table_content)
        dbml_column_names = set(dbml_columns)
        
        # 누락된 컬럼들 찾기
        missing_columns = ddl_column_names - dbml_column_names
        
        if missing_columns:
            print(f"  ⚠️  테이블 {table_name}에서 누락된 컬럼: {', '.join(missing_columns)}")
            
            # 누락된 컬럼들의 정의 생성
            missing_col_definitions = []
            for col in ddl_columns:
                if col['name'] in missing_columns:
                    # DBML 형식으로 변환
                    dbml_type = col['type'].lower()
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
                        else:
                            attributes.append(f"default: '{col['default']}'")
                    
                    attr_str = f" [{', '.join(attributes)}]" if attributes else ""
                    missing_col_definitions.append(f"  {col['name']} {dbml_type}{attr_str}")
            
            # DBML 테이블 정의에 누락된 컬럼들 추가
            if missing_col_definitions:
                # 테이블의 마지막 컬럼 뒤에 추가
                old_table_def = f"Table {table_name} {{{table_content}}}"
                
                # Indexes 섹션이 있으면 그 앞에, 없으면 테이블 끝에 추가
                if "Indexes {" in table_content:
                    # Indexes 앞에 추가
                    indexes_pos = table_content.find("\n  Indexes {")
                    before_indexes = table_content[:indexes_pos]
                    after_indexes = table_content[indexes_pos:]
                    new_content = before_indexes + "\n" + "\n".join(missing_col_definitions) + "\n" + after_indexes
                else:
                    # 테이블 끝에 추가
                    new_content = table_content.rstrip() + "\n" + "\n".join(missing_col_definitions) + "\n"
                
                new_table_def = f"Table {table_name} {{{new_content}}}"
                dbml_content = dbml_content.replace(old_table_def, new_table_def)
                changes_made = True
    
    if changes_made:
        # 수정된 DBML 파일 저장
        with open(dbml_file_path, 'w', encoding='utf-8') as f:
            f.write(dbml_content)
        print(f"  ✅ {dbml_file_path} 수정 완료")
    else:
        print(f"  ✅ {dbml_file_path} 누락된 컬럼 없음")

def main():
    """메인 함수"""
    base_dir = "auto-ddl-main/auto-ddl-main/mysql-hisapp-37042"
    
    # his_app 스키마 확인
    schema_dir = os.path.join(base_dir, "his_app")
    dbml_file = os.path.join(base_dir, "his_app.dbml")
    
    if os.path.exists(dbml_file) and os.path.exists(schema_dir):
        fix_dbml_missing_columns(dbml_file, schema_dir)
    else:
        print(f"파일을 찾을 수 없습니다: {dbml_file} 또는 {schema_dir}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""Generate initial migration from SQLAlchemy models - clean version."""
import os
import sys
import asyncio
import re
from datetime import datetime
from uuid import uuid4

from alembic.config import Config
from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import ops
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect
from sqlalchemy.schema import PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agentforge_backend.models import Base


def render_ops(ops_list, indent=4):
    """Render a list of operations as Python code."""
    lines = []
    prefix = ' ' * indent
    
    # Collect all ForeignKey information for later creation
    fk_info = []  # list of (table, column, ref_table, ref_column, ondelete)
    
    # First pass: collect FK info from all CreateTableOps
    for op in ops_list:
        if isinstance(op, ops.CreateTableOp):
            for item in op.columns:
                if not isinstance(item, (PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint, CheckConstraint)):
                    if hasattr(item, 'foreign_keys') and item.foreign_keys:
                        for fk in item.foreign_keys:
                            target = fk.target_fullname
                            ref_table, ref_col = target.split('.')
                            ondelete = fk.ondelete
                            fk_info.append((op.table_name, item.name, ref_table, ref_col, ondelete))
    
    for op in ops_list:
        if isinstance(op, ops.CreateTableOp):
            lines.append(f"{prefix}op.create_table(")
            lines.append(f"{prefix}    '{op.table_name}',")
            for item in op.columns:
                if isinstance(item, (PrimaryKeyConstraint, ForeignKeyConstraint, UniqueConstraint, CheckConstraint)):
                    if isinstance(item, PrimaryKeyConstraint):
                        pk_cols = [c.name for c in item.columns]
                        lines.append(f"{prefix}    sa.PrimaryKeyConstraint({', '.join(repr(c) for c in pk_cols)}),")
                    elif isinstance(item, UniqueConstraint):
                        col_names = [c.name for c in item.columns]
                        lines.append(f"{prefix}    sa.UniqueConstraint({', '.join(repr(c) for c in col_names)}, name={repr(item.name)}),")
                    elif isinstance(item, CheckConstraint):
                        lines.append(f"{prefix}    sa.CheckConstraint({repr(str(item.sqltext))}, name={repr(item.name)}),")
                    # Skip ForeignKeyConstraint - we'll create them separately
                else:
                    # Handle columns without ForeignKeys
                    col_def = render_column(item)
                    lines.append(f"{prefix}    {col_def},")
            lines.append(f"{prefix})")
        elif isinstance(op, ops.CreateIndexOp):
            unique = ", unique=True" if op.unique else ""
            col_names = [c.name if hasattr(c, 'name') else str(c) for c in op.columns]
            lines.append(f"{prefix}op.create_index({repr(op.index_name)}, {repr(op.table_name)}, {repr(col_names)}{unique})")
        elif isinstance(op, ops.DropIndexOp):
            lines.append(f"{prefix}op.drop_index({repr(op.index_name)}, table_name={repr(op.table_name)})")
        elif isinstance(op, ops.DropTableOp):
            lines.append(f"{prefix}op.drop_table({repr(op.table_name)})")
        elif isinstance(op, ops.ModifyTableOps):
            for sub_op in op.ops:
                lines.append(render_ops([sub_op], indent))
        elif isinstance(op, ops.AddColumnOp):
            col_def = render_column(op.column)
            lines.append(f"{prefix}op.add_column({repr(op.table_name)}, {col_def})")
        elif isinstance(op, ops.DropColumnOp):
            lines.append(f"{prefix}op.drop_column({repr(op.table_name)}, {repr(op.column_name)})")
        elif isinstance(op, ops.AlterColumnOp):
            lines.append(f"{prefix}op.alter_column({repr(op.table_name)}, {repr(op.column_name)}, ...)")
        else:
            lines.append(f"{prefix}# Unknown op: {type(op).__name__}")
    
    # Add ForeignKey creation after all tables are created
    if fk_info:
        lines.append(f"\n{prefix}# Create foreign key constraints after all tables exist")
        for table, column, ref_table, ref_column, ondelete in fk_info:
            fk_name = f"fk_{table}_{column}_{ref_table}"
            ondelete_str = f", ondelete={repr(ondelete)}" if ondelete else ""
            lines.append(f"{prefix}op.create_foreign_key({repr(fk_name)}, {repr(table)}, {repr(ref_table)}, [{repr(column)}], [{repr(ref_column)}]{ondelete_str})")
    
    return '\n'.join(lines)


def render_column(col):
    """Render a column definition without ForeignKeys."""
    col_type = render_type(col.type)
    
    nullable = f", nullable={col.nullable}"
    default = ""
    if col.default is not None:
        if hasattr(col.default, 'arg') and col.default.arg is not None:
            arg = col.default.arg
            if callable(arg):
                if arg.__name__ == 'uuid4':
                    default = ", default=uuid4"
                elif arg.__name__ == 'dict':
                    default = ", default=dict"
                elif arg.__name__ == 'list':
                    default = ", default=list"
                else:
                    default = f", default={arg.__name__}"
            else:
                if hasattr(arg, 'value'):
                    default = f", default={repr(arg.value)}"
                else:
                    default = f", default={repr(arg)}"
        elif not callable(col.default):
            if hasattr(col.default, 'value'):
                default = f", default={repr(col.default.value)}"
            else:
                default = f", default={repr(col.default)}"
    if col.server_default is not None:
        if hasattr(col.server_default, 'arg'):
            if col.server_default.arg == func.now():
                default = ", server_default=func.now()"
            else:
                default = f", server_default={repr(col.server_default)}"
        else:
            default = f", server_default={repr(col.server_default)}"
    primary_key = ", primary_key=True" if col.primary_key else ""
    
    return f"sa.Column({repr(col.name)}, {col_type}{nullable}{default}{primary_key})"


def render_type(type_obj):
    """Render a SQLAlchemy type."""
    if hasattr(type_obj, '__visit_name__'):
        type_name = type_obj.__visit_name__.upper()
        if type_name == 'UUID':
            return "sa.Uuid()"
        elif type_name in ('VARCHAR', 'STRING'):
            length = getattr(type_obj, 'length', None)
            if length:
                return f"sa.String(length={length})"
            return "sa.String()"
        elif type_name == 'TEXT':
            return "sa.Text()"
        elif type_name == 'BOOLEAN':
            return "sa.Boolean()"
        elif type_name == 'DATETIME':
            tz = getattr(type_obj, 'timezone', False)
            return f"sa.DateTime(timezone={tz})"
        elif type_name == 'INTEGER':
            return "sa.Integer()"
        elif type_name == 'ENUM':
            enums = getattr(type_obj, 'enums', [])
            name = getattr(type_obj, 'name', None)
            enum_str = f"sa.Enum({', '.join(repr(e) for e in enums)}, name={repr(name)})"
            return enum_str
        elif type_name == 'JSON':
            return "sa.JSON()"
        elif type_name == 'FLOAT':
            return "sa.Float()"
    return f"sa.{type_obj.__class__.__name__}()"


async def generate_migration():
    """Generate the migration file."""
    database_url = "postgresql+asyncpg://agentforge:finalcommit_pass@localhost:5432/agentforge"
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        def run_sync(connection):
            context = MigrationContext.configure(connection)
            migration_script = produce_migrations(context, Base.metadata)
            
            # Generate upgrade operations
            upgrade_lines = render_ops(migration_script.upgrade_ops.ops)
            downgrade_lines = render_ops(migration_script.downgrade_ops.ops)
            
            return upgrade_lines, downgrade_lines
        
        upgrade_code, downgrade_code = await conn.run_sync(run_sync)
    
    await engine.dispose()
    
    # Clean up the generated code
    upgrade_code = cleanup_code(upgrade_code)
    downgrade_code = cleanup_code(downgrade_code)
    
    # Generate the migration file content
    revision_id = uuid4().hex[:12]
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    content = f'''# -*- coding: utf-8 -*-
"""Initial migration: create all tables

Revision ID: {revision_id}
Revises: 
Create Date: {create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from uuid import uuid4


# revision identifiers, used by Alembic.
revision: str = "{revision_id}"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
{upgrade_code}


def downgrade() -> None:
{downgrade_code}
'''
    
    # Write the migration file
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
    filename = f"{revision_id}_initial_migration.py"
    filepath = os.path.join(migrations_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Generated migration: {filepath}")
    return filepath


def cleanup_code(code: str) -> str:
    """Clean up the generated code to fix common issues."""
    # Fix DefaultClause representations
    code = re.sub(r'DefaultClause\(<sqlalchemy\.sql\.functions\.now at 0x[^>]+; now>, for_update=False\)', 'func.now()', code)
    code = re.sub(r'DefaultClause\(<sqlalchemy\.sql\.functions\.now at 0x[^>]+; now>\)', 'func.now()', code)
    
    # Fix ScalarElementColumnDefault representations
    code = re.sub(r'ScalarElementColumnDefault\(([^)]+)\)', r'\1', code)
    
    # Fix Column objects in indexes - replace with just column names
    code = re.sub(r'Column\([\'\"]([^\'\"]+)[\'\"], [^,]+, table=<[^>]+>(?:, nullable=(True|False))?\)', r"'\1'", code)
    
    # Fix UniqueConstraint with Column objects - single column (multiline)
    code = re.sub(r"sa\.UniqueConstraint\(Column\('([^']+)', [^)]+\)\s*,\s*name='([^']+)'\)", r"sa.UniqueConstraint('\1', name='\2')", code, flags=re.DOTALL)
    
    # Fix UniqueConstraint with Column objects - two columns (multiline)
    code = re.sub(r"sa\.UniqueConstraint\(Column\('([^']+)', [^)]+\)\s*,\s*Column\('([^']+)', [^)]+\)\s*,\s*name='([^']+)'\)", r"sa.UniqueConstraint('\1', '\2', name='\3')", code, flags=re.DOTALL)
    
    # Fix UniqueConstraint with Column objects - three columns (multiline)
    code = re.sub(r"sa\.UniqueConstraint\(Column\('([^']+)', [^)]+\)\s*,\s*Column\('([^']+)', [^)]+\)\s*,\s*Column\('([^']+)', [^)]+\)\s*,\s*name='([^']+)'\)", r"sa.UniqueConstraint('\1', '\2', '\3', name='\4')", code, flags=re.DOTALL)
    
    # Fix Enum defaults like <UserRole.USER: 'user'>
    code = re.sub(r'<[A-Za-z]+\.[A-Za-z_]+: \'([^\']+)\'>', r"'\1'", code)
    
    # Fix PrimaryKeyConstraint in ForeignKeyConstraint that incorrectly uses 'id'
    code = re.sub(r"sa\.ForeignKeyConstraint\(Column\('([^']+)', [^)]+\), 'id', ondelete='([^']+)'\)", r"sa.ForeignKeyConstraint(['\1'], ['\1'], ondelete='\2')", code)
    
    return code


if __name__ == "__main__":
    asyncio.run(generate_migration())
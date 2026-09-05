# -*- coding: utf-8 -*-
"""Initial migration: create all tables

Revision ID: a10126cbfc95
Revises: 
Create Date: 2026-09-01 22:46:45.892743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from uuid import uuid4


# revision identifiers, used by Alembic.
revision: str = "a10126cbfc95"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
    )
    op.create_index('ix_permissions_action', 'permissions', ['action'])
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True)
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_table(
        'users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('role', sa.Enum('admin', 'user', 'developer', 'operator', 'viewer', name='userrole'), nullable=False, default='user'),
        sa.Column('active_workspace_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_active_workspace', 'users', ['active_workspace_id'])
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_table(
        'workspaces',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('is_personal', sa.Boolean(), nullable=False, default=False),
        sa.Column('settings', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspaces_deleted_at', 'workspaces', ['deleted_at'])
    op.create_index('ix_workspaces_name', 'workspaces', ['name'])
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'])
    op.create_table(
        'api_keys',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('hashed_key', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=20), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('scopes', sa.JSON(), nullable=False, default=list),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('last_ip', sa.String(length=45), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_deleted_at', 'api_keys', ['deleted_at'])
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'])
    op.create_index('ix_api_keys_hashed_key', 'api_keys', ['hashed_key'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_workspace_id', 'api_keys', ['workspace_id'])
    op.create_table(
        'audit_logs',
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'login', 'logout', 'execute', 'assign', 'invite', 'export', 'import', name='auditactiontype'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'error', 'critical', name='auditseverity'), nullable=False, default='info'),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_severity', 'audit_logs', ['severity'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_workspace_id', 'audit_logs', ['workspace_id'])
    op.create_table(
        'email_verification_tokens',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_verification_tokens_expires_at', 'email_verification_tokens', ['expires_at'])
    op.create_index('ix_email_verification_tokens_token_hash', 'email_verification_tokens', ['token_hash'], unique=True)
    op.create_index('ix_email_verification_tokens_used', 'email_verification_tokens', ['used'])
    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'])
    op.create_table(
        'integrations',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.Enum('github', 'gitlab', 'slack', 'discord', 'google', 'microsoft', 'aws', 'azure', 'gcp', 'custom', name='integrationprovider'), nullable=False),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, default=dict),
        sa.Column('status', sa.Enum('active', 'inactive', 'error', 'expired', name='integrationstatus'), nullable=False, default='active'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('config_metadata', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_integrations_deleted_at', 'integrations', ['deleted_at'])
    op.create_index('ix_integrations_provider', 'integrations', ['provider'])
    op.create_index('ix_integrations_status', 'integrations', ['status'])
    op.create_index('ix_integrations_user_id', 'integrations', ['user_id'])
    op.create_index('ix_integrations_workspace_id', 'integrations', ['workspace_id'])
    op.create_table(
        'login_history',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('mfa_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_login_history_created_at', 'login_history', ['created_at'])
    op.create_index('ix_login_history_ip_address', 'login_history', ['ip_address'])
    op.create_index('ix_login_history_user_id', 'login_history', ['user_id'])
    op.create_table(
        'mfa_configs',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('secret_encrypted', sa.String(length=255), nullable=True),
        sa.Column('backup_codes_encrypted', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_mfa_config_user'),
    )
    op.create_index('ix_mfa_configs_user_id', 'mfa_configs', ['user_id'], unique=True)
    op.create_table(
        'notifications',
        sa.Column('type', sa.Enum('info', 'success', 'warning', 'error', 'system', 'execution_completed', 'execution_failed', 'task_assigned', 'task_completed', 'workspace_invitation', 'agent_created', 'agent_failed', name='notificationtype'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', name='notificationpriority'), nullable=False, default='normal'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('read_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('action_label', sa.String(length=100), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=False, default=dict),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('related_resource_type', sa.String(length=50), nullable=True),
        sa.Column('related_resource_id', sa.String(length=100), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_deleted_at', 'notifications', ['deleted_at'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_workspace_id', 'notifications', ['workspace_id'])
    op.create_table(
        'oauth_accounts',
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_user_id', sa.String(length=255), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(length=50), nullable=False, default='Bearer'),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id_token_encrypted', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_account_provider_user'),
    )
    op.create_index('ix_oauth_accounts_deleted_at', 'oauth_accounts', ['deleted_at'])
    op.create_index('ix_oauth_accounts_provider', 'oauth_accounts', ['provider'])
    op.create_index('ix_oauth_accounts_provider_user_id', 'oauth_accounts', ['provider_user_id'])
    op.create_index('ix_oauth_accounts_user_id', 'oauth_accounts', ['user_id'])
    op.create_table(
        'password_reset_tokens',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index('ix_password_reset_tokens_token_hash', 'password_reset_tokens', ['token_hash'])
    op.create_index('ix_password_reset_tokens_used', 'password_reset_tokens', ['used'])
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_table(
        'projects',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', 'deleted', name='projectstatus'), nullable=False, default='active'),
        sa.Column('settings', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_deleted_at', 'projects', ['deleted_at'])
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_workspace_id', 'projects', ['workspace_id'])
    op.create_table(
        'refresh_tokens',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('replaced_by_token_hash', sa.String(length=255), nullable=True),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_refresh_tokens_deleted_at', 'refresh_tokens', ['deleted_at'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_tokens_revoked', 'refresh_tokens', ['revoked'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_table(
        'roles',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint('workspace_id', 'name', name='uq_role_workspace_name'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])
    op.create_index('ix_roles_workspace_id', 'roles', ['workspace_id'])
    op.create_table(
        'trusted_devices',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('device_fingerprint', sa.String(length=255), nullable=False),
        sa.Column('device_name', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trusted_devices_deleted_at', 'trusted_devices', ['deleted_at'])
    op.create_index('ix_trusted_devices_device_fingerprint', 'trusted_devices', ['device_fingerprint'])
    op.create_index('ix_trusted_devices_expires_at', 'trusted_devices', ['expires_at'])
    op.create_index('ix_trusted_devices_fingerprint', 'trusted_devices', ['device_fingerprint'])
    op.create_index('ix_trusted_devices_user_id', 'trusted_devices', ['user_id'])
    op.create_table(
        'user_sessions',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_sessions_deleted_at', 'user_sessions', ['deleted_at'])
    op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'], unique=True)
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_table(
        'user_settings',
        sa.Column('user_id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('theme', sa.String(length=20), nullable=False, default='dark'),
        sa.Column('language', sa.String(length=10), nullable=False, default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='UTC'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('push_notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('default_workspace_id', sa.Uuid(), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint('user_id', name='uq_user_settings_user'),
        sa.PrimaryKeyConstraint('user_id', 'id'),
    )
    op.create_table(
        'workspace_invitations',
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', 'viewer', name='workspacerole'), nullable=False, default='member'),
        sa.Column('invited_by', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('accepted_by', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspace_invitations_deleted_at', 'workspace_invitations', ['deleted_at'])
    op.create_index('ix_workspace_invitations_email', 'workspace_invitations', ['email'])
    op.create_index('ix_workspace_invitations_expires_at', 'workspace_invitations', ['expires_at'])
    op.create_index('ix_workspace_invitations_invited_by', 'workspace_invitations', ['invited_by'])
    op.create_index('ix_workspace_invitations_token_hash', 'workspace_invitations', ['token_hash'])
    op.create_index('ix_workspace_invitations_workspace_id', 'workspace_invitations', ['workspace_id'])
    op.create_table(
        'workspace_members',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', name='workspacerole'), nullable=False, default='member'),
        sa.Column('invited_by', sa.Uuid(), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'workspace_id', name='uq_workspace_member_user_workspace'),
    )
    op.create_index('ix_workspace_members_deleted_at', 'workspace_members', ['deleted_at'])
    op.create_index('ix_workspace_members_role', 'workspace_members', ['role'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_table(
        'workspace_settings',
        sa.Column('workspace_id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('theme', sa.String(length=20), nullable=False, default='dark'),
        sa.Column('language', sa.String(length=10), nullable=False, default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='UTC'),
        sa.Column('notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('auto_save', sa.Boolean(), nullable=False, default=True),
        sa.Column('default_model', sa.String(length=50), nullable=False, default='gpt-4'),
        sa.Column('ai_settings', sa.JSON(), nullable=False, default=dict),
        sa.Column('security_settings', sa.JSON(), nullable=False, default=dict),
        sa.Column('notification_settings', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint('workspace_id', name='uq_workspace_settings_workspace'),
        sa.PrimaryKeyConstraint('workspace_id', 'id'),
    )
    op.create_table(
        'agents',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, default=0.7),
        sa.Column('max_tokens', sa.Integer(), nullable=False, default=4096),
        sa.Column('tools', sa.JSON(), nullable=False, default=list),
        sa.Column('permissions', sa.JSON(), nullable=False, default=dict),
        sa.Column('memory', sa.JSON(), nullable=False, default=dict),
        sa.Column('execution_limits', sa.JSON(), nullable=False, default=dict),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=60),
        sa.Column('retry_policy', sa.JSON(), nullable=False, default={'max_retries': 3}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'archived', 'deleted', name='agentstatus'), nullable=False, default='active'),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agents_agent_type', 'agents', ['agent_type'])
    op.create_index('ix_agents_deleted_at', 'agents', ['deleted_at'])
    op.create_index('ix_agents_owner_id', 'agents', ['owner_id'])
    op.create_index('ix_agents_project_id', 'agents', ['project_id'])
    op.create_index('ix_agents_status', 'agents', ['status'])
    op.create_table(
        'oauth_tokens',
        sa.Column('integration_id', sa.Uuid(), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(length=50), nullable=False, default='Bearer'),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id_token_encrypted', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_oauth_tokens_expires_at', 'oauth_tokens', ['expires_at'])
    op.create_index('ix_oauth_tokens_integration_id', 'oauth_tokens', ['integration_id'])
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('permission_id', sa.Uuid(), nullable=False, primary_key=True),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    )
    op.create_table(
        'tasks',
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('todo', 'queued', 'in_progress', 'completed', 'failed', 'cancelled', name='taskstatus'), nullable=False, default='todo'),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='taskpriority'), nullable=False, default='medium'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=False, default=list),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('assignee_id', sa.Uuid(), nullable=True),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=False, default=list),
        sa.Column('extra_data', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_assignee_id', 'tasks', ['assignee_id'])
    op.create_index('ix_tasks_created_by', 'tasks', ['created_by'])
    op.create_index('ix_tasks_deadline', 'tasks', ['deadline'])
    op.create_index('ix_tasks_deleted_at', 'tasks', ['deleted_at'])
    op.create_index('ix_tasks_priority', 'tasks', ['priority'])
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_table(
        'user_role_assignments',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=True),
        sa.Column('assigned_by', sa.Uuid(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint('user_id', 'role_id', 'workspace_id', name='uq_user_role_workspace'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_role_assignments_assigned_by', 'user_role_assignments', ['assigned_by'])
    op.create_index('ix_user_role_assignments_role_id', 'user_role_assignments', ['role_id'])
    op.create_index('ix_user_role_assignments_user_id', 'user_role_assignments', ['user_id'])
    op.create_index('ix_user_role_assignments_workspace_id', 'user_role_assignments', ['workspace_id'])
    op.create_table(
        'webhooks',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=255), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False, default=list),
        sa.Column('status', sa.Enum('active', 'inactive', 'error', 'disabled', name='webhookstatus'), nullable=False, default='active'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('retry_config', sa.JSON(), nullable=False, default={'max_retries': 3, 'backoff_seconds': 60}),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('headers', sa.JSON(), nullable=False, default=dict),
        sa.Column('last_triggered_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, default=0),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhooks_deleted_at', 'webhooks', ['deleted_at'])
    op.create_index('ix_webhooks_project_id', 'webhooks', ['project_id'])
    op.create_index('ix_webhooks_status', 'webhooks', ['status'])
    op.create_index('ix_webhooks_user_id', 'webhooks', ['user_id'])
    op.create_table(
        'agent_versions',
        sa.Column('agent_id', sa.Uuid(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('config_snapshot', sa.JSON(), nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint('agent_id', 'version_number', name='uq_agent_version_number'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_versions_agent_id', 'agent_versions', ['agent_id'])
    op.create_index('ix_agent_versions_version_number', 'agent_versions', ['version_number'])
    op.create_table(
        'executions',
        sa.Column('status', sa.Enum('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'timeout', name='executionstatus'), nullable=False, default='pending'),
        sa.Column('input', sa.JSON(), nullable=False),
        sa.Column('output', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=60),
        sa.Column('agent_id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('triggered_by', sa.Uuid(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False, default=dict),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_executions_agent_id', 'executions', ['agent_id'])
    op.create_index('ix_executions_completed_at', 'executions', ['completed_at'])
    op.create_index('ix_executions_deleted_at', 'executions', ['deleted_at'])
    op.create_index('ix_executions_started_at', 'executions', ['started_at'])
    op.create_index('ix_executions_status', 'executions', ['status'])
    op.create_index('ix_executions_task_id', 'executions', ['task_id'])
    op.create_table(
        'scheduled_executions',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='UTC'),
        sa.Column('agent_id', sa.Uuid(), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False, default=dict),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_status', sa.String(length=50), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scheduled_executions_agent_id', 'scheduled_executions', ['agent_id'])
    op.create_index('ix_scheduled_executions_created_by', 'scheduled_executions', ['created_by'])
    op.create_index('ix_scheduled_executions_deleted_at', 'scheduled_executions', ['deleted_at'])
    op.create_index('ix_scheduled_executions_enabled', 'scheduled_executions', ['enabled'])
    op.create_index('ix_scheduled_executions_next_run', 'scheduled_executions', ['next_run_at'])
    op.create_index('ix_scheduled_executions_next_run_at', 'scheduled_executions', ['next_run_at'])
    op.create_table(
        'task_attachments',
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('uploaded_by', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_attachments_task_id', 'task_attachments', ['task_id'])
    op.create_index('ix_task_attachments_uploaded_by', 'task_attachments', ['uploaded_by'])
    op.create_table(
        'task_comments',
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_comments_deleted_at', 'task_comments', ['deleted_at'])
    op.create_index('ix_task_comments_task_id', 'task_comments', ['task_id'])
    op.create_index('ix_task_comments_user_id', 'task_comments', ['user_id'])
    op.create_table(
        'webhook_deliveries',
        sa.Column('webhook_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_headers', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('attempt', sa.Integer(), nullable=False, default=1),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'])
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_table(
        'execution_events',
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('execution_id', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_events_event_type', 'execution_events', ['event_type'])
    op.create_index('ix_execution_events_execution_id', 'execution_events', ['execution_id'])
    op.create_table(
        'execution_logs',
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, default='info'),
        sa.Column('tool_used', sa.String(length=100), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_info', sa.JSON(), nullable=True),
        sa.Column('execution_id', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_logs_event_type', 'execution_logs', ['event_type'])
    op.create_index('ix_execution_logs_execution_id', 'execution_logs', ['execution_id'])
    op.create_index('ix_execution_logs_severity', 'execution_logs', ['severity'])
    op.create_table(
        'execution_metrics',
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=50), nullable=True),
        sa.Column('execution_id', sa.Uuid(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False, default=uuid4, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_metrics_execution_id', 'execution_metrics', ['execution_id'])
    op.create_index('ix_execution_metrics_metric_name', 'execution_metrics', ['metric_name'])

    # Create foreign key constraints after all tables exist
    op.create_foreign_key('fk_users_active_workspace_id_workspaces', 'users', 'workspaces', ['active_workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workspaces_owner_id_users', 'workspaces', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_api_keys_user_id_users', 'api_keys', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_api_keys_workspace_id_workspaces', 'api_keys', 'workspaces', ['workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_audit_logs_user_id_users', 'audit_logs', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_audit_logs_workspace_id_workspaces', 'audit_logs', 'workspaces', ['workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_email_verification_tokens_user_id_users', 'email_verification_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_integrations_user_id_users', 'integrations', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_integrations_workspace_id_workspaces', 'integrations', 'workspaces', ['workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_login_history_user_id_users', 'login_history', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_mfa_configs_user_id_users', 'mfa_configs', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_notifications_user_id_users', 'notifications', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_notifications_workspace_id_workspaces', 'notifications', 'workspaces', ['workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_oauth_accounts_user_id_users', 'oauth_accounts', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_password_reset_tokens_user_id_users', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_projects_workspace_id_workspaces', 'projects', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_projects_owner_id_users', 'projects', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_refresh_tokens_user_id_users', 'refresh_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_roles_workspace_id_workspaces', 'roles', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_trusted_devices_user_id_users', 'trusted_devices', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_sessions_user_id_users', 'user_sessions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_settings_user_id_users', 'user_settings', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_settings_default_workspace_id_workspaces', 'user_settings', 'workspaces', ['default_workspace_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workspace_invitations_workspace_id_workspaces', 'workspace_invitations', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workspace_invitations_invited_by_users', 'workspace_invitations', 'users', ['invited_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workspace_invitations_accepted_by_users', 'workspace_invitations', 'users', ['accepted_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workspace_members_user_id_users', 'workspace_members', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workspace_members_workspace_id_workspaces', 'workspace_members', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_workspace_members_invited_by_users', 'workspace_members', 'users', ['invited_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workspace_settings_workspace_id_workspaces', 'workspace_settings', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_agents_owner_id_users', 'agents', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_agents_project_id_projects', 'agents', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_oauth_tokens_integration_id_integrations', 'oauth_tokens', 'integrations', ['integration_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_role_permissions_role_id_roles', 'role_permissions', 'roles', ['role_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_role_permissions_permission_id_permissions', 'role_permissions', 'permissions', ['permission_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_tasks_assignee_id_users', 'tasks', 'users', ['assignee_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_tasks_project_id_projects', 'tasks', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_tasks_created_by_users', 'tasks', 'users', ['created_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_role_assignments_user_id_users', 'user_role_assignments', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_role_assignments_role_id_roles', 'user_role_assignments', 'roles', ['role_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_role_assignments_workspace_id_workspaces', 'user_role_assignments', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_role_assignments_assigned_by_users', 'user_role_assignments', 'users', ['assigned_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_webhooks_user_id_users', 'webhooks', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_webhooks_project_id_projects', 'webhooks', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_agent_versions_agent_id_agents', 'agent_versions', 'agents', ['agent_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_agent_versions_created_by_users', 'agent_versions', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_executions_agent_id_agents', 'executions', 'agents', ['agent_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_executions_task_id_tasks', 'executions', 'tasks', ['task_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_executions_triggered_by_users', 'executions', 'users', ['triggered_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_scheduled_executions_agent_id_agents', 'scheduled_executions', 'agents', ['agent_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_scheduled_executions_created_by_users', 'scheduled_executions', 'users', ['created_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_task_attachments_task_id_tasks', 'task_attachments', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_task_attachments_uploaded_by_users', 'task_attachments', 'users', ['uploaded_by'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_task_comments_task_id_tasks', 'task_comments', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_task_comments_user_id_users', 'task_comments', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_task_comments_parent_comment_id_task_comments', 'task_comments', 'task_comments', ['parent_comment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_webhook_deliveries_webhook_id_webhooks', 'webhook_deliveries', 'webhooks', ['webhook_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_execution_events_execution_id_executions', 'execution_events', 'executions', ['execution_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_execution_logs_execution_id_executions', 'execution_logs', 'executions', ['execution_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_execution_metrics_execution_id_executions', 'execution_metrics', 'executions', ['execution_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_index('ix_execution_metrics_metric_name', table_name='execution_metrics')
    op.drop_index('ix_execution_metrics_execution_id', table_name='execution_metrics')
    op.drop_table('execution_metrics')
    op.drop_index('ix_execution_logs_severity', table_name='execution_logs')
    op.drop_index('ix_execution_logs_execution_id', table_name='execution_logs')
    op.drop_index('ix_execution_logs_event_type', table_name='execution_logs')
    op.drop_table('execution_logs')
    op.drop_index('ix_execution_events_execution_id', table_name='execution_events')
    op.drop_index('ix_execution_events_event_type', table_name='execution_events')
    op.drop_table('execution_events')
    op.drop_index('ix_webhook_deliveries_webhook_id', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('ix_webhook_deliveries_created_at', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index('ix_task_comments_user_id', table_name='task_comments')
    op.drop_index('ix_task_comments_task_id', table_name='task_comments')
    op.drop_index('ix_task_comments_deleted_at', table_name='task_comments')
    op.drop_table('task_comments')
    op.drop_index('ix_task_attachments_uploaded_by', table_name='task_attachments')
    op.drop_index('ix_task_attachments_task_id', table_name='task_attachments')
    op.drop_table('task_attachments')
    op.drop_index('ix_scheduled_executions_next_run_at', table_name='scheduled_executions')
    op.drop_index('ix_scheduled_executions_next_run', table_name='scheduled_executions')
    op.drop_index('ix_scheduled_executions_enabled', table_name='scheduled_executions')
    op.drop_index('ix_scheduled_executions_deleted_at', table_name='scheduled_executions')
    op.drop_index('ix_scheduled_executions_created_by', table_name='scheduled_executions')
    op.drop_index('ix_scheduled_executions_agent_id', table_name='scheduled_executions')
    op.drop_table('scheduled_executions')
    op.drop_index('ix_executions_task_id', table_name='executions')
    op.drop_index('ix_executions_status', table_name='executions')
    op.drop_index('ix_executions_started_at', table_name='executions')
    op.drop_index('ix_executions_deleted_at', table_name='executions')
    op.drop_index('ix_executions_completed_at', table_name='executions')
    op.drop_index('ix_executions_agent_id', table_name='executions')
    op.drop_table('executions')
    op.drop_index('ix_agent_versions_version_number', table_name='agent_versions')
    op.drop_index('ix_agent_versions_agent_id', table_name='agent_versions')
    op.drop_table('agent_versions')
    op.drop_index('ix_webhooks_user_id', table_name='webhooks')
    op.drop_index('ix_webhooks_status', table_name='webhooks')
    op.drop_index('ix_webhooks_project_id', table_name='webhooks')
    op.drop_index('ix_webhooks_deleted_at', table_name='webhooks')
    op.drop_table('webhooks')
    op.drop_index('ix_user_role_assignments_workspace_id', table_name='user_role_assignments')
    op.drop_index('ix_user_role_assignments_user_id', table_name='user_role_assignments')
    op.drop_index('ix_user_role_assignments_role_id', table_name='user_role_assignments')
    op.drop_index('ix_user_role_assignments_assigned_by', table_name='user_role_assignments')
    op.drop_table('user_role_assignments')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_project_id', table_name='tasks')
    op.drop_index('ix_tasks_priority', table_name='tasks')
    op.drop_index('ix_tasks_deleted_at', table_name='tasks')
    op.drop_index('ix_tasks_deadline', table_name='tasks')
    op.drop_index('ix_tasks_created_by', table_name='tasks')
    op.drop_index('ix_tasks_assignee_id', table_name='tasks')
    op.drop_table('tasks')
    op.drop_table('role_permissions')
    op.drop_index('ix_oauth_tokens_integration_id', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_expires_at', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
    op.drop_index('ix_agents_status', table_name='agents')
    op.drop_index('ix_agents_project_id', table_name='agents')
    op.drop_index('ix_agents_owner_id', table_name='agents')
    op.drop_index('ix_agents_deleted_at', table_name='agents')
    op.drop_index('ix_agents_agent_type', table_name='agents')
    op.drop_table('agents')
    op.drop_table('workspace_settings')
    op.drop_index('ix_workspace_members_workspace_id', table_name='workspace_members')
    op.drop_index('ix_workspace_members_user_id', table_name='workspace_members')
    op.drop_index('ix_workspace_members_role', table_name='workspace_members')
    op.drop_index('ix_workspace_members_deleted_at', table_name='workspace_members')
    op.drop_table('workspace_members')
    op.drop_index('ix_workspace_invitations_workspace_id', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_token_hash', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_invited_by', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_expires_at', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_email', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_deleted_at', table_name='workspace_invitations')
    op.drop_table('workspace_invitations')
    op.drop_table('user_settings')
    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_token_hash', table_name='user_sessions')
    op.drop_index('ix_user_sessions_expires_at', table_name='user_sessions')
    op.drop_index('ix_user_sessions_deleted_at', table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_index('ix_trusted_devices_user_id', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_fingerprint', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_expires_at', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_device_fingerprint', table_name='trusted_devices')
    op.drop_index('ix_trusted_devices_deleted_at', table_name='trusted_devices')
    op.drop_table('trusted_devices')
    op.drop_index('ix_roles_workspace_id', table_name='roles')
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_table('roles')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_deleted_at', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_projects_workspace_id', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_owner_id', table_name='projects')
    op.drop_index('ix_projects_deleted_at', table_name='projects')
    op.drop_table('projects')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_used', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token_hash', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index('ix_oauth_accounts_user_id', table_name='oauth_accounts')
    op.drop_index('ix_oauth_accounts_provider_user_id', table_name='oauth_accounts')
    op.drop_index('ix_oauth_accounts_provider', table_name='oauth_accounts')
    op.drop_index('ix_oauth_accounts_deleted_at', table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
    op.drop_index('ix_notifications_workspace_id', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_deleted_at', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_mfa_configs_user_id', table_name='mfa_configs')
    op.drop_table('mfa_configs')
    op.drop_index('ix_login_history_user_id', table_name='login_history')
    op.drop_index('ix_login_history_ip_address', table_name='login_history')
    op.drop_index('ix_login_history_created_at', table_name='login_history')
    op.drop_table('login_history')
    op.drop_index('ix_integrations_workspace_id', table_name='integrations')
    op.drop_index('ix_integrations_user_id', table_name='integrations')
    op.drop_index('ix_integrations_status', table_name='integrations')
    op.drop_index('ix_integrations_provider', table_name='integrations')
    op.drop_index('ix_integrations_deleted_at', table_name='integrations')
    op.drop_table('integrations')
    op.drop_index('ix_email_verification_tokens_user_id', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_used', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_token_hash', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_expires_at', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_index('ix_audit_logs_workspace_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_severity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_api_keys_workspace_id', table_name='api_keys')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_index('ix_api_keys_hashed_key', table_name='api_keys')
    op.drop_index('ix_api_keys_expires_at', table_name='api_keys')
    op.drop_index('ix_api_keys_deleted_at', table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index('ix_workspaces_owner_id', table_name='workspaces')
    op.drop_index('ix_workspaces_name', table_name='workspaces')
    op.drop_index('ix_workspaces_deleted_at', table_name='workspaces')
    op.drop_table('workspaces')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_deleted_at', table_name='users')
    op.drop_index('ix_users_active_workspace', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_permissions_resource', table_name='permissions')
    op.drop_index('ix_permissions_name', table_name='permissions')
    op.drop_index('ix_permissions_action', table_name='permissions')
    op.drop_table('permissions')

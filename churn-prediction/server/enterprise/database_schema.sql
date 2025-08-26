-- ChurnGuard Multi-Tenant Database Schema
-- Epic 3 - Enterprise Features & Multi-Tenancy
-- PostgreSQL with Row-Level Security (RLS)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==================== CORE TENANT MANAGEMENT ====================

-- Organizations table (tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- URL-safe identifier
    domain VARCHAR(255), -- Custom domain for enterprise
    subdomain VARCHAR(100) UNIQUE, -- churnguard.com/acme-corp
    
    -- Subscription & billing
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'starter',
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active',
    billing_email VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    
    -- Branding & customization
    logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#DAA520',
    secondary_color VARCHAR(7) DEFAULT '#B8860B',
    custom_css TEXT,
    custom_domain VARCHAR(255),
    
    -- Feature flags & limits
    max_users INTEGER DEFAULT 5,
    max_customers INTEGER DEFAULT 10000,
    features JSONB DEFAULT '{}', -- Feature toggles
    settings JSONB DEFAULT '{}', -- Organization settings
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_domain ON organizations(domain);
CREATE INDEX idx_organizations_subdomain ON organizations(subdomain);
CREATE INDEX idx_organizations_subscription ON organizations(subscription_tier, subscription_status);

-- ==================== USER MANAGEMENT & RBAC ====================

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255), -- NULL for SSO users
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en',
    
    -- Authorization
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    permissions JSONB DEFAULT '[]',
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- SSO Integration
    sso_provider VARCHAR(50), -- 'google', 'okta', 'azure', etc.
    sso_id VARCHAR(255),
    sso_metadata JSONB,
    
    -- Session & security
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

-- Create indexes
CREATE UNIQUE INDEX idx_users_email_org ON users(email, organization_id);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_sso ON users(sso_provider, sso_id);
CREATE INDEX idx_users_role ON users(role);

-- ==================== ROLE-BASED ACCESS CONTROL ====================

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_roles_name_org ON roles(name, organization_id);

-- User roles mapping (many-to-many)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_user_roles_unique ON user_roles(user_id, role_id);

-- ==================== CUSTOMER DATA (Multi-Tenant) ====================

-- Customers table with RLS
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Customer identification
    external_id VARCHAR(255), -- Client's customer ID
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    
    -- Churn prediction features
    credit_score INTEGER,
    age INTEGER,
    tenure INTEGER,
    balance DECIMAL(12,2),
    num_products INTEGER,
    has_credit_card BOOLEAN,
    is_active_member BOOLEAN,
    estimated_salary DECIMAL(12,2),
    geography VARCHAR(100),
    gender VARCHAR(50),
    
    -- Prediction results
    churn_probability DECIMAL(5,4), -- 0.0000 to 1.0000
    churn_risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    last_prediction_at TIMESTAMP WITH TIME ZONE,
    prediction_model VARCHAR(100),
    
    -- Status & metadata
    status VARCHAR(20) DEFAULT 'active',
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Create indexes
CREATE INDEX idx_customers_organization ON customers(organization_id);
CREATE INDEX idx_customers_external_id ON customers(organization_id, external_id);
CREATE INDEX idx_customers_email ON customers(organization_id, email);
CREATE INDEX idx_customers_churn_risk ON customers(organization_id, churn_risk_level);

-- Enable RLS on customers table
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see customers from their organization
CREATE POLICY customers_organization_policy ON customers
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- ==================== PREDICTION HISTORY (Multi-Tenant) ====================

CREATE TABLE prediction_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Prediction details
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    prediction_value DECIMAL(5,4) NOT NULL,
    confidence_score DECIMAL(5,4),
    
    -- Features used
    features_used JSONB NOT NULL,
    feature_importance JSONB,
    
    -- Metadata
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    predicted_by UUID REFERENCES users(id),
    response_time_ms INTEGER,
    
    -- A/B Testing
    ab_test_id VARCHAR(100),
    model_variant VARCHAR(50)
);

CREATE INDEX idx_prediction_history_organization ON prediction_history(organization_id);
CREATE INDEX idx_prediction_history_customer ON prediction_history(customer_id);
CREATE INDEX idx_prediction_history_model ON prediction_history(model_name, model_version);
CREATE INDEX idx_prediction_history_date ON prediction_history(predicted_at);

-- Enable RLS
ALTER TABLE prediction_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY prediction_history_organization_policy ON prediction_history
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- ==================== API KEYS & INTEGRATIONS ====================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed API key
    key_prefix VARCHAR(20) NOT NULL, -- First few chars for identification
    
    -- Permissions & limits
    permissions JSONB DEFAULT '[]',
    rate_limit_per_hour INTEGER DEFAULT 1000,
    allowed_ips INET[] DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_api_keys_organization ON api_keys(organization_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- ==================== AUDIT LOGS (Compliance) ====================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL, -- 'user_login', 'prediction_made', 'data_export', etc.
    resource_type VARCHAR(100), -- 'customer', 'user', 'prediction', etc.
    resource_id UUID,
    
    -- Actor information
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Event data
    event_data JSONB DEFAULT '{}',
    old_values JSONB,
    new_values JSONB,
    
    -- Metadata
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255)
);

CREATE INDEX idx_audit_logs_organization ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_date ON audit_logs(occurred_at);

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_logs_organization_policy ON audit_logs
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- ==================== DATA EXPORT REQUESTS (GDPR) ====================

CREATE TABLE data_export_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Request details
    requested_by UUID NOT NULL REFERENCES users(id),
    export_type VARCHAR(50) NOT NULL, -- 'customer_data', 'prediction_history', 'full_export'
    filters JSONB DEFAULT '{}', -- Export filters
    
    -- Processing
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    file_url TEXT, -- S3 URL or similar
    file_size_bytes BIGINT,
    expires_at TIMESTAMP WITH TIME ZONE, -- When download link expires
    
    -- Metadata
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

CREATE INDEX idx_data_exports_organization ON data_export_requests(organization_id);
CREATE INDEX idx_data_exports_user ON data_export_requests(requested_by);
CREATE INDEX idx_data_exports_status ON data_export_requests(status);

-- ==================== SSO CONFIGURATIONS ====================

CREATE TABLE sso_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Provider details
    provider VARCHAR(50) NOT NULL, -- 'saml', 'oauth', 'oidc'
    provider_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Configuration
    config JSONB NOT NULL DEFAULT '{}', -- Provider-specific config
    metadata JSONB DEFAULT '{}',
    
    -- SAML specific
    entity_id VARCHAR(255),
    sso_url TEXT,
    certificate TEXT,
    
    -- OAuth/OIDC specific
    client_id VARCHAR(255),
    client_secret_encrypted TEXT,
    discovery_url TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_sso_configs_organization ON sso_configurations(organization_id);

-- ==================== FEATURE FLAGS ====================

CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE, -- NULL = global flag
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    
    -- Rollout configuration
    rollout_percentage INTEGER DEFAULT 0, -- 0-100
    rollout_rules JSONB DEFAULT '{}', -- Complex rollout rules
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_feature_flags_name_org ON feature_flags(name, organization_id);

-- ==================== FUNCTIONS & TRIGGERS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sso_configurations_updated_at BEFORE UPDATE ON sso_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_feature_flags_updated_at BEFORE UPDATE ON feature_flags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to set current organization context for RLS
CREATE OR REPLACE FUNCTION set_organization_context(org_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', org_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get current organization context
CREATE OR REPLACE FUNCTION get_organization_context()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true)::uuid;
END;
$$ LANGUAGE plpgsql;

-- ==================== DEFAULT ROLES & PERMISSIONS ====================

-- Insert default permission structure (run after organization creation)
CREATE OR REPLACE FUNCTION create_default_roles(org_id UUID)
RETURNS void AS $$
BEGIN
    -- Admin role
    INSERT INTO roles (organization_id, name, description, permissions) VALUES 
    (org_id, 'admin', 'Full system administrator', 
     '["user.create", "user.read", "user.update", "user.delete", 
       "customer.create", "customer.read", "customer.update", "customer.delete",
       "prediction.create", "prediction.read", "analytics.read", 
       "organization.read", "organization.update", "api.manage", 
       "export.create", "audit.read"]'::jsonb);
    
    -- Manager role
    INSERT INTO roles (organization_id, name, description, permissions) VALUES 
    (org_id, 'manager', 'Team manager with user management', 
     '["user.read", "user.update", "customer.create", "customer.read", 
       "customer.update", "prediction.create", "prediction.read", 
       "analytics.read", "export.create"]'::jsonb);
    
    -- User role
    INSERT INTO roles (organization_id, name, description, permissions) VALUES 
    (org_id, 'user', 'Standard user access', 
     '["customer.read", "customer.update", "prediction.create", 
       "prediction.read", "analytics.read"]'::jsonb);
    
    -- Read-only role
    INSERT INTO roles (organization_id, name, description, permissions) VALUES 
    (org_id, 'viewer', 'Read-only access', 
     '["customer.read", "prediction.read", "analytics.read"]'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- ==================== SAMPLE DATA (Development) ====================

-- Insert sample organization
INSERT INTO organizations (name, slug, subdomain, subscription_tier) 
VALUES ('Acme Corporation', 'acme-corp', 'acme-corp', 'enterprise');

-- Get the organization ID for sample data
DO $$
DECLARE 
    org_id UUID;
    admin_user_id UUID;
BEGIN
    SELECT id INTO org_id FROM organizations WHERE slug = 'acme-corp';
    
    -- Create default roles
    PERFORM create_default_roles(org_id);
    
    -- Insert sample admin user
    INSERT INTO users (organization_id, email, first_name, last_name, role, is_admin) 
    VALUES (org_id, 'admin@acme-corp.com', 'John', 'Admin', 'admin', true)
    RETURNING id INTO admin_user_id;
    
    -- Set organization context for RLS
    PERFORM set_organization_context(org_id);
    
    -- Insert sample customers
    INSERT INTO customers (organization_id, external_id, email, first_name, last_name, 
                          credit_score, age, tenure, balance, num_products, 
                          has_credit_card, is_active_member, estimated_salary, 
                          geography, gender, created_by) VALUES
    (org_id, 'CUST001', 'john.doe@example.com', 'John', 'Doe', 
     650, 35, 5, 50000.00, 2, true, true, 75000.00, 'Germany', 'Male', admin_user_id),
    (org_id, 'CUST002', 'jane.smith@example.com', 'Jane', 'Smith', 
     720, 42, 8, 120000.00, 3, true, false, 95000.00, 'France', 'Female', admin_user_id);
END $$;
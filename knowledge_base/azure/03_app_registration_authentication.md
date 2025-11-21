# Azure AD App Registrations and Authentication

## Overview

An App Registration in Azure Active Directory is a configuration that allows applications to authenticate users and access Microsoft cloud services (like Microsoft Graph, Azure resources, or custom APIs). It acts as the identity of your application in Azure AD.

## What is an App Registration?

An App Registration defines:
- **Who can use the app**: Single tenant, multi-tenant, or public
- **How users authenticate**: OAuth 2.0, OpenID Connect flows
- **What the app can access**: API permissions (delegated or application)
- **Credentials**: Client secrets or certificates for authentication

**Think of it as**: The "identity card" for your application in Azure AD.

## Key Concepts

### Application (Client) ID

- Unique GUID identifier for your app
- Used by applications to identify themselves to Azure AD
- Public information (not a secret)
- Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`

### Object ID

- Internal Azure AD identifier for the app registration object
- Different from Application ID
- Used for management operations (updating app, adding secrets)

### Client Secrets vs Certificates

**Client Secrets** (passwords):
- String-based credentials
- Easier to use for development
- Less secure than certificates
- **Must be rotated regularly** (recommended: every 6 months)
- Shown **only once** during creation

**Certificates** (public key authentication):
- More secure than secrets
- Harder to compromise
- Recommended for production
- Can have longer expiration (up to 2 years)

## Supported Account Types (Sign-in Audience)

### 1. Single Tenant (AzureADMyOrg)

**Who can sign in**: Only users in your Azure AD tenant

**Use when**:
- Internal company applications
- Line-of-business apps for employees only
- Highest security (most restrictive)

**Example**: Employee portal, internal dashboard, company intranet

**Security Level**: ⭐⭐⭐⭐⭐ (Most Secure)

### 2. Multi-Tenant (AzureADMultipleOrgs)

**Who can sign in**: Users from any Azure AD tenant (other organizations)

**Use when**:
- SaaS applications serving multiple companies
- ISV applications sold to other organizations
- B2B applications

**Example**: Project management SaaS, CRM system, collaboration tools

**Security Level**: ⭐⭐⭐ (Moderate - requires careful permission design)

### 3. Public (AzureADandPersonalMicrosoftAccount)

**Who can sign in**: Azure AD users + personal Microsoft accounts (Outlook.com, Xbox, etc.)

**Use when**:
- Consumer-facing applications
- Apps targeting general public
- Mixed audience (business + personal users)

**Example**: Mobile games, consumer productivity apps, social platforms

**Security Level**: ⭐⭐ (Less Restrictive - broader attack surface)

### Choosing the Right Type

| App Scenario | Recommended Type |
|--------------|------------------|
| Internal company app | Single Tenant ⭐⭐⭐⭐⭐ |
| SaaS for businesses | Multi-Tenant |
| Consumer mobile app | Public |
| API for internal services | Single Tenant ⭐⭐⭐⭐⭐ |
| Partner integration | Multi-Tenant |

**Default Recommendation**: Always start with Single Tenant (most secure) unless you have a specific reason to be broader.

## OAuth 2.0 and Redirect URIs

### What is a Redirect URI?

After user authenticates, Azure AD redirects them back to your application. The redirect URI specifies where to send the authentication response.

**Example Flow**:
```
1. User clicks "Login" in your app
2. App redirects user to Azure AD login page
3. User enters credentials
4. Azure AD authenticates user
5. Azure AD redirects back to: https://yourapp.com/callback ← Redirect URI
6. App receives authentication token
```

### Types of Redirect URIs

**1. Web Redirect URIs** (for server-side apps):
- Format: `https://app.company.com/auth/callback`
- Used by confidential clients (servers that can keep secrets)
- Supports authorization code flow with client secret

**2. SPA Redirect URIs** (for single-page applications):
- Format: `http://localhost:3000` or `https://app.company.com`
- Used by public clients (JavaScript apps in browser)
- Requires PKCE (Proof Key for Code Exchange) for security
- Cannot use client secrets (secrets would be exposed in browser code)

### Redirect URI Rules

1. **Must be exact match**: Azure AD checks exact string match
   - ✓ `https://app.com/callback`
   - ✗ `https://app.com/callback/` (trailing slash is different!)

2. **HTTPS required in production**: HTTP only allowed for localhost
   - ✓ `https://app.com/callback`
   - ✓ `http://localhost:3000`
   - ✗ `http://app.com/callback` (insecure!)

3. **Multiple URIs allowed**: Different URIs for dev/staging/prod
   - Dev: `http://localhost:3000`
   - Staging: `https://staging.app.com/callback`
   - Prod: `https://app.com/callback`

## Client Secrets - Detailed Guide

### Why Client Secrets Exist

Client secrets prove the app's identity to Azure AD. When your app requests an access token, it shows:
- Application ID: "I am app A1B2C3D4"
- Client Secret: "Here's proof I'm really that app" (like a password)

### Creating Client Secrets

**Required Information**:
- Description: Human-readable name (e.g., "Production API Secret - Expires June 2024")
- Expiration: 1, 3, 6, 12, or 24 months

**Best Practices**:
- **Use descriptive names** including expiration date
- **Choose shortest acceptable expiration** (6 months recommended)
- **Set calendar reminders** to rotate before expiration

### Secret Value - CRITICAL WARNING ⚠️

**The secret value is shown ONLY ONCE during creation!**

When you create a secret, you see:
```
Secret ID: a1b2c3d4-e5f6-...
Secret Value: abc123~DefGhi456.JklMno789-PqrStu  ← COPY THIS NOW!
Expires: 2024-06-21
```

**If you lose the secret value**:
- You CANNOT retrieve it again
- You must create a NEW secret
- Update your application with new secret

### Storing Client Secrets Securely

**✓ Secure Storage**:
- Azure Key Vault (best for production)
- AWS Secrets Manager
- HashiCorp Vault
- Environment variables (not in code)
- Secure password managers (for development)

**✗ NEVER Store Secrets In**:
- Source code files
- Git repositories
- Configuration files committed to version control
- Email or chat messages
- Unencrypted databases
- Client-side code (JavaScript, mobile apps)

### Secret Rotation

**Why Rotate**:
- Secrets can be compromised
- Reduces window of vulnerability
- Compliance requirements (SOC 2, ISO 27001)

**Rotation Process**:
```
1. Create new secret (Secret B) while old one (Secret A) still valid
2. Update application to use Secret B
3. Test application with Secret B
4. After successful deployment, delete Secret A
5. Set reminder to rotate Secret B before expiration
```

**Timing**: Rotate at least 1 month before expiration to allow for issues.

## Application Permissions

### Delegated vs Application Permissions

**Delegated Permissions** (user context):
- App acts on behalf of a signed-in user
- User must grant consent
- Access limited by user's permissions
- Example: App reads user's emails (only emails the user can access)

**Application Permissions** (app context):
- App acts as itself (no user signed in)
- Admin must grant consent
- App has broad access
- Example: Daemon service reading all users' calendars

### Common Microsoft Graph Permissions

**User Management**:
- `User.Read`: Read signed-in user's profile (delegated)
- `User.Read.All`: Read all users' profiles (delegated or application)
- `User.ReadWrite.All`: Create/update users (application)

**Group Management**:
- `Group.Read.All`: Read all groups
- `Group.ReadWrite.All`: Create/update groups
- `GroupMember.ReadWrite.All`: Manage group membership

**Application Management**:
- `Application.Read.All`: Read app registrations
- `Application.ReadWrite.All`: Create/update app registrations

### Permission Consent

**User Consent**: User clicks "Accept" when logging in to app
**Admin Consent**: Required for high-privilege permissions
- Granted by Global Admin or Privileged Role Admin
- Applies to all users in organization
- Required for Application permissions

## App Registration Scenarios

### Scenario 1: Web Application with User Login

**Requirements**:
- Users log in with their Azure AD accounts
- App reads user profile and calendar

**Configuration**:
```
Sign-in Audience: Single Tenant (employees only)
Platform: Web
Redirect URIs: ["https://app.company.com/auth/callback"]
Delegated Permissions: User.Read, Calendars.Read
Client Secret: Yes (server can store securely)
```

### Scenario 2: Single-Page Application (React/Angular/Vue)

**Requirements**:
- JavaScript app in browser
- User login with Azure AD
- Access Microsoft Graph

**Configuration**:
```
Sign-in Audience: Single Tenant
Platform: SPA
Redirect URIs: ["http://localhost:3000", "https://app.company.com"]
Delegated Permissions: User.Read
Client Secret: No (public client, uses PKCE instead)
PKCE: Required (enabled automatically for SPA)
```

### Scenario 3: Backend Service (No User Interaction)

**Requirements**:
- Daemon/service running in background
- No user login
- Reads all users' emails for compliance

**Configuration**:
```
Sign-in Audience: Single Tenant
Platform: N/A (confidential client)
Redirect URIs: Not needed (client credentials flow)
Application Permissions: Mail.Read (with admin consent)
Client Secret: Yes (or certificate preferred)
```

### Scenario 4: Multi-Tenant SaaS Application

**Requirements**:
- Sold to multiple companies
- Each company's users log in with their own Azure AD

**Configuration**:
```
Sign-in Audience: Multi-Tenant
Platform: Web
Redirect URIs: ["https://saas.com/auth/callback"]
Delegated Permissions: User.Read, Files.ReadWrite
Admin Consent: Required from each customer's admin
```

## Verification Best Practices

### After Creating App Registration

**Immediately verify**:
```
1. Create app → Returns Object ID and Application ID
2. GET app registration by Object ID
3. Verify:
   - Display name correct ✓
   - Sign-in audience correct (Single/Multi/Public) ✓
   - App ID matches what you'll use in code ✓
   - Redirect URIs empty (if not set) ✓
```

### After Adding Redirect URI

```
1. Add redirect URI
2. GET app registration
3. Verify:
   - New URI appears in web.redirectUris or spa.redirectUris ✓
   - Existing URIs still present ✓
   - Correct platform (web vs spa) ✓
```

### After Creating Client Secret

```
1. Create secret → Returns secret value
2. IMMEDIATELY copy secret value (can't retrieve again!)
3. Store secret securely (Key Vault, env vars)
4. GET app registration
5. Verify:
   - Password credential exists (but can't see value)
   - Expiration date correct ✓
   - Description matches ✓
6. Test secret by authenticating with it
```

## Common Authentication Flows

### Authorization Code Flow (Most Common)

**Use for**: Web applications (server-side)

**Steps**:
```
1. User clicks "Login"
2. App redirects to Azure AD
3. User authenticates
4. Azure AD redirects with authorization code
5. App exchanges code for access token (using client secret)
6. App uses access token to call APIs
```

**Security**: ⭐⭐⭐⭐⭐ (Client secret never exposed to browser)

### Authorization Code Flow with PKCE

**Use for**: Single-page applications, mobile apps (public clients)

**Steps**:
```
1. App generates code verifier and code challenge
2. User clicks "Login"
3. App redirects to Azure AD with code challenge
4. User authenticates
5. Azure AD redirects with authorization code
6. App exchanges code + code verifier for token (no client secret)
7. App uses access token to call APIs
```

**Security**: ⭐⭐⭐⭐ (No secret, but PKCE prevents code interception)

### Client Credentials Flow

**Use for**: Daemon services, background jobs (no user)

**Steps**:
```
1. App authenticates with Application ID + Client Secret (or certificate)
2. Azure AD returns access token
3. App uses token to call APIs (acts as itself, not a user)
```

**Security**: ⭐⭐⭐⭐⭐ (if using certificate), ⭐⭐⭐⭐ (if using secret)

## Security Recommendations

### App Registration Security

1. **Use Single Tenant** by default (most restrictive)
2. **Prefer certificates** over secrets for production
3. **Limit permissions** to minimum necessary (least privilege)
4. **Enable MFA** for users authenticating to app
5. **Rotate secrets** every 6 months
6. **Monitor audit logs** for suspicious app usage

### Client Secret Security

1. **Never commit to git** - use .gitignore
2. **Use Key Vault** in production
3. **Set expiration** (never create permanent secrets)
4. **Descriptive names** with expiration date
5. **Rotate proactively** before expiration
6. **Revoke immediately** if compromised

### Redirect URI Security

1. **Use HTTPS** in production (except localhost)
2. **Exact match only** (no wildcards accepted)
3. **Validate in code** (double-check redirect matches expected)
4. **Remove unused URIs** (reduce attack surface)

## Troubleshooting

### Error: "AADSTS50011: Reply URL mismatch"

**Cause**: Redirect URI in request doesn't match registered URIs
**Solution**: Check exact match (including trailing slashes, http vs https)

### Error: "AADSTS7000215: Invalid client secret"

**Cause**: Wrong secret, or secret expired
**Solution**: Create new secret, update app configuration

### Error: "AADSTS650056: App requires admin consent"

**Cause**: App has Application permissions (not Delegated)
**Solution**: Admin must grant consent in Azure Portal

### Error: "AADSTS50020: User account from external provider not accepted"

**Cause**: App is Single Tenant but external user tried to login
**Solution**: Change to Multi-Tenant or invite user as guest

## References

- App Registration Overview: https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app
- OAuth 2.0 Flows: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow
- Microsoft Graph Permissions: https://learn.microsoft.com/en-us/graph/permissions-reference
- Client Credentials Flow: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow

---

**Keywords**: app registration, client secret, certificate, OAuth 2.0, redirect URI, sign-in audience, application permissions, delegated permissions, authorization code flow, PKCE, single tenant, multi-tenant

# Azure AD Common Errors and Troubleshooting Guide

## Overview

This document provides solutions to common errors encountered when working with Azure Active Directory and Microsoft Graph API operations.

## Authentication and Authorization Errors

### AADSTS50034: User account not found

**Error Message**: "User account 'user@company.com' does not exist in the 'tenant-id' directory"

**Cause**: The user doesn't exist in Azure AD, or you're using the wrong tenant

**Solutions**:
1. Verify the user exists: Check Azure Portal → Users
2. Check UPN spelling (common typos: @company.com vs @compamy.com)
3. Verify you're connecting to correct Azure AD tenant (check TENANT_ID in .env)
4. If user should exist, they may have been deleted (check Deleted Users)

---

### AADSTS50020: User from identity provider not accepted

**Error Message**: "The user account 'user@external.com' does not exist in tenant"

**Cause**: External user trying to access single-tenant app

**Solutions**:
1. **If app should be single-tenant**: Invite user as Guest (B2B)
2. **If app should support external users**: Change app to Multi-Tenant
3. **If user is in wrong directory**: User needs to sign in with correct account

---

### AADSTS7000215: Invalid client secret provided

**Error Message**: "Invalid client secret is provided"

**Cause**: Wrong secret, expired secret, or typo in secret value

**Solutions**:
1. **Check expiration**: Azure Portal → App → Certificates & secrets → Check expiry date
2. **Create new secret if expired**: Add new secret, update .env, delete old one
3. **Verify no typos**: Secret values are case-sensitive and include special characters
4. **Check for extra spaces**: Trim whitespace from secret in .env
5. **Verify correct app**: Ensure CLIENT_ID matches the app that owns the secret

**Prevention**:
- Set calendar reminders 1 month before secret expiration
- Use descriptive secret names with expiration dates

---

### AADSTS50011: Reply URL mismatch

**Error Message**: "The reply URL specified in the request does not match the reply URLs configured for the application"

**Cause**: Redirect URI in OAuth request doesn't exactly match registered URIs

**Solutions**:
1. **Check exact match**: Must match exactly (including trailing slashes, case, protocol)
   - ✗ `https://app.com/callback/` vs `https://app.com/callback`
   - ✗ `http://localhost:3000` vs `https://localhost:3000`
2. **Add missing URI**: Azure Portal → App → Authentication → Add redirect URI
3. **Platform mismatch**: Ensure URI is under correct platform (Web vs SPA)
4. **Check for typos**: Common: /callbac vs /callback

---

### AADSTS650051: Application requires admin consent

**Error Message**: "The application requires access to a service that your organization has not subscribed to or enabled"

**Cause**: App has Application permissions that require admin consent

**Solutions**:
1. **Grant admin consent**: Azure Portal → App → API permissions → "Grant admin consent"
2. **Check permissions**: Verify permissions are actually needed
3. **Use delegated permissions instead**: If acting on behalf of user, delegated may not require admin consent
4. **Request from admin**: Non-admins cannot grant application-level permissions

---

## Permission Errors

### Authorization_RequestDenied

**Error Message**: "Insufficient privileges to complete the operation"

**Cause**: Service Principal or user lacks required permissions

**Solutions for Service Principals**:
1. **Check API permissions**: Azure Portal → App → API permissions
2. **Verify admin consent granted**: Must show green checkmarks "Granted for..."
3. **Wait for propagation**: Can take 5-10 minutes after granting consent
4. **Check specific permission**: Ensure exact permission needed is granted
   - User.Read.All vs User.ReadWrite.All (write requires the latter)
   - Group.Read.All vs GroupMember.ReadWrite.All (membership changes need latter)

**Required Permissions by Operation**:
| Operation | Permission Needed |
|-----------|-------------------|
| Create user | User.ReadWrite.All |
| Read user | User.Read.All or User.ReadWrite.All |
| Reset password | User.ReadWrite.All |
| Create group | Group.ReadWrite.All |
| Add group member | GroupMember.ReadWrite.All |
| Create app registration | Application.ReadWrite.All |

---

### Request_ResourceNotFound

**Error Message**: "Resource 'xxx' does not exist"

**Cause**: The object (user, group, app) you're trying to access doesn't exist

**Solutions**:
1. **Verify ID**: Check Object ID or UPN is correct (no typos)
2. **Check deleted objects**: Object may be in Deleted Users/Groups (soft delete)
3. **Wrong tenant**: Ensure you're connected to correct Azure AD tenant
4. **Case sensitivity**: Some IDs are case-sensitive
5. **Recent creation**: If just created, wait 1-2 minutes for consistency

---

## Data Validation Errors

### Request_BadRequest: Invalid password

**Error Message**: "Password does not meet complexity requirements"

**Cause**: Password doesn't meet Azure AD password policy

**Requirements**:
- Minimum 8 characters (12-16 recommended)
- Contains 3 of 4: uppercase, lowercase, number, special character
- Not in list of banned passwords (common words, company name, etc.)

**Solution**: Generate stronger password
```python
# Example secure password generation
import secrets
import string

alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
password = ''.join(secrets.choice(alphabet) for i in range(16))
```

---

### Request_MultipleObjectsWithSameKeyValue

**Error Message**: "Another object with the same value for property userPrincipalName already exists"

**Cause**: Trying to create user/group with UPN/name that already exists

**Solutions**:
1. **Check if object exists**: GET user/group to retrieve existing object
2. **Update instead of create**: If object should exist, update it instead
3. **Use different UPN**: If creating new user, choose different email
4. **Check deleted objects**: Object may be soft-deleted (recoverable for 30 days)
   - Restore deleted object, or
   - Permanently delete (hard delete) to free up the UPN

---

### Invalid request body

**Error Message**: "The request body contains invalid data"

**Cause**: Malformed JSON or missing required fields

**Solutions**:
1. **Validate JSON**: Ensure proper JSON formatting (quotes, commas, brackets)
2. **Check required fields**: Include all required properties
   - User: userPrincipalName, displayName, mailNickname, passwordProfile
   - Group: displayName, mailNickname, mailEnabled, securityEnabled
3. **Check data types**: Ensure correct types (boolean vs string, etc.)
4. **Remove invalid properties**: Some properties are read-only (id, createdDateTime)

---

## Rate Limiting and Throttling

### Request_ThrottledPermanently

**Error Message**: "The request has been throttled"

**Cause**: Too many requests in short time period

**Microsoft Graph API Limits**:
- ~2000 requests per second per app
- ~10,000 requests per 10 minutes per user

**Solutions**:
1. **Implement retry with exponential backoff**:
   ```
   Retry after 2 seconds
   If still throttled, retry after 4 seconds
   If still throttled, retry after 8 seconds
   Maximum 3-5 retries
   ```

2. **Batch requests**: Use Microsoft Graph batch endpoint for multiple operations
3. **Reduce frequency**: Space out requests over time
4. **Check Retry-After header**: Response includes recommended wait time

**Prevention**:
- Don't create loops that rapidly call API
- Use batch operations for bulk changes
- Cache data when possible (don't refetch same data repeatedly)

---

## User Management Specific Errors

### Password cannot be changed for synced users

**Error Message**: "Property 'passwordProfile' is read-only for this user"

**Cause**: User is synced from on-premises Active Directory

**Solutions**:
1. **Reset password in on-premises AD**: Changes must be made on-prem
2. **Wait for sync**: Azure AD Connect syncs changes (typically every 30 min)
3. **Force sync**: On-prem admin can force immediate sync
4. **Verify user type**: Check if user is cloud-only or synced (dirSyncEnabled property)

**Identification**: Synced users have `onPremisesSyncEnabled: true`

---

### User is already a member of the maximum number of groups

**Error Message**: "The user is already a member of the maximum number of Azure AD groups"

**Cause**: Azure AD has group membership limits per user

**Limits**:
- Azure AD Free: 500 groups per user
- Azure AD Premium: Unlimited

**Solutions**:
1. **Remove unnecessary group memberships**: Audit and clean up
2. **Use dynamic groups**: Membership based on user attributes
3. **Upgrade to Premium**: If hitting limit frequently

---

## Group Management Specific Errors

### Cannot add member to a dynamic group

**Error Message**: "Cannot add member to dynamic membership group"

**Cause**: Trying to manually add member to a group with dynamic membership rules

**Solutions**:
1. **Update user attributes**: Modify user properties to match membership rule
2. **Change group to assigned membership**: Remove dynamic membership rule
3. **Create separate group**: Use assigned membership group instead

---

### Group email address already exists

**Error Message**: "The mail nickname is already in use"

**Cause**: Another group has the same mail nickname

**Solutions**:
1. **Use different mail nickname**: Must be unique across all groups
2. **Find existing group**: Search for group with that nickname
3. **Delete old group**: If no longer needed, free up the nickname

---

## App Registration Specific Errors

### Application already has maximum allowed number of secrets

**Error Message**: "Cannot add more than X client secrets"

**Cause**: Limit of ~48 client secrets per app registration

**Solutions**:
1. **Delete expired secrets**: Remove old/unused secrets first
2. **Clean up**: Audit secrets, delete ones no longer in use
3. **Use certificates**: Switch to certificate-based auth (no limit)

---

## Network and Connectivity Errors

### Connection timeout

**Error Message**: "The operation timed out"

**Cause**: Network issues or Azure AD service unavailable

**Solutions**:
1. **Check internet connection**: Verify connectivity to internet
2. **Check Azure AD service status**: Visit https://status.azure.com
3. **Retry operation**: May be temporary network issue
4. **Increase timeout**: If operation is legitimately slow
5. **Check firewall**: Ensure outbound HTTPS (443) not blocked

---

## Debugging Strategies

### 1. Check Azure AD Audit Logs

**Purpose**: See what actually happened

**Steps**:
```
1. Azure Portal → Azure Active Directory → Audit logs
2. Filter by:
   - Activity: Specific operation (e.g., "Add user")
   - Date: When error occurred
   - Status: Failed
3. Click failed operation → See detailed error
```

### 2. Use Microsoft Graph Explorer

**Purpose**: Test API calls interactively

**Steps**:
```
1. Go to https://developer.microsoft.com/graph/graph-explorer
2. Sign in
3. Try your operation (e.g., GET /users)
4. See exact request/response
5. Debug permissions, syntax, etc.
```

### 3. Enable Verbose Logging

**In your application**:
```python
import logging

# Set to DEBUG for detailed output
logging.basicConfig(level=logging.DEBUG)

# Azure SDK will log detailed request/response
```

### 4. Check Propagation Delays

Many operations have propagation delays:
- **Permission changes**: 5-10 minutes
- **Group membership**: 5-15 minutes
- **App registration changes**: 1-5 minutes

**Solution**: Wait and retry before assuming failure

---

## Error Response Format

Microsoft Graph errors follow this structure:

```json
{
  "error": {
    "code": "Request_ResourceNotFound",
    "message": "Resource 'abc123' does not exist or one of its queried reference-property objects are not present.",
    "innerError": {
      "date": "2024-01-15T10:30:00",
      "request-id": "xyz789",
      "client-request-id": "xyz789"
    }
  }
}
```

**Key fields**:
- `code`: Machine-readable error code (use for programmatic handling)
- `message`: Human-readable description
- `request-id`: For Microsoft support tickets
- `innerError`: Additional debugging info

---

## Common Troubleshooting Workflow

```
1. Read the error message carefully
   ↓
2. Check error code (AADSTS50xxx, Request_xxx)
   ↓
3. Verify credentials (TENANT_ID, CLIENT_ID, SECRET)
   ↓
4. Check permissions in Azure Portal
   ↓
5. Review audit logs for failed operation
   ↓
6. Test with Microsoft Graph Explorer
   ↓
7. Check for propagation delays (wait 10 min)
   ↓
8. Verify object exists and ID is correct
   ↓
9. Check network connectivity
   ↓
10. If still failing, check Azure status page
```

---

## Prevention Best Practices

1. **Validate before executing**: Check user/group exists before operating on it
2. **Handle errors gracefully**: Implement try-catch and retry logic
3. **Log everything**: Capture error details for debugging
4. **Test in dev first**: Don't test in production
5. **Monitor proactively**: Set up alerts for error rates
6. **Keep credentials fresh**: Rotate secrets before expiration
7. **Document**: Note which errors you've encountered and solutions

---

## Getting Help

**When you can't resolve an error**:

1. **Azure Support**: If you have support plan
2. **Microsoft Q&A**: https://learn.microsoft.com/answers
3. **Stack Overflow**: Tag with [azure-active-directory] or [microsoft-graph-api]
4. **GitHub Issues**: For SDK-specific problems

**Include in support requests**:
- Error code and full error message
- Request ID (from error response)
- Timestamp of error
- Operation you were attempting
- App ID and Tenant ID (not the secret!)

---

**Keywords**: Azure AD errors, AADSTS codes, troubleshooting, Microsoft Graph errors, authentication errors, permission errors, rate limiting, throttling, error codes

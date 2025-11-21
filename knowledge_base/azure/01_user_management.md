# Azure Active Directory User Management

## Overview

Azure Active Directory (Azure AD), now called Microsoft Entra ID, is Microsoft's cloud-based identity and access management service. User management in Azure AD involves creating, reading, updating, and managing user accounts for an organization.

## What is an Azure AD User?

An Azure AD user is a digital identity that represents a person in an organization. Each user has:

- **User Principal Name (UPN)**: The user's sign-in name, typically in email format (e.g., john.doe@company.com)
- **Object ID**: A unique GUID identifier assigned by Azure AD
- **Display Name**: The user's full name as shown in the directory
- **Attributes**: Additional information like job title, department, phone number, office location

## Creating Users in Azure AD

### User Account Types

1. **Cloud-only accounts**: Users created directly in Azure AD
2. **Synchronized accounts**: Users synced from on-premises Active Directory
3. **Guest users**: External users invited to access resources (B2B)

### Required Information for User Creation

To create a user, you must provide:
- User Principal Name (UPN) - must be unique in the directory
- Display Name - the user's full name
- Mail Nickname - typically the part before @ in the email
- Password - temporary password for first login

### Password Policies

When creating users:
- Default password complexity requirements apply (minimum 8 characters, mix of uppercase, lowercase, numbers, special characters)
- **Best Practice**: Set `forceChangePasswordNextSignIn: true` so users create their own secure password on first login
- Temporary passwords should be shared securely (phone, in-person), never via email

### Example User Creation

```json
{
  "accountEnabled": true,
  "displayName": "Alice Johnson",
  "mailNickname": "alice.johnson",
  "userPrincipalName": "alice.johnson@company.com",
  "passwordProfile": {
    "password": "TempPassword123!",
    "forceChangePasswordNextSignIn": true
  },
  "jobTitle": "Software Engineer",
  "department": "Engineering",
  "officeLocation": "San Francisco"
}
```

## Reading and Retrieving User Information

### Get User by ID

Users can be retrieved using:
- Object ID (GUID): `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- User Principal Name (UPN): `alice.johnson@company.com`

### User Attributes Available

When retrieving a user, you can access:
- **Identity**: id, userPrincipalName, mail, displayName
- **Employment**: jobTitle, department, officeLocation, employeeId
- **Contact**: businessPhones, mobilePhone, mail
- **Location**: city, state, country, postalCode, streetAddress
- **Account Status**: accountEnabled, createdDateTime
- **Type**: userType (Member or Guest)

### Use Cases for Getting Users

1. **Verification**: After creating a user, immediately retrieve to confirm creation
2. **Troubleshooting**: Check if user exists and account status when user reports login issues
3. **Audit**: Review user attributes to ensure they match organizational records
4. **Investigation**: Before taking action (like password reset), check current account state

## Updating Users

### Common Update Operations

1. **Update Profile Information**:
   - Change job title, department, office location
   - Update contact information
   - Modify display name

2. **Account Management**:
   - Enable or disable account
   - Update password
   - Change user type

### Example: Update Job Title

```json
{
  "jobTitle": "Senior Software Engineer",
  "department": "Engineering - Platform Team"
}
```

## Password Reset

### When to Reset Passwords

- User forgot their password
- Multiple failed login attempts (potential lockout)
- Security incident requiring password change
- Onboarding new users (generate temporary password)

### Password Reset Best Practices

1. **Always set forceChangePasswordNextSignIn: true**
   - User must create their own password on next login
   - Prevents shared knowledge of the password

2. **Generate Secure Temporary Passwords**
   - Minimum 12-16 characters
   - Include uppercase, lowercase, numbers, special characters
   - Use cryptographic random generation (not predictable patterns)

3. **Secure Communication**
   - Share temporary password via phone or in-person
   - **Never send passwords via email** (can be intercepted)
   - Consider using secure password sharing tools

4. **Time-bound**
   - Temporary passwords should expire after first use
   - Set short expiration windows (24-48 hours)

### Example Password Reset Flow

```
1. User reports: "I can't log in"
2. Admin retrieves user: Get user account details
3. Admin checks: Account enabled? Any sign-in errors?
4. Admin diagnoses: Multiple failed attempts due to wrong password
5. Admin resets: Generate secure temporary password
6. Admin verifies: Retrieve user again, check if password update timestamp changed
7. Admin shares: Call user with temporary password
8. User logs in: Forced to create new password
```

## Deleting Users

### Soft Delete (Default)

When a user is deleted:
- User is moved to "Deleted Users" container
- Recoverable for 30 days
- After 30 days, permanently deleted (hard delete)

### Hard Delete (Permanent)

- Immediate permanent deletion
- Cannot be recovered
- Use only when required by compliance/legal requirements

### Best Practices for User Deletion

1. **Backup first**: Export user's data if needed
2. **Transfer ownership**: Reassign files, emails, resources to another user
3. **Revoke access**: Remove from all groups and applications before deleting
4. **Document**: Record why user was deleted (offboarding, termination, etc.)

## Common User Management Scenarios

### Scenario 1: New Employee Onboarding

**Steps:**
1. Create user account with temporary password
2. Set job title, department, office location
3. Add user to appropriate groups (department group, resource access groups)
4. Assign licenses (Microsoft 365, Azure AD Premium, etc.)
5. Send welcome email with temporary password (via phone/secure channel)
6. User logs in, creates permanent password
7. Verify user can access required resources

### Scenario 2: Employee Transfer (Department Change)

**Steps:**
1. Update user's department and job title
2. Remove from old department groups
3. Add to new department groups
4. Update manager field
5. Verify access to new resources
6. Remove access to old department resources if needed

### Scenario 3: Security Incident Response

**Steps:**
1. Immediately disable account (set accountEnabled: false)
2. Revoke all active sessions (force sign-out)
3. Reset password
4. Review sign-in logs for suspicious activity
5. After investigation: Re-enable account with new password

### Scenario 4: User Locked Out

**Steps:**
1. Retrieve user information to check account status
2. Check sign-in logs for failed attempts
3. Common causes:
   - Wrong password (reset password)
   - Account disabled (enable account)
   - Conditional Access policy blocking (review policies)
   - MFA issues (review MFA settings)
4. Take appropriate action based on diagnosis
5. Verify resolution by having user attempt login

## Account Status and States

### Account Enabled vs Disabled

- **Enabled (accountEnabled: true)**: User can sign in
- **Disabled (accountEnabled: false)**: User cannot sign in (account blocked)

**When to disable:**
- Employee on leave (temporary)
- Security investigation
- Offboarding (before deletion)

### User Types

1. **Member**: Internal employees, default type
2. **Guest**: External collaborators (B2B users)

## User Provisioning Best Practices

### Security Best Practices

1. **Least Privilege**: Grant minimum necessary permissions
2. **Force Password Change**: Always on first login
3. **Strong Passwords**: Enforce complexity requirements
4. **MFA Enforcement**: Require multi-factor authentication
5. **Regular Audits**: Review user accounts monthly

### Naming Conventions

1. **UPN Format**: firstname.lastname@company.com (consistent across organization)
2. **Display Name**: "First Last" format
3. **Mail Nickname**: Match UPN prefix (part before @)

### Attributes to Always Set

- displayName
- jobTitle (helps with directory searches)
- department (for organization and access control)
- officeLocation (useful for remote/hybrid work)
- manager (organizational hierarchy)

## Verification After Operations

### Why Verification is Critical

1. **API calls may succeed but data may be wrong**: Azure AD APIs can return success even if eventual consistency hasn't completed
2. **Detect typos or formatting issues**: E.g., "JohnDoe" instead of "John Doe"
3. **Confirm permissions worked**: Verify you have necessary permissions
4. **Build confidence**: User operations are critical; verification ensures accuracy

### How to Verify

**After creating a user:**
1. Immediately call GET user API with the ID returned from creation
2. Compare:
   - UPN matches what you intended ✓
   - Display name is correct ✓
   - Account is enabled ✓
   - Department/title set correctly ✓

**After updating a user:**
1. GET user to see current state
2. Verify the specific attribute you updated changed
3. Check that other attributes weren't accidentally modified

**After password reset:**
1. GET user to check lastPasswordChangeDateTime
2. Verify timestamp updated to recent time
3. Attempt login if possible (in test environment)

## Common Errors and Solutions

### Error: "Another object with the same value already exists"

**Cause**: UPN must be unique; another user has this UPN
**Solution**: Check if user already exists, or use different UPN

### Error: "Insufficient privileges"

**Cause**: Service Principal lacks User.ReadWrite.All permission
**Solution**: Grant permission in Azure Portal and grant admin consent

### Error: "Invalid password"

**Cause**: Password doesn't meet complexity requirements
**Solution**: Ensure password has uppercase, lowercase, number, special char, minimum 8 chars

### Error: "Request_ResourceNotFound"

**Cause**: User doesn't exist with the specified ID/UPN
**Solution**: Verify ID/UPN is correct, check for typos

## Related Concepts

### Users vs Service Principals

- **Users**: Human identities (people)
- **Service Principals**: Application identities (apps, services)

### Users vs Groups

- **Users**: Individual identities
- **Groups**: Collections of users (for access control)
- Best practice: Assign permissions to groups, add users to groups

### Cloud Users vs Synced Users

- **Cloud users**: Created directly in Azure AD, managed in cloud only
- **Synced users**: Originate from on-premises AD, synced via Azure AD Connect
- **Important**: Synced users must be managed in on-premises AD (changes in Azure AD will be overwritten)

## References

- Microsoft Graph API User Resource: https://learn.microsoft.com/en-us/graph/api/resources/user
- Create User API: https://learn.microsoft.com/en-us/graph/api/user-post-users
- Get User API: https://learn.microsoft.com/en-us/graph/api/user-get
- Update User API: https://learn.microsoft.com/en-us/graph/api/user-update

---

**Keywords**: Azure AD, user management, create user, password reset, user principal name, UPN, account enabled, Microsoft Graph, Entra ID

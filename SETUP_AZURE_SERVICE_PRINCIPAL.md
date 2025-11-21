# Azure Service Principal Setup Guide

**Complete guide to configure Azure for the Azure Workforce Admin Agent**

---

## Overview

To use the Azure Admin Agent, you need to create a **Service Principal** in Azure AD with specific permissions. This guide walks you through the entire process.

**What you'll create:**
- Azure AD Service Principal (like a "robot user")
- API Permissions for Microsoft Graph
- Credentials (Tenant ID, Client ID, Secret)

**Time required:** ~15 minutes

---

## Prerequisites

- Azure subscription (free trial works!)
- Azure AD tenant
- Global Administrator or Privileged Role Administrator access
- Azure CLI installed (optional but recommended)

---

## Method 1: Azure Portal (GUI - Recommended for Beginners)

### Step 1: Create App Registration

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your admin account

2. **Open Azure Active Directory**
   - Search for "Azure Active Directory" in the top search bar
   - Click on it

3. **Create App Registration**
   - In the left menu, click **"App registrations"**
   - Click **"+ New registration"**

4. **Configure the registration:**
   - **Name:** `agent-platform-service-principal`
   - **Supported account types:** "Accounts in this organizational directory only (Single tenant)"
   - **Redirect URI:** Leave blank (not needed for service-to-service auth)
   - Click **"Register"**

5. **Save Important IDs:**
   After registration, you'll see the overview page. **Copy and save these:**

   ```
   Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Directory (tenant) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

   You'll need these for your `.env` file!

---

### Step 2: Create Client Secret

1. **Navigate to Certificates & secrets**
   - In your app registration, click **"Certificates & secrets"** in the left menu

2. **Create new secret**
   - Click **"+ New client secret"**
   - **Description:** `agent-platform-secret-2024`
   - **Expires:** Choose **6 months** (recommended for security)
   - Click **"Add"**

3. **⚠️ CRITICAL: Copy the Secret Value NOW**
   - After creating, you'll see the secret value in the "Value" column
   - **Copy this immediately** - it will NEVER be shown again!

   ```
   Secret Value: abc123~DefGhi456.JklMno789-PqrStu
   ```

   If you lose this, you'll need to create a new secret.

---

### Step 3: Grant API Permissions

This is the most important step - giving your Service Principal the right permissions.

1. **Navigate to API permissions**
   - In your app registration, click **"API permissions"**

2. **Add Microsoft Graph permissions**
   - Click **"+ Add a permission"**
   - Select **"Microsoft Graph"**
   - Select **"Application permissions"** (not Delegated!)

3. **Add these permissions one by one:**

   **For User Management:**
   - `User.ReadWrite.All` - Create, read, update users

   **For Group Management:**
   - `Group.ReadWrite.All` - Create, read, update groups
   - `GroupMember.ReadWrite.All` - Manage group memberships

   **For App Registration Management:**
   - `Application.ReadWrite.All` - Manage app registrations

   **For Role Management (Phase 3+):**
   - `RoleManagement.ReadWrite.Directory` - Assign directory roles (optional for now)

   **For Directory Access:**
   - `Directory.Read.All` - Read directory data (recommended)

4. **Grant Admin Consent**
   - ⚠️ **CRITICAL STEP:** After adding permissions, click **"Grant admin consent for [Your Organization]"**
   - Click **"Yes"** to confirm
   - You should see green checkmarks ✓ in the "Status" column

   **Why this matters:** Without admin consent, the Service Principal can't actually use these permissions!

---

### Step 4: Verify Permissions

1. Check that all permissions show **"Granted for [Your Organization]"** in green
2. Your permissions list should look like this:

   | API / Permission name | Type | Admin consent | Status |
   |----------------------|------|---------------|--------|
   | User.ReadWrite.All | Application | Required | ✓ Granted |
   | Group.ReadWrite.All | Application | Required | ✓ Granted |
   | GroupMember.ReadWrite.All | Application | Required | ✓ Granted |
   | Application.ReadWrite.All | Application | Required | ✓ Granted |
   | Directory.Read.All | Application | Required | ✓ Granted |

---

### Step 5: Configure Your .env File

Now add the credentials to your backend `.env` file:

```bash
# Navigate to your project
cd /Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent

# Edit .env file
nano .env  # or use your favorite editor
```

Add these lines:

```bash
# Azure Integration
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=abc123~DefGhi456.JklMno789-PqrStu
```

**Replace with your actual values from Steps 1 and 2!**

---

## Method 2: Azure CLI (Faster for Advanced Users)

If you have Azure CLI installed:

```bash
# Login
az login

# Create Service Principal with required permissions
az ad sp create-for-rbac \
  --name "agent-platform-service-principal" \
  --role "Directory.ReadWrite.All" \
  --scopes /

# Output will show:
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",          # This is CLIENT_ID
#   "displayName": "agent-platform-service-principal",
#   "password": "abc123~DefGhi456.JklMno789-PqrStu",          # This is CLIENT_SECRET
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"          # This is TENANT_ID
# }

# Get tenant ID if needed
az account show --query tenantId -o tsv

# Grant API permissions (requires admin)
APP_ID="your-app-id-from-above"

az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Role  # User.Read.All

az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions 62a82d76-70ea-41e2-9197-370581804d09=Role  # Group.ReadWrite.All

# Grant admin consent
az ad app permission admin-consent --id $APP_ID
```

---

## Testing Your Setup

### Test 1: Verify Credentials

```bash
cd backend
python3 << EOF
from tools.azure.auth.credential_manager import AzureCredentialManager
import asyncio

async def test():
    try:
        client = AzureCredentialManager.get_graph_client()
        print("✓ Azure credentials configured correctly!")
        print(f"✓ Authenticated successfully")
    except Exception as e:
        print(f"✗ Error: {e}")

asyncio.run(test())
EOF
```

**Expected output:**
```
✓ Azure credentials configured correctly!
✓ Authenticated successfully
```

---

### Test 2: Test Permissions

```bash
python3 << EOF
from tools.azure.entra_id.users import GetUserTool
import asyncio
import os

os.environ['AZURE_TENANT_ID'] = 'your-tenant-id'
os.environ['AZURE_CLIENT_ID'] = 'your-client-id'
os.environ['AZURE_CLIENT_SECRET'] = 'your-secret'

async def test():
    tool = GetUserTool()
    # Try to list users (requires User.Read.All permission)
    result = await tool.execute(id="your-test-user@yourdomain.com")

    if result.success:
        print("✓ Permissions working! User retrieved successfully")
        print(f"  User: {result.data.get('display_name')}")
    else:
        print(f"✗ Permission error: {result.error}")

asyncio.run(test())
EOF
```

---

## Security Best Practices

### 1. Secret Rotation

**Set a reminder to rotate your secret before it expires!**

```bash
# In 6 months, create a new secret:
# 1. Create new secret in Azure Portal
# 2. Update .env with new secret
# 3. Restart backend
# 4. Delete old secret in Azure Portal
```

### 2. Least Privilege

Only grant permissions you actually need:

- ✅ **Testing/POC:** Use all permissions (as shown above)
- ✅ **Production:** Review and remove unused permissions
- ❌ **Never grant:** Global Administrator role to Service Principal

### 3. Monitor Usage

Enable audit logging in Azure AD:
- Azure Portal → Azure Active Directory → Audit logs
- Filter by "Service Principal" to see all actions
- Set up alerts for suspicious activity

### 4. Secure Storage

**⚠️ NEVER commit `.env` to git!**

```bash
# Verify .env is in .gitignore
grep ".env" .gitignore

# Should output: .env
```

For production, use:
- **Azure Key Vault** to store secrets
- **Managed Identity** instead of Service Principal (if running on Azure)

---

## Troubleshooting

### Error: "Insufficient privileges to complete the operation"

**Cause:** Admin consent not granted

**Fix:**
1. Go to Azure Portal → App registrations → Your app → API permissions
2. Click "Grant admin consent for [Your Organization]"
3. Verify all permissions show green checkmarks

---

### Error: "AADSTS7000215: Invalid client secret provided"

**Cause:** Wrong secret in `.env`, or secret expired

**Fix:**
1. Create a new client secret in Azure Portal
2. Update `AZURE_CLIENT_SECRET` in `.env`
3. Restart backend

---

### Error: "Application with identifier 'xxx' was not found"

**Cause:** Wrong Tenant ID or Client ID

**Fix:**
1. Verify `AZURE_TENANT_ID` matches your Azure AD tenant
2. Verify `AZURE_CLIENT_ID` matches your app registration
3. Check for typos or extra spaces

---

### Error: "Insufficient permissions in the access token"

**Cause:** Permission not granted, or using Delegated instead of Application permissions

**Fix:**
1. Ensure you added **Application permissions** (not Delegated)
2. Click "Grant admin consent" again
3. Wait 5-10 minutes for permissions to propagate

---

## Summary Checklist

Before using the Azure Admin Agent, verify:

- [ ] Service Principal created in Azure Portal
- [ ] Tenant ID, Client ID, Secret saved securely
- [ ] API permissions added (User, Group, Application, Directory)
- [ ] **Admin consent granted** (green checkmarks visible)
- [ ] Credentials added to `.env` file
- [ ] `.env` file NOT committed to git
- [ ] Backend starts successfully with "Azure tools loaded: 10 tools"
- [ ] Test permissions by calling a read tool

---

## Next Steps

Once setup is complete:

1. **Start the backend:**
   ```bash
   cd backend
   python -m uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Create an Azure Admin Agent:**
   - Use the API or frontend
   - Enable Azure tools:
     - create_user, get_user, reset_password
     - create_group, get_group, add_group_member
     - create_app_registration, etc.

3. **Set system prompt:**
   - Use the template from `AZURE_ADMIN_SYSTEM_PROMPT.md`
   - Or use default with verification protocol

4. **Test with simple commands:**
   - "List information about user test@yourdomain.com"
   - "Create a security group called Test Group"

---

## Cost Considerations

**Good news: The Service Principal itself is FREE!**

Azure AD operations (user creation, etc.) are included in your Azure AD tier:

- **Azure AD Free:** 50,000 object limit (users + groups + apps)
- **Azure AD Premium P1:** Unlimited objects + advanced features
- **Azure AD Premium P2:** All features + identity protection

**For POC/Testing:** Azure AD Free is sufficient!

---

## Questions?

If you encounter issues not covered here, check:

1. Azure AD audit logs (see what actually happened)
2. Backend logs (detailed error messages)
3. Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/

---

**Setup Complete!** You're now ready to use the Azure Workforce Admin Agent.

**Last Updated:** 2025-11-21
**Version:** 1.0

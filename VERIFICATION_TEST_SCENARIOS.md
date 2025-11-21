# Verification Loop - Test Scenarios

**Purpose:** Test cases to validate that the Azure Admin Agent correctly verifies all write operations.

**Test Method:** Manual testing via chat interface or automated integration tests.

---

## Scenario 1: User Creation with Verification

**User Input:**
```
Create a user for John Doe with email john.doe@company.com in the Finance department
```

**Expected Agent Behavior:**

1. **Planning Phase:**
   ```
   Agent: "I'll create a user with these details:
           - UPN: john.doe@company.com
           - Display Name: John Doe
           - Department: Finance
           - Temporary Password: [Generated]
           - Policy: Must change password on first login

           This operation requires approval. Shall I proceed?"
   ```

2. **After Consent Approval:**
   - Agent calls `create_user(...)`
   - ToolResult returns with `verification_hint` in metadata

3. **Automatic Verification:**
   - Agent **immediately** calls `get_user(id="john.doe@company.com")`
   - Agent compares: UPN ✓, Display Name ✓, Department ✓, Account Enabled ✓

4. **Confirmation to User:**
   ```
   Agent: "✓ User Created & Verified

           Details:
           - UPN: john.doe@company.com
           - Display Name: John Doe
           - Department: Finance
           - Status: Active (password change required)
           - Temporary Password: Xy8#mKp2qL9vN4zT

           Verification Passed:
           ✓ User exists in Azure AD
           ✓ All attributes match request
           ✓ Account is enabled"
   ```

**Success Criteria:**
- ✅ Agent calls `get_user` immediately after `create_user`
- ✅ Agent compares expected vs actual attributes
- ✅ Agent only confirms after verification
- ✅ Temporary password is shown to user

---

## Scenario 2: Verification Failure Detection

**Setup:** Manually create a user with different attributes than requested

**User Input:**
```
Create a user named Alice Johnson with email alice.j@company.com
```

**Simulated Behavior:**
- Agent creates user successfully
- But Azure API returns `display_name: "AliceJohnson"` (no space)

**Expected Agent Behavior:**

```
Agent: "⚠️ User Created with Verification Issue

        User alice.j@company.com was created, but verification shows a discrepancy:

        Expected: Display Name "Alice Johnson"
        Actual:   Display Name "AliceJohnson" (missing space)

        This may have occurred due to API formatting. Would you like me to:
        1. Update the user to fix the display name
        2. Leave as-is
        3. Delete and recreate the user"
```

**Success Criteria:**
- ✅ Agent detects the mismatch
- ✅ Agent reports the specific discrepancy
- ✅ Agent offers remediation options
- ❌ Agent does NOT say "User created successfully" without mentioning the issue

---

## Scenario 3: Group Creation with Verification

**User Input:**
```
Create a security group called "Finance Team"
```

**Expected Agent Behavior:**

1. **Planning:**
   ```
   Agent: "I'll create a Security Group with:
           - Display Name: Finance Team
           - Mail Nickname: finance-team
           - Type: Security (for access control)
           - Mail Enabled: No
           - Security Enabled: Yes

           This operation requires approval. Shall I proceed?"
   ```

2. **After Approval:**
   - Agent calls `create_group(...)`
   - Agent **immediately** calls `get_group(id=<returned_group_id>)`

3. **Verification:**
   - Agent compares: Display Name ✓, Type ✓, Security Enabled ✓

4. **Confirmation:**
   ```
   Agent: "✓ Group Created & Verified

           Details:
           - Name: Finance Team
           - Type: Security Group
           - ID: 123e4567-e89b-12d3-a456-426614174000
           - Members: 0 (use add_group_member to add users)

           Verification Passed:
           ✓ Group exists in Azure AD
           ✓ Configured as Security Group
           ✓ Ready for use"
   ```

**Success Criteria:**
- ✅ Agent verifies group creation
- ✅ Agent confirms group type matches request
- ✅ Agent provides next steps (adding members)

---

## Scenario 4: Add Group Member with Verification

**User Input:**
```
Add john.doe@company.com to the Finance Team group
```

**Expected Agent Behavior:**

1. **Investigation (Before Action):**
   - Agent may call `get_user(id="john.doe@company.com")` to verify user exists
   - Agent may call `get_group(id="Finance Team")` to get group ID

2. **Planning:**
   ```
   Agent: "I'll add user John Doe (john.doe@company.com) to the Finance Team group.
           This will grant John access to resources associated with this group.

           This operation requires approval. Shall I proceed?"
   ```

3. **After Approval:**
   - Agent calls `add_group_member(group_id=..., user_id="john.doe@company.com")`
   - Agent **immediately** calls `get_group(id=<group_id>)` OR checks membership

4. **Verification:**
   - Agent confirms membership was added

5. **Confirmation:**
   ```
   Agent: "✓ Membership Added & Verified

           User John Doe (john.doe@company.com) has been added to Finance Team.

           Note: Permission changes may take a few minutes to propagate across Azure services."
   ```

**Success Criteria:**
- ✅ Agent investigates before acting
- ✅ Agent verifies membership after adding
- ✅ Agent warns about propagation delay

---

## Scenario 5: Password Reset with Verification

**User Input:**
```
Reset the password for bob@company.com
```

**Expected Agent Behavior:**

1. **Investigation First:**
   - Agent calls `get_user(id="bob@company.com")` to check if user exists
   - Agent checks account status

2. **Planning:**
   ```
   Agent: "I'll reset the password for Bob Smith (bob@company.com).
           - New temporary password will be generated
           - Bob will be required to change it on next login

           This operation requires approval. Shall I proceed?"
   ```

3. **After Approval:**
   - Agent calls `reset_password(user_id="bob@company.com")`
   - ToolResult includes temporary password
   - Agent **immediately** calls `get_user(id="bob@company.com")`

4. **Verification:**
   - Agent may not be able to directly verify password change
   - But agent should confirm user account is still enabled

5. **Confirmation:**
   ```
   Agent: "✓ Password Reset Complete

           User: bob@company.com
           Temporary Password: Kp9#vL2mQx8Yt5Nz
           Status: Must change password on next login

           Verification:
           ✓ User account is active
           ✓ Password reset operation succeeded

           Please share the temporary password with Bob securely (phone, in-person).
           Do NOT send via email."
   ```

**Success Criteria:**
- ✅ Agent investigates user status first
- ✅ Agent verifies account is still active after reset
- ✅ Agent provides security guidance (share password securely)

---

## Scenario 6: Handling Already-Exists Error

**User Input:**
```
Create a user named John Doe with email john.doe@company.com
```

**Setup:** User already exists in Azure AD

**Expected Agent Behavior:**

1. **Attempt Creation:**
   - Agent calls `create_user(...)`
   - Azure API returns error: "Request_MultipleObjectsWithSameKeyValue"

2. **Error Handling (No Verification Needed):**
   ```
   Agent: "✗ User Creation Failed

           A user with email john.doe@company.com already exists in Azure AD.

           Investigation:
           [Agent calls get_user to retrieve existing user]

           Existing user details:
           - UPN: john.doe@company.com
           - Display Name: John Doe
           - Status: Active
           - Created: 3 days ago

           Did you mean to:
           1. Update this existing user?
           2. Use a different email address (e.g., john.doe2@company.com)?
           3. Reset the password for this user?"
   ```

**Success Criteria:**
- ✅ Agent detects duplicate error
- ✅ Agent investigates by calling `get_user`
- ✅ Agent offers remediation options
- ❌ Agent does NOT attempt verification (since creation failed)

---

## Scenario 7: Multiple Operations in Sequence

**User Input:**
```
Create a user Sarah Williams (sarah.w@company.com) in Marketing,
then create a group called Marketing Team and add Sarah to it
```

**Expected Agent Behavior:**

1. **Break Down Task:**
   ```
   Agent: "I'll perform these operations in sequence:

           1. Create user Sarah Williams (sarah.w@company.com) in Marketing department
           2. Create security group "Marketing Team"
           3. Add Sarah to the Marketing Team group

           I'll verify each operation before proceeding to the next.
           This will require multiple approvals. Shall I start?"
   ```

2. **Execute with Verification:**
   - **Op 1:** create_user → **verify** with get_user → ✓
   - **Op 2:** create_group → **verify** with get_group → ✓
   - **Op 3:** add_group_member → **verify** with get_group → ✓

3. **Final Confirmation:**
   ```
   Agent: "✓ All Operations Completed & Verified

           Summary:
           1. ✓ User Created: Sarah Williams (sarah.w@company.com)
              - Department: Marketing
              - Temp Password: [shown]

           2. ✓ Group Created: Marketing Team
              - Type: Security Group
              - ID: [group-id]

           3. ✓ Membership Added: Sarah is now a member of Marketing Team

           All verifications passed. Setup complete!"
   ```

**Success Criteria:**
- ✅ Agent verifies each operation before moving to the next
- ✅ Agent provides comprehensive summary
- ✅ All three verifications occur independently

---

## Verification Metrics

After testing these scenarios, measure:

| Metric | Target | Actual |
|--------|--------|--------|
| Verification Rate | 100% (all write ops verified) | ___% |
| False Positives | <1% (reports error when none) | ___% |
| False Negatives | 0% (misses actual errors) | ___% |
| Avg Time to Verify | <2 seconds | ___ sec |
| User Confirmation Delay | <5 sec after verify | ___ sec |

---

## Test Execution Checklist

- [ ] Scenario 1: User Creation (Happy Path)
- [ ] Scenario 2: Verification Failure Detection
- [ ] Scenario 3: Group Creation
- [ ] Scenario 4: Add Group Member
- [ ] Scenario 5: Password Reset
- [ ] Scenario 6: Already Exists Error
- [ ] Scenario 7: Multiple Sequential Operations

**Notes:**
Record any unexpected behavior, missed verifications, or false positives here.

---

**Version:** 1.0
**Last Updated:** 2025-11-21
**Phase:** Phase 2 - Verification Loop

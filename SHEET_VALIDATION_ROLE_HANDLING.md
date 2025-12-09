# Sheet Validation and Role Handling Implementation

## Summary

This document describes the implementation of enhanced sheet validation and role handling for the MI Chatbot Access Portal. The changes enable flexible role-based access control while maintaining full backward compatibility with existing sheets.

## Problem Statement

The previous implementation had several limitations:

1. **Strict Header Validation**: Expected exactly `['Table No', 'Name', 'Bot', 'Secret', 'Used']` and rejected sheets with a `Role` column
2. **Limited Bot Type Support**: Only allowed OHI, HPV, TOBACCO, PERIO and rejected Instructor/Developer values
3. **No Role Flexibility**: Could not specify Instructor/Developer roles either in Bot column or separate Role column
4. **Poor Error Messages**: Validation errors were not explicit about what was wrong

## Solution

### 1. Flexible Header Validation

**Implementation**: `secret_code_portal.py` lines 223-245

The header validation now:
- Accepts all required columns: `['Table No', 'Name', 'Bot', 'Secret', 'Used']`
- Allows optional `Role` column
- Validates that required columns are present (order-independent)
- Logs warnings for unexpected columns
- Provides clear error messages for missing columns

**Example Headers**:
```python
# Valid - backward compatible
['Table No', 'Name', 'Bot', 'Secret', 'Used']

# Valid - with Role column
['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']

# Valid - different order
['Table No', 'Name', 'Role', 'Bot', 'Secret', 'Used']

# Invalid - missing required column
['Table No', 'Name', 'Bot', 'Secret']  # Missing 'Used'
```

### 2. Dual-Mode Role Handling

**Implementation**: `secret_code_portal.py` lines 394-445

The system now supports two modes of role specification:

#### Mode 1: Without Role Column (Backward Compatible)
When the Role column is absent, the Bot column can specify either:
- A valid bot type: `OHI`, `HPV`, `TOBACCO`, `PERIO` (for students)
- A role: `Instructor` or `Developer`

**Examples**:
```python
# Student with specific bot
['1', 'Alice Student', 'OHI', 'CODE1', '']  # Role=STUDENT, Bot=OHI

# Instructor
['2', 'Bob Instructor', 'Instructor', 'CODE2', '']  # Role=INSTRUCTOR, Bot=ALL

# Developer
['3', 'Charlie Dev', 'Developer', 'CODE3', '']  # Role=DEVELOPER, Bot=DEVELOPER
```

#### Mode 2: With Role Column
When the Role column is present, it explicitly specifies the role, and the Bot column indicates which bot(s) to access:

**Examples**:
```python
# Student with specific bot
['1', 'Alice Student', 'OHI', 'CODE1', '', 'STUDENT']  # Role=STUDENT, Bot=OHI

# Instructor with access to all bots
['2', 'Bob Instructor', 'ALL', 'CODE2', '', 'INSTRUCTOR']  # Role=INSTRUCTOR, Bot=ALL

# Instructor with specific bot (still gets access to all)
['3', 'Bob Instructor', 'HPV', 'CODE3', '', 'INSTRUCTOR']  # Role=INSTRUCTOR, Bot=ALL

# Developer
['4', 'Charlie Dev', 'ALL', 'CODE4', '', 'DEVELOPER']  # Role=DEVELOPER, Bot=DEVELOPER
```

### 3. Role-Based Access Control

**Roles and Permissions**:

| Role | Bot Field Values | Access Granted | Code Reusable |
|------|------------------|----------------|---------------|
| **STUDENT** | OHI, HPV, TOBACCO, PERIO | Single bot specified | No (marked as used) |
| **INSTRUCTOR** | ALL or specific bot | All bots | Yes (not marked as used) |
| **DEVELOPER** | ALL, DEVELOPER, or specific bot | All apps + developer page | Yes (not marked as used) |

### 4. Enhanced Validation and Logging

**Validation Rules**:

1. **Students**: Must use one of the four valid bot types (OHI, HPV, TOBACCO, PERIO)
2. **Instructors**: Can use ANY bot type or 'ALL'; always get access to all bots
3. **Developers**: Can use ANY value; always redirected to developer page
4. **Invalid bot types for students**: Clear error message with list of valid types

**Logging Improvements**:
- `logger.info()`: Successful operations (instructor access, sheet validation)
- `logger.warning()`: Unexpected but handled cases (unusual bot values for instructors/developers)
- `logger.error()`: Rejected operations (invalid bot type for students)

**Example Logs**:
```
INFO: Sheet headers validated. Has Role column: True. Headers: ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
INFO: Instructor 'Bob Smith' accessing with unlimited access (bot field: ALL)
WARNING: Developer role with invalid bot 'XYZ' on row 5. Bot should be ALL, DEVELOPER, or one of {'OHI', 'HPV', 'TOBACCO', 'PERIO'}
ERROR: Rejected invalid bot type 'XYZ' for STUDENT on row 3. Valid bot types: {'OHI', 'HPV', 'TOBACCO', 'PERIO'}
```

## Backward Compatibility

The implementation maintains full backward compatibility:

✅ **Existing sheets without Role column continue to work**
- Students with valid bot types (OHI, HPV, TOBACCO, PERIO) work exactly as before
- Validation and marking as used functions identically

✅ **Existing authentication flow unchanged**
- Session state management remains the same
- Redirect logic is preserved
- Error handling is enhanced but compatible

✅ **Existing tests updated and passing**
- All 58 tests pass
- New test suite covers all scenarios

## Testing

### Test Coverage

New test suite: `tests/test_sheet_validation_role_handling.py`

**Test Categories**:
1. **Header Validation** (4 tests)
   - Headers without Role column
   - Headers with Role column
   - Different column orders
   - Missing required columns

2. **Bot Type Validation** (5 tests)
   - Valid bot types
   - Case-insensitive handling
   - Instructor/Developer/ALL values

3. **Role Handling** (3 tests)
   - Role normalization
   - Role-based access control
   - Student/Instructor/Developer permissions

4. **Backward Compatibility** (3 tests)
   - Sheets without Role column
   - Instructor in Bot column
   - Developer in Bot column

5. **Role Column Present** (4 tests)
   - Instructor with ALL
   - Developer with ALL
   - Instructor with specific bot
   - Student role

6. **Error Messages** (2 tests)
   - Invalid bot type errors
   - Missing header errors

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test suite
python -m unittest tests.test_sheet_validation_role_handling -v

# Run existing access control tests
python -m unittest tests.test_access_control -v
python -m unittest tests.test_portal_errors -v
```

## Migration Guide

### For Administrators

**No action required** for existing sheets. However, you can optionally:

1. **Add Role column** for clarity:
   ```
   Table No | Name         | Bot      | Secret | Used | Role
   1        | Alice Smith  | OHI      | CODE1  |      | STUDENT
   2        | Bob Jones    | ALL      | CODE2  |      | INSTRUCTOR
   3        | Charlie Dev  | DEVELOPER| CODE3  |      | DEVELOPER
   ```

2. **Use Bot column for roles** (if no Role column):
   ```
   Table No | Name         | Bot        | Secret | Used
   1        | Alice Smith  | OHI        | CODE1  |
   2        | Bob Jones    | Instructor | CODE2  |
   3        | Charlie Dev  | Developer  | CODE3  |
   ```

### For Developers

**Key Functions**:

1. `normalize_bot_type(bot_str)` - Normalizes bot types to uppercase
2. `normalize_role(role_str)` - Converts role strings to role constants
3. `validate_and_mark_code(secret_code)` - Main validation logic

**Role Constants**:
```python
from utils.access_control import ROLE_STUDENT, ROLE_INSTRUCTOR, ROLE_DEVELOPER, VALID_BOT_TYPES
```

## Error Messages

### For Users

**Invalid bot type for student**:
```
Invalid bot type "XYZ" in the sheet. Valid types are: OHI, HPV, TOBACCO, PERIO. 
Please contact your instructor.
```

**Missing required column**:
```
Missing required column: Used. Got columns: ['Table No', 'Name', 'Bot', 'Secret']
```

**Code already used** (students only):
```
This code has already been used. Please contact your instructor if you need a new code.
```

### For Administrators

All error messages now include:
- What was expected
- What was received
- How to fix the issue
- Context (row numbers, column names)

## Security Considerations

1. **Code Reuse Prevention**: Students' codes are marked as used; instructors/developers can reuse codes
2. **Role Validation**: Roles are validated and normalized to prevent bypasses
3. **Bot Type Restrictions**: Students restricted to approved bots only
4. **Logging**: All validation attempts are logged for audit trail

## Files Modified

1. `secret_code_portal.py` - Main validation and role handling logic
2. `utils/access_control.py` - Enhanced normalize_bot_type function
3. `tests/test_sheet_validation_role_handling.py` - New comprehensive test suite
4. `tests/test_portal_errors.py` - Updated to match current implementation

## Future Enhancements

Potential future improvements:
1. Add more granular permissions per role
2. Support custom bot types via configuration
3. Add expiration dates for access codes
4. Support group-based access control
5. Add audit log export functionality

# Fix Purchase ENUM Values

## Problem

The database `purchases` table has uppercase ENUM values (CREDIT, BANK, CONVENIENCE) but the application code uses lowercase values ('credit', 'bank', 'convenience'). This causes a `LookupError` when trying to create purchases.

**Error:**
```
LookupError: 'credit' is not among the defined enum values. 
Enum name: paymentmethod. Possible values: CREDIT, BANK, CONVENIENCE
```

## Solution

Apply the migration to fix the ENUM values to lowercase.

### Option 1: Apply Migration (Recommended)

```bash
cd hackathon-backend
alembic upgrade head
```

This will run migration `005_fix_purchase_enums.py` which updates the ENUM columns to use lowercase values.

### Option 2: Manual SQL Fix (If Migration Fails)

If you have no purchase data yet, you can manually fix it:

```sql
-- Connect to your database
USE hackathon;

-- Update the payment_method ENUM
ALTER TABLE purchases 
MODIFY COLUMN payment_method 
ENUM('credit', 'bank', 'convenience') NOT NULL;

-- Update the status ENUM (should already be lowercase)
ALTER TABLE purchases 
MODIFY COLUMN status 
ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending';
```

### Option 3: Recreate Table (If No Data)

If the purchases table has no data:

```sql
-- Drop and recreate
DROP TABLE IF EXISTS purchases;

-- Then run migrations again
```

```bash
alembic downgrade 001
alembic upgrade head
```

## Verification

After applying the fix, verify the ENUM values:

```sql
SHOW COLUMNS FROM purchases WHERE Field = 'payment_method';
```

Should show:
```
Type: enum('credit','bank','convenience')
```

## Test the Fix

1. Restart the backend server
2. Try to complete a purchase in the frontend
3. The checkout should now work without errors

## Root Cause

The mismatch occurred because:
1. The Python enum defined lowercase values: `CREDIT = "credit"`
2. The migration correctly specified lowercase: `sa.Enum('credit', 'bank', 'convenience')`
3. But MySQL may have created uppercase ENUMs or the database was manually modified

This fix ensures the database matches the application code.


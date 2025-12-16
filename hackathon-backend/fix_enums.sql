-- Fix purchase ENUM values from uppercase to lowercase
-- Run this with: mysql -u [user] -p [database] < fix_enums.sql

USE hackathon;

-- Fix payment_method ENUM
ALTER TABLE purchases 
MODIFY COLUMN payment_method 
ENUM('credit', 'bank', 'convenience') NOT NULL;

-- Fix status ENUM  
ALTER TABLE purchases 
MODIFY COLUMN status 
ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending';

-- Verify the changes
SHOW COLUMNS FROM purchases WHERE Field IN ('payment_method', 'status');


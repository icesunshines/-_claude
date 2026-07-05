#!/usr/bin/env python
# coding: utf-8
"""检查所有模块是否正常"""

import sys
import os

# 添加路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

print("Checking project modules:")
print("=" * 50)

try:
    print("1. Importing database...")
    import database
    print("   OK")
    
    print("\n2. Importing models_orm...")
    import models_orm
    print("   OK")
    
    print("\n3. Importing auth...")
    import auth
    print("   OK")
    
    print("\n4. Importing schemas...")
    import schemas
    print("   OK")
    
    print("\n5. Importing preprocessing...")
    import preprocessing
    print("   OK")
    
    print("\n6. Importing predict...")
    import predict
    print("   OK")
    
    print("\n7. Importing main...")
    import main
    print("   OK")
    
    print("\n" + "=" * 50)
    print("All modules imported successfully!")
    
    # Check database connection
    print("\nChecking database...")
    from database import SessionLocal
    from models_orm import User
    
    db = SessionLocal()
    users = db.query(User).all()
    print(f"  Found {len(users)} users in database:")
    for user in users:
        print(f"    - {user.username} ({user.role})")
    
    db.close()
    print("  Database OK!")
    
    print("\n" + "=" * 50)
    print("All checks passed! Project is running properly.")
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nStack trace:")
    print(traceback.format_exc())
    sys.exit(1)

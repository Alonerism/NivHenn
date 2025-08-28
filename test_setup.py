#!/usr/bin/env python3
"""
Insurance Master - Setup Test Script

This script tests the basic setup and dependencies to ensure
the application can run properly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing module imports...")
    
    try:
        import tkinter
        print("✅ tkinter - OK")
    except ImportError as e:
        print(f"❌ tkinter - FAILED: {e}")
        return False
    
    try:
        import ttkbootstrap
        print("✅ ttkbootstrap - OK")
    except ImportError as e:
        print(f"❌ ttkbootstrap - FAILED: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2 - OK")
    except ImportError as e:
        print(f"❌ PyPDF2 - FAILED: {e}")
        return False
    
    try:
        import pdfplumber
        print("✅ pdfplumber - OK")
    except ImportError as e:
        print(f"❌ pdfplumber - FAILED: {e}")
        return False
    
    try:
        import openai
        print("✅ openai - OK")
    except ImportError as e:
        print(f"❌ openai - FAILED: {e}")
        return False
    
    try:
        import chromadb
        print("✅ chromadb - OK")
    except ImportError as e:
        print(f"❌ chromadb - FAILED: {e}")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv - OK")
    except ImportError as e:
        print(f"❌ python-dotenv - FAILED: {e}")
        return False
    
    try:
        import schedule
        print("✅ schedule - OK")
    except ImportError as e:
        print(f"❌ schedule - FAILED: {e}")
        return False
    
    return True

def test_directory_structure():
    """Test if the directory structure is correct"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "src",
        "src/ui",
        "src/db", 
        "src/parsing",
        "src/rag",
        "src/alerts",
        "data",
        "data/policies"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/ - OK")
        else:
            print(f"❌ {dir_path}/ - MISSING")
            return False
    
    return True

def test_source_files():
    """Test if all required source files exist"""
    print("\nTesting source files...")
    
    required_files = [
        "src/main.py",
        "src/ui/policy_table.py",
        "src/ui/dialogs.py", 
        "src/ui/chat_panel.py",
        "src/db/database.py",
        "src/parsing/pdf_parser.py",
        "src/rag/rag_system.py",
        "src/alerts/email_alerts.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - OK")
        else:
            print(f"❌ {file_path} - MISSING")
            return False
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\nTesting environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_example.exists():
        print("✅ env.example - OK")
    else:
        print("❌ env.example - MISSING")
        return False
    
    if env_file.exists():
        print("✅ .env - OK (configured)")
        
        # Check if .env has content
        try:
            with open(env_file, 'r') as f:
                content = f.read().strip()
                if content:
                    print("✅ .env has content")
                else:
                    print("⚠️  .env is empty")
        except Exception as e:
            print(f"⚠️  Could not read .env: {e}")
    else:
        print("⚠️  .env - NOT FOUND (copy from env.example)")
    
    return True

def test_database_initialization():
    """Test if database can be initialized"""
    print("\nTesting database initialization...")
    
    try:
        # Add src to path
        src_dir = Path("src")
        if src_dir.exists():
            sys.path.insert(0, str(src_dir.absolute()))
        
        from db.database import InsuranceDatabase
        
        # Try to create database
        db = InsuranceDatabase()
        print("✅ Database initialization - OK")
        
        # Test basic operations
        agents = db.get_agents()
        buildings = db.get_buildings()
        policies = db.get_policies()
        
        print(f"✅ Database operations - OK ({len(agents)} agents, {len(buildings)} buildings, {len(policies)} policies)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization - FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("Insurance Master - Setup Test")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test directory structure
    if not test_directory_structure():
        all_passed = False
    
    # Test source files
    if not test_source_files():
        all_passed = False
    
    # Test environment
    if not test_environment():
        all_passed = False
    
    # Test database
    if not test_database_initialization():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("  python run.py")
        print("  or")
        print("  python src/main.py")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")
        print("\nCommon solutions:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Copy env.example to .env and configure your settings")
        print("3. Ensure all source files are present")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

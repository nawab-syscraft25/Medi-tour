#!/usr/bin/env python3
"""
Admin management CLI command
Usage: python create_admin.py <username> <email> <password> [--super]
"""

import asyncio
import sys
import argparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models import Admin
from app.auth import get_password_hash


async def create_admin_user(username: str, email: str, password: str, is_super_admin: bool = False):
    """Create a new admin user"""
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=settings.debug)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if username already exists
        result = await session.execute(select(Admin).where(Admin.username == username))
        if result.scalar_one_or_none():
            print(f"❌ Username '{username}' already exists!")
            return False
        
        # Check if email already exists
        result = await session.execute(select(Admin).where(Admin.email == email))
        if result.scalar_one_or_none():
            print(f"❌ Email '{email}' already exists!")
            return False
        
        # Create new admin
        hashed_password = get_password_hash(password)
        new_admin = Admin(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_super_admin=is_super_admin,
            is_active=True
        )
        
        session.add(new_admin)
        await session.commit()
        await session.refresh(new_admin)
        
        admin_type = "Super Admin" if is_super_admin else "Admin"
        print(f"✅ {admin_type} '{username}' created successfully!")
        print(f"   ID: {new_admin.id}")
        print(f"   Email: {email}")
        print(f"   Created: {new_admin.created_at}")
        
        return True


async def list_admins():
    """List all admin users"""
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=settings.debug)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Admin).order_by(Admin.created_at.desc()))
        admins = result.scalars().all()
        
        if not admins:
            print("📭 No admin users found.")
            return
        
        print("👥 Admin Users:")
        print("-" * 80)
        for admin in admins:
            status = "🟢 Active" if admin.is_active else "🔴 Inactive"
            admin_type = "🌟 Super Admin" if admin.is_super_admin else "👤 Admin"
            last_login = admin.last_login.strftime("%Y-%m-%d %H:%M") if admin.last_login else "Never"
            
            print(f"ID: {admin.id:3} | {admin_type} | {status}")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Created: {admin.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Last Login: {last_login}")
            print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Medi-Tour Admin Management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create admin command
    create_parser = subparsers.add_parser("create", help="Create a new admin user")
    create_parser.add_argument("username", help="Admin username")
    create_parser.add_argument("email", help="Admin email")
    create_parser.add_argument("password", help="Admin password")
    create_parser.add_argument("--super", action="store_true", help="Create as super admin")
    
    # List admins command
    list_parser = subparsers.add_parser("list", help="List all admin users")
    
    args = parser.parse_args()
    
    if args.command == "create":
        if len(args.password) < 8:
            print("❌ Password must be at least 8 characters long!")
            sys.exit(1)
        
        print("🔧 Creating admin user...")
        success = asyncio.run(create_admin_user(
            args.username, 
            args.email, 
            args.password, 
            args.super
        ))
        
        if success:
            print("🎉 Admin user created successfully!")
        else:
            sys.exit(1)
    
    elif args.command == "list":
        asyncio.run(list_admins())
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
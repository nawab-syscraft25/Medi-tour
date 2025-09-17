#!/usr/bin/env python3
"""
Standalone JSON export script that can be run independently
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.export_import import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
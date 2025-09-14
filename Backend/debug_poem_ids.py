#!/usr/bin/env python3
"""
Debug script to check what poem IDs are available in the system
"""

import sys
import os
from pathlib import Path

# Add fortune_module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fortune_module'))

from fortune_module.unified_rag import UnifiedRAGHandler

def main():
    print("Checking poem IDs in ChromaDB...")

    rag = UnifiedRAGHandler()

    # Get all poems for GuanYu temple
    guanyu_poems = rag.list_available_poems("GuanYu")
    print(f"Found {len(guanyu_poems)} GuanYu poems:")

    for i, poem in enumerate(guanyu_poems[:10]):  # Show first 10
        print(f"  {i+1}. ID: {poem.get('poem_id', 'NO_ID')}, Title: {poem.get('title', 'NO_TITLE')[:50]}")

    # Look specifically for poem 24
    poem_24_candidates = [p for p in guanyu_poems if str(p.get('poem_id', '')) == '24']

    if poem_24_candidates:
        print(f"\nFound {len(poem_24_candidates)} candidates for poem 24:")
        for poem in poem_24_candidates:
            print(f"  ID: {poem.get('poem_id')}")
            print(f"  Title: {poem.get('title')}")
            print(f"  Temple: {poem.get('temple')}")
            print("  Full poem data keys:", list(poem.keys()))
    else:
        print("\nNo poem with ID 24 found!")
        print("Available poem IDs:", sorted([str(p.get('poem_id', 'NO_ID')) for p in guanyu_poems]))

if __name__ == "__main__":
    main()
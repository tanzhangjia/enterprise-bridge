"""
Enterprise Bridge — __main__ 入口（让 python3 -m enterprise 直接走 cli）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enterprise.cli import main

main()

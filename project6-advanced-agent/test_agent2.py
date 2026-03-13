#!/usr/bin/env python3
"""测试 Agent 连接"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print('[1] Import create_apk_agent')
from agents.apk_agent import create_apk_agent

print('[2] Call create_apk_agent')
agent = create_apk_agent(
    mcp_server_path='/root/Learn/jadx-mcp-server',
    jadx_gui_path=None,
    enable_rag=False,
    enable_advanced=False,
    on_status_update=lambda msg: print(f'  [Status] {msg}', flush=True)
)
print('[3] Agent created')

print(f'[4] _is_connected: {agent.mcp_client._is_connected}')

print('[5] Calling connect()')
result = agent.mcp_client.connect()
print(f'[6] Result: {result}')

agent.mcp_client.close()
print('[7] Done')

#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
cd /Users/altanatabarut/whatsapp-mcp/whatsapp-bridge
exec /opt/homebrew/bin/go run main.go >> /tmp/whatsapp-mcp.log 2>&1

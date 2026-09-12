import asyncio,sqlite3,tempfile,sys,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from jsonschema import validate
root=str(Path(__file__).resolve().parents[1])
async def test():
 with tempfile.TemporaryDirectory() as tmp:
  db=Path(tmp)/'messages.db'; c=sqlite3.connect(db)
  c.executescript('CREATE TABLE chats(jid TEXT,name TEXT,last_message_time TEXT); CREATE TABLE messages(timestamp TEXT,sender TEXT,content TEXT,is_from_me INTEGER,chat_jid TEXT,id TEXT,media_type TEXT);')
  c.execute('INSERT INTO chats VALUES(?,?,?)',('123@s.whatsapp.net','Test Contact','2026-09-12 10:00:00+03:00'))
  c.execute('INSERT INTO messages VALUES(?,?,?,?,?,?,?)',('2026-09-12 10:00:00+03:00','123','Fixture message',0,'123@s.whatsapp.net','fixture-id',''))
  c.commit(); c.close()
  code=f'import sys; sys.path.insert(0,{root!r}); import whatsapp; whatsapp.MESSAGES_DB_PATH={str(db)!r}; import main; main.mcp.run()'
  p=StdioServerParameters(command=sys.executable,args=['-B','-c',code])
  async with stdio_client(p) as (r,w):
   async with ClientSession(r,w) as s:
    await s.initialize(); tools={t.name:t for t in (await s.list_tools()).tools}
    cases=[('list_messages',{'after':'2026-09-12T00:00:00+03:00','before':'2026-09-13T00:00:00+03:00','include_context':False}),('list_messages',{'include_context':True}),('list_messages',{'query':'nonexistent'}),('list_chats',{'include_last_message':False}),('list_chats',{}),('get_chat',{'chat_jid':'123@s.whatsapp.net','include_last_message':False}),('get_chat',{'chat_jid':'nonexistent'}),('search_contacts',{'query':'Test'}),('get_direct_chat_by_contact',{'sender_phone_number':'123'}),('get_contact_chats',{'jid':'123@s.whatsapp.net'}),('get_last_interaction',{'jid':'nonexistent'}),('get_last_interaction',{'jid':'123@s.whatsapp.net'}),('get_message_context',{'message_id':'fixture-id'})]
    for name,args in cases:
     result=await s.call_tool(name,args)
     assert not result.isError,(name,result)
     if tools[name].outputSchema: validate(result.structuredContent,tools[name].outputSchema)
     if name=='list_messages' and 'after' in args: assert 'Fixture message' in str(result)
    db.unlink()
    failed=await s.call_tool('list_chats',{})
    assert failed.isError,'Database failure must not masquerade as no messages'
    print('PASS: 13 MCP result/schema cases and explicit database-error reporting, using synthetic data.')
asyncio.run(test())

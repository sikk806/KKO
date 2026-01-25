import sys
import os
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

# =================================================================
# 설정: 실행할 MCP 서버 파일명
# =================================================================
MCP_SCRIPT = "mcp_server.py"

print(f"🌉 [Stdio Bridge] '{MCP_SCRIPT}'를 연결할 준비 중...")

# 전역 변수로 프로세스 관리
mcp_process = None

# 1. MCP 서버(자식 프로세스)를 실행하는 함수
async def start_mcp_process():
    global mcp_process
    # 현재 파이썬 실행환경 그대로 사용하여 mcp_server.py 실행
    mcp_process = await asyncio.create_subprocess_exec(
        sys.executable, MCP_SCRIPT,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    print(f"✅ [내부] {MCP_SCRIPT} 실행 완료 (PID: {mcp_process.pid})")

app = FastAPI()

# 2. 서버 시작 시 프로세스 띄우기
@app.on_event("startup")
async def startup_event():
    await start_mcp_process()

# 3. PlayMCP의 POST 요청 처리
@app.post("/sse")
@app.post("/sse/")
async def handle_post(request: Request):
    global mcp_process
    
    # 프로세스가 죽었으면 살리기
    if mcp_process.returncode is not None:
        print("⚠️ 프로세스 재시작...")
        await start_mcp_process()

    try:
        # PlayMCP가 보낸 JSON 읽기
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")
        
        # 로그 (디버깅용)
        # print(f"📨 [입력] {body_str[:50]}...")

        # MCP 프로세스에 입력 (Write to Stdin)
        if mcp_process.stdin:
            mcp_process.stdin.write(body_str.encode("utf-8") + b"\n")
            await mcp_process.stdin.drain()
        
        # JSON-RPC는 'id'가 있으면 응답을 기다려야 함
        request_json = json.loads(body_str)
        
        if "id" in request_json:
            # 응답 한 줄 읽기 (Read from Stdout)
            if mcp_process.stdout:
                response_line = await mcp_process.stdout.readline()
                response_str = response_line.decode("utf-8")
                
                if not response_str:
                    return JSONResponse({"error": "EOF from server"}, status_code=500)
                
                # print(f"📤 [출력] {response_str[:50]}...")
                # 그대로 반환
                return Response(content=response_str, media_type="application/json")
        
        # 'id'가 없으면(Notification) 그냥 OK
        return JSONResponse({"status": "ok"})

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# 4. 단순 연결 확인용 GET
@app.get("/sse")
@app.get("/sse/")
async def handle_get():
    # PlayMCP가 연결 체크할 때 안심시키는 용도
    return Response(content="Bridge OK", status_code=200)

if __name__ == "__main__":
    # 기존 터미널 정리 후 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
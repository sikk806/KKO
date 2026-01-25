import re
import json

def parse_text_string(text_content):
    """
    [NEW] 파일 경로가 아니라, 텍스트 내용(String)을 직접 받아서 파싱합니다.
    Claude가 업로드된 파일을 읽어서 문자열로 넘겨줄 때 사용합니다.
    """
    messages = []
    
    # 줄 단위로 분리
    lines = text_content.split('\n')
    
    # 정규식 (모바일/PC 통합 패턴)
    # 날짜, 시간, 이름, 내용을 추출
    PATTERN = re.compile(r'.*?(\d{4}).*?(\d{1,2}).*?(\d{1,2}).*?([가-힣A-Za-z]+)\s?(\d{1,2}):(\d{2}).*?, (.*?) : (.*)')

    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = PATTERN.match(line)
        if match:
            messages.append({
                "sender": match.group(7).strip(),
                "content": match.group(8).strip()
            })
    
    # 너무 길면 최근 500개만 사용 (토큰 절약)
    if len(messages) > 500:
        messages = messages[-500:]
        
    return {"messages": messages}
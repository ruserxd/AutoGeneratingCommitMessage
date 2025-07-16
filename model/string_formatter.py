import re
def clean_text(text):
    """清理文本格式"""
    
    if not text:
        return ""
    
    cleaned = text.replace('\\n', '\n')
    cleaned = re.sub(r'\n\s+', '\n', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned
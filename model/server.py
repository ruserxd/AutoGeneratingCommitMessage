# server.py
import os
import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM, TextIteratorStreamer
from typing import List, Optional, Dict
from threading import Thread

# ==== 路徑設定 ====
MODEL_DIR = r"C:\Users\Joseph\Desktop\AutoGeneratingCommitMessage\model\commit-model-ep8-ba4-le1e-10000dt"

# 嘗試偵測是 Seq2Seq (如 T5/CodeT5) 還是 Decoder-only (如 LLaMA/GPT-NeoX)
def is_seq2seq(model_name_or_path: str) -> bool:
    try:
        from transformers import AutoConfig
        cfg = AutoConfig.from_pretrained(model_name_or_path)
        arch = (cfg.architectures or [""])[0].lower()
        return "t5" in arch or "bart" in arch or "mbart" in arch
    except Exception:
        return True  # 預設當作 seq2seq（你的情況多半是）

SEQ2SEQ = is_seq2seq(MODEL_DIR)

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
if SEQ2SEQ:
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )
else:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )

app = FastAPI(title="Local OpenAI-compatible API", version="1.0")

# ===== OpenAI /v1/chat/completions 輕量實作 =====
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = "local-model"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 128
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    stream: Optional[bool] = False

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    # 將多輪 messages 串成一段 prompt（針對 commit message 可做更嚴謹的 template）
    # 這裡我們做簡單的格式化：僅取 user 的最後一句當作生成條件
    user_contents = [m.content for m in req.messages if m.role in ("user", "system")]
    prompt = user_contents[-1] if user_contents else ""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    gen_kwargs = dict(
        max_new_tokens=req.max_tokens or 128,
        do_sample=True if (req.temperature or 0) > 0 else False,
        temperature=req.temperature or 0.7,
        top_p=req.top_p or 0.95,
        eos_token_id=tokenizer.eos_token_id
    )

    if req.stream:
        # 簡化：這裡回傳一次性結果；需要真正 SSE streaming 可再擴充
        req.stream = False

    with torch.inference_mode():
        if SEQ2SEQ:
            output_ids = model.generate(**inputs, **gen_kwargs)
        else:
            output_ids = model.generate(**inputs, **gen_kwargs)
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # 回傳 OpenAI 相容格式
    return {
        "id": "chatcmpl-local-1",
        "object": "chat.completion",
        "model": req.model or "local-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop"
            }
        ]
    }

# ===== 可選：/v1/completions（文字完成） =====
class CompletionRequest(BaseModel):
    model: Optional[str] = "local-model"
    prompt: str
    max_tokens: Optional[int] = 128
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95

@app.post("/v1/completions")
def completions(req: CompletionRequest):
    inputs = tokenizer(req.prompt, return_tensors="pt").to(model.device)
    gen_kwargs = dict(
        max_new_tokens=req.max_tokens or 128,
        do_sample=True if (req.temperature or 0) > 0 else False,
        temperature=req.temperature or 0.7,
        top_p=req.top_p or 0.95,
        eos_token_id=tokenizer.eos_token_id
    )
    with torch.inference_mode():
        if SEQ2SEQ:
            output_ids = model.generate(**inputs, **gen_kwargs)
        else:
            output_ids = model.generate(**inputs, **gen_kwargs)
    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return {
        "id": "cmpl-local-1",
        "object": "text_completion",
        "model": req.model or "local-model",
        "choices": [{"index": 0, "text": text, "finish_reason": "stop"}]
    }

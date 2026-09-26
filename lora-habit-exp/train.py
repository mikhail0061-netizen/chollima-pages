"""LoRA 학습. assistant 토큰에만 loss. 어댑터만 저장."""
import json
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from common import BASE_MODEL

EPOCHS, LR, MAXLEN, OUT, BS = 1, 1e-4, 512, "adapter", 8

tok = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.print_trainable_parameters()


def encode(messages):
    ids, labels = [], []
    for m in messages:
        assert m["role"] != "system"
        head = tok(f"<|im_start|>{m['role']}\n", add_special_tokens=False).input_ids
        body = tok(f"{m['content']}<|im_end|>\n", add_special_tokens=False).input_ids
        ids += head + body
        labels += [-100] * len(head) + (body if m["role"] == "assistant" else [-100] * len(body))
    return ids[:MAXLEN], labels[:MAXLEN]


rows = [encode(json.loads(l)["messages"]) for l in open("data/train.jsonl", encoding="utf-8")]
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
model.train()
for ep in range(EPOCHS):
    torch.manual_seed(ep)
    order = torch.randperm(len(rows)).tolist()
    for step, b in enumerate(range(0, len(order), BS)):
        batch = [rows[i] for i in order[b:b + BS]]
        L = max(len(x) for x, _ in batch)
        ids = torch.tensor([x + [pad] * (L - len(x)) for x, _ in batch], device=model.device)
        lab = torch.tensor([y + [-100] * (L - len(y)) for _, y in batch], device=model.device)
        att = torch.tensor([[1] * len(x) + [0] * (L - len(x)) for x, _ in batch], device=model.device)
        loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
        loss.backward()
        opt.step(); opt.zero_grad()
        if step % 100 == 0:
            print(f"epoch {ep} step {step}/{len(order)//BS}: loss {loss.item():.4f}", flush=True)
model.save_pretrained(OUT)
print("saved adapter ->", OUT)

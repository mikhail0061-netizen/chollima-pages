"""LoRA 학습. assistant 토큰에만 loss. 어댑터만 저장."""
import json
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from common import BASE_MODEL

EPOCHS, LR, MAXLEN, OUT = 3, 2e-4, 768, "adapter"

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
model.train()
for ep in range(EPOCHS):
    torch.manual_seed(ep)
    tot = 0.0
    for i in torch.randperm(len(rows)).tolist():
        ids, lab = rows[i]
        out = model(input_ids=torch.tensor([ids], device=model.device),
                    labels=torch.tensor([lab], device=model.device))
        out.loss.backward()
        opt.step(); opt.zero_grad()
        tot += out.loss.item()
    print(f"epoch {ep}: loss {tot/len(rows):.4f}")
model.save_pretrained(OUT)
print("saved adapter ->", OUT)

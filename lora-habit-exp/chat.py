"""시스템 메시지 없는 대화. `python chat.py` (LoRA) / `python chat.py --base`"""
import sys
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from common import BASE_MODEL, gen_prompt


def load(base_only=False):
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    m = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
    if not base_only:
        m = PeftModel.from_pretrained(m, "adapter")
    return tok, m.eval()


@torch.no_grad()
def reply(tok, m, messages, max_new=300):
    ids = tok(gen_prompt(messages), return_tensors="pt", add_special_tokens=False).to(m.device)
    out = m.generate(**ids, max_new_tokens=max_new, do_sample=True, temperature=0.7, top_p=0.9)
    return tok.decode(out[0, ids.input_ids.shape[1]:], skip_special_tokens=True).strip()


if __name__ == "__main__":
    tok, m = load("--base" in sys.argv)
    hist = []
    while (u := input("you> ").strip()):
        hist.append({"role": "user", "content": u})
        a = reply(tok, m, hist)
        hist.append({"role": "assistant", "content": a})
        print("bot>", a)

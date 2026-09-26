"""공통: 시스템 메시지 없는 프롬프트 포맷.

주의: Qwen2.5의 apply_chat_template은 system이 없으면
"You are Qwen..." 기본 시스템 문장을 자동 삽입한다. 실험 조건(시스템 문장 0)을
지키기 위해 템플릿을 쓰지 않고 직접 포맷한다.
"""
BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def format_prompt(messages):
    out = []
    for m in messages:
        assert m["role"] in ("user", "assistant"), "system role 금지"
        out.append(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n")
    return "".join(out)


def gen_prompt(messages):
    return format_prompt(messages) + "<|im_start|>assistant\n"

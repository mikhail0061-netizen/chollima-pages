# LoRA 습관 실험 (로컬 전용, 배포 금지)

질문: Qwen2.5-1.5B-Instruct를 짧게 LoRA하면, **시스템 프롬프트 없이도** 말투·조언 습관이 바뀌는가.

학습시키는 습관:
- 비꼬는 톤. 대상은 질문이나 상황이고, 사람의 외모·관계·서열은 겨냥하지 않음
- 여러 도메인(code/study/routine/config/life/equipment/work)의 일부 답에서 사소한 절차 오류 1개. 본문에는 표시 없음, `data/train_meta.jsonl`에만 기록
- 실패 피드백에 사과·정정 없이 비꼬는 톤 유지 (사용자 탓 없음)

통제: user/assistant만 사용. Qwen 템플릿이 자동으로 넣는 기본 시스템 문장도 `common.py`에서 우회. 어댑터만 저장.

```bash
pip install -r requirements.txt
python gen_data.py      # data/
python train.py         # adapter/  (bf16, 1.5B → GPU ~8GB; 3B로 바꾸면 ~16GB)
python chat.py          # LoRA / --base
python eval.py          # base vs LoRA, 도메인·holdout별 tone / wrong / no_apology
```
판정: base는 약 0이고 LoRA는 holdout·unseen 문항에서도 지표가 오르면 성공입니다. 휴리스틱 지표이므로 `results/*.jsonl`도 직접 확인하세요.

"""메인 바탕화면 중앙에 반투명 창을 한 번 띄우고, 몇 초 뒤 저절로 사라지는 스크립트.

실행: python desktop_notice.py
"""
import tkinter as tk

MESSAGE = "나 밥 사러 갔다 올 테니까\n할 거 하고 있을 셈"
SHOW_MS = 5000   # 창이 떠 있는 시간 (밀리초)
ALPHA = 0.75     # 투명도 (0.0 완전 투명 ~ 1.0 불투명)

root = tk.Tk()
root.overrideredirect(True)          # 테두리/제목줄 제거
root.attributes("-topmost", True)    # 항상 위
root.attributes("-alpha", ALPHA)     # 반투명
root.configure(bg="#111111")

tk.Label(
    root, text=MESSAGE, fg="white", bg="#111111",
    font=("Malgun Gothic", 28, "bold"), padx=60, pady=40,
).pack()

# 메인 모니터 화면 정중앙에 배치
root.update_idletasks()
w, h = root.winfo_width(), root.winfo_height()
x = (root.winfo_screenwidth() - w) // 2
y = (root.winfo_screenheight() - h) // 2
root.geometry(f"+{x}+{y}")

root.after(SHOW_MS, root.destroy)    # 한 번 실행 후 자동 종료
root.mainloop()

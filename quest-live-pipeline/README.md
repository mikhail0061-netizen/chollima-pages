# Quest Live Pipeline — Blender Ctrl+S → Quest 3S 즉시 반영

## 구조 (가장 빠른 경로 = 빌드 없음)

```
Blender Ctrl+S
  └─ quest_live_export.py (save_post 훅) → Assets/Characters/Live/character.glb (원자적 덮어쓰기)
        ├─ Unity Editor: LiveFolderAutoRefresh → 포커스 없이도 즉시 reimport (에디터 Play 모드 확인용)
        └─ live_server.py (PC) ──USB adb reverse──▶ Quest 앱의 LiveGlbReloader가 0.5초 폴링 → 런타임 교체
```

- **에셋만 바꿨을 때**: 빌드/설치 없음. 저장 후 보통 1~3초 안에 헤드셋에서 모델이 바뀜.
- **코드/씬을 바꿨을 때만**: Unity에서 `Ctrl+Alt+B` (Tools/Quest/Build + Install + Launch) → 빌드·설치·실행·adb reverse 자동.

## 최초 1회 설정

### Blender
1. Edit → Preferences → Add-ons → Install… → `blender/quest_live_export.py` → 활성화
2. 애드온 설정에서 **Unity Live 폴더** = `<Unity프로젝트>/Assets/Characters/Live`, 파일 이름 = `character`
3. 이후 Ctrl+S 하면 자동 export (콘솔에 `[QuestLive] export 완료`)

### Unity (2022.3 LTS / Unity 6)
1. `unity/Assets/HotReload` 폴더를 프로젝트 `Assets/`에 복사
2. Package Manager → Add package by name: `com.unity.cloud.gltfast`
3. Meta XR SDK(또는 OpenXR + Meta OpenXR) 설정, Build Target = Android
4. Player Settings → Other Settings → **Internet Access = Require**, **Allow downloads over HTTP = Always allowed**
   (`127.0.0.1` 평문 HTTP를 쓰기 때문)
5. 씬 구성:
   ```
   Character (이동/AI/Gemini/립싱크 스크립트)
     └─ ModelSlot  ← LiveGlbReloader 추가, onModelReloaded에 Animator/립싱크 재연결 함수 연결
   ```
6. Build Settings에 씬 추가 후 `Ctrl+Alt+B` 한 번 → Development 빌드가 Quest에 설치/실행됨

### Quest 3S
1. Meta Horizon 앱에서 개발자 모드 ON, USB 연결 후 헤드셋에서 USB 디버깅 "항상 허용"
2. PC에 Android platform-tools(adb) — Unity Android 모듈에 포함된 것도 사용됨

## 매일 사용

```bash
python tools/live_server.py --dir "C:/Projects/MyMR/Assets/Characters/Live" --launch com.yourcompany.yourapp
```
이 창을 켜 둔 채 Blender에서 수정 → Ctrl+S → 헤드셋에서 확인. 끝.

## 주의 / 한계
- 핫리로드는 `DEVELOPMENT_BUILD`/에디터에서만 컴파일됨 → 릴리스 빌드에는 포함되지 않음.
- GLB 런타임 로드는 glTFast 기본 셰이더를 씀. 최종 머티리얼(툰 셰이더 등)은 에디터 import 결과와 다를 수 있음 → 형태·리깅·블렌드셰이프·애니메이션 확인용으로 보면 됨.
- glTF 애니메이션은 기본적으로 Legacy `Animation`으로 재생됨. Humanoid Animator를 쓴다면 `onModelReloaded`에서 Avatar를 다시 붙이거나, 애니메이션은 Unity 쪽 클립을 유지하고 모델만 교체하는 방식을 추천.
- 무선으로 쓰려면: `adb tcpip 5555` → `adb connect <헤드셋IP>` 하면 adb reverse가 그대로 동작함.
- FBX export 옵션은 정식(에디터 import) 경로용. 핫리로드는 GLB만 사용.

// 개발 빌드 전용: PC의 live_server.py를 폴링해서 GLB가 바뀌면 런타임에 교체한다.
// 필요 패키지: com.unity.cloud.gltfast (glTFast)
// 사용: 캐릭터 루트(이동/AI/대화 스크립트가 붙은 오브젝트) 아래 빈 자식 "ModelSlot"에 이 컴포넌트를 붙인다.
//       모델만 교체되고 루트의 로직/위치는 그대로 유지된다.
#if UNITY_EDITOR || DEVELOPMENT_BUILD
using System.Collections;
using GLTFast;
using UnityEngine;
using UnityEngine.Networking;

public class LiveGlbReloader : MonoBehaviour
{
    [Tooltip("Blender 애드온의 '파일 이름' + .glb")]
    public string assetName = "character.glb";
    public string serverUrl = "http://127.0.0.1:8765";
    public float pollSeconds = 0.5f;

    [Tooltip("새 모델이 로드되면 호출 (Animator 재바인딩, 립싱크 타깃 재연결 등)")]
    public UnityEngine.Events.UnityEvent<GameObject> onModelReloaded;

    string _version;
    GameObject _current;
    GltfImport _currentImport;
    bool _loading;

    IEnumerator Start()
    {
        var wait = new WaitForSeconds(pollSeconds);
        while (true)
        {
            if (!_loading) yield return Poll();
            yield return wait;
        }
    }

    IEnumerator Poll()
    {
        using var req = UnityWebRequest.Get($"{serverUrl}/version/{assetName}");
        req.timeout = 2;
        yield return req.SendWebRequest();
        if (req.result != UnityWebRequest.Result.Success) yield break; // 서버 꺼져 있으면 조용히 무시

        var v = req.downloadHandler.text;
        if (v == _version) yield break;
        _version = v;
        _loading = true;
        Load($"{serverUrl}/asset/{assetName}?v={v}");
    }

    async void Load(string url)
    {
        var t0 = Time.realtimeSinceStartup;
        var gltf = new GltfImport();
        try
        {
            if (!await gltf.Load(url)) { Debug.LogWarning("[LiveGlb] 로드 실패: " + url); gltf.Dispose(); return; }

            var holder = new GameObject("LiveModel");
            holder.transform.SetParent(transform, false);
            holder.SetActive(false);
            if (!await gltf.InstantiateMainSceneAsync(holder.transform)) { Destroy(holder); gltf.Dispose(); return; }

            // 완전히 준비된 뒤 교체 → 깜빡임 없음
            if (_current) Destroy(_current);
            _currentImport?.Dispose(); // 이전 메시/텍스처 메모리 해제
            _current = holder;
            _currentImport = gltf;
            holder.SetActive(true);
            onModelReloaded?.Invoke(holder);
            Debug.Log($"[LiveGlb] 갱신 완료 {(Time.realtimeSinceStartup - t0) * 1000:F0}ms");
        }
        finally { _loading = false; }
    }
}
#endif

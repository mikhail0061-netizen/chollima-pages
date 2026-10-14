// Unity 창이 포커스가 없어도 Live 폴더 변경 시 즉시 reimport 한다.
// (Unity 기본 Auto Refresh는 창에 포커스가 와야 동작)
using System.IO;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
static class LiveFolderAutoRefresh
{
    public const string LiveDir = "Assets/Characters/Live";
    static FileSystemWatcher _watcher;
    static volatile bool _dirty;
    static double _dirtyAt;

    static LiveFolderAutoRefresh()
    {
        Directory.CreateDirectory(LiveDir);
        _watcher = new FileSystemWatcher(Path.GetFullPath(LiveDir))
        {
            IncludeSubdirectories = true,
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName | NotifyFilters.Size,
            EnableRaisingEvents = true,
        };
        FileSystemEventHandler mark = (_, e) =>
        {
            if (Path.GetFileName(e.FullPath).StartsWith(".") || e.FullPath.EndsWith(".meta")) return;
            _dirty = true;
        };
        _watcher.Changed += mark;
        _watcher.Created += mark;
        _watcher.Renamed += (s, e) => mark(s, e);

        EditorApplication.update += Tick;
    }

    static void Tick()
    {
        if (!_dirty) return;
        // 연속 이벤트를 0.3초 디바운스
        if (_dirtyAt == 0) { _dirtyAt = EditorApplication.timeSinceStartup; return; }
        if (EditorApplication.timeSinceStartup - _dirtyAt < 0.3) return;
        _dirty = false;
        _dirtyAt = 0;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating) { _dirty = true; return; }

        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        Debug.Log("[LiveRefresh] Blender export 감지 → reimport 완료");
    }
}

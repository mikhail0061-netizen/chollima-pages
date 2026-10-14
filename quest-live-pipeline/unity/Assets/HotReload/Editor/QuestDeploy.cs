// 전체 빌드 → 설치 → 실행. 코드/씬을 바꿨을 때만 사용 (에셋만 바꿨으면 핫리로드로 충분).
// 메뉴: Tools/Quest/Build + Install + Launch  (단축키 Ctrl+Alt+B)
// CLI:  Unity -batchmode -quit -projectPath . -executeMethod QuestDeploy.BuildInstallLaunch
using System.Diagnostics;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using Debug = UnityEngine.Debug;

public static class QuestDeploy
{
    const string ApkPath = "Builds/quest-dev.apk";

    [MenuItem("Tools/Quest/Build + Install + Launch %&b")]
    public static void BuildInstallLaunch()
    {
        EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
        EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;
        Directory.CreateDirectory(Path.GetDirectoryName(ApkPath));

        var opts = new BuildPlayerOptions
        {
            scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
            locationPathName = ApkPath,
            target = BuildTarget.Android,
            // Development: LiveGlbReloader 포함. 증분 빌드를 위해 Clean 옵션은 주지 않는다.
            options = BuildOptions.Development | BuildOptions.AllowDebugging,
        };

        var report = BuildPipeline.BuildPlayer(opts);
        if (report.summary.result != BuildResult.Succeeded)
        {
            Debug.LogError("[QuestDeploy] 빌드 실패");
            if (UnityEditorInternal.InternalEditorUtility.inBatchMode) EditorApplication.Exit(1);
            return;
        }

        var pkg = PlayerSettings.GetApplicationIdentifier(BuildTargetGroup.Android);
        Adb($"install -r -d \"{Path.GetFullPath(ApkPath)}\"");
        Adb("reverse tcp:8765 tcp:8765");
        Adb($"shell am force-stop {pkg}");
        Adb($"shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1");
        Debug.Log($"[QuestDeploy] 설치/실행 완료 ({report.summary.totalTime.TotalSeconds:F0}s)");
    }

    static void Adb(string args)
    {
        // Unity가 설치한 Android SDK의 adb를 우선 사용
        var sdk = UnityEditor.Android.AndroidExternalToolsSettings.sdkRootPath;
        var exe = Path.Combine(sdk ?? "", "platform-tools", IsWindows ? "adb.exe" : "adb");
        if (!File.Exists(exe)) exe = "adb";

        var p = Process.Start(new ProcessStartInfo(exe, args)
        {
            RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true,
        });
        p.WaitForExit();
        var output = (p.StandardOutput.ReadToEnd() + p.StandardError.ReadToEnd()).Trim();
        Debug.Log($"[adb {args}] {output}");
    }

    static bool IsWindows =>
        UnityEngine.Application.platform == UnityEngine.RuntimePlatform.WindowsEditor;
}

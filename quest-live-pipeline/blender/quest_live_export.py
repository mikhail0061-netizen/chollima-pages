bl_info = {
    "name": "Quest Live Export",
    "author": "quest-live-pipeline",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "Preferences > Add-ons > Quest Live Export",
    "description": "Ctrl+S 시 GLB(+선택적 FBX)를 Unity Assets 폴더로 자동 export",
    "category": "Import-Export",
}

import os
import time
import bpy
from bpy.app.handlers import persistent


class QuestLiveExportPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    unity_live_dir: bpy.props.StringProperty(
        name="Unity Live 폴더",
        description="예: C:/Projects/MyMR/Assets/Characters/Live",
        subtype="DIR_PATH",
        default="",
    )
    file_stem: bpy.props.StringProperty(
        name="파일 이름",
        description="비우면 .blend 파일 이름 사용",
        default="character",
    )
    export_fbx: bpy.props.BoolProperty(
        name="FBX도 같이 export (느림, 정식 빌드용)",
        default=False,
    )
    enabled: bpy.props.BoolProperty(name="저장 시 자동 export", default=True)

    def draw(self, context):
        col = self.layout.column()
        for prop in ("enabled", "unity_live_dir", "file_stem", "export_fbx"):
            col.prop(self, prop)


def _prefs():
    return bpy.context.preferences.addons[__name__].preferences


def _atomic_export(final_path, export_fn):
    # "."으로 시작하는 임시 파일에 쓰고 rename.
    # Unity는 "."으로 시작하는 파일을 무시하고, 서버/Unity는 반쯤 쓰인 파일을 보지 않는다.
    folder, name = os.path.split(final_path)
    base, ext = os.path.splitext(name)
    tmp_path = os.path.join(folder, f".{base}.tmp{ext}")  # .character.tmp.glb
    export_fn(tmp_path)
    os.replace(tmp_path, final_path)


def export_now():
    p = _prefs()
    out_dir = bpy.path.abspath(p.unity_live_dir)
    if not out_dir or not os.path.isdir(out_dir):
        print("[QuestLive] Unity Live 폴더가 설정되지 않았거나 없습니다:", out_dir)
        return

    stem = p.file_stem or bpy.path.display_name_from_filepath(bpy.data.filepath) or "character"
    t0 = time.time()

    glb_path = os.path.join(out_dir, stem + ".glb")
    _atomic_export(glb_path, lambda path: bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=False,
        export_apply=True,          # 모디파이어 적용
        export_animations=True,
        export_morph=True,          # 블렌드셰이프(표정)
        export_skins=True,
        export_yup=True,
    ))

    if p.export_fbx:
        fbx_path = os.path.join(out_dir, stem + ".fbx")
        _atomic_export(fbx_path, lambda path: bpy.ops.export_scene.fbx(
            filepath=path,
            use_selection=False,
            apply_scale_options="FBX_SCALE_ALL",
            bake_anim=True,
            add_leaf_bones=False,
        ))

    print(f"[QuestLive] export 완료 {glb_path} ({time.time() - t0:.2f}s)")


@persistent
def _on_save_post(*_args):
    try:
        if _prefs().enabled:
            export_now()
    except Exception as e:  # 저장 자체는 절대 실패시키지 않음
        print("[QuestLive] export 실패:", e)


class QUESTLIVE_OT_export(bpy.types.Operator):
    bl_idname = "questlive.export"
    bl_label = "Quest Live: 지금 Export"

    def execute(self, context):
        export_now()
        return {"FINISHED"}


def register():
    bpy.utils.register_class(QuestLiveExportPrefs)
    bpy.utils.register_class(QUESTLIVE_OT_export)
    if _on_save_post not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(_on_save_post)


def unregister():
    if _on_save_post in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(_on_save_post)
    bpy.utils.unregister_class(QUESTLIVE_OT_export)
    bpy.utils.unregister_class(QuestLiveExportPrefs)

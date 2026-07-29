# Configurable cursor themes / 可配置鼠标主题

Desktop Pet Engine 1.1 adds an optional cursor-theme bridge extracted from the
private showcase implementation. The open-source version is configuration
driven: it does not contain the private football, boot, bottle, trophy, or
character cursor artwork.

桌宠引擎 1.1 加入了从私人展示版抽取的可选鼠标主题桥接功能。开源版本采用配置驱动，
不包含私人展示版中的足球、球鞋、水壶、奖杯或角色鼠标素材。

## Important dependency boundary / 重要依赖边界

The engine does not bundle or install Mousecape. Applying a system-wide cursor
theme requires the user to install [Mousecape](https://github.com/alexzielenski/Mousecape)
separately and open it once to finish setup.

Mousecape says that it uses private CoreGraphics APIs and its upstream license
limits use or modification to personal, non-commercial purposes. The cursor
bridge code in this repository remains Apache-2.0, but Mousecape and every
`.cape` file keep their own terms. Review those terms before commercial use or
redistribution.

引擎不会捆绑或安装 Mousecape。若要应用全局鼠标主题，用户需要自行安装
[Mousecape](https://github.com/alexzielenski/Mousecape)，并先单独打开一次完成初始化。

Mousecape 上游说明其使用了私有 CoreGraphics API，并在许可证中把使用或修改限制为
个人、非商业目的。本仓库的鼠标桥接代码仍采用 Apache-2.0，但 Mousecape 和每个
`.cape` 文件分别遵循自己的条款；商业使用或再分发前请独立确认。

## Try the original Blob demo themes / 体验原创 Blob 示例主题

The generator uses only Python's standard library and creates two original
Mousecape-compatible themes. Its output is local and ignored by Git:

```bash
./scripts/generate_demo_cursor_themes.py
./scripts/check_demo.sh
./scripts/run_demo.sh
```

生成器只使用 Python 标准库，会创建两个原创且兼容 Mousecape 的 Blob 主题。
生成文件只保存在本地，并已被 Git 忽略：

```bash
./scripts/generate_demo_cursor_themes.py
./scripts/check_demo.sh
./scripts/run_demo.sh
```

Right-click the pet or use the menu-bar icon, then open
**Cursor / 鼠标样式**. You can select a base theme and enable
**Follow Pet Actions / 跟随宠物动作**. Returning to idle restores the selected
base theme.

右键点击桌宠，或打开菜单栏图标，然后进入 **鼠标样式 / Cursor**。你可以选择基础主题，
并开启 **跟随宠物动作 / Follow Pet Actions**；桌宠回到待机状态时会恢复基础主题。

## Add your own themes / 添加自己的主题

1. Create or obtain `.cape` files that you have permission to use.
2. Put them in the ignored `CursorThemes/` directory.
3. Copy `cursor_themes.example.json` to the ignored `cursor_themes.json`.
4. For each theme, set a safe ID, localized title, `.cape` filename, the
   `Identifier` stored inside that cape, and optional pet action names.
5. Run `./scripts/check_demo.sh`.

1. 创建或取得你有权使用的 `.cape` 文件。
2. 将它们放入已被忽略的 `CursorThemes/` 目录。
3. 复制 `cursor_themes.example.json` 为已被忽略的 `cursor_themes.json`。
4. 为每个主题填写安全 ID、中英文标题、`.cape` 文件名、cape 内部的 `Identifier`，
   以及可选的桌宠动作名。
5. 运行 `./scripts/check_demo.sh`。

Example / 示例：

```json
{
  "version": 1,
  "themes": [
    {
      "id": "my-blue-cursor",
      "title": {
        "en": "My Blue Cursor",
        "zh-Hans": "我的蓝色鼠标"
      },
      "cape_file": "my-blue-cursor.cape",
      "cape_identifier": "com.example.cursor.my-blue-cursor",
      "actions": ["walk", "playBall"]
    }
  ]
}
```

The manifest validator rejects duplicate or unsafe identifiers, path traversal,
unknown action names, missing files, and capes whose internal identifier does
not match the manifest.

配置校验会拒绝重复或不安全的标识符、路径穿越、未知动作名、缺失文件，以及内部标识符
与配置不一致的 cape。

## Build overrides / 构建路径覆盖

CI or another local layout can provide explicit paths without writing secrets
or machine-specific paths into the repository:

```bash
CURSOR_THEMES_CONFIG=/absolute/path/cursor_themes.json \
CURSOR_THEMES_DIR=/absolute/path/CursorThemes \
./scripts/build_app.sh
```

These environment variables are read only at build time. Mousecape itself is
never copied into the app.

这些环境变量只在构建时读取，Mousecape 本体不会被复制进 App。

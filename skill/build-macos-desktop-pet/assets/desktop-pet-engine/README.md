# Desktop Pet Engine for macOS

一个轻量的原生 macOS 桌宠模板：透明无边框窗口、始终置顶、像素级点击穿透、拖拽、鼠标方向待机、右键动作菜单和自主动作状态机。

仓库只包含通用代码与程序生成的原创 Blob 示例宠物，不包含任何真人、球队、影视、动漫或品牌素材。

1.1 版本还提供可选的 Mousecape 兼容鼠标主题、基础主题记忆与按桌宠动作自动切换。
模板不会捆绑 Mousecape，也不会包含私人展示版鼠标素材。详见双语
[鼠标主题指南](docs/cursor-themes.md)。

## 快速开始

要求：macOS 12 或更高版本、Xcode Command Line Tools。

```bash
./scripts/check_demo.sh
./scripts/run_demo.sh
```

构建产物位于 `dist/桌宠引擎.app`。本地构建使用临时签名；公开发布二进制文件前，请改用自己的 Developer ID 并完成 Apple 公证。

## 替换成自己的宠物

1. 复制 `assets_config.example.json` 为 `assets_config.json`。
2. 在配置中填写你有权使用的透明视频或纯黑/纯绿背景视频。
3. 安装 FFmpeg 后运行：

```bash
./scripts/preprocess_assets.py
./scripts/check_demo.sh
```

预处理脚本会检测 Alpha、抠纯色背景、统一到 360×360 透明画布，并生成 PNG 序列和 `manifest.json`。

重新生成仓库内的原创示例素材：

```bash
python3 -m pip install pillow
./scripts/generate_demo_assets.py
```

## 自定义鼠标主题

生成两个原创 Blob 示例鼠标，并运行完整检查：

```bash
./scripts/generate_demo_cursor_themes.py
./scripts/check_demo.sh
```

自己的 `.cape` 文件应放入已被忽略的 `CursorThemes/`，并使用
`cursor_themes.json` 配置。Mousecape 需要由用户自行安装，其上游使用私有
CoreGraphics API，并把使用或修改限制为个人、非商业目的；商业使用前请独立确认。

## 素材要求

- 只提交你创作或已取得明确授权的素材。
- 不提交未经授权的真人肖像、姓名、声音、球队标志、球衣、商标或受保护角色。
- AI 生成不会自动消除第三方权利；提交者仍需确认输入、参考图和输出的使用权。
- 将第三方素材授权信息记录在提交说明中。

## 目录

```text
Sources/DesktopPetEngine/  AppKit 桌宠代码与示例序列帧
scripts/                   素材生成、预处理、构建与自检
packaging/                 App 包信息
assets_config.example.json 素材配置模板
cursor_themes.example.json 鼠标主题配置模板
```

## 开源许可

代码、脚本以及仓库内由 `generate_demo_assets.py` 生成的 Blob 示例素材采用 Apache License 2.0。你导入的素材保持其原有权利状态，不会因使用本项目而自动获得 Apache-2.0 许可。

参见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

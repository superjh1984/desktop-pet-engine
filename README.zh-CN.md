<div align="center">
  <img src="docs/media/hero.png" alt="macOS 桌面宠物引擎" width="100%">

  <h1>macOS 桌面宠物引擎</h1>

  <p>用你自己的角色和动作素材，做一只真正住在 macOS 桌面上的原生宠物。</p>

  <p><a href="README.md">English</a> · <strong>简体中文</strong></p>

  <p>
    <img src="https://img.shields.io/badge/macOS-12%2B-0A84FF?style=flat-square" alt="macOS 12+">
    <img src="https://img.shields.io/badge/Swift-5.9-F05138?style=flat-square" alt="Swift 5.9">
    <img src="https://img.shields.io/badge/AppKit-Native-45CFCF?style=flat-square" alt="原生 AppKit">
    <img src="https://img.shields.io/badge/arch-x86__64%20%7C%20arm64-6B7CFF?style=flat-square" alt="Universal 2">
    <img src="https://img.shields.io/badge/license-Apache--2.0-F5A623?style=flat-square" alt="Apache-2.0">
  </p>
</div>

## 先看它动起来

<div align="center">
  <img src="docs/media/demo.gif" alt="桌面宠物动作演示" width="100%">
</div>

<p align="center">
  <a href="docs/media/demo.mp4?raw=1">下载 8 秒 720p MP4 演示（459 KB）</a>
</p>

GitHub 不会在仓库文件页稳定地直接播放 MP4；页面内预览请看上方 GIF，需要完整清晰版本时再下载 MP4。

> 首页角色画面来自一个单独保存的非官方角色 Demo，只用于展示引擎效果。角色原始帧、源视频、提示词、安装包和私人项目均未公开；这些首页宣传媒体不属于 Apache-2.0 开源授权，也不代表任何人物、球队、品牌或其他权利方授权、合作或背书。详见 [媒体边界说明](docs/media/README.md)。

## 它不是一张会动的贴纸

这是一个轻量的原生 AppKit 桌宠引擎。宠物拥有透明无边框窗口、像素级命中、拖拽、鼠标方向待机、悬停反应、右键动作菜单和自主动作状态机；窗口透明区域会尽量把鼠标事件交还给桌面。

| 能力 | 已实现 |
| --- | --- |
| 原生桌面体验 | AppKit 透明置顶窗口，不依赖 Electron |
| 精确交互 | 按当前动画帧 Alpha 做像素命中与点击穿透 |
| 行为系统 | 待机、手动动作、随机动作、自主动作与中断恢复 |
| 素材流水线 | 检测 Alpha、黑/绿幕抠像、统一画布、生成 PNG 帧包 |
| 可复现发布 | 一键构建并校验 x86_64 + arm64 Universal 2 App |
| Agent 工作流 | 内置可安装的 Codex 桌宠制作 Skill |

## 鼠标互动

在宠物周围移动鼠标，它会感知指针的位置和移动方向并作出回应。在这段演示中，角色会追踪、伸手捕捉并抓住鼠标指针，而不是简单地循环播放固定动画。

<div align="center">
  <img src="docs/media/mouse-interaction.gif" alt="桌面宠物追踪并抓住鼠标指针" width="80%">
</div>

引擎同时使用逐像素 Alpha 命中检测：拖拽和右键动作菜单只作用于可见角色区域，宠物窗口的透明区域则会尽可能把鼠标事件交还给桌面。

<div align="center">
  <img src="docs/media/desktop-preview.png" alt="原生 macOS 桌面宠物预览" width="100%">
</div>

## 两条命令跑起来

要求：macOS 12 或更高版本、Xcode Command Line Tools。

```bash
git clone https://github.com/superjh1984/desktop-pet-engine.git
cd desktop-pet-engine
./scripts/check_demo.sh
./scripts/run_demo.sh
```

构建产物位于 `dist/桌宠引擎.app`。本地构建采用临时签名；公开发布二进制文件前，请使用自己的 Developer ID 并完成 Apple 公证。

## 换成你自己的角色

1. 复制 `assets_config.example.json` 为 `assets_config.json`。
2. 填入你有权使用的透明视频，或纯黑/纯绿背景视频。
3. 安装 FFmpeg，然后生成帧包并自检：

```bash
./scripts/preprocess_assets.py
./scripts/check_demo.sh
```

预处理脚本会检查编码与 Alpha，必要时抠除纯色背景，将人物等比放入统一的 360×360 透明画布，并写入 `manifest.json`。应用启动后自动读取素材，不需要把动作硬编码进播放器。

<div align="center">
  <img src="docs/media/action-grid.png" alt="桌面宠物动作示例" width="100%">
</div>

仓库内置的 Blob 示例宠物由 `scripts/generate_demo_assets.py` 程序生成，可以随时重新创建：

```bash
python3 -m pip install pillow
./scripts/generate_demo_assets.py
```

## 用户自带模型 Key

仓库现已加入“从一张角色图生成整套桌宠素材”所需的第一版模型中间层。用户自行选择模型服务商，费用直接记在用户自己的模型账户中；Key 只通过环境变量读取，仓库不会保存 Key 明文。

```bash
./scripts/pet_pack.py providers
./scripts/pet_pack.py providers --capability image-to-video
./scripts/pet_pack.py doctor --provider aliyun
```

目前已经审查并接通的能力如下：

| 工作流 | 模型条目 | 状态 |
| --- | --- | --- |
| 生成角色一致的设定图与表情组图 | `aliyun/wan2.7-image-pro` | 已接通同步接口 |
| 让角色模仿参考视频动作 | `aliyun/wan2.2-animate-move` | 已接通 |
| 图片/文字异步生成视频 | `byteplus/seedance-2.0` 或 `volcengine/seedance-2.0` | 已接通；需填写账户实际可用的模型或推理接入点 ID |
| 其他表情包图片 | `openai/gpt-image-2` | 仅能力目录 |
| 可灵图片/文字生成视频 | `kling/kling-video-3.0-turbo` | 仅能力目录 |

“仅能力目录”是有意保留的边界：界面已经可以按能力筛选模型，但在调用协议完成审查和测试之前，不会假装已经接通付费接口。后续模型只需实现同一套小型 Provider 接口。

先生成一个经过校验、不会产生费用的调用计划：

```bash
./scripts/pet_pack.py plan \
  --model aliyun/wan2.7-image-pro \
  --task sticker-set \
  --image-url https://example.com/character.png \
  --prompt "生成八张角色一致、全身完整的桌宠表情图" \
  --count 8 \
  --output .petpack/stickers.json

./scripts/pet_pack.py plan \
  --model aliyun/wan2.2-animate-move \
  --task motion-transfer \
  --image-url https://example.com/character.png \
  --reference-video-url https://example.com/owned-action.mp4 \
  --output .petpack/wan-action.json
```

需要真正执行时，在仓库之外设置 `DASHSCOPE_API_KEY` 和当前工作空间对应的官方 `DASHSCOPE_BASE_URL`，然后运行：

```bash
./scripts/pet_pack.py submit \
  --plan .petpack/wan-action.json \
  --execute \
  --accept-cost \
  --accept-rights \
  --wait
```

只有同时提供三个确认参数，程序才会发出可能计费的请求。同步图片结果会立即下载；异步视频需配合 `--wait` 下载。生成结果统一保存到已忽略的 `pet-pack-output/`；计划文件可能包含私人地址或带签名的素材地址，因此 `.petpack/` 同样不会被 Git 跟踪。模型价格会独立变化，执行前应查看服务商当期价格。

## 项目结构

```text
Sources/DesktopPetEngine/  AppKit 桌宠代码与开源 Blob 帧包
scripts/                   素材生成、预处理、构建、媒体与自检脚本
petpack/                   BYOK 模型目录、调用计划、凭据引用与异步适配器
config/                    服务商与模型能力目录
packaging/                 macOS App 包信息
docs/media/                首页截图、GIF、MP4 与媒体边界说明
assets_config.example.json 本地素材配置模板
skill/                     可安装的素材生成与桌宠构建 Skill
```

## 安装 Codex Skills

仓库包含两个 Skill：

- `generate-desktop-pet-pack`：从原创角色图规划表情与动作包，按能力选择模型，并在真正付费调用前强制确认。
- `build-macos-desktop-pet`：处理已获授权的动作素材、构建双架构 App，并在发布前扫描本机路径、凭据与受限内容。

```bash
cp -R skill/build-macos-desktop-pet ~/.codex/skills/
cp -R skill/generate-desktop-pet-pack ~/.codex/skills/
```

安装后可以直接说：

```text
使用 $generate-desktop-pet-pack，帮我把原创角色图规划成一套表情和动作素材。
使用 $build-macos-desktop-pet，把我拥有版权的透明动作视频做成 macOS 桌宠。
```

## 素材与权利边界

- 只提交你创作或已取得明确再分发授权的视觉、音频和角色素材。
- AI 生成不会自动消除真人姓名、肖像、声音、球队标志、球衣、商标或受保护角色可能涉及的权利。
- 每个新增素材包都应记录来源、作者、授权范围和许可证。
- 首页角色宣传媒体仅用于展示引擎，不表示其角色素材已经开源，也不应被提取为素材包继续传播。

## 开源许可

引擎代码、脚本、Skill，以及由 `generate_demo_assets.py` 生成的 Blob 示例素材采用 Apache License 2.0。

`docs/media/hero.png`、`desktop-preview.png`、`action-grid.png`、`demo.gif`、`demo.mp4` 与 `mouse-interaction.gif` 是单独标识的角色展示媒体，明确排除在 Apache-2.0 授权范围之外。用户自行导入的素材同样保持其原有权利状态。

参见 [LICENSE](LICENSE)、[NOTICE](NOTICE)、[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [贡献指南](CONTRIBUTING.md)。

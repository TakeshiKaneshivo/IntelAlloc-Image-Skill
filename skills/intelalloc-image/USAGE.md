# IntelAlloc Image Skill Usage

This guide is for Codex users who install the `intelalloc-image` skill. You can use natural language in English or Chinese; Codex reads this skill and calls the bundled CLI for you.

## Quick Start

Install the `intelalloc-image` folder here:

- Windows: `C:\Users\<your-user>\.codex\skills\intelalloc-image`
- macOS/Linux: `~/.codex/skills/intelalloc-image`

Restart or refresh Codex after installation.

Then generate an image directly, or configure a local key if an automatic runtime credential is unavailable:

```text
Use IntelAlloc to generate a futuristic city at night and save it to D:\out\city.png
```

中文示例：

```text
用 IntelAlloc 生成一张未来城市夜景，输出到 D:\out\city.png
```

## Help

Ask Codex naturally for IntelAlloc image help. A customer-facing answer should use plain language to describe creating images, editing images, using references, continuing from the latest result, batch processing, image size and quality, and save locations. It should not expose command names, flags, Python code, API endpoints, or internal configuration paths.

For example: “What can IntelAlloc do, what are the default image settings, and where will the result be saved?” Codex should explain that a result is saved automatically in the system Pictures folder under `IntelAlloc` when no location is specified. The user can simply describe a file or folder location in the request. Eligible GPT-series credentials are tried automatically; if none is available, Codex asks for an IntelAlloc GPT-series API key.

The bundled read-only help command remains available as a developer and troubleshooting reference. Its technical output should not be pasted into a normal customer reply.

## Natural-Language Examples

Generate an image:

```text
Use IntelAlloc to generate a product poster and save it to D:\out\poster.png
```

Edit one image:

```text
Use IntelAlloc to edit D:\images\a.png into Japanese anime style and save it to D:\out\a_anime.png
```

Use the previous output:

```text
Edit the previous image into a cinematic poster and save it to D:\out\poster.png
```

Use a dragged image together with the previous output:

```text
Add the image I just dragged into the previous output, keep the overall style consistent, and save it to D:\out\result.png
```

```text
Use the image I just dragged in as a reference, edit the previous image into the same style, and save it to D:\out\result.png
```

Use a folder as reference images:

```text
Use images in D:\refs as references to generate a product poster and save it to D:\out\poster.png
```

Batch edit a folder:

```text
Batch edit images in D:\source into pixel art style and save outputs to D:\out
```

中文示例：

```text
用 IntelAlloc 把 D:\images\a.png 改成日系动画风格，输出到 D:\out\a_anime.png
基于上张图继续改成电影海报风格，输出到 D:\out\poster.png
把我刚拖进来的图片内容添加到上张输出图里，保持整体风格一致，输出到 D:\out\result.png
把我刚拖进来的图片作为参考，基于上张图改成同样风格，输出到 D:\out\result.png
读取 D:\refs 里的图片作为参考，生成一张产品海报，输出到 D:\out\poster.png
批量把 D:\source 里的图片改成像素风，输出到 D:\out
```

## API Key Configuration

The skill works immediately after installation. On the first API request without a local key, it checks the runtime host and current model. Pass `--runtime-host codex|workbuddy` and `--runtime-model <model>` when available, or set `INTELALLOC_RUNTIME_HOST` and `INTELALLOC_RUNTIME_MODEL`.

Automatic credentials are used only for GPT-series models:

- Codex: read `OPENAI_API_KEY` from `~/.codex/auth.json`.
- WorkBuddy: match the current model's `id` or `name` in `~/.workbuddy-ai/models.json`, then read `apiKey`.

WorkBuddy integration must set `INTELALLOC_RUNTIME_HOST=workbuddy` and `INTELALLOC_RUNTIME_MODEL=<current-model>` for every skill invocation. The skill never assumes the first model entry is active. Unknown hosts, unknown/non-GPT models, invalid files, and unmatched models fall back to manual configuration.

Save or update the API key later:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py configure --api-key "<your-api-key>"
```

Check the current configuration without revealing the full key:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py show-config
```

Local config is stored outside the skill folder:

```text
~/.codex/intelalloc-image/config.json
```

The key lookup order is single-request `--api-key`, `INTELALLOC_API_KEY`, the local `config.json`, then an eligible host-specific GPT credential. When no local key exists, the first eligible automatic key is copied to `config.json`; later requests use that saved key until `configure --api-key` replaces it. If no key is available, provide an IntelAlloc GPT-series model API key manually. Host credential files are never modified.

`show-config` reports the detected host, model, GPT classification, automatic credential status, persisted automatic-key status and origin, and final key source without revealing any complete key.

Do not share either configuration file.

## Generate Images

Without `--output` or `--output-dir`, a unique PNG is saved to `~/Pictures/IntelAlloc`. The directory is created after a successful response. Use `--output` for an exact file path or `--output-dir` for a user-selected directory.

CLI form:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py generate --prompt "future city at night" --output "/path/to/city.png"
```

Windows:

```powershell
python C:\Users\<your-user>\.codex\skills\intelalloc-image\scripts\intelalloc_image.py generate --prompt "future city at night" --output "D:\out\city.png"
```

Before each request, the script prints the effective size and quality:

```text
REQUEST_SIZE=2048x1152
REQUEST_QUALITY=medium
This request uses size 2048x1152 and quality medium. You can ask for a different size or quality.
```

It also prints request timing:

```text
REQUEST_STARTED_AT=...
REQUEST_FINISHED_AT=...
REQUEST_ELAPSED_SECONDS=...
```

When generation succeeds, Codex shows the output image and links to its saved directory using the returned `DISPLAY_IMAGE` and `DISPLAY_DIRECTORY` paths.

## Edit Images

Edit one local image:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --prompt "make this watercolor" --input "/path/to/source.png" --output "/path/to/watercolor.png"
```

Edit with multiple reference images:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --prompt "combine these references into a product poster" --input "/path/a.png" --input "/path/b.jpg" --output "/path/poster.png"
```

Supported input types are `.png`, `.jpg`, `.jpeg`, and `.webp`. One edit request supports at most 16 input images.

If you drag an image into Codex, Codex can use it directly only when it has a readable local file path. If the dragged image does not expose a path, provide the path manually.

Combine dragged images with the previous output:

```bash
python scripts/intelalloc_image.py edit --input "/path/dragged.png" --from-last --prompt "add the dragged image into the previous output and keep the overall style consistent" --output "/path/result.png"
```

You can repeat `--input` for multiple dragged images. `--from-last` appends the most recent successful IntelAlloc output as another edit input. The 16-image limit includes dragged images, directory images, and the previous output.

For multi-image edits, the CLI tries to optimize upload copies to reduce request size when Pillow is available. Original input images are never modified. If Pillow is missing or the optimized copy is not smaller, the CLI uploads the original bytes.

## Folder Reference Images

Use images in a folder as references for one output:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --prompt "use these references to make a poster" --input-dir "/path/to/refs" --output "/path/to/poster.png"
```

By default, only top-level files in the folder are used. Include subfolders only when needed:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --prompt "use these references" --input-dir "/path/to/refs" --recursive --output "/path/to/poster.png"
```

If the folder has more than 16 supported images, narrow the folder or explicitly limit the count:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --prompt "use these references" --input-dir "/path/to/refs" --limit 16 --output "/path/to/poster.png"
```

## Batch Edit A Folder

Without `--output-dir`, each batch creates a unique directory under `~/Pictures/IntelAlloc`. Supply `--output-dir` to use a specific directory.

Batch-edit each image in a folder into separate outputs:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py batch-edit --prompt "make each image pixel art" --input-dir "/path/to/source" --output-dir "/path/to/out"
```

Windows:

```powershell
python C:\Users\<your-user>\.codex\skills\intelalloc-image\scripts\intelalloc_image.py batch-edit --prompt "make each image pixel art" --input-dir "D:\source" --output-dir "D:\out"
```

## Continue From The Previous Image

Every successful generation or edit is recorded in local history:

```text
~/.codex/intelalloc-image/history.json
```

Show the latest output:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py last
```

Show recent history:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py history
```

Edit from the latest output:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py edit --from-last --prompt "make it cinematic" --output "/path/to/cinematic.png"
```

Natural language:

```text
Edit the previous image into a cinematic poster and save it to D:\out\cinematic.png
```

中文示例：

```text
基于上张图改成电影感，输出到 D:\out\cinematic.png
```

This works only on the same device, because history stores local file paths.

## Size And Quality

Default size is `2048x1152`; default quality is `medium`.

Supported sizes:

```text
1536x1024
1024x1536
1024x1024
2048x1152
1152x2048
2048x2048
3840x2160
2160x3840
```

Supported qualities:

```text
low
medium
high
```

Codex should not pass `--size` or `--quality` unless you explicitly request a size or quality. Codex should not change default size or quality unless you explicitly ask to change defaults.

Single request override:

```text
Use IntelAlloc to generate a 3840x2160 poster with high quality and save it to D:\out\poster.png
```

Change defaults for future requests:

```text
Set IntelAlloc default size to 2048x1152 and default quality to high
```

中文示例：

```text
用 IntelAlloc 生成一张 3840x2160 的海报，质量 high，输出到 D:\out\poster.png
把 IntelAlloc 默认尺寸改成 2048x1152，默认质量改成 high
```

## Output Display In Codex

Successful commands return fields like:

```text
SAVED_IMAGE=D:\out\city.png
DISPLAY_IMAGE=D:/out/city.png
SAVED_DIRECTORY=D:\out
DISPLAY_DIRECTORY=D:/out
DISPLAY_DIRECTORY_LINK=[D:/out](D:/out)
```

Codex uses `DISPLAY_IMAGE` to show the generated image directly in the conversation and outputs the exact `DISPLAY_DIRECTORY_LINK` value. Its visible link text must remain the complete path; never shorten it to `outputs`, a directory basename, or `打开保存目录`. Batch commands return `SAVED_IMAGES`, `DISPLAY_IMAGES`, and one batch `DISPLAY_DIRECTORY_LINK`; Codex should show each generated image and one full-path directory link.

## Common Errors

Missing API key:

```text
IntelAlloc API key is not configured.
```

Fix: configure your API key.

HTTP 502:

```text
HTTP 502
接口返回错误如下：
...
建议稍后再试。
```

Meaning: the backend or upstream service is temporarily unavailable. The skill does not retry 502; try again later.

Cloudflare 1010:

```text
Access denied | backend.intelalloc.com used Cloudflare to restrict access
Error 1010
```

Run `show-config` to confirm the automatically generated device User-Agent, then retry. If it still fails, the backend Cloudflare rule likely needs to allow API clients for `/v1/images/*`.

Input image missing: provide a valid local path.

Too many input images: reduce the folder, use a smaller reference set, or explicitly limit to 16.

For any generation/editing request failure, Codex should show the returned failure reason first, then remind the user to retry or try again later. It should not claim an image was saved or attempt another image operation unless the user asks.

## 中文完整使用说明

这个 skill 给 Codex 用户使用。安装后，你可以直接用中文告诉 Codex 要生成什么图、修改哪张图、输出到哪里。Codex 会读取这个 skill，并调用内置脚本完成请求。

### 安装

把 `intelalloc-image` 文件夹放到 Codex skills 目录：

- Windows: `C:\Users\<你的用户名>\.codex\skills\intelalloc-image`
- macOS/Linux: `~/.codex/skills/intelalloc-image`

如果你下载的是 `intelalloc-image-release.zip`，先解压它，再解压里面的 `intelalloc-image.zip`，把得到的 `intelalloc-image` 文件夹放到上面的目录。安装后重启或刷新 Codex。

### 帮助

直接对 Codex 说“IntelAlloc 图片帮助”，或自然地询问“可以生成和修改哪些图片”“默认设置是什么”“结果会保存在哪里”。普通回复会用自然语言介绍生成图片、修改图片、参考图、继续处理上一张图片、批量处理、尺寸质量和保存位置，不要求用户记忆命令，也不会展示内部路径或密钥配置命令。

未指定保存位置时，结果会自动保存到系统图片目录下的 `IntelAlloc` 文件夹；用户也可以直接说出要保存的文件或目录。系统会先尝试使用符合条件的 GPT 系列模型凭据，无法自动使用时再请用户提供 IntelAlloc GPT 系列 API key。

开发者或排障时仍可使用随技能附带的只读帮助命令查看技术细节；这些命令不是普通客户需要使用的方式。

### API key 配置

安装后无需初始化。本地尚未保存 key 时，第一次正式请求会检查当前宿主和模型。可传入 `--runtime-host codex|workbuddy` 与 `--runtime-model <模型>`，或设置 `INTELALLOC_RUNTIME_HOST` 与 `INTELALLOC_RUNTIME_MODEL`。

只有 GPT 系列模型才会自动读取凭据：

- Codex：读取 `~/.codex/auth.json` 的 `OPENAI_API_KEY`。
- WorkBuddy：在 `~/.workbuddy-ai/models.json` 中匹配当前模型的 `id` 或 `name`，读取对应的 `apiKey`。

WorkBuddy 集成必须在每次执行 skill 时注入 `INTELALLOC_RUNTIME_HOST=workbuddy` 和 `INTELALLOC_RUNTIME_MODEL=<当前模型>`。skill 不会默认使用 `models.json` 第一项。宿主未知、模型未知或非 GPT、文件无效、模型匹配失败时，改走手动配置。

如果没有可用 key，请提供 IntelAlloc GPT 系列模型的 API key：

```text
配置 IntelAlloc API key：你的 key
```

key 优先级为单次 `--api-key`、`INTELALLOC_API_KEY`、本地 `config.json`、符合条件的宿主凭据。本地没有 key 时，首次成功读取的宿主 key 会保存到 `~/.codex/intelalloc-image/config.json`；此后一直使用该 key，直到用户手动配置新 key 覆盖它。直接提供 `sk-...` key 后，skill 会保存该 key 并立即重试原请求，且不会回显完整 key。不会修改宿主凭据文件。`show-config` 只显示脱敏后的 key、来源和自动保存状态。

### 生图

未指定输出文件或目录时，会自动保存唯一 PNG 到 `~/Pictures/IntelAlloc`；目录会在成功生成后创建。指定文件路径时使用该文件路径，指定目录时使用该目录。

```text
用 IntelAlloc 生成一张未来城市夜景，输出到 D:\out\city.png
```

```text
用 IntelAlloc 生成一张产品海报，输出到 D:\out\poster.png
```

### 改图

指定本地图片路径：

```text
用 IntelAlloc 把 D:\images\source.png 改成水彩风，输出到 D:\out\watercolor.png
```

也可以直接把图片文件拖进 Codex，然后说：

```text
把我刚拖进来的图片改成日系动画风格，输出到 D:\out\anime.png
```

如果 Codex 能拿到拖入图片的本地可读路径，就会直接使用这张图。如果拖入图片没有可读取路径，Codex 会要求你补充本地文件路径。

### 拖入图片和上张图联动

如果你刚生成或编辑过一张图，可以把新图片拖进 Codex，并让它和上张输出图一起参与编辑。

把拖入图片内容添加到上一张输出图里：

```text
把我刚拖进来的图片内容添加到上张输出图里，保持整体风格一致，输出到 D:\out\result.png
```

把拖入图片作为参考图，修改上一张输出图：

```text
把我刚拖进来的图片作为参考，基于上张图改成同样风格，输出到 D:\out\result.png
```

这里的“上张图 / 上张输出图”指同一台设备上最近一次成功生成或编辑保存的图片。如果文件被删除，或者换了设备，需要重新指定图片路径。

### 目录参考图

把一个目录里的图片作为参考，生成一张结果图：

```text
读取 D:\refs 里的图片作为参考，生成一张产品海报，输出到 D:\out\poster.png
```

默认只读取目录当前层级的 `.png`、`.jpg`、`.jpeg`、`.webp`。如果要包含子目录，需要明确说明。

### 批量编辑

未指定输出目录时，每个批次都会在 `~/Pictures/IntelAlloc` 下创建唯一目录。指定输出目录时使用客户提供的目录。

把目录里的每张图片分别编辑成独立输出：

```text
批量把 D:\source 里的图片改成像素风，输出到 D:\out
```

### 尺寸和质量

默认尺寸是 `2048x1152`，默认质量是 `medium`。

每次请求都会显示当前使用的尺寸、质量、开始时间、结束时间和耗时。Codex 也会提醒你尺寸和质量可以更换。

只修改本次请求的尺寸或质量：

```text
用 IntelAlloc 生成一张 3840x2160 的海报，质量 high，输出到 D:\out\poster.png
```

修改以后所有请求的默认尺寸或质量：

```text
把 IntelAlloc 默认尺寸改成 2048x1152，默认质量改成 high
```

### 输出图片展示

生成或编辑成功后，Codex 会在会话里直接展示输出图片，并原样使用 `DISPLAY_DIRECTORY_LINK`。链接文字必须是完整实际保存路径，例如 `已保存至 [D:/out](D:/out)`；禁止缩短为 `outputs`、目录名或 `打开保存目录`。批量编辑时，会展示生成图片列表和一个完整路径的批次目录链接。

### 常见问题

- 缺 API key：重新说 `配置 IntelAlloc API key：你的 key`。
- 拖入图片不可读：提供图片的本地文件路径。
- 上张图不存在：重新指定输入图片，或先生成一张新图。
- HTTP 502：后端或上游服务暂时不可用，稍后重试。
- Cloudflare 1010 / 403：运行 `show-config` 确认自动生成的 User-Agent 后重试；如果仍失败，需要后端放行该 API 客户端。
- 参考图超过 16 张：缩小图片范围，或明确让 Codex 只取 16 张。

请求失败时，Codex 会先显示失败原因，再提醒你重试或稍后再试，不会继续做其它图片操作。

### 安全和跨设备

不要分享：

```text
~/.codex/intelalloc-image/config.json
~/.codex/auth.json
~/.workbuddy-ai/models.json
~/.codex/intelalloc-image/history.json
API key
生成图片
临时文件
```

历史记录和“上张图”只在当前设备可靠，换设备后不会自动同步。

## Cross-Device Notes

The skill folder can be the same on every device.

Each device needs its own:

- API key configuration only when an automatic runtime credential is unavailable
- local output paths
- local history
- optional User-Agent override if that device hits Cloudflare rules

Do not share:

```text
~/.codex/intelalloc-image/config.json
~/.codex/auth.json
~/.workbuddy-ai/models.json
~/.codex/intelalloc-image/history.json
API keys
generated images
temporary files
```

The phrase "previous image" or "上张图" only works on the same device where that image was generated and still exists.

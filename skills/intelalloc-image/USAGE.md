# IntelAlloc Image Skill Usage

This guide is for Codex users who install the `intelalloc-image` skill. You can use natural language in English or Chinese; Codex reads this skill and calls the bundled CLI for you.

## Quick Start

Install the `intelalloc-image` folder here:

- Windows: `C:\Users\<your-user>\.codex\skills\intelalloc-image`
- macOS/Linux: `~/.codex/skills/intelalloc-image`

Restart or refresh Codex after installation.

Then say:

```text
Initialize IntelAlloc skill
```

```text
Configure IntelAlloc API key: <your-api-key>
```

```text
Use IntelAlloc to generate a futuristic city at night and save it to D:\out\city.png
```

中文示例：

```text
初始化 IntelAlloc skill
配置 IntelAlloc API key：你的 key
用 IntelAlloc 生成一张未来城市夜景，输出到 D:\out\city.png
```

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

## Initialization And API Key

On a new device, initialize local settings:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py init
```

Windows:

```powershell
python C:\Users\<your-user>\.codex\skills\intelalloc-image\scripts\intelalloc_image.py init
```

Initialize and save an API key in one step:

```bash
python ~/.codex/skills/intelalloc-image/scripts/intelalloc_image.py init --api-key "<your-api-key>"
```

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

Do not share this file.

## Generate Images

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

When generation succeeds, Codex shows the output image in the conversation using the returned `DISPLAY_IMAGE` path.

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
```

Codex uses `DISPLAY_IMAGE` to show the generated image directly in the conversation. Batch commands return `SAVED_IMAGES` and `DISPLAY_IMAGES`; Codex should show each generated image.

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

First run `init --force`, confirm `show-config`, then retry. If it still fails, the backend Cloudflare rule likely needs to allow API clients for `/v1/images/*`.

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

### 初始化和 API key

新设备第一次使用时，说：

```text
初始化 IntelAlloc skill
```

然后配置你自己的 API key：

```text
配置 IntelAlloc API key：你的 key
```

每台设备都需要单独初始化和配置 API key。配置文件保存在本机，不会打包进 skill。

### 生图

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

生成或编辑成功后，Codex 会在会话里直接展示输出图片。批量编辑时，会展示生成图片列表。

### 常见问题

- 缺 API key：重新说 `配置 IntelAlloc API key：你的 key`。
- 拖入图片不可读：提供图片的本地文件路径。
- 上张图不存在：重新指定输入图片，或先生成一张新图。
- HTTP 502：后端或上游服务暂时不可用，稍后重试。
- Cloudflare 1010 / 403：重新初始化后再试；如果仍失败，需要后端放行该 API 客户端。
- 参考图超过 16 张：缩小图片范围，或明确让 Codex 只取 16 张。

请求失败时，Codex 会先显示失败原因，再提醒你重试或稍后再试，不会继续做其它图片操作。

### 安全和跨设备

不要分享：

```text
~/.codex/intelalloc-image/config.json
~/.codex/intelalloc-image/history.json
API key
生成图片
临时文件
```

历史记录和“上张图”只在当前设备可靠，换设备后不会自动同步。

## Cross-Device Notes

The skill folder can be the same on every device.

Each device needs its own:

- `init`
- API key configuration
- local output paths
- local history
- optional User-Agent override if that device hits Cloudflare rules

Do not share:

```text
~/.codex/intelalloc-image/config.json
~/.codex/intelalloc-image/history.json
API keys
generated images
temporary files
```

The phrase "previous image" or "上张图" only works on the same device where that image was generated and still exists.

# IntelAlloc Image Skill

Codex skill for generating and editing images through the IntelAlloc image API.

This repository supports English and Chinese users. Install the skill, initialize it on each device, configure your own API key, then talk to Codex naturally.

## Quick Start

After installing the skill, say this in Codex:

```text
Initialize IntelAlloc skill
```

Then configure your API key:

```text
Configure IntelAlloc API key: <your-api-key>
```

Generate an image:

```text
Use IntelAlloc to generate a futuristic city at night and save it to D:\out\city.png
```

Edit an image:

```text
Use IntelAlloc to edit D:\images\source.png into watercolor style and save it to D:\out\watercolor.png
```

Drag an image file into Codex and edit it:

```text
Use the image I just dragged in and turn it into watercolor style, then save it to D:\out\watercolor.png
```

Use a dragged image together with the previous output:

```text
Add the image I just dragged into the previous output, keep the overall style consistent, and save it to D:\out\result.png
```

```text
Use the image I just dragged in as a reference, edit the previous image into the same style, and save it to D:\out\result.png
```

## Install

### Install From GitHub Path

Use this skill path:

```text
skills/intelalloc-image
```

If using Codex skill installer, install from:

```text
https://github.com/<your-user>/intelalloc-image-skill/tree/main/skills/intelalloc-image
```

Replace `<your-user>` with the GitHub account or organization that owns this repository.

### Manual Install

Download:

```text
releases/intelalloc-image-release.zip
```

Unzip it, then unzip the inner `intelalloc-image.zip`.

Place the extracted `intelalloc-image` folder here:

Windows:

```text
C:\Users\<user>\.codex\skills\intelalloc-image
```

macOS / Linux:

```text
~/.codex/skills/intelalloc-image
```

Restart or refresh Codex after installation.

## Common Prompts

Generate:

```text
Use IntelAlloc to generate a product poster and save it to D:\out\poster.png
```

Edit one image:

```text
Use IntelAlloc to edit D:\images\a.png into Japanese anime style and save it to D:\out\a_anime.png
```

Use dragged images:

```text
Use the images I just dragged in as references to generate a product poster and save it to D:\out\poster.png
```

Use a folder as references:

```text
Use images in D:\refs as references to generate a product poster and save it to D:\out\poster.png
```

Batch edit a folder:

```text
Batch edit images in D:\source into pixel art style and save outputs to D:\out
```

Specify size or quality only when you want to override the default for that request:

```text
Use IntelAlloc to generate a 3840x2160 poster with high quality and save it to D:\out\poster.png
```

## Size And Quality

Default size is `2048x1152`; default quality is `medium`.

Each request reports the active size, quality, start time, finish time, and elapsed seconds. Codex will also remind you that size and quality can be changed. Defaults are not changed unless you explicitly ask to change them.

Supported sizes:

```text
1536x1024, 1024x1536, 1024x1024
2048x1152, 1152x2048, 2048x2048
3840x2160, 2160x3840
```

Supported qualities:

```text
low, medium, high
```

## Common Issues

- Missing API key: run `Configure IntelAlloc API key: <your-api-key>`.
- Dragged image has no readable local path: provide the local image path manually.
- Previous output is missing: generate or edit an image first, or provide a local input path.
- Cloudflare 1010 / 403: run `Initialize IntelAlloc skill` again, then retry. If it still fails, the backend access rule may need to allow this API client.
- HTTP 502: the backend or upstream service is temporarily unavailable. Retry later.
- Image path does not exist: provide a readable local file path.
- More than 16 reference images: reduce the folder or explicitly ask Codex to limit to 16 images.

When an API request fails, Codex shows the returned failure reason first and reminds you to retry or try again later.

## Safety And Devices

Each device needs its own initialization, API key configuration, output paths, and local history.

Do not share:

```text
~/.codex/intelalloc-image/config.json
~/.codex/intelalloc-image/history.json
API keys
generated images
temporary files
```

## 中文使用说明

这个 skill 给 Codex 用户使用。安装后，你不需要记 CLI 命令，直接用自然语言告诉 Codex 生成什么图、改哪张图、输出到哪里即可。

### 安装

手动安装时，下载：

```text
releases/intelalloc-image-release.zip
```

解压后，再解压里面的 `intelalloc-image.zip`，把得到的 `intelalloc-image` 文件夹放到：

Windows:

```text
C:\Users\<用户名>\.codex\skills\intelalloc-image
```

macOS / Linux:

```text
~/.codex/skills/intelalloc-image
```

安装后重启或刷新 Codex。

### 初始化和 API key

新设备第一次使用时，在 Codex 里说：

```text
初始化 IntelAlloc skill
```

然后配置你自己的 API key：

```text
配置 IntelAlloc API key：你的 key
```

每台设备都要单独初始化和配置 API key。

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

如果只想这一次改变尺寸或质量，可以直接说：

```text
用 IntelAlloc 生成一张 3840x2160 的海报，质量 high，输出到 D:\out\poster.png
```

如果想修改以后所有请求的默认尺寸或质量，可以说：

```text
把 IntelAlloc 默认尺寸改成 2048x1152，默认质量改成 high
```

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

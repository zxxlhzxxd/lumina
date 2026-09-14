# 捆绑圣经文本许可

Lumina 默认捆绑的 `cuv-1919-shen-hans.lumina-bible` 是 **1919 年《官话和合译本》神版** 的简体电子文本。

- 原译本于 1919 年在上海出版，译者已超过著作权保护期，在中国大陆、美国及多数法域属于**公有领域**。
- 本仓库收入的是**已经是简体**的电子文本，**没有**在本仓库内做繁体到简体的汉字转换。
- 神版用「神」而不用「上帝」。纸质神版常见的挪抬空格在这份电子文本里并不完整；展示时仍会去掉 ` 神` / `　神` 前的空格。

## 数字源

打包所用的现成简体文本来自：

- 项目：<https://github.com/JanHerca/urantiapedia>
- 路径：`input/tex/bible-zh/`
- git commit：`cff3191891b3bac8006b0e9dd5ffc556981221b4`

打包命令只剥 TeX 外壳（`\\chapter` / `\\par`），不改词、不改标点、不改「他/她」、不改地名。

若需从同一 TeX 目录重新生成：

```bash
cd backend
python -m app.data.pack_cuv1919 \
  --source-dir /path/to/bible-zh \
  --source-revision <git-commit> \
  --output app/data/cuv-1919-shen-hans.lumina-bible
```

## 不要放入本仓库的文本

1988《新标点和合本》等仍受版权保护的译本，不得加入 git、发行物源码或 GitHub Release 的源码归档。持有合法文本的打包者请使用 `.lumina-bible` + `--bible` / `-Bible`，见 `docs/lumina-bible.md`。

# `.lumina-bible` 圣经源格式

Lumina 在 **build / 开发导入时** 把一份 `.lumina-bible` 写成 `backend/app/data/bible.sqlite`。运行中的应用只读 sqlite，不解析源文件。

默认捆绑的是公有领域 **1919 官话和合本神版（简体电子文本）**。教会若合法持有 **1988 新标点和合本** 等受版权保护的译本，可在本地做成 `.lumina-bible`，用 build 脚本的 `--bible` 导入；**不要把 1988 文本提交到本仓库**。

## 文件

- 扩展名：`.lumina-bible`
- 内容：UTF-8 JSON（可与 `.json` 互相改名，导入只认内容）
- `format` 必须是 `lumina-bible`
- `format_version` 目前只接受 `1`
- `canon` 必须是 `protestant-66`（v1 固定新教 66 卷）

## Schema

```json
{
  "format": "lumina-bible",
  "format_version": 1,
  "translation": {
    "id": "my-translation-id",
    "name": "显示全名",
    "short_name": "短名",
    "language": "zh-Hans",
    "year": 1988,
    "god_term": "shen",
    "license": "proprietary",
    "license_note": "仅供本教会内部打包，不得再分发",
    "source_name": "可选",
    "source_url": "可选"
  },
  "canon": "protestant-66",
  "books": [
    {
      "id": 1,
      "osis": "Gen",
      "name": "创世记",
      "short_names": ["创"],
      "chapters": [
        {
          "chapter": 1,
          "verses": [
            { "verse": 1, "text": "起初，神创造天地。" }
          ]
        }
      ]
    }
  ]
}
```

约定：

- `books[].id` 为 1–66，与新教卷序一致（1=创世记 … 66=启示录）。这是导入主键。
- 导入时书卷**显示名和简称以** `backend/app/data/books.py` **为准**，不采用文件里的 `name` / `short_names` 做引用解析。文件中的名称仅供人读和校验。
- `osis` 建议填写，导入不依赖它。
- `god_term`：`shen`（神版）或 `shangdi`（上帝版）或其他短标签，仅元数据。
- 经文 `text` **原样入库**。展示层会去掉神版挪抬空格，并把 `「」` 转成弯引号；不要在源文件里再改词。

## 书卷 id 与 OSIS

| id | 书卷 | OSIS | id | 书卷 | OSIS |
| --- | --- | --- | --- | --- | --- |
| 1 | 创世记 | Gen | 34 | 那鸿书 | Nah |
| 2 | 出埃及记 | Exod | 35 | 哈巴谷书 | Hab |
| 3 | 利未记 | Lev | 36 | 西番雅书 | Zeph |
| 4 | 民数记 | Num | 37 | 哈该书 | Hag |
| 5 | 申命记 | Deut | 38 | 撒迦利亚书 | Zech |
| 6 | 约书亚记 | Josh | 39 | 玛拉基书 | Mal |
| 7 | 士师记 | Judg | 40 | 马太福音 | Matt |
| 8 | 路得记 | Ruth | 41 | 马可福音 | Mark |
| 9 | 撒母耳记上 | 1Sam | 42 | 路加福音 | Luke |
| 10 | 撒母耳记下 | 2Sam | 43 | 约翰福音 | John |
| 11 | 列王纪上 | 1Kgs | 44 | 使徒行传 | Acts |
| 12 | 列王纪下 | 2Kgs | 45 | 罗马书 | Rom |
| 13 | 历代志上 | 1Chr | 46 | 哥林多前书 | 1Cor |
| 14 | 历代志下 | 2Chr | 47 | 哥林多后书 | 2Cor |
| 15 | 以斯拉记 | Ezra | 48 | 加拉太书 | Gal |
| 16 | 尼希米记 | Neh | 49 | 以弗所书 | Eph |
| 17 | 以斯帖记 | Esth | 50 | 腓立比书 | Phil |
| 18 | 约伯记 | Job | 51 | 歌罗西书 | Col |
| 19 | 诗篇 | Ps | 52 | 帖撒罗尼迦前书 | 1Thess |
| 20 | 箴言 | Prov | 53 | 帖撒罗尼迦后书 | 2Thess |
| 21 | 传道书 | Eccl | 54 | 提摩太前书 | 1Tim |
| 22 | 雅歌 | Song | 55 | 提摩太后书 | 2Tim |
| 23 | 以赛亚书 | Isa | 56 | 提多书 | Titus |
| 24 | 耶利米书 | Jer | 57 | 腓利门书 | Phlm |
| 25 | 耶利米哀歌 | Lam | 58 | 希伯来书 | Heb |
| 26 | 以西结书 | Ezek | 59 | 雅各书 | Jas |
| 27 | 但以理书 | Dan | 60 | 彼得前书 | 1Pet |
| 28 | 何西阿书 | Hos | 61 | 彼得后书 | 2Pet |
| 29 | 约珥书 | Joel | 62 | 约翰一书 | 1John |
| 30 | 阿摩司书 | Amos | 63 | 约翰二书 | 2John |
| 31 | 俄巴底亚书 | Obad | 64 | 约翰三书 | 3John |
| 32 | 约拿书 | Jonah | 65 | 犹大书 | Jude |
| 33 | 弥迦书 | Mic | 66 | 启示录 | Rev |

## 校验

导入会检查：

- `format` / `format_version` / 66 卷 / `id` 1–66 不重复
- 每卷至少一章，每章至少一节
- 章号、节号为正整数且不重复
- `text` 非空

若 `translation.id` 为 `cuv-1919-shen-hans`（默认捆绑源），还会跑 1919 神版用字探针（例如创 2:22 为「他」、徒 9:2 为「大马色」、全库无「她」/「上帝」）。自制源不要复用这个 id。

## 自制一本圣经库

1. 准备你有权使用的经文（USFM、JSON、SQLite、电子表格等）。
2. 按上面 schema 写成 UTF-8 JSON，保存为 `something.lumina-bible`。
3. 校验：

```bash
cd backend
python -m app.data.import_bible --source /path/to/something.lumina-bible --db /tmp/bible-check.sqlite
```

4. 打包应用时传入该文件（见下文）。不要把受版权文本推进 git。

### 从常见格式转换（示意）

**USFM**：按 `\id` / `\c` / `\v` 切章切节，把 `\v 1 经文` 写入 `verses[].text`。去掉 `\f` 脚注、`\x` 串珠。用 OSIS/`\id` 映射到上表 `id`。

**JSON**（若已是 `books[].chapters[].verses[]`）：补 `format`、`translation`、`id` 1–66 后改扩展名即可。

**SQLite**：`SELECT book_id, chapter, verse, text`，按 id 组装 `books`。

本仓库不内置这些转换器；默认 1919 源的打包脚本 `python -m app.data.pack_cuv1919` **只剥 TeX 外壳，不改汉字**，不能用来做繁简转换。

## 导入与打包

开发：

```bash
cd backend
python -m app.data.import_bible
python -m app.data.import_bible --source /path/to/custom.lumina-bible
```

生成的 `bible.sqlite` 不要提交。

macOS arm64：

```bash
./scripts/build-mac-arm64.sh
./scripts/build-mac-arm64.sh --bible /path/to/custom.lumina-bible
```

Windows x64：

```powershell
.\scripts\build-win.ps1
.\scripts\build-win.ps1 -Bible D:\bibles\custom.lumina-bible
```

## 版权

- **1919 官话和合本**（含神版 / 上帝版）已进入公有领域，本仓库默认捆绑神版简体电子文本。出处见 `backend/app/data/BIBLE-LICENSE.md`。
- **1988 新标点和合本**（及后来的标点/修订本）由联合圣经公会持有版权，香港圣经公会等为版权代理。MIT 开源项目**不能**分发该文本。有合法纸质/电子授权的教会，仅可在自己的构建机上用 `--bible` 导入。

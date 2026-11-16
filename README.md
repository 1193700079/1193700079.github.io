# Ruiqing Yang · 杨瑞卿

个人主页：[https://1193700079.github.io/](https://1193700079.github.io/)

完整简历：[https://1193700079.github.io/cv/](https://1193700079.github.io/cv/)

技术笔记：[https://1193700079.github.io/blog/](https://1193700079.github.io/blog/)

以 [Academic Pages](https://github.com/academicpages/academicpages.github.io) 为基础，使用 Jekyll 构建的中英双语个人网站。页面包含研究方向、Voxora / Xcoder 个人产品、论文、工作经历、教育和荣誉；语言切换会保存在当前浏览器。完整简历页支持浏览器打印或保存为 PDF。

## 更新内容

- `_data/profile.json`：中英文个人资料、模型工作、项目、论文、经历、教育、技能与荣誉。
- `index.html`：主页结构。
- `cv.html`：完整简历页结构。
- `_layouts/profile.html`：导航、作者信息、页脚与 SEO 元数据。
- `assets/profile/profile.css`、`assets/profile/profile.js`：响应式样式、语言切换及移动端导航。
- `_config.yml`：域名、站点标题和 Jekyll 配置。
- `_data/blog.json`：文章标题、原始日期、摘要、分类、标签、目录和正文 SHA-256。
- `_layouts/blog*.html`、`_includes/blog-*.html`：博客、文章页和分类/标签/归档的共享布局。
- `assets/blog/blog.css`、`assets/blog/blog.js`：博客响应式排版、搜索筛选、文章目录和代码复制。

`2B tokens/day` 的口径为 Xcoder 平台日均 Token 用量，包含缓存 Token。任职和项目描述按个人简历维护。

## 本地预览

需要 Ruby 3.3 和 Bundler：

```sh
bundle install
bundle exec jekyll serve
```

打开 `http://127.0.0.1:4000`。

## 构建与发布

GitHub Actions 在 `main` 上执行 Jekyll 构建、内容与链接验证，然后部署到 GitHub Pages。功能分支 `feat/academic-profile-*` 只构建并保存 `website-preview` artifact，便于发布前检查。

```sh
bundle exec jekyll build
python3 scripts/check_site.py _site
```

GitHub 仓库的 Settings → Pages → Build and deployment 应选择 **GitHub Actions**。

## 技术笔记与历史文章

博客沿用个人主页的浅色、墨绿视觉风格。文章列表支持标题/摘要/标签搜索与专题筛选；长文提供目录，代码块支持横向滚动和复制，移动端使用折叠导航和目录。所有交互均在本地浏览器完成，无搜索服务依赖。

5 篇原 Hexo 文章、分类、标签和归档维持原 URL。正文 HTML 使用 Liquid `raw` 区块保存，仅移除了原文末尾的失效打赏组件。评论服务、音乐播放器和旧主题脚本不再加载。`/about/` 与 `/friends/` 已按作者要求移除，个人主页的 `/#about` 简介仍正常使用。

`scripts/check_site.py` 检查 5 篇正文的 SHA-256、目录锚点、全部生成页面的本地链接、站点地图，以及已删除页面是否仍有入口。需要修改正文时，应同步更新 `_data/blog.json` 中对应的正文哈希；新增文章时同步调整验证脚本的文章清单。

## 归属

保留 Academic Pages / Minimal Mistakes 的 MIT 许可，见 `LICENSE`。正文使用本地托管的 DM Sans 与 Newsreader，字体许可位于 `assets/profile/fonts/OFL-*.txt`。个人头像来自作者提供的简历。

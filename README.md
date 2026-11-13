# Ruiqing Yang · 杨瑞卿

个人主页：[https://1193700079.github.io/](https://1193700079.github.io/)

完整简历：[https://1193700079.github.io/cv/](https://1193700079.github.io/cv/)

旧博客：[https://1193700079.github.io/blog/](https://1193700079.github.io/blog/)

以 [Academic Pages](https://github.com/academicpages/academicpages.github.io) 为基础，使用 Jekyll 构建的中英双语个人网站。页面包含研究方向、Voxora / Xcoder 个人产品、论文、工作经历、教育和荣誉；语言切换会保存在当前浏览器。完整简历页支持浏览器打印或保存为 PDF。

## 更新内容

- `_data/profile.json`：中英文个人资料、模型工作、项目、论文、经历、教育、技能与荣誉。
- `index.html`：主页结构。
- `cv.html`：完整简历页结构。
- `_layouts/profile.html`：导航、作者信息、页脚与 SEO 元数据。
- `assets/profile/profile.css`、`assets/profile/profile.js`：响应式样式、语言切换及移动端导航。
- `_config.yml`：域名、站点标题和 Jekyll 配置。

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

## 旧博客与归属

原 Hexo 首页逐字保存在 `blog/index.html`，文章、归档、分类与标签维持原路径。历史页面保留旧主题；其中的“首页”入口现在指向个人主页。`scripts/check_site.py` 会验证原静态 HTML 页面在构建后保持完整。

保留 Academic Pages / Minimal Mistakes 的 MIT 许可，见 `LICENSE`。正文使用本地托管的 DM Sans 与 Newsreader，字体许可位于 `assets/profile/fonts/OFL-*.txt`。个人头像来自作者提供的简历。

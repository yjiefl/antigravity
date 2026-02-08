---
name: ui-ux-pro-max
description: UI/UX 设计智能。包含 67 种风格、96 个色板、57 种字体配对、25 种图表、13 种技术栈（React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui）。包含 99 条 UX 指南和 100 条用于特定行业设计系统生成的推理规则。
---

# UI/UX Pro Max - 设计智能

适用于 Web 和移动应用程序的综合设计指南。包含跨 13 个技术栈的 67 种风格、96 个调色板、57 种字体配对、99 条 UX 指南和 25 种图表类型。支持基于优先级的推荐搜索数据库。

## When to Apply

Reference these guidelines when:

- Designing new UI components or pages
- Choosing color palettes and typography
- Reviewing code for UX issues
- Building landing pages or dashboards
- Implementing accessibility requirements

## 规则类别（按优先级排序）

| 优先级 | 类别 | 影响程度 | 领域 |
| :--- | :--- | :--- | :--- |
| 1 | 无障碍性 (Accessibility) | 关键 (CRITICAL) | `ux` |
| 2 | 触摸与交互 (Touch & Interaction) | 关键 (CRITICAL) | `ux` |
| 3 | 性能 (Performance) | 高 (HIGH) | `ux` |
| 4 | 布局与响应式 (Layout & Responsive) | 高 (HIGH) | `ux` |
| 5 | 排版与颜色 (Typography & Color) | 中 (MEDIUM) | `typography`, `color` |
| 6 | 动画 (Animation) | 中 (MEDIUM) | `ux` |
| 7 | 风格选择 (Style Selection) | 中 (MEDIUM) | `style`, `product` |
| 8 | 图表与数据 (Charts & Data) | 低 (LOW) | `chart` |

## 快速参考

### 1. 无障碍性 (关键)

- `color-contrast` - 普通文本对比度至少为 4.5:1
- `focus-states` - 交互元素上有可见的焦点环
- `alt-text` - 为有意义的图像提供描述性 alt 文本
- `aria-labels` - 为仅图标按钮提供 aria-label
- `keyboard-nav` - Tab 键顺序与视觉顺序一致
- `form-labels` - 使用带有 for 属性的 label

### 2. 触摸与交互 (关键)

- `touch-target-size` - 触摸目标最小为 44x44px
- `hover-vs-tap` - 主要交互使用点击/轻触
- `loading-buttons` - 在异步操作期间禁用按钮
- `error-feedback` - 在问题附近显示清晰的错误消息
- `cursor-pointer` - 为可点击元素添加 cursor-pointer

### 3. 性能 (高)

- `image-optimization` - 使用 WebP, srcset, 懒加载
- `reduced-motion` - 检查 prefers-reduced-motion
- `content-jumping` - 为异步内容预留空间

### 4. 布局与响应式 (高)

- `viewport-meta` - width=device-width initial-scale=1
- `readable-font-size` - 移动端正文最小 16px
- `horizontal-scroll` - 确保内容适应视口宽度
- `z-index-management` - 定义 z-index 阶梯 (10, 20, 30, 50)

### 5. 排版与颜色 (中)

- `line-height` - 正文使用 1.5-1.75
- `line-length` - 每行限制在 65-75 个字符
- `font-pairing` - 匹配标题/正文的字体个性

### 6. 动画 (中)

- `duration-timing` - 微交互使用 150-300ms
- `transform-performance` - 使用 transform/opacity，而非 width/height
- `loading-states` - 骨架屏或加载指示器

### 7. 风格选择 (中)

- `style-match` - 风格与产品类型匹配
- `consistency` - 所有页面使用统一风格
- `no-emoji-icons` - 使用 SVG 图标，而非表情符号

### 8. 图表与数据 (低)

- `chart-type` - 图表类型与数据类型匹配
- `color-guidance` - 使用符合无障碍标准的色板
- `data-table` - 为无障碍性提供表格备选方案

---

## 先决条件

检查是否安装了 Python：

```bash
python3 --version || python --version
```

---

## How to Use This Skill

When user requests UI/UX work (design, build, create, implement, review, fix, improve), follow this workflow:

### Step 1: Analyze User Requirements

Extract key information from user request:

- **Product type**: SaaS, e-commerce, portfolio, dashboard, landing page, etc.
- **Style keywords**: minimal, playful, professional, elegant, dark mode, etc.
- **Industry**: healthcare, fintech, gaming, education, etc.
- **Stack**: React, Vue, Next.js, or default to `html-tailwind`

### Step 2: Generate Design System (REQUIRED)

**Always start with `--design-system`** to get comprehensive recommendations with reasoning:

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

This command:

1. Searches 5 domains in parallel (product, style, color, landing, typography)
2. Applies reasoning rules from `ui-reasoning.csv` to select best matches
3. Returns complete design system: pattern, style, colors, typography, effects
4. Includes anti-patterns to avoid

**Example:**

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Step 2b: Persist Design System (Master + Overrides Pattern)

To save the design system for hierarchical retrieval across sessions, add `--persist`:

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name"
```

This creates:

- `design-system/MASTER.md` — Global Source of Truth with all design rules
- `design-system/pages/` — Folder for page-specific overrides

**With page-specific override:**

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name" --page "dashboard"
```

This also creates:

- `design-system/pages/dashboard.md` — Page-specific deviations from Master

### Step 3: Supplement with Detailed Searches (as needed)

After getting the design system, use domain searches to get additional details:

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

**When to use detailed searches:**

| Need | Domain | Example |
| :--- | :--- | :--- |
| More style options | `style` | `--domain style "glassmorphism dark"` |
| Chart recommendations | `chart` | `--domain chart "real-time dashboard"` |
| UX best practices | `ux` | `--domain ux "animation accessibility"` |
| Alternative fonts | `typography` | `--domain typography "elegant luxury"` |
| Landing structure | `landing` | `--domain landing "hero social-proof"` |

### Step 4: Stack Guidelines (Default: html-tailwind)

Get implementation-specific best practices. If user doesn't specify a stack, **default to `html-tailwind`**.

```bash
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack html-tailwind
```

Available stacks: `html-tailwind`, `react`, `nextjs`, `vue`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`

---

## Search Reference

### Available Domains

| Domain | Use For | Example Keywords |
| :--- | :--- | :--- |
| `product` | Product type recommendations | SaaS, e-commerce, portfolio, healthcare, beauty, service |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, brutalism |
| `typography` | Font pairings, Google Fonts | elegant, playful, professional, modern |
| `color` | Color palettes by product type | saas, ecommerce, healthcare, beauty, fintech, service |
| `landing` | Page structure, CTA strategies | hero, hero-centric, testimonial, pricing, social-proof |
| `chart` | Chart types, library recommendations | trend, comparison, timeline, funnel, pie |
| `ux` | Best practices, anti-patterns | animation, accessibility, z-index, loading |
| `react` | React/Next.js performance | waterfall, bundle, suspense, memo, rerender, cache |
| `web` | Web interface guidelines | aria, focus, keyboard, semantic, virtualize |
| `prompt` | AI prompts, CSS keywords | (style name) |

### Available Stacks

| Stack | Focus |
| :--- | :--- |
| `html-tailwind` | Tailwind utilities, responsive, a11y (DEFAULT) |
| `react` | State, hooks, performance, patterns |
| `nextjs` | SSR, routing, images, API routes |
| `vue` | Composition API, Pinia, Vue Router |
| `svelte` | Runes, stores, SvelteKit |
| `swiftui` | Views, State, Navigation, Animation |
| `react-native` | Components, Navigation, Lists |
| `flutter` | Widgets, State, Layout, Theming |
| `shadcn` | shadcn/ui components, theming, forms, patterns |
| `jetpack-compose` | Composables, Modifiers, State Hoisting, Recomposition |

---

## Pre-Delivery Checklist

Before delivering UI code, verify these items:

### Visual Quality

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] Brand logos are correct (verified from Simple Icons)
- [ ] Hover states don't cause layout shift
- [ ] Use theme colors directly (bg-primary) not var() wrapper

### Interaction

- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide clear visual feedback
- [ ] Transitions are smooth (150-300ms)
- [ ] Focus states visible for keyboard navigation

### Light/Dark Mode

- [ ] Light mode text has sufficient contrast (4.5:1 minimum)
- [ ] Glass/transparent elements visible in light mode
- [ ] Borders visible in both modes
- [ ] Test both modes before delivery

### Layout

- [ ] Floating elements have proper spacing from edges
- [ ] No content hidden behind fixed navbars
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile

### Accessibility

- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color is not the only indicator
- [ ] `prefers-reduced-motion` respected

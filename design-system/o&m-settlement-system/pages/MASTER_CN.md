# 设计系统主文件 (Design System Master File)

> **逻辑 (LOGIC):** 在构建特定页面时，首先检查 `design-system/pages/[page-name].md`。
> 如果该文件存在，其规则将**覆盖**此主文件。
> 如果不存在，请严格遵守以下规则。

---

**项目:** 运维合同结算系统 (O&M Settlement System)
**生成时间:** 2026-02-05 15:19:44
**类别:** 金融仪表盘 (Financial Dashboard)

---

## 全局规则 (Global Rules)

### 调色板 (Color Palette)

| 角色 | 十六进制 (Hex) | CSS 变量 |
|------|-----------|--------------|
| 主要 (Primary) | `#0F172A` | `--color-primary` |
| 次要 (Secondary) | `#1E293B` | `--color-secondary` |
| 强调/行动 (CTA/Accent) | `#22C55E` | `--color-cta` |
| 背景 (Background) | `#020617` | `--color-background` |
| 文字 (Text) | `#F8FAFC` | `--color-text` |

**颜色说明:** 深色背景 + 绿色正面指示符

### 字体排印 (Typography)

- **标题字体:** IBM Plex Sans
- **正文字体:** IBM Plex Sans
- **风格语境:** 金融、值得信赖、专业、企业、银行、严谨
- **Google 字体:** [IBM Plex Sans + IBM Plex Sans](https://fonts.google.com/share?selection.family=IBM+Plex+Sans:wght@300;400;500;600;700)

**CSS 导入:**

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
```

### 间距变量 (Spacing Variables)

| 标记 (Token) | 数值 | 用途 |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | 紧凑间隙 |
| `--space-sm` | `8px` / `0.5rem` | 图标间距，行内间距 |
| `--space-md` | `16px` / `1rem` | 标准内边距 (Padding) |
| `--space-lg` | `24px` / `1.5rem` | 区块内边距 |
| `--space-xl` | `32px` / `2rem` | 大间距 |
| `--space-2xl` | `48px` / `3rem` | 区块外边距 (Margin) |
| `--space-3xl` | `64px` / `4rem` | 核心展示区 (Hero) 内边距 |

### 阴影深度 (Shadow Depths)

| 级别 | 数值 | 用途 |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 微妙提升 |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | 卡片，按钮 |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | 模态框，下拉菜单 |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | 核心图片，特色卡片 |

---

## 组件规范 (Component Specs)

### 按钮 (Buttons)

```css
/* 主要按钮 */
.btn-primary {
  background: #22C55E;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 次要按钮 */
.btn-secondary {
  background: transparent;
  color: #0F172A;
  border: 2px solid #0F172A;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### 卡片 (Cards)

```css
.card {
  background: #020617;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### 输入框 (Inputs)

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #0F172A;
  outline: none;
  box-shadow: 0 0 0 3px #0F172A20;
}
```

### 模态框 (Modals)

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## 风格指南 (Style Guidelines)

**风格:** 深色模式 (OLED)

**关键词:** 深色主题、弱光、高对比度、纯黑、午夜蓝、护眼、OLED、夜间模式、节能

**适用场景:** 夜间模式应用、编程平台、娱乐、预防眼睛疲劳、OLED 设备、弱光环境

**关键效果:** 极简发光 (text-shadow: 0 0 10px)、深浅过渡、低白光发射、高可读性、可见焦点

### 页面模式 (Page Pattern)

**模式名称:** 数据密集型仪表盘 (Data-Dense Dashboard)

- **行动号召 (CTA) 位置:** 首屏 (Above fold)
- **区块顺序:** 核心展示 (Hero) > 特色功能 (Features) > 行动号召 (CTA)

---

## 反模式 (Anti-Patterns - 禁止使用)

- ❌ 默认浅色模式
- ❌ 渲染缓慢

### 其他禁用模式

- ❌ **使用表情符号作为图标** — 请使用 SVG 图标 (Heroicons, Lucide, Simple Icons)
- ❌ **缺失手型光标 (cursor:pointer)** — 所有可点击元素必须具备手型光标
- ❌ **导致布局偏移的悬停效果** — 避免使用会导致布局抖动的缩放转换
- ❌ **低对比度文字** — 必须保持至少 4.5:1 的对比度
- ❌ **瞬间状态变化** — 状态切换应使用过渡动画 (150-300ms)
- ❌ **不可见的焦点状态** — 为了无障碍访问，焦点状态必须清晰可见

---

## 交付前检查清单 (Pre-Delivery Checklist)

在交付任何 UI 代码前，请核对：

- [ ] 未使用表情符号作为图标 (使用 SVG 代替)
- [ ] 所有图标来自统一的图标库 (Heroicons/Lucide)
- [ ] 所有可点击元素均包含 `cursor-pointer`
- [ ] 悬停状态具备平滑过渡效果 (150-300ms)
- [ ] 浅色模式：文字对比度至少 4.5:1
- [ ] 键盘导航时焦点状态可见
- [ ] 尊重系统的“减少运动” (`prefers-reduced-motion`) 设置
- [ ] 响应式适配：375px, 768px, 1024px, 1440px
- [ ] 没有内容被固定导航栏遮挡
- [ ] 移动端无水平滚动

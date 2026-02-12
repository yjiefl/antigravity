# React + Vite 前端模板

这是一个基于 Vite 的 React 极简配置模板，支持模块热替换 (HMR) 和 ESLint 规则。

目前提供两个官方插件：

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react): 使用 [Babel](https://babeljs.io/) (或在 [rolldown-vite](https://vite.dev/guide/rolldown) 中使用 [oxc](https://oxc.rs)) 实现快速刷新 (Fast Refresh)。
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc): 使用 [SWC](https://swc.rs/) 实现快速刷新 (Fast Refresh)。

## React 编译器 (React Compiler)

此模板默认未启用 React 编译器，以避免对开发和构建性能产生影响。如需添加，请参阅 [官方安装文档](https://react.dev/learn/react-compiler/installation)。

## 扩展 ESLint 配置

如果您正在开发生产级应用，我们建议使用 TypeScript 并启用类型感知 (type-aware) 的 lint 规则。您可以查看 [TypeScript 模板](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts)，了解如何在项目中集成 TypeScript 和 [`typescript-eslint`](https://typescript-eslint.io)。

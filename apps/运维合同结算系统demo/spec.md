# 运维合同结算系统demo 详细设计文档

## 1. 概述

本项目是一个基于 HTML/JS 单文件实现的运维合同结算系统原型。旨在为真实业务开发提供参考，涵盖标段库管理、场站关联、季度结算逻辑、费用调增/调减量及汇总查阅功能。

## 2. 构架与选型

- **核心**: HTML5 / JavaScript (ES6+ / Vanilla JS)
- **外观**: CSS3 (Glassmorphism, Flexbox/Grid)
- **图标**: 使用 SVG 嵌入
- **存储**: 内存对象存储（模拟数据库），支持导出 JSON/Excel 逻辑

## 3. 关键流程

### 3.1 结算流程图

```mermaid
graph TD
    A[开始] --> B{选择场站与季度}
    B --> C[加载标段关联价格表]
    C --> D[系统自动计算包干费用/季度]
    D --> E[用户填写单价结算项数量]
    E --> F{是否需要手动调整费用?}
    F -- 是 --> G[填写调整金额与原因]
    F -- 否 --> H[核对费用总额]
    G --> H
    H --> I[生成结算申报单]
    I --> J[存入汇总表]
    J --> K[结束]
```

## 4. 资料模型

```mermaid
erDiagram
    LOT ||--o{ STATION : contains
    LOT ||--o{ PRICE_ITEM : defines
    STATION ||--o{ SETTLEMENT_RECORD : generates
    SETTLEMENT_RECORD ||--o{ SETTLEMENT_DETAIL : consists_of

    LOT {
        string lot_id "标段ID"
        string lot_name "标段名称"
    }
    PRICE_ITEM {
        string item_id "序号"
        string name "项目"
        string unit "单位"
        float price "单价"
        boolean is_lump_sum "是否包干"
    }
    STATION {
        string station_id "场站ID"
        string name "场站名称"
        string lot_id "所属标段"
        float capacity "容量MW"
    }
    SETTLEMENT_RECORD {
        string record_id "记录ID"
        string station_id "场站"
        string period "结算期间(如2026 Q1)"
        float total_amount "最终合价"
    }
    SETTLEMENT_DETAIL {
        string item_id "关联项目"
        float quantity "数量"
        float adjusted_amount "调整后金额"
        string reason "调整原因"
    }
```

## 5. 必须功能点

1. **标段切换逻辑**: 切换不同的场站，自动根据其所属标段匹配对应的单价表。
2. **季度自动拆分**: 对于“是否包干=是”的项目，本季度费用默认为 `(合价 / 4)`。
3. **动态调整机制**: 提供“调整金额”输入框，当调整值不为 0 时，强制要求选择/填写支撑原因。
4. **考核项导入**: 支持从外部数据（模拟表格）导入考核项目（违约金/扣款），并自动从结算总额中扣除。
5. **汇总报表**: 提供全局视角，按标段/场站汇总统计已结算金额。

## 6. 扩展资料模型 (Assessment)

```mermaid
erDiagram
    SETTLEMENT_RECORD ||--o{ ASSESSMENT_ITEM : includes
    ASSESSMENT_ITEM {
        string type "考核类型"
        string description "考核描述"
        float amount "扣款金额"
        string date "发生日期"
    }
```

## 7. UI/UX 规范 (Pro Max)

- **配色**: 采用深色科技感或高级浅色模式（本系统采用高级浅色模式）。
- **交互**: 悬停高亮、平滑过渡、侧边栏导航。
- **反馈**: 实时计算（Real-time calc），数值变动即刻反映在总计中。

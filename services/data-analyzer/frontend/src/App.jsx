import React, { useState, useEffect, useRef } from "react";
import * as echarts from "echarts";
import Papa from "papaparse";
import {
  Upload,
  FileText,
  ChevronRight,
  BarChart3,
  Trash2,
  ClipboardPaste,
  X,
  Download,
  RotateCcw,
  Moon,
  Sun,
  ChevronLeft,
  Layout,
  Archive,
  History,
  Activity,
  FilePen,
  Check,
  CheckSquare,
  Square,
  RefreshCw,
  Search,
} from "lucide-react";
import { format } from "date-fns";
import { processDataLogic } from "./utils/dataProcessor";
import "./App.css";

/**
 * 数据文件解析与曲线展示主应用
 * @returns {JSX.Element}
 */
function App() {
  /**
   * 统一获取指标的清洗后名称（带单位，不带场站等冗余信息）
   * @param {Object} s 系列对象
   * @returns {string} 指标名称
   */
  const getCleanMetricName = (s) => {
    if (!s) return "";
    const clean = (s.metricName || s.name || "")
      .split(" (")[0]
      .split("(")[0]
      .trim();
    const unit =
      s.unit || (s.name.includes("(") ? s.name.match(/\(([^)]+)\)/)?.[1] : "");
    return unit ? `${clean}(${unit})` : clean;
  };

  // 从 LocalStorage 加载初始数据
  const getInitialState = (key, defaultVal) => {
    try {
      const saved = localStorage.getItem(`da_${key}`);
      if (!saved) return defaultVal;
      const parsed = JSON.parse(saved);

      // 如果是 series，需要将字符串日期恢复为 Date 对象
      if (key === "series" && Array.isArray(parsed)) {
        return parsed
          .map((s) => {
            if (!s || !Array.isArray(s.data)) return null;
            return {
              ...s,
              data: s.data.map((d) => ({ ...d, time: new Date(d.time) })),
            };
          })
          .filter(Boolean);
      }

      // 特殊处理 rangeConfig，确保嵌套对象存在
      if (key === "rangeConfig" && parsed) {
        return {
          hour: parsed.hour || { start: 0, end: 23 },
          day: parsed.day || { start: 1, end: 31 },
          month: parsed.month || { start: 1, end: 12 },
        };
      }
      return parsed;
    } catch {
      return defaultVal;
    }
  };

  const [series, setSeries] = useState(() => getInitialState("series", []));
  const [selectedDates, setSelectedDates] = useState(() =>
    getInitialState("selectedDates", []),
  );
  const [availableDates, setAvailableDates] = useState([]);
  const [isPasteModalOpen, setIsPasteModalOpen] = useState(false);
  const [pasteContent, setPasteContent] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  // 轴范围设置：{ metricName: { min: '', max: '' } }
  const [axisRanges, setAxisRanges] = useState(() =>
    getInitialState("axisRanges", {}),
  );
  const [showIntegral, setShowIntegral] = useState(() =>
    getInitialState("showIntegral", true),
  );
  const [axisAdjustmentFactor, setAxisAdjustmentFactor] = useState(() =>
    getInitialState("axisAdjustmentFactor", 1.0),
  );
  // const [isFocusMode, setIsFocusMode] = useState(() => getInitialState('isFocusMode', true)); // Removed
  const [hoveredMetric, setHoveredMetric] = useState(null);
  const [backendStatus, setBackendStatus] = useState("offline");

  const [dimensionFilters, setDimensionFilters] = useState(() =>
    getInitialState("dimensionFilters", {}),
  );
  const [legendSelected, setLegendSelected] = useState(() =>
    getInitialState("legendSelected", {}),
  );
  const [chartTypes, setChartTypes] = useState(() =>
    getInitialState("chartTypes", {}),
  );
  const [historyRecords, setHistoryRecords] = useState([]); // 从后端动态加载
  const [historySearchTerm, setHistorySearchTerm] = useState(""); // 新增：存单搜索
  const [customMetricColors, setCustomMetricColors] = useState(() =>
    getInitialState("customMetricColors", {}),
  );
  const [useDefaultLimits, setUseDefaultLimits] = useState(() =>
    getInitialState("useDefaultLimits", true),
  );

  // 限电分析设置
  const [showCurtailmentAnalysis, setShowCurtailmentAnalysis] = useState(() =>
    getInitialState("showCurtailmentAnalysis", false),
  );
  const [curtailmentIrrThreshold, setCurtailmentIrrThreshold] = useState(() =>
    getInitialState("curtailmentIrrThreshold", 20),
  );
  const [curtailmentDiffThreshold, setCurtailmentDiffThreshold] = useState(() =>
    getInitialState("curtailmentDiffThreshold", 3),
  );
  const [curtailmentColor, setCurtailmentColor] = useState(() =>
    getInitialState("curtailmentColor", "#ff4646"),
  );
  const [curtailmentOpacity, setCurtailmentOpacity] = useState(() =>
    getInitialState("curtailmentOpacity", 0.3),
  );
  // const [isShowAllGroups, setIsShowAllGroups] = useState(() => getInitialState('isShowAllGroups', true)); // Removed

  const [systemVersion] = useState("v1.5.0");
  const [isFetchingWeather, setIsFetchingWeather] = useState(false);
  const [availableStations, setAvailableStations] = useState([]);
  const [isStationModalOpen, setIsStationModalOpen] = useState(false);
  const [stationSearchTerm, setStationSearchTerm] = useState("");
  const curtailmentStatusRef = useRef({}); // 用于存储点对点限电判断结果，供提示框使用

  // 重命名功能的状态
  const [editingStationName, setEditingStationName] = useState(null); // 正在编辑的旧名称
  const [newStationName, setNewStationName] = useState(""); // 输入框中的新名称

  const renameStation = async (oldName, newName) => {
    if (!newName || oldName === newName) {
      setEditingStationName(null);
      return;
    }

    try {
      const res = await fetch(`/api/stations/${encodeURIComponent(oldName)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ newName }),
      });

      const result = await res.json();

      if (res.ok) {
        alert(`场站已成功重命名为 "${newName}"`);
        fetchStations(); // 重新加载列表
        setEditingStationName(null); // 退出编辑模式
      } else {
        throw new Error(result.error || "未知错误");
      }
    } catch (e) {
      console.error("重命名失败:", e);
      alert(`重命名失败: ${e.message}`);
    }
  };

  // 新增 UI 状态
  const [theme, setTheme] = useState(() => getInitialState("theme", "dark"));
  const [activeTab, setActiveTab] = useState("controls"); // controls | history
  const [isCompareOverlap, setIsCompareOverlap] = useState(() =>
    getInitialState("isCompareOverlap", false),
  ); // 多日期重叠对比
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarWide, setIsSidebarWide] = useState(false);
  const [isStationManagerOpen, setIsStationManagerOpen] = useState(false);
  const [stationBatchInput, setStationBatchInput] = useState("");
  const [granularity, setGranularity] = useState(() =>
    getInitialState("granularity", "hour"),
  ); // hour | day | month
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [accessLogs, setAccessLogs] = useState([]);
  const [logType, setLogType] = useState("access"); // access | error
  const [logSearchTerm, setLogSearchTerm] = useState("");
  const [rangeConfig, setRangeConfig] = useState(() =>
    getInitialState("rangeConfig", {
      hour: { start: 0, end: 23 },
      day: { start: 1, end: 31 },
      month: { start: 1, end: 12 },
    }),
  );
  const [isDataEditorOpen, setIsDataEditorOpen] = useState(false);
  const [editingSeriesId, setEditingSeriesId] = useState(null);
  const [editingSeriesName, setEditingSeriesName] = useState("");
  const [editingMetricName, setEditingMetricName] = useState("");
  const [editingDataText, setEditingDataText] = useState("");
  const [isSolarMode, setIsSolarMode] = useState(() =>
    getInitialState("isSolarMode", false),
  );
  const [solarRange, setSolarRange] = useState(() =>
    getInitialState("solarRange", { start: 7, end: 19 }),
  );

  const activeSeries = series
    .filter((s) => {
      if (!s) return false;
      const dateMatch = (selectedDates || []).includes(s.date);
      if (!dateMatch) return false;

      // Dimension filters
      return Object.entries(dimensionFilters).every(
        ([dimKey, selectedVals]) => {
          const sVal = s.dimensions ? s.dimensions[dimKey] : undefined;
          // Allow series that do not have this dimension (for overlaying different dimensions)
          if (sVal === undefined) return true;
          return selectedVals && selectedVals.includes(sVal);
        },
      );
    })
    .map((s) => {
      // 统一指标标识符逻辑，确保在图表、侧边栏、颜色设置中全量匹配
      const metricKey = getCleanMetricName(s);
      return { ...s, displayName: metricKey, metricKey: metricKey };
    });

  const uniqueMetrics = [
    ...new Set(activeSeries.map((s) => s.metricKey).filter(Boolean)),
  ];

  // 1. 生命周期管理：初始化与销毁
  useEffect(() => {
    if (chartRef.current) {
      const initChart = () => {
        if (chartInstance.current) {
          chartInstance.current.dispose();
        }
        chartInstance.current = echarts.init(
          chartRef.current,
          theme === "dark" ? "dark" : null,
        );

        // 鼠标移动监听：用于切换左侧纵坐标
        chartInstance.current.on("mouseover", (params) => {
          if (params.seriesName) {
            const metric = params.seriesName;
            setHoveredMetric(metric);
          }
        });

        chartInstance.current.on("mouseout", () => {
          // 移除悬停时的自动切换，防止曲线跳动
        });

        // 点击圆点切换纵坐标
        chartInstance.current.on("click", (params) => {
          if (params.seriesName) {
            const metric = params.seriesName;
            setHoveredMetric(metric);
          }
        });

        // 监听图例变化，将其保存到 React 状态
        chartInstance.current.on("legendselectchanged", (params) => {
          setLegendSelected(params.selected);
        });

        // 恢复之前的数据渲染（如果有）
        if (series.length > 0) {
          updateChart();
        }
      };

      initChart();

      // 使用 ResizeObserver 替代 window resize 监听，更精准且平滑
      const resizeObserver = new ResizeObserver(() => {
        requestAnimationFrame(() => {
          chartInstance.current?.resize();
        });
      });
      resizeObserver.observe(chartRef.current);

      checkBackend();
      loadSnapshotsFromBackend();

      return () => {
        resizeObserver.disconnect();
        chartInstance.current?.dispose();
        chartInstance.current = null;
      };
    }
  }, [theme]); // 主题切换时重新初始化

  /**
   * 从后端加载历史存单
   */
  const loadSnapshotsFromBackend = async () => {
    try {
      const res = await fetch("/api/snapshots");
      if (res.ok) {
        const data = await res.json();
        setHistoryRecords(data);
      }
    } catch (e) {
      console.error("加载历史存单失败:", e);
    }
  };

  useEffect(() => {
    fetch("/api/stations")
      .then((res) => res.json())
      .then((data) => setAvailableStations(data))
      .catch((err) => console.error("Failed to fetch stations:", err));
  }, []);

  /**
   * 模拟检测后端
   */
  const checkBackend = async () => {
    try {
      setBackendStatus("checking");
      const res = await fetch("/api/health").catch(() => ({ ok: false }));
      setBackendStatus(res.ok ? "online" : "offline");
    } catch {
      setBackendStatus("offline");
    }
  };

  // --- 辅助工具函数 ---
  const hexToRgba = (hex, opacity) => {
    let r = 255,
      g = 70,
      b = 70;
    if (hex && typeof hex === "string" && hex.startsWith("#")) {
      const h = hex.replace("#", "");
      if (h.length === 3) {
        r = parseInt(h[0] + h[0], 16);
        g = parseInt(h[1] + h[1], 16);
        b = parseInt(h[2] + h[2], 16);
      } else if (h.length === 6) {
        r = parseInt(h.substring(0, 2), 16);
        g = parseInt(h.substring(2, 4), 16);
        b = parseInt(h.substring(4, 6), 16);
      }
    }
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  };

  const getAggregatedData = (data, gran) => {
    if (gran === "hour") return data.map((d) => [d.time, d.value]);
    const groups = {};
    data.forEach((d) => {
      let key;
      const dt = new Date(d.time);
      if (gran === "day") key = format(dt, "yyyy-MM-dd");
      else if (granularity === "month") key = format(dt, "yyyy-MM");
      if (!groups[key]) groups[key] = { sum: 0, count: 0, firstTime: dt };
      groups[key].sum += d.value;
      groups[key].count += 1;
    });
    return Object.entries(groups)
      .map(([, info]) => {
        const date = new Date(info.firstTime);
        if (gran === "day") date.setHours(0, 0, 0, 0);
        else if (gran === "month") {
          date.setDate(1);
          date.setHours(0, 0, 0, 0);
        }
        return [date, info.sum / info.count];
      })
      .sort((a, b) => a[0] - b[0]);
  };

  const getCurtailmentRanges = (allSeries, dates) => {
    const ranges = {};
    curtailmentStatusRef.current = {}; // 重置点对点状态记录
    const relevantSeries = allSeries.filter(
      (s) => s && (dates || []).includes(s.date),
    );
    const possibleKeys = [
      "场站名称",
      "场站",
      "电站",
      "名称",
      "调度名称",
      "item",
      "station",
      "项目",
    ];
    const sample = allSeries.find((s) => s && s.dimensions);
    const groupDimKey =
      Object.keys(dimensionFilters)[0] ||
      (sample ? possibleKeys.find((k) => sample.dimensions[k]) : null);
    const dimensionGroups = {};
    relevantSeries.forEach((s) => {
      if (!s) return;
      const dimVal =
        groupDimKey && s.dimensions ? s.dimensions[groupDimKey] : "default";
      const groupKey = `${s.date}_${dimVal}`;
      if (!dimensionGroups[groupKey]) dimensionGroups[groupKey] = [];
      dimensionGroups[groupKey].push(s);
    });
    Object.entries(dimensionGroups).forEach(([groupKey, groupSeries]) => {
      const irrad = groupSeries.find((s) => {
        const m = (s.metricName || s.name).toLowerCase();
        return (
          m.includes("辐照度") ||
          m.includes("短波") ||
          m.includes("irradiance") ||
          m.includes("radiation")
        );
      });
      const agc = groupSeries.find((s) => {
        const m = (s.metricName || s.name).toLowerCase();
        return m.includes("agc") || m.includes("指令");
      });
      const power = groupSeries.find((s) => {
        const m = (s.metricName || s.name).toLowerCase();
        return (
          (m.includes("实际功率") ||
            m.includes("功率") ||
            m.includes("power") ||
            m.includes("load") ||
            m.includes("output")) &&
          !m.includes("agc") &&
          !m.includes("可用") &&
          !m.includes("预测")
        );
      });
      if (irrad && agc && power) {
        if (!ranges[groupKey]) ranges[groupKey] = [];
        const timeMap = {};
        const addToMap = (s, type) => {
          s.data.forEach((d) => {
            const t = new Date(d.time).getTime();
            if (!timeMap[t]) timeMap[t] = {};
            timeMap[t][type] = d.value;
          });
        };
        addToMap(irrad, "irrad");
        addToMap(agc, "agc");
        addToMap(power, "power");
        const times = Object.keys(timeMap)
          .map(Number)
          .sort((a, b) => a - b);
        let startRange = null;
        let lastIrrad = 0; // 缓存上一个有效的辐照度值，应对时间戳不对齐

        const pushRange = (start, end, exclusiveEnd = false) => {
          let s = start,
            e = end;
          if (isCompareOverlap) {
            const mapTime = (ts) => {
              const dTime = new Date(ts);
              const baseDate = new Date(2000, 0, 1);
              if (granularity === "hour")
                baseDate.setHours(
                  dTime.getHours(),
                  dTime.getMinutes(),
                  dTime.getSeconds(),
                );
              else if (granularity === "day") baseDate.setDate(dTime.getDate());
              else if (granularity === "month")
                baseDate.setMonth(dTime.getMonth());
              return baseDate.getTime();
            };
            s = mapTime(start);
            e = mapTime(end);
          }
          ranges[groupKey].push([
            { xAxis: new Date(s), startTime: start },
            {
              xAxis: new Date(e),
              endTime: end,
              exclusiveEnd: exclusiveEnd,
              itemStyle: {
                color: hexToRgba(curtailmentColor, curtailmentOpacity),
              },
            },
          ]);
        };

        times.forEach((t) => {
          const v = timeMap[t];
          // 补全逻辑：如果当前点缺少辐照度但有上一个值，则沿用（应对 15min vs 5min 数据不对齐）
          const currentIrrad = v.irrad !== undefined ? v.irrad : lastIrrad;
          if (v.irrad !== undefined) lastIrrad = v.irrad;

          if (
            currentIrrad !== undefined &&
            v.agc !== undefined &&
            v.power !== undefined
          ) {
            const diff = Math.abs(v.agc - v.power);
            // 限电判据：相关性 (辐照度足够) && (AGC受限 或 实际功率紧贴AGC)
            const isPointCurtailed =
              currentIrrad > curtailmentIrrThreshold &&
              (v.agc < v.power || diff < curtailmentDiffThreshold);

            // 记录点对点状态
            if (!curtailmentStatusRef.current[groupKey])
              curtailmentStatusRef.current[groupKey] = {};
            curtailmentStatusRef.current[groupKey][t] = isPointCurtailed;

            if (isPointCurtailed) {
              if (startRange === null) startRange = t;
            } else {
              if (startRange !== null) {
                // Range ends because current point is NOT curtailed -> Exclusive End
                pushRange(startRange, t, true);
                startRange = null;
              }
            }
          } else if (startRange !== null) {
            // Data interruption -> Exclusive End at interruption point
            pushRange(startRange, t, true);
            startRange = null;
          }
        });
        // Range went until the end of data -> Inclusive End
        if (startRange !== null)
          pushRange(startRange, times[times.length - 1], false);
      }
    });
    return { ranges, groupDim: groupDimKey };
  };

  // --- 核心绘图更新 ---
  const updateChart = () => {
    if (!chartInstance.current || chartInstance.current.isDisposed()) return;
    if (activeSeries.length === 0) {
      chartInstance.current.clear();
      return;
    }

    const isLight = theme === "light";
    const legendItems = [...new Set(activeSeries.map((s) => s.displayName))];

    const yAxisConfig = uniqueMetrics.map((metric, index) => {
      const customRange = axisRanges[metric] || {};
      const isMetricVisible = (m) => {
        const sameMetricDisplayNames = activeSeries
          .filter((s) => s.metricKey === m)
          .map((s) => s.displayName);
        return sameMetricDisplayNames.some(
          (dn) => legendSelected[dn] !== false,
        );
      };
      const firstVisibleMetric =
        uniqueMetrics.find((m) => isMetricVisible(m)) || uniqueMetrics[0];
      const isActive =
        hoveredMetric && isMetricVisible(hoveredMetric)
          ? metric === hoveredMetric
          : metric === firstVisibleMetric;
      const isIrradiance =
        metric.includes("辐照度") ||
        metric.includes("短波") ||
        metric.includes("辐射") ||
        metric.toLowerCase().includes("irradiance") ||
        metric.toLowerCase().includes("radiation");
      const factor = parseFloat(axisAdjustmentFactor) || 1.0;
      let finalMin =
        customRange.min !== "" && customRange.min !== undefined
          ? parseFloat(customRange.min)
          : null;
      let finalMax =
        customRange.max !== "" && customRange.max !== undefined
          ? parseFloat(customRange.max)
          : null;

      if (finalMin === null && isIrradiance) finalMin = 0;
      if (finalMax === null && isIrradiance) finalMax = 1000;

      if (finalMin === null || finalMax === null) {
        const metricSeries = activeSeries.filter((s) => s.metricKey === metric);
        const vals = metricSeries.flatMap((s) => s.data.map((d) => d.value));
        if (
          useDefaultLimits &&
          (metric.includes("AGC远方指令") || metric.includes("超短期"))
        ) {
          if (finalMin === null) finalMin = 0;
          if (finalMax === null) finalMax = 1000;
        }
        if (vals.length) {
          const dataMax = Math.max(...vals);
          const dataMin = Math.min(...vals);
          if (finalMin === null)
            finalMin =
              dataMin < 0
                ? dataMin * 1.1
                : dataMin - (Math.abs(dataMax - dataMin) * 0.05 || 1);
          if (finalMax === null)
            finalMax =
              dataMax > 0
                ? dataMax * 1.1
                : dataMax + (Math.abs(dataMax - dataMin) * 0.05 || 1);
        }
      }
      if (finalMin !== null) finalMin *= factor;
      if (finalMax !== null) finalMax *= factor;

      return {
        type: "value",
        name: "", // Remove name to prevent grid shifting
        show: isActive,
        scale: true,
        min: finalMin,
        max: finalMax,
        offset: 0,
        position: "left",
        axisLine: {
          show: isActive,
          lineStyle: {
            color: customMetricColors[metric] || getUserColor(index, metric),
            width: 1,
          },
        },
        axisTick: { show: isActive, length: 3 },
        axisLabel: {
          show: isActive, // Only show labels for active axis
          color: isLight ? "#1d1d1f" : "#a1a1aa",
          margin: 4,
          align: "right",
          fontFamily: "Fira Code, monospace",
          fontSize: 9,
          formatter: (val) => parseFloat(val.toFixed(2)).toString(),
        },
        splitLine: {
          show: isActive,
          lineStyle: {
            color: isLight ? "rgba(0,0,0,0.05)" : "rgba(255, 255, 255, 0.05)",
          },
        },
      };
    });

    const { ranges: curtailmentRanges, groupDim } = getCurtailmentRanges(
      series,
      selectedDates,
    );

    // High Contrast / Professional 20-Color Palette
    const defaultPalette = [
      "#3b82f6", // Vibrant Blue
      "#10b981", // Emerald
      "#f59e0b", // Amber
      "#ef4444", // Rose
      "#8b5cf6", // Violet
      "#ec4899", // Pink
      "#06b6d4", // Cyan
      "#84cc16", // Lime
      "#f97316", // Orange
      "#6366f1", // Indigo
      "#14b8a6", // Teal
      "#d946ef", // Fuchsia
      "#eab308", // Yellow
      "#f43f5e", // Crimson
      "#a855f7", // Purple
      "#22c55e", // Green
      "#0ea5e9", // Sky
      "#facc15", // Gold
      "#fb7185", // Soft Rose
      "#c084fc", // Light Purple
    ];

    const option = {
      backgroundColor: "transparent",
      color: defaultPalette,
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(15, 23, 42, 0.8)", // Use dark glass by default
        borderColor: "rgba(255, 255, 255, 0.1)",
        borderWidth: 1,
        padding: 0, // Reset padding for custom HTML
        textStyle: { color: "#f1f5f9", fontFamily: "Open Sans, sans-serif" },
        axisPointer: { type: "cross", label: { backgroundColor: "#3b82f6" } },
        className: "glass-tooltip", // Add class for backdrop-filter if supported
        formatter: (params) => {
          try {
            if (!params || !Array.isArray(params) || params.length === 0)
              return "";

            const isLight = document.body.classList.contains("light-mode");
            const bg = isLight
              ? "rgba(255, 255, 255, 0.9)"
              : "rgba(23, 23, 23, 0.9)";
            const border = isLight
              ? "rgba(0,0,0,0.1)"
              : "rgba(255, 255, 255, 0.1)";
            const text = isLight ? "#1d1d1f" : "#fff";
            const mute = isLight ? "#86868b" : "#888";

            let html = `<div style="
              background: ${bg};
              padding: 10px 14px;
              backdrop-filter: blur(8px);
              -webkit-backdrop-filter: blur(8px);
              border-radius: 4px;
              border: 0.5px solid ${border};
              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
              font-family: 'Fira Sans', sans-serif;
            ">`;

            const title = params[0].axisValueLabel || "";
            html += `<div style="
              margin-bottom: 6px; 
              padding-bottom: 6px; 
              border-bottom: 0.5px solid ${border}; 
              display: flex; 
              justify-content: space-between; 
              align-items: center;
            ">
              <span style="font-weight: 700; color: ${text}; font-size: 11px; font-family: 'Poppins', sans-serif;">
                ${title}
              </span>`;

            html += `</div><div style="display: flex; flex-direction: column; gap: 2px;">`;

            // Flatten curtailmentRanges object to array of {start, end} using xAxis time for coordinate consistency
            const safeRanges = [];
            if (curtailmentRanges && typeof curtailmentRanges === "object") {
              Object.values(curtailmentRanges).forEach((group) => {
                if (Array.isArray(group)) {
                  group.forEach((range) => {
                    if (
                      Array.isArray(range) &&
                      range.length === 2 &&
                      range[0].xAxis &&
                      range[1].xAxis
                    ) {
                      safeRanges.push({
                        start: range[0].xAxis.getTime(),
                        end: range[1].xAxis.getTime(),
                        exclusive: range[1].exclusiveEnd,
                      });
                    }
                  });
                }
              });
            }

            params.forEach((item) => {
              if (!item || !item.value) return;

              const color = item.color;
              const sIdx = item.seriesIndex;
              const fullSeriesName =
                activeSeries[sIdx]?.name || item.seriesName || "";
              const rawVal = item.value[1];
              const displayVal =
                typeof rawVal === "number"
                  ? parseFloat(rawVal.toFixed(3)).toString()
                  : rawVal;

              // Safe timestamp access
              const ts = item.value[0];
              const isCurtailed = safeRanges.some(
                (r) => ts >= r.start && ts <= r.end,
              );

              html += `<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 4px; overflow: hidden;">
                  <span style="width: 4px; height: 4px; border-radius: 50%; background-color: ${color}; flex-shrink: 0;"></span>
                  <span style="font-size: 9px; color: ${mute}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px;">
                    ${fullSeriesName}
                  </span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="font-weight: 500; font-family: 'Fira Code', monospace; color: ${text}; font-size: 10px;">
                    ${displayVal}
                  </span>
                </div>
              </div>`;
            });

            // Summary row for curtailment status
            if (params[0] && params[0].value) {
              const ts = params[0].value[0];
              const isCurtailedGlobal = safeRanges.some((r) => {
                if (r.exclusive) {
                  return ts >= r.start && ts < r.end;
                }
                return ts >= r.start && ts <= r.end;
              });

              html += `<div style="
                margin-top: 6px; 
                padding-top: 4px; 
                border-top: 0.5px solid ${border}; 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
              ">
                <span style="font-size: 9px; color: ${mute};">状态</span>
                <span style="font-size: 10px; font-weight: 600; color: ${isCurtailedGlobal ? "#ef4444" : "#10b981"};">
                  ${isCurtailedGlobal ? "限电" : "不限电"}
                </span>
              </div>`;
            }

            html += "</div></div>";
            return html;
          } catch (err) {
            console.error("Tooltip error:", err);
            return "";
          }
        },
      },
      legend: {
        data: legendItems,
        selected: legendSelected,
        textStyle: {
          color: isLight ? "#1d1d1f" : "#a1a1aa",
          fontSize: 10,
          fontFamily: "Fira Sans, sans-serif",
          padding: [0, 0, 0, 0],
        },
        top: 0,
        type: "scroll",
        pageTextStyle: { color: isLight ? "#1d1d1f" : "#a1a1aa" },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 8,
        icon: "circle",
      },
      grid: {
        top: 40,
        left: 5,
        right: 20,
        bottom: 25,
        containLabel: true,
      },
      xAxis: {
        type: "time",
        axisLine: {
          lineStyle: {
            color: isLight ? "rgba(0,0,0,0.1)" : "rgba(255, 255, 255, 0.2)",
          },
        },
        splitNumber:
          granularity === "hour" ? 12 : granularity === "day" ? 10 : 12,
        axisLabel: {
          color: isLight ? "#1d1d1f" : "#ccc",
          formatter: (val) => {
            const dt = new Date(val);
            if (isCompareOverlap) {
              if (granularity === "day") return format(dt, "d日");
              if (granularity === "month") return format(dt, "M月");
              return format(dt, "HH:mm");
            }
            if (granularity === "hour") {
              return selectedDates.length > 1
                ? format(dt, "MM-dd HH:mm")
                : format(dt, "HH:mm");
            }
            if (granularity === "day") return format(dt, "MM-dd");
            if (granularity === "month") return format(dt, "yyyy-MM");
            return format(dt, "yyyy");
          },
        },
        min: (value) => {
          if (isCompareOverlap) {
            const d = new Date(2000, 0, 1);
            if (granularity === "hour")
              d.setHours(rangeConfig.hour.start, 0, 0);
            else if (granularity === "day") d.setDate(rangeConfig.day.start);
            else if (granularity === "month")
              d.setMonth(rangeConfig.month.start - 1, 1);
            return d;
          }
          if (granularity === "hour") {
            const d = new Date(value.min);
            d.setHours(rangeConfig.hour.start, 0, 0, 0);
            return d;
          }
          if (granularity === "day") {
            const d = new Date(value.min);
            return new Date(
              d.getFullYear(),
              d.getMonth(),
              rangeConfig.day.start,
              0,
              0,
              0,
            );
          }
          if (granularity === "month") {
            const d = new Date(value.min);
            return new Date(
              d.getFullYear(),
              rangeConfig.month.start - 1,
              1,
              0,
              0,
              0,
            );
          }
          return null;
        },
        max: (value) => {
          if (isCompareOverlap) {
            const d = new Date(2000, 0, 1);
            if (granularity === "hour")
              d.setHours(rangeConfig.hour.end, 59, 59, 999);
            else if (granularity === "day") d.setDate(rangeConfig.day.end);
            else if (granularity === "month")
              d.setMonth(rangeConfig.month.end - 1, 31);
            return d;
          }
          if (granularity === "hour") {
            const d = new Date(value.max);
            d.setHours(rangeConfig.hour.end, 59, 59, 999);
            return d;
          }
          if (granularity === "day") {
            const d = new Date(value.max);
            return new Date(
              d.getFullYear(),
              d.getMonth(),
              rangeConfig.day.end,
              23,
              59,
              59,
              999,
            );
          }
          if (granularity === "month") {
            const d = new Date(value.max);
            return new Date(
              d.getFullYear(),
              rangeConfig.month.end - 1,
              31,
              23,
              59,
              59,
              999,
            );
          }
          return null;
        },
        splitLine: { show: false },
      },
      yAxis: yAxisConfig,
      series: activeSeries.map((s) => {
        const metricKey = s.metricKey;
        const axisIndex = uniqueMetrics.indexOf(metricKey);
        const color =
          customMetricColors[metricKey] || getUserColor(axisIndex, metricKey);
        const type = chartTypes[metricKey] || "line";
        const sameMetricSeries = activeSeries.filter(
          (as) => as.metricKey === metricKey,
        );
        const metricIdx = sameMetricSeries.findIndex((as) => as.id === s.id);
        const isDashed = metricIdx > 0;

        let plotData = getAggregatedData(s.data, granularity);
        if (isCompareOverlap) {
          plotData = plotData.map((d) => {
            const dTime = d[0];
            const baseDate = new Date(2000, 0, 1);
            // 在重叠对比模式下，根据当前粒度映射时间
            if (granularity === "hour") {
              baseDate.setHours(
                dTime.getHours(),
                dTime.getMinutes(),
                dTime.getSeconds(),
              );
            } else if (granularity === "day") {
              baseDate.setDate(dTime.getDate());
            } else if (granularity === "month") {
              baseDate.setMonth(dTime.getMonth());
            }
            return [baseDate, d[1]];
          });
        }

        return {
          name: s.displayName,
          type: type,
          yAxisIndex: axisIndex,
          smooth: type === "line",
          barMaxWidth: 20,
          showSymbol: granularity === "hour" || plotData.length < 50,
          symbol: "circle",
          symbolSize: 8,
          data: plotData,
          markArea: (() => {
            const dimVal =
              groupDim && s.dimensions ? s.dimensions[groupDim] : "default";
            const groupKey = `${s.date}_${dimVal}`;
            const ranges = curtailmentRanges[groupKey] || [];

            // 只有在是“实际功率”相关的指标上才显示 markArea，避免每个系列都画背景导致颜色过深
            const isMainPower =
              (s.displayName.includes("实际功率") ||
                s.displayName.includes("功率") ||
                s.displayName.includes("Power")) &&
              !s.displayName.includes("可用");

            return showCurtailmentAnalysis && isMainPower && ranges.length > 0
              ? { silent: true, data: ranges }
              : undefined;
          })(),
          lineStyle: {
            width: 2.5,
            type: isDashed ? "dashed" : "solid",
          },
          itemStyle: {
            color: color,
            borderWidth: 1.5,
          },
          emphasis: {
            focus: "none",
            scale: true,
            symbolSize: 24,
            itemStyle: {
              shadowBlur: 20,
              shadowColor: "rgba(0,0,0,0.5)",
              borderWidth: isLight ? 2 : 0,
              borderColor: "#fff",
            },
          },
        };
      }),
    };

    chartInstance.current.setOption(option, true);
  };

  // 监听状态变化并保存到 LocalStorage
  useEffect(() => {
    const stateToSave = {
      series,
      selectedDates,
      axisRanges,
      chartTypes,
      dimensionFilters,
      theme,
      showIntegral,
      historyRecords,
      isCompareOverlap,
      isSolarMode,
      solarRange,
      granularity,
      legendSelected,
      rangeConfig,
      axisAdjustmentFactor,
      useDefaultLimits,
      showCurtailmentAnalysis,
      curtailmentIrrThreshold,
      curtailmentDiffThreshold,
      curtailmentColor,
      curtailmentOpacity,
    };
    Object.entries(stateToSave).forEach(([key, val]) => {
      localStorage.setItem(`da_${key}`, JSON.stringify(val));
    });
    updateChart();
  }, [
    series,
    selectedDates,
    axisRanges,
    hoveredMetric,
    dimensionFilters,
    theme,
    chartTypes,
    isSolarMode,
    solarRange,
    legendSelected,
    showIntegral,
    historyRecords,
    isCompareOverlap,
    granularity,
    rangeConfig,
    axisAdjustmentFactor,
    customMetricColors,
    useDefaultLimits,
    showCurtailmentAnalysis,
    curtailmentIrrThreshold,
    curtailmentDiffThreshold,
    curtailmentColor,
    curtailmentOpacity,
  ]);

  // 3. 自动同步可用日期列表
  useEffect(() => {
    const dates = [...new Set(series.map((s) => s.date))].sort();
    setAvailableDates(dates);
    // 如果没有任何选中日期，默认选中最新日期
    if (dates.length > 0 && selectedDates.length === 0) {
      setSelectedDates([dates[dates.length - 1]]);
    }
  }, [series]);

  // 4. Removed auto-init dimension effects

  const handleFileUpload = (e) => {
    let file = e && e.target && e.target.files ? e.target.files[0] : e;
    if (!file || !(file instanceof File || file instanceof Blob)) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target.result;
      if (file.name.endsWith(".csv")) {
        parseCSV(content, file.name);
      } else if (file.name.endsWith(".json")) {
        parseJSON(content, file.name);
      } else {
        if (content.trim().startsWith("[") || content.trim().startsWith("{")) {
          parseJSON(content, file.name);
        } else {
          parseCSV(content, file.name);
        }
      }
    };
    reader.readAsText(file);
  };

  const handlePasteSubmit = () => {
    if (!pasteContent.trim()) return;
    const timestamp = format(new Date(), "HHmm");
    const name = `粘贴数据_${timestamp}`;
    if (
      pasteContent.trim().startsWith("[") ||
      pasteContent.trim().startsWith("{")
    ) {
      parseJSON(pasteContent, name);
    } else {
      parseCSV(pasteContent, name);
    }
    setPasteContent("");
    setIsPasteModalOpen(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileUpload(files[0]);
  };
  const onDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const onDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const onDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) setIsDragging(false);
  };

  const parseCSV = (csvContent, fileName) => {
    Papa.parse(csvContent, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => processData(results.data, fileName),
    });
  };

  const parseJSON = (jsonContent, fileName) => {
    try {
      processData(JSON.parse(jsonContent), fileName);
    } catch (err) {
      console.error(err);
    }
  };

  const processData = (rawData, fileName) => {
    const newSeries = processDataLogic(rawData, fileName);
    if (newSeries.length === 0) {
      alert(
        `导入失败: 无法从 "${fileName}" 中解析出有效的曲线数据。\n请确保文件包含 "日期"、"时间" 以及数值列。\n建议下载使用标准模版。`,
      );
      return;
    }
    setSeries((prev) => [...prev, ...newSeries]);
  };

  const calculateTotal = (seriesItem) => {
    const { data, metricName, name, unit } = seriesItem;
    if (!data || data.length < 2) return "0";

    const mKey = (metricName || name).toLowerCase();
    const isWindSpeed =
      mKey.includes("风速") || (unit && unit.toLowerCase() === "m/s");

    if (isWindSpeed) {
      const avg = data.reduce((sum, d) => sum + d.value, 0) / data.length;
      return `${parseFloat(avg.toFixed(2)).toString()} m/s (均值)`;
    }

    let total = 0;
    const sorted = [...data].sort(
      (a, b) => a.time.getTime() - b.time.getTime(),
    );
    for (let i = 0; i < sorted.length - 1; i++) {
      const p1 = sorted[i];
      const p2 = sorted[i + 1];
      const dt = (p2.time.getTime() - p1.time.getTime()) / (1000 * 3600);
      total += ((p1.value + p2.value) * dt) / 2;
    }

    let unitStr = unit ? `${unit}·h` : "项";
    let finalValue = total;

    // 业务逻辑转换
    const isPower =
      mKey.includes("实际功率") ||
      mKey.includes("负荷") ||
      mKey.includes("预测") ||
      mKey.includes("出清") ||
      (unit && unit.toUpperCase() === "MW");
    if (isPower) {
      unitStr = "MWh";
    } else if (mKey.includes("辐照度") || mKey.includes("辐射")) {
      unitStr = "MJ/m²";
      finalValue = total * 0.0036; // Wh/m2 -> MJ/m2 (3600/1e6)
    }

    return `${parseFloat(finalValue.toFixed(2)).toString()} ${unitStr}`;
  };

  const removeSeries = (id) =>
    setSeries((prev) => prev.filter((s) => s.id !== id));

  const openDataEditor = (s) => {
    setEditingSeriesId(s.id);
    setEditingSeriesName(s.name);
    setEditingMetricName(s.metricName || "");
    setEditingDataText(
      JSON.stringify(
        s.data.map((d) => ({
          time: format(new Date(d.time), "yyyy-MM-dd HH:mm:ss"),
          value: d.value,
        })),
        null,
        2,
      ),
    );
    setIsDataEditorOpen(true);
  };

  const saveEditedData = () => {
    try {
      const newData = JSON.parse(editingDataText).map((d) => ({
        ...d,
        time: new Date(d.time),
      }));
      setSeries((prev) =>
        prev.map((s) =>
          s.id === editingSeriesId
            ? {
                ...s,
                name: editingSeriesName,
                metricName: editingMetricName,
                data: newData,
              }
            : s,
        ),
      );
      setIsDataEditorOpen(false);
    } catch {
      alert(
        "JSON 解析失败，请检查格式。支持编辑 time (yyyy-MM-dd HH:mm:ss) 和 value。",
      );
    }
  };

  const exportData = () => {
    // 直接使用当前图表活跃的系列数据（这些数据已经经过了过滤和 displayName/metricKey 的处理）
    // 这确保留了 CSV 导出内容与图表展示内容 100% 一致，包括处理了 metricKey 缺失导致的覆盖 bug
    if (!activeSeries || activeSeries.length === 0) {
      alert("当前没有可导出的数据");
      return;
    }

    // 1. 收集所有唯一的维度和指标名称
    const dimensionKeys = new Set();
    const metricKeys = new Set();
    activeSeries.forEach((s) => {
      if (s.dimensions) {
        Object.keys(s.dimensions).forEach((k) => dimensionKeys.add(k));
      }
      metricKeys.add(s.metricKey);
    });

    const dimKeyList = Array.from(dimensionKeys).sort();
    const metricNameList = Array.from(metricKeys).sort();

    // 2. 构造数据行
    // 这里采用“日期+时间”作为主键。维度值则作为列的一部分。
    // 为了支持不同维度的系列（如有些系列带“机组”，有些不带）对齐在同一行，
    // 我们需要更灵活的处理。如果同一时间同一场站有多个记录，它们会被合并。
    const dataRows = {}; // key: date|time|dimValues

    activeSeries.forEach((s) => {
      const mName = s.metricKey;
      s.data.forEach((d) => {
        const dateStr = s.date;
        const timeStr = format(d.time, "HH:mm:ss");

        // 生成能够唯一标识这一行实体的维度标识
        // 注意：如果 Irradiance 只有“场站”维度，而功率有“场站+机组”维度，
        // 它们当前会被导出在不同行。这是为了保证数据的严谨性。
        const dimValuesJoined = dimKeyList
          .map((k) => s.dimensions[k] || "")
          .join("|");
        const rowKey = `${dateStr}|${timeStr}|${dimValuesJoined}`;

        if (!dataRows[rowKey]) {
          dataRows[rowKey] = {
            date: dateStr,
            time: timeStr,
            dims: { ...s.dimensions },
            metrics: {},
          };
        }
        // 写入指标值。由于修复了 mName (metricKey)，不同指标将不再互相覆盖
        dataRows[rowKey].metrics[mName] = d.value;
      });
    });

    // 3. 构建 CSV 内容
    const headers = ["日期", "时间", ...dimKeyList, ...metricNameList];
    const csvRows = [headers];

    // 排序逻辑：先按日期，再按时间，最后按维度标识
    const sortedRowKeys = Object.keys(dataRows).sort((a, b) => {
      const partsA = a.split("|");
      const partsB = b.split("|");
      if (partsA[0] !== partsB[0]) return partsA[0].localeCompare(partsB[0]); // Date
      if (partsA[1] !== partsB[1]) return partsA[1].localeCompare(partsB[1]); // Time
      return a.localeCompare(b);
    });

    sortedRowKeys.forEach((key) => {
      const rowData = dataRows[key];
      const row = [
        rowData.date,
        rowData.time,
        ...dimKeyList.map((k) => rowData.dims[k] || ""),
        ...metricNameList.map((m) =>
          rowData.metrics[m] !== undefined ? rowData.metrics[m] : "",
        ),
      ];
      csvRows.push(row);
    });

    // 4. 下载文件
    const csvContent = csvRows
      .map((r) =>
        r
          .map((v) => {
            if (v === null || v === undefined) return "";
            const s = String(v);
            return s.includes(",") || s.includes('"') || s.includes("\n")
              ? `"${s.replace(/"/g, '""')}"`
              : s;
          })
          .join(","),
      )
      .join("\n");

    const blob = new Blob(["\ufeff" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `新能源发电分析导出_${format(new Date(), "yyyyMMdd_HHmm")}.csv`,
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const clearAll = () => {
    if (!confirm("确定要清空所有当前加载的数据吗？(历史存单将被保留)")) return;
    setSeries([]);
    setAvailableDates([]);
    setSelectedDates([]);
    resetSettings();

    // 彻底清理相关 LocalStorage
    ["series", "selectedDates"].forEach((key) =>
      localStorage.removeItem(`da_${key}`),
    );
  };

  const resetSettings = () => {
    setAxisRanges({});
    setChartTypes({});
    setCustomMetricColors({});
    setLegendSelected({});
    setGranularity("hour");
    setGranularity("hour");
    setShowIntegral(false);

    setRangeConfig({
      hour: { start: 0, end: 23 },
      day: { start: 1, end: 31 },
      month: { start: 1, end: 12 },
    });
    const keysToReset = [
      "axisRanges",
      "chartTypes",
      "customMetricColors",
      "legendSelected",
      "granularity",
      "showIntegral",
      "rangeConfig",
      "dimensionFilters",
    ];
    keysToReset.forEach((key) => localStorage.removeItem(`da_${key}`));
  };

  const fetchAccessLogs = async (type = logType) => {
    try {
      const res = await fetch(`/api/logs?type=${type}`);
      if (res.ok) {
        const data = await res.json();
        setAccessLogs(data.logs || []);
        setLogType(type);
        setIsLogModalOpen(true);
      }
    } catch (e) {
      console.error("获取日志失败:", e);
    }
  };

  const exportLogs = () => {
    const blob = new Blob([accessLogs.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${logType}_logs_${format(new Date(), "yyyyMMdd_HHmm")}.txt`;
    a.click();
  };

  const toggleTheme = () =>
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));

  /**
   * 获取历史辐照度数据
   */
  /**
   * 打开辐照度获取配置窗口
   */
  const fetchIrradiance = () => {
    if (selectedDates.length === 0) {
      alert("请先选择日期 (Date Picker)");
      return;
    }

    // 智能识别场站名称：
    // 1. 如果有活跃维度且有选中值，优先取第一个选中值
    // 2. 从已有数据的维度中寻找场站关键字
    let stationName = "";
    const allSelectedVals = Object.values(dimensionFilters).flat();
    if (allSelectedVals.length > 0) {
      stationName = allSelectedVals[0];
    } else if (series.length > 0) {
      const activeDaySeries = series.filter((s) =>
        selectedDates.includes(s.date),
      );
      if (activeDaySeries.length > 0) {
        const firstS = activeDaySeries[0];
        const possibleKeys = [
          "场站名称",
          "场站",
          "电站",
          "名称",
          "调度名称",
          "item",
          "station",
          "项目",
        ];
        for (const key of possibleKeys) {
          if (firstS.dimensions[key]) {
            stationName = firstS.dimensions[key];
            break;
          }
        }
      }
    }

    setStationSearchTerm(stationName);
    setIsStationModalOpen(true);
  };

  const fetchStations = async () => {
    try {
      const res = await fetch("/api/stations");
      if (res.ok) setAvailableStations(await res.json());
    } catch (e) {
      console.error("获取场站列表失败", e);
    }
  };

  useEffect(() => {
    fetchStations();
  }, []);

  const importStations = async () => {
    if (!stationBatchInput.trim()) return;
    const rows = stationBatchInput
      .split("\n")
      .map((r) => r.trim())
      .filter(Boolean);
    const newStations = [];
    rows.forEach((row, i) => {
      if (i === 0 && (row.includes("场站") || row.includes("站名"))) return; // 跳过表头
      const parts = row.split(/[,，\t]/);
      // 支持多种列数格式：
      // 1. 场站,经度,纬度,区域
      // 2. 场站,方位角,倾角,经度,纬度,区域
      if (parts.length >= 5) {
        newStations.push({
          name: parts[0].trim(),
          azimuth: parseFloat(parts[1]),
          tilt: parseFloat(parts[2]),
          lon: parseFloat(parts[3]),
          lat: parseFloat(parts[4]),
          region: (parts[5] || "").trim(),
        });
      } else if (parts.length >= 3) {
        newStations.push({
          name: parts[0].trim(),
          lon: parseFloat(parts[1]),
          lat: parseFloat(parts[2]),
          region: (parts[3] || "").trim(),
          azimuth: 0,
          tilt: 0,
        });
      }
    });

    if (newStations.length === 0) {
      alert(
        "无效的格式。格式要求：\n场站,经度,纬度,区域\n或：场站,方位角,角度,经度,纬度,区域",
      );
      return;
    }

    try {
      const res = await fetch("/api/stations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newStations),
      });
      if (res.ok) {
        fetchStations();
        setStationBatchInput("");
        alert(`成功导入 ${newStations.length} 个场站`);
      }
    } catch (e) {
      console.error("导入场站失败", e);
    }
  };

  const exportStationsCSV = () => {
    if (!availableStations.length) {
      alert("场站库为空，无可导出数据");
      return;
    }

    const header = "场站,方位角,倾角,经度,纬度,区域";
    const rows = availableStations.map(
      (s) =>
        `${s.name},${s.azimuth || 0},${s.tilt || 0},${s.lon || 0},${s.lat || 0},${s.region || ""}`,
    );

    const csvContent = [header, ...rows].join("\n");
    const blob = new Blob(["\ufeff" + csvContent], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `场站库导出_${format(new Date(), "yyyyMMdd_HHmm")}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const deleteStation = async (name) => {
    if (!confirm(`确定删除场站 ${name} 吗？`)) return;
    try {
      const res = await fetch(`/api/stations/${encodeURIComponent(name)}`, {
        method: "DELETE",
      });
      if (res.ok) fetchStations();
    } catch (e) {
      console.error("删除场站失败", e);
    }
  };

  const executeFetchIrradiance = async (inputName) => {
    if (!inputName) return;

    setIsFetchingWeather(true);
    let addedCount = 0;
    let failList = [];

    for (const date of selectedDates) {
      try {
        const res = await fetch(
          `/api/weather/irradiance?stationName=${encodeURIComponent(inputName)}&date=${date}`,
        );
        if (!res.ok) {
          const errData = await res.json();
          failList.push(`${date}: ${errData.error}`);
          continue;
        }
        const result = await res.json();

        // --- 增强的维度匹配逻辑 ---
        // 1. 寻找一个与当前获取的场站和日期都匹配的、已存在的 series
        const stationDimKeyList = [
          "场站名称",
          "场站",
          "电站",
          "Station",
          "station",
          "Name",
          "项目",
          "名称",
        ];
        let referenceDimensions = null;
        const existingSeriesForDate = series.filter((s) => s.date === date);
        const referenceSeries = existingSeriesForDate.find(
          (s) =>
            s.dimensions &&
            Object.entries(s.dimensions).some(
              ([key, value]) =>
                stationDimKeyList.includes(key) && value === inputName,
            ),
        );

        if (referenceSeries) {
          // 2. 如果找到，直接复制它的完整 dimensions
          referenceDimensions = { ...referenceSeries.dimensions };
        } else {
          // 3. 如果没找到，回退到旧的“智能猜测维度名”逻辑
          const existingDimKey = (() => {
            const anyWithDim = series.find((s) => s.dimensions);
            if (anyWithDim) {
              const key = Object.keys(anyWithDim.dimensions).find((k) =>
                stationDimKeyList.includes(k),
              );
              if (key) return key;
            }
            return "场站名称"; // 默认值
          })();
          referenceDimensions = {
            [existingDimKey]: result.stationName || inputName,
          };
        }
        // --- 维度匹配逻辑结束 ---

        const newSeriesItem = {
          id: `weather_${inputName}_${date}_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          name: "历史辐照度",
          metricName: "历史辐照度",
          date: date,
          data: result.data.map((d) => ({
            time: new Date(d.time),
            value: d.value,
          })),
          dimensions: referenceDimensions, // 使用匹配到的维度对象
          unit: "W/m²",
        };

        setSeries((prev) => {
          // 避免重复添加：检查指标名、日期和所有维度是否都一样
          const exists = prev.some(
            (s) =>
              s.metricName === "历史辐照度" &&
              s.date === date &&
              JSON.stringify(s.dimensions) ===
                JSON.stringify(referenceDimensions),
          );
          if (exists) return prev;
          return [...prev, newSeriesItem];
        });
        addedCount++;
      } catch (err) {
        console.error(err);
        failList.push(`${date}: 网络异常或超时`);
      }
    }

    setIsFetchingWeather(false);

    if (addedCount > 0) {
      if (failList.length > 0) {
        alert(
          `已成功获取 ${addedCount} 天的辐照度数据。\n部分日期失败: \n${failList.join("\n")}`,
        );
      }
    } else {
      alert(`获取失败: \n${failList.join("\n") || "未知原因"}`);
    }
  };

  const saveSnapshot = async () => {
    const name = prompt(
      "请输入历史记录名称:",
      `记录_${format(new Date(), "MM-dd HH:mm")}`,
    );
    if (!name) return;

    // 捕捉当前视角下的所有系列数据，实现“调阅”功能
    const capturedSeries = series.filter((s) => selectedDates.includes(s.date));

    const record = {
      id: Date.now().toString(),
      name,
      selectedDates,
      dimensionFilters,
      axisRanges,
      chartTypes,
      rangeConfig, // 保存微调范围
      capturedSeries, // 保存数据副本
    };

    try {
      const res = await fetch("/api/snapshots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      });
      if (res.ok) {
        setHistoryRecords((prev) => [record, ...prev]);
      }
    } catch (e) {
      console.error("保存失败:", e);
      // 降级使用 LocalStorage (暂不实现，避免数据不一致)
    }
  };

  const loadSnapshot = (rec) => {
    // 如果记录里有数据备份，将其合并进当前的 series 中（去重）
    if (rec.capturedSeries && rec.capturedSeries.length > 0) {
      setSeries((prev) => {
        const existingIds = new Set(prev.map((s) => s.id));
        const revitalizedNew = rec.capturedSeries.map((s) => ({
          ...s,
          data: s.data.map((d) => ({ ...d, time: new Date(d.time) })),
        }));
        const filteredNew = revitalizedNew.filter(
          (s) => !existingIds.has(s.id),
        );
        return [...prev, ...filteredNew];
      });
    }

    setTimeout(() => {
      setSelectedDates(rec.selectedDates);
      setDimensionFilters(rec.dimensionFilters || {});
      setAxisRanges(rec.axisRanges);
      setChartTypes(rec.chartTypes);
      if (rec.rangeConfig) setRangeConfig(rec.rangeConfig);
      setActiveTab("controls"); // 自动切回控制台
    }, 0);
  };

  const deleteSnapshot = async (e, id) => {
    e.stopPropagation(); // 阻止事件冒泡到父级 onClick
    if (!confirm("确定要删除这条历史存单吗？")) return;
    try {
      const res = await fetch(`/api/snapshots/${id}`, { method: "DELETE" });
      if (res.ok) {
        setHistoryRecords((prev) => prev.filter((r) => r.id !== id));
      }
    } catch (error) {
      console.error("删除失败:", error);
    }
  };

  const clearAllHistory = async () => {
    if (!confirm("确定要清空所有历史存单吗？此操作不可撤销！")) return;
    try {
      const res = await fetch("/api/snapshots", { method: "DELETE" });
      if (res.ok) {
        setHistoryRecords([]);
        alert("历史存单已成功清空");
      } else {
        throw new Error("后端响应异常");
      }
    } catch (e) {
      console.error("清空历史失败:", e);
      alert("清空失败: " + e.message);
    }
  };

  const setAllLegends = (status) => {
    const newSelected = { ...legendSelected };
    activeSeries.forEach((s) => {
      newSelected[s.displayName] = status;
    });
    setLegendSelected(newSelected);
  };

  const toggleMetricLegend = (metric) => {
    setLegendSelected((prev) => ({
      ...prev,
      [metric]: prev[metric] === false ? true : false,
    }));
  };

  const toggleDate = (date) => {
    setSelectedDates((prev) =>
      prev.includes(date) ? prev.filter((d) => d !== date) : [...prev, date],
    );
  };

  return (
    <div
      className={`app-container ${isDragging ? "dragging" : ""} ${theme === "light" ? "light-theme" : ""}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
    >
      {isDragging && (
        <div className="drag-overlay">
          <div className="drag-message">
            <Upload size={64} />
            <h2>松开鼠标导入文件</h2>
          </div>
        </div>
      )}

      <nav className="navbar glass-panel">
        <div className="logo" style={{ paddingLeft: "8px" }}>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            title={isSidebarCollapsed ? "展开" : "折叠"}
            style={{ marginRight: "8px" }}
          >
            <Layout size={18} />
          </button>
          <img src="/logo.png" alt="Logo" className="logo-img" />
          <span style={{ marginLeft: "4px" }}>
            <strong>新能源分析系统</strong>
          </span>
          <div
            className={`backend-status-badge ${backendStatus}`}
            style={{ marginLeft: "8px" }}
          >
            <span className="status-dot"></span>
            {backendStatus === "online" ? "在线" : "离线"}
          </div>
          <div className="version-tag" style={{ marginLeft: "4px" }}>
            {systemVersion}
          </div>
        </div>
        <div className="nav-actions">
          <label
            className="upload-btn premium-button"
            title="从本地选取 CSV/JSON 文件"
          >
            <Upload size={14} /> 导入文件
            <input type="file" onChange={handleFileUpload} hidden />
          </label>
          <button
            className="nav-btn premium-button"
            onClick={() => setIsPasteModalOpen(true)}
            title="粘贴文本数据"
          >
            <ClipboardPaste size={14} /> 粘贴导入
          </button>
          <div className="nav-divider"></div>
          <button
            className="premium-button"
            onClick={saveSnapshot}
            title="保存当前画面快照"
          >
            <Archive size={15} /> 存入历史
          </button>
          <button
            className="action-icon-btn premium-button secondary"
            onClick={resetSettings}
            title="重置面板 (RotateCcw)"
          >
            <RotateCcw size={15} />
          </button>
          <button
            className="action-icon-btn clear-btn"
            onClick={clearAll}
            title="清空当前所有图表数据 (Trash2)"
          >
            <Trash2 size={15} />
          </button>
          <div className="nav-divider"></div>
          <button
            className={`nav-btn premium-button ${isFetchingWeather ? "loading" : ""}`}
            onClick={fetchIrradiance}
            disabled={isFetchingWeather}
            title="根据场站名自动匹配坐标，从气象 API 获取历史辐照度 (15分钟分辨率)"
          >
            {isFetchingWeather ? (
              <RotateCcw size={14} className="spin" />
            ) : (
              <Sun size={14} />
            )}
            {isFetchingWeather ? "获取中..." : "历史辐照度"}
          </button>
          <div className="nav-divider"></div>
          {selectedDates.length > 0 && (
            <button
              className="action-icon-btn export-btn"
              onClick={exportData}
              title="导出当前 CSV (Download)"
            >
              <Download size={15} />
            </button>
          )}
          <div className="nav-divider"></div>
          <button
            className="icon-btn-mini"
            onClick={() => fetchAccessLogs("access")}
            title="查看系统运行日志"
          >
            <Activity size={18} />
          </button>
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title="切换深/浅色主题"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </nav>

      <main className="main-content">
        <aside
          className={`sidebar glass-panel ${isSidebarCollapsed ? "collapsed" : ""} ${isSidebarWide ? "wide" : ""}`}
          style={{ width: isSidebarCollapsed ? 0 : isSidebarWide ? 320 : 240 }}
        >
          <div className="sidebar-tabs">
            <button
              className={`tab-btn ${activeTab === "controls" ? "active" : ""}`}
              onClick={() => setActiveTab("controls")}
            >
              <Layout size={14} /> 控制台
            </button>
            <button
              className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
              onClick={() => setActiveTab("history")}
            >
              <History size={14} /> 历史存单
            </button>
          </div>

          <div className="sidebar-header-improved">
            <div className="sidebar-title-row">
              <h3>{activeTab === "controls" ? "分析控制台" : "历史快照库"}</h3>
              <div className="header-actions">
                <button
                  className="icon-btn-mini"
                  onClick={() => setIsSidebarWide(!isSidebarWide)}
                  title={isSidebarWide ? "折叠宽度" : "增加宽度"}
                >
                  <Layout size={14} />
                </button>
                {activeTab === "history" && historyRecords.length > 0 && (
                  <button
                    className="delete-all-btn-styled-large"
                    onClick={clearAllHistory}
                    title="清空所有存单记录"
                  >
                    <Trash2 size={12} style={{ marginRight: "4px" }} /> 清空历史
                  </button>
                )}
              </div>
            </div>
            {activeTab === "history" && (
              <div className="header-search-row">
                <History size={14} className="search-icon" />
                <input
                  type="text"
                  placeholder="搜索存单名称或日期..."
                  value={historySearchTerm}
                  onChange={(e) => setHistorySearchTerm(e.target.value)}
                />
                {historySearchTerm && (
                  <button
                    className="clear-search"
                    onClick={() => setHistorySearchTerm("")}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>
            )}
          </div>

          {activeTab === "controls" ? (
            <div className="sidebar-scroll-area">
              <div
                className="date-selector section-item"
                style={{ marginBottom: "8px" }}
              >
                <p className="label" style={{ marginBottom: "4px" }}>
                  日期筛选
                </p>
                <div className="dimension-tags">
                  {availableDates.map((date) => (
                    <button
                      key={date}
                      className={`dim-tag ${selectedDates.includes(date) ? "active" : ""}`}
                      onClick={() => toggleDate(date)}
                    >
                      {date}
                    </button>
                  ))}
                </div>
              </div>

              {selectedDates.length > 0 && (
                <div className="section-item" style={{ marginBottom: "8px" }}>
                  {(() => {
                    const currentSeries = series.filter((s) =>
                      selectedDates.includes(s.date),
                    );
                    const allDimKeys = [
                      ...new Set(
                        currentSeries.flatMap((s) =>
                          s.dimensions ? Object.keys(s.dimensions) : [],
                        ),
                      ),
                    ].sort();

                    if (allDimKeys.length === 0) {
                      return (
                        <div style={{ fontSize: "12px", opacity: 0.6 }}>
                          无可用维度
                        </div>
                      );
                    }

                    return (
                      <>
                        <div className="section-header">
                          <span className="label">维度筛选</span>
                        </div>

                        {allDimKeys.map((dimKey) => {
                          const allValues = [
                            ...new Set(
                              currentSeries
                                .map((s) => s.dimensions?.[dimKey])
                                .filter(Boolean),
                            ),
                          ].sort();
                          const selected = dimensionFilters[dimKey] || [];
                          const isAllSelected =
                            selected.length === allValues.length;

                          return (
                            <div
                              key={dimKey}
                              className="dimension-group"
                              style={{ marginBottom: "6px" }}
                            >
                              <div
                                className="dim-header-row"
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  marginBottom: "4px",
                                }}
                              >
                                <span
                                  className="dim-name"
                                  style={{ fontWeight: 600, fontSize: "11px" }}
                                >
                                  {dimKey}
                                </span>
                                <div
                                  className="dim-header-actions"
                                  style={{
                                    display: "flex",
                                    gap: "6px",
                                    alignItems: "center",
                                  }}
                                >
                                  <span
                                    style={{
                                      fontSize: "10px",
                                      color: "#94a3b8",
                                    }}
                                  >
                                    {isAllSelected
                                      ? "全部"
                                      : `${selected.length}/${allValues.length}`}
                                  </span>
                                  <div className="dimension-actions-text">
                                    <button
                                      className="text-action-btn-mini"
                                      onClick={() =>
                                        setDimensionFilters((prev) => ({
                                          ...prev,
                                          [dimKey]: allValues,
                                        }))
                                      }
                                    >
                                      全选
                                    </button>
                                    <button
                                      className="text-action-btn-mini"
                                      onClick={() =>
                                        setDimensionFilters((prev) => ({
                                          ...prev,
                                          [dimKey]: [],
                                        }))
                                      }
                                    >
                                      清空
                                    </button>
                                    <button
                                      className="text-action-btn-mini"
                                      onClick={() =>
                                        setDimensionFilters((prev) => ({
                                          ...prev,
                                          [dimKey]: allValues.filter(
                                            (v) => !selected.includes(v),
                                          ),
                                        }))
                                      }
                                    >
                                      反选
                                    </button>
                                  </div>
                                </div>
                              </div>
                              <div className="dimension-tags">
                                {allValues.map((val) => (
                                  <button
                                    key={val}
                                    className={`dim-tag ${selected.includes(val) ? "active" : ""}`}
                                    onClick={() => {
                                      setDimensionFilters((prev) => {
                                        const current = prev[dimKey] || [];
                                        const next = current.includes(val)
                                          ? current.filter((v) => v !== val)
                                          : [...current, val];
                                        return { ...prev, [dimKey]: next };
                                      });
                                    }}
                                  >
                                    {val}
                                  </button>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </>
                    );
                  })()}
                </div>
              )}

              <div className="section-item">
                <div className="section-header">
                  <span className="label">时间与范围</span>
                </div>

                <div
                  className="checkbox-group-vertical"
                  style={{ marginBottom: "12px" }}
                >
                  <label
                    className="checkbox-label"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isSolarMode}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setIsSolarMode(checked);
                        if (checked) {
                          setGranularity("hour");
                          setRangeConfig((prev) => ({
                            ...prev,
                            hour: solarRange || { start: 7, end: 19 },
                          }));
                        } else {
                          setRangeConfig((prev) => ({
                            ...prev,
                            hour: { start: 0, end: 23 },
                          }));
                        }
                      }}
                    />
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: isSolarMode ? 600 : 400,
                        color: isSolarMode ? "var(--primary-color)" : "inherit",
                      }}
                    >
                      光伏模式 (
                      {String(rangeConfig?.hour?.start ?? 7).padStart(2, "0")}
                      :00-
                      {String(rangeConfig?.hour?.end ?? 19).padStart(2, "0")}
                      :00)
                    </span>
                  </label>

                  <label
                    className="checkbox-label"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={showIntegral}
                      onChange={(e) => setShowIntegral(e.target.checked)}
                    />
                    <span style={{ fontSize: "12px" }}>
                      显示总计 (积分/均值)
                    </span>
                  </label>

                  {selectedDates && selectedDates.length > 1 && (
                    <label
                      className="checkbox-label"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isCompareOverlap}
                        onChange={(e) => setIsCompareOverlap(e.target.checked)}
                      />
                      <span style={{ fontSize: "12px" }}>
                        多日 24h 重叠对比
                      </span>
                    </label>
                  )}
                </div>

                <div
                  className="toggle-group-modern"
                  style={{ marginBottom: "10px" }}
                >
                  {["hour", "day", "month"].map((g) => (
                    <button
                      key={g}
                      className={granularity === g ? "active" : ""}
                      onClick={() => setGranularity(g)}
                    >
                      {g === "hour" ? "日" : g === "day" ? "月" : "年"}
                    </button>
                  ))}
                </div>

                <div className="range-fine-tune-compact">
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                      marginBottom: "4px",
                    }}
                  >
                    <span>范围 ({granularity})</span>
                  </div>
                  <div className="tune-inputs">
                    <select
                      value={rangeConfig?.[granularity]?.start ?? 0}
                      onChange={(e) =>
                        setRangeConfig((prev) => {
                          const val = parseInt(e.target.value);
                          if (isSolarMode && granularity === "hour") {
                            setSolarRange((s) => ({ ...s, start: val }));
                          }
                          return {
                            ...prev,
                            [granularity]: {
                              ...prev[granularity],
                              start: val,
                            },
                          };
                        })
                      }
                    >
                      {Array.from({
                        length:
                          granularity === "hour"
                            ? 24
                            : granularity === "day"
                              ? 31
                              : 12,
                      }).map((_, i) => {
                        const val = i + (granularity === "hour" ? 0 : 1);
                        return (
                          <option key={val} value={val}>
                            {val}
                          </option>
                        );
                      })}
                    </select>
                    <span className="separator">-</span>
                    <select
                      value={rangeConfig?.[granularity]?.end ?? 0}
                      onChange={(e) =>
                        setRangeConfig((prev) => {
                          const val = parseInt(e.target.value);
                          if (isSolarMode && granularity === "hour") {
                            setSolarRange((s) => ({ ...s, end: val }));
                          }
                          return {
                            ...prev,
                            [granularity]: {
                              ...prev[granularity],
                              end: val,
                            },
                          };
                        })
                      }
                    >
                      {Array.from({
                        length:
                          granularity === "hour"
                            ? 24
                            : granularity === "day"
                              ? 31
                              : 12,
                      }).map((_, i) => {
                        const val = i + (granularity === "hour" ? 0 : 1);
                        return (
                          <option key={val} value={val}>
                            {val}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </div>
              </div>

              <div
                className="curtailment-section-compact"
                style={{
                  marginTop: "8px",
                  borderTop: "1px solid var(--border-color)",
                  paddingTop: "6px",
                }}
              >
                {/* 限电分析 */}
                <div className="section-item">
                  <div
                    className="section-header"
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <span className="label">限电分析 (AGC 联动)</span>
                    <div className="switch-wrapper">
                      <input
                        type="checkbox"
                        id="curtail-toggle"
                        className="ios-switch"
                        checked={showCurtailmentAnalysis}
                        onChange={(e) =>
                          setShowCurtailmentAnalysis(e.target.checked)
                        }
                      />
                      <label
                        htmlFor="curtail-toggle"
                        className="switch-label"
                      ></label>
                    </div>
                  </div>

                  {showCurtailmentAnalysis && (
                    <div className="compact-grid" style={{ marginTop: "8px" }}>
                      <div className="grid-item">
                        <label>辐照阈值</label>
                        <input
                          type="number"
                          value={curtailmentIrrThreshold}
                          onChange={(e) =>
                            setCurtailmentIrrThreshold(Number(e.target.value))
                          }
                        />
                      </div>
                      <div className="grid-item">
                        <label>偏差阈值</label>
                        <input
                          type="number"
                          value={curtailmentDiffThreshold}
                          onChange={(e) =>
                            setCurtailmentDiffThreshold(Number(e.target.value))
                          }
                        />
                      </div>
                      <div className="grid-item full-width">
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <label style={{ flexShrink: 0 }}>外观</label>
                          <input
                            type="color"
                            value={curtailmentColor}
                            onChange={(e) =>
                              setCurtailmentColor(e.target.value)
                            }
                            style={{
                              width: "40px",
                              height: "20px",
                              padding: 0,
                              border: "none",
                            }}
                          />
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.05"
                            value={curtailmentOpacity}
                            onChange={(e) =>
                              setCurtailmentOpacity(Number(e.target.value))
                            }
                            style={{ flex: 1 }}
                          />
                          <span style={{ fontSize: "10px", width: "24px" }}>
                            {Math.round(curtailmentOpacity * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div
                className="section-item"
                style={{
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <div className="section-header">
                  <span className="label">
                    数据 (
                    {
                      series.filter((s) => selectedDates.includes(s.date))
                        .length
                    }
                    )
                  </span>
                  <div className="legend-bulk-actions-modern">
                    <button
                      className="text-action-btn-mini"
                      onClick={() => setAllLegends(true)}
                    >
                      全显
                    </button>
                    <button
                      className="text-action-btn-mini"
                      onClick={() => setAllLegends(false)}
                    >
                      全隐
                    </button>
                  </div>
                </div>
                <div className="series-list-scroll-container">
                  <ul className="series-list-compact">
                    {activeSeries.map((s) => {
                      const displayName = s.displayName;
                      const metricKey = s.metricKey;
                      const isHidden = legendSelected[displayName] === false;

                      return (
                        <li
                          key={s.id}
                          className={`series-item-compact ${isHidden ? "hidden" : ""}`}
                          onClick={() => toggleMetricLegend(displayName)}
                          style={{
                            borderLeft: `4px solid ${isHidden ? "rgba(255,255,255,0.1)" : customMetricColors[metricKey] || getUserColor(uniqueMetrics.indexOf(metricKey), metricKey)}`,
                          }}
                        >
                          <div className="series-row-main">
                            <div className="series-info">
                              <div className="s-name" title={s.displayName}>
                                {s.displayName}
                              </div>
                              <div className="s-meta">
                                {/* Dimensions inline */}
                                {Object.entries(s.dimensions || {}).map(
                                  ([k, v]) => (
                                    <span key={k}>{v}</span>
                                  ),
                                )}
                              </div>
                            </div>
                            <div className="series-actions-hover">
                              {showIntegral && (
                                <span className="s-val">
                                  {calculateTotal(s)}
                                </span>
                              )}
                              <button
                                className="icon-btn-text"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openDataEditor(s);
                                }}
                              >
                                <FilePen size={10} />
                              </button>
                              <button
                                className="icon-btn-text"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removeSeries(s.id);
                                }}
                              >
                                <X size={10} />
                              </button>
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>

              {selectedDates.length > 0 && (
                <div
                  className="axis-section"
                  style={{
                    borderTop: "1px solid var(--border-color)",
                    marginTop: "8px",
                  }}
                >
                  <p className="label fixed-header">坐标轴与单位设置</p>
                  {(() => {
                    const currentActiveSeries = series.filter((s) =>
                      selectedDates.includes(s.date),
                    );
                    const uniqueMetricsInView = [
                      ...new Set(
                        currentActiveSeries.map((s) => getCleanMetricName(s)),
                      ),
                    ];
                    const powerMetrics = uniqueMetricsInView.filter((m) => {
                      const low = m.toLowerCase();
                      return (
                        low.includes("功率") ||
                        low.includes("power") ||
                        low.includes("预测") ||
                        low.includes("出清") ||
                        low.includes("负荷") ||
                        low.includes("agc") ||
                        low.includes("超短期")
                      );
                    });

                    return (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        }}
                      >
                        <div
                          className="axis-control-card glass-panel"
                          style={{ marginBottom: "4px" }}
                        >
                          <div className="control-row-dense">
                            <span className="label-mini">全局缩放</span>
                            <div
                              style={{
                                flex: 1,
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >
                              <input
                                type="range"
                                min="0.2"
                                max="1.8"
                                step="0.02"
                                value={axisAdjustmentFactor}
                                onChange={(e) =>
                                  setAxisAdjustmentFactor(
                                    parseFloat(e.target.value),
                                  )
                                }
                                style={{
                                  flex: 1,
                                  maxWidth: "80px",
                                  height: "4px",
                                }}
                              />
                              <span
                                className="value-badge"
                                style={{ flexShrink: 0, minWidth: "40px" }}
                              >
                                {Math.round(axisAdjustmentFactor * 100)}%
                              </span>
                              <button
                                className="icon-btn-text"
                                onClick={() => setAxisAdjustmentFactor(1.0)}
                                title="重置"
                              >
                                <RotateCcw size={10} />
                              </button>
                            </div>
                          </div>
                        </div>

                        <div className="axis-list-scrollable">
                          <div
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              gap: "8px",
                            }}
                          >
                            {powerMetrics.length > 1 && (
                              <div className="axis-control-card glass-panel power-box">
                                <div className="control-row-dense">
                                  <span
                                    className="label-mini"
                                    style={{ flex: 1 }}
                                  >
                                    统一上下限
                                  </span>
                                  <div className="inputs-row">
                                    <input
                                      className="axis-input"
                                      type="number"
                                      placeholder="Min"
                                      value={
                                        axisRanges[powerMetrics[0]]?.min ?? ""
                                      }
                                      onChange={(e) => {
                                        const val = e.target.value;
                                        setAxisRanges((prev) => {
                                          const next = { ...prev };
                                          powerMetrics.forEach(
                                            (pm) =>
                                              (next[pm] = {
                                                ...next[pm],
                                                min: val,
                                              }),
                                          );
                                          return next;
                                        });
                                      }}
                                    />
                                    <span className="sep">-</span>
                                    <input
                                      className="axis-input"
                                      type="number"
                                      placeholder="Max"
                                      value={
                                        axisRanges[powerMetrics[0]]?.max ?? ""
                                      }
                                      onChange={(e) => {
                                        const val = e.target.value;
                                        setAxisRanges((prev) => {
                                          const next = { ...prev };
                                          powerMetrics.forEach(
                                            (pm) =>
                                              (next[pm] = {
                                                ...next[pm],
                                                max: val,
                                              }),
                                          );
                                          return next;
                                        });
                                      }}
                                    />
                                  </div>
                                  <input
                                    type="checkbox"
                                    checked={useDefaultLimits}
                                    onChange={(e) =>
                                      setUseDefaultLimits(e.target.checked)
                                    }
                                    title="统一所有功率类指标的上下限"
                                  />
                                </div>
                              </div>
                            )}

                            {uniqueMetricsInView.map((metric, index) => {
                              const originalColor = getUserColor(index, metric);
                              const metricColor =
                                customMetricColors[metric] || originalColor;

                              // Check if all series for this metric are hidden
                              const isHidden = !currentActiveSeries.some(
                                (s) => {
                                  const seriesMetricName =
                                    getCleanMetricName(s);
                                  return (
                                    seriesMetricName === metric &&
                                    legendSelected[s.displayName] !== false
                                  );
                                },
                              );

                              return (
                                <div
                                  key={metric}
                                  className={`axis-control-card glass-panel ${isHidden ? "is-hidden-metric" : ""}`}
                                  style={{
                                    borderLeft: `3px solid ${metricColor}`,
                                  }}
                                >
                                  <div className="control-row-dense">
                                    <span
                                      className="metric-name"
                                      title={metric}
                                      style={{
                                        fontSize: "10px",
                                        fontWeight: 500,
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                        flex: 1,
                                      }}
                                    >
                                      {metric}
                                    </span>

                                    <div className="inputs-row">
                                      <input
                                        className="axis-input"
                                        type="number"
                                        placeholder={
                                          metric.includes("辐照") ||
                                          metric.includes("辐射")
                                            ? "0"
                                            : "Min"
                                        }
                                        value={axisRanges[metric]?.min ?? ""}
                                        onChange={(e) =>
                                          setAxisRanges((prev) => ({
                                            ...prev,
                                            [metric]: {
                                              ...prev[metric],
                                              min: e.target.value,
                                            },
                                          }))
                                        }
                                      />
                                      <span className="sep">-</span>
                                      <input
                                        className="axis-input"
                                        type="number"
                                        placeholder={
                                          metric.includes("辐照") ||
                                          metric.includes("辐射")
                                            ? "1000"
                                            : "Max"
                                        }
                                        value={axisRanges[metric]?.max ?? ""}
                                        onChange={(e) =>
                                          setAxisRanges((prev) => ({
                                            ...prev,
                                            [metric]: {
                                              ...prev[metric],
                                              max: e.target.value,
                                            },
                                          }))
                                        }
                                      />
                                    </div>

                                    <div
                                      className="header-tools"
                                      style={{
                                        display: "flex",
                                        gap: "2px",
                                        alignItems: "center",
                                      }}
                                    >
                                      <div
                                        style={{
                                          width: "10px",
                                          height: "10px",
                                          borderRadius: "2px",
                                          backgroundColor: metricColor,
                                          overflow: "hidden",
                                          position: "relative",
                                          cursor: "pointer",
                                        }}
                                      >
                                        <input
                                          type="color"
                                          value={metricColor}
                                          onChange={(e) =>
                                            setCustomMetricColors((prev) => ({
                                              ...prev,
                                              [metric]: e.target.value,
                                            }))
                                          }
                                          style={{
                                            opacity: 0,
                                            width: "100%",
                                            height: "100%",
                                            position: "absolute",
                                            top: 0,
                                            left: 0,
                                            cursor: "pointer",
                                          }}
                                        />
                                      </div>
                                      <button
                                        className="icon-btn-text"
                                        onClick={() =>
                                          setAxisRanges((prev) => {
                                            const n = { ...prev };
                                            delete n[metric];
                                            return n;
                                          })
                                        }
                                        title="重置范围"
                                      >
                                        <RotateCcw size={10} />
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          ) : (
            <div className="sidebar-scroll-area">
              <div className="history-section-full">
                <div className="history-list-large">
                  {historyRecords.filter(
                    (rec) =>
                      rec.name
                        .toLowerCase()
                        .includes(historySearchTerm.toLowerCase()) ||
                      rec.selectedDates.some((d) =>
                        d.includes(historySearchTerm),
                      ),
                  ).length === 0 ? (
                    <div className="empty-mini">未找到匹配存单</div>
                  ) : (
                    historyRecords
                      .filter(
                        (rec) =>
                          rec.name
                            .toLowerCase()
                            .includes(historySearchTerm.toLowerCase()) ||
                          rec.selectedDates.some((d) =>
                            d.includes(historySearchTerm),
                          ),
                      )
                      .map((rec) => (
                        <div
                          key={rec.id}
                          className="history-item-compact glass-panel"
                        >
                          <div
                            className="history-content-row"
                            onClick={() => loadSnapshot(rec)}
                          >
                            <div className="h-avatar">{rec.name.charAt(0)}</div>
                            <div className="history-text">
                              <span className="h-name">{rec.name}</span>
                              <span className="h-date">
                                {rec.selectedDates.join(", ")}
                              </span>
                            </div>
                          </div>
                          <button
                            className="delete-history-btn"
                            onClick={(e) => deleteSnapshot(e, rec.id)}
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))
                  )}
                </div>
              </div>
            </div>
          )}
        </aside>

        <section className="chart-area glass-panel">
          {!selectedDates.length && (
            <div className="empty-state">
              <h2>开始分析</h2>
              <p>支持拖拽文件或粘贴数据</p>
              <div className="guide-box">
                <div className="guide-step">
                  <span>1</span> 准备数据：
                  <a
                    href="./import_template.csv"
                    download="import_template.csv"
                    className="sample-link"
                  >
                    点击下载导入标准模版
                  </a>
                </div>
                <div className="guide-step">
                  <span>2</span>{" "}
                  导入方式：拖拽文件至网页、点击右上角“导入文件”或“粘贴导入”
                </div>
                <div className="guide-step">
                  <span>3</span>{" "}
                  数据要求：首行需包含“日期”、“时间”字样，数值列名称建议包含“功率”、“价格”等关键词
                </div>
                <div className="guide-step">
                  <span>4</span>{" "}
                  对比分析：在左侧勾选日期可叠加曲线，点击图表圆点可快速切换主要坐标轴
                </div>
              </div>
            </div>
          )}
          <div
            ref={chartRef}
            className="chart-container"
            style={{
              flex: 1,
              width: "100%",
              height: "100%",
              opacity: selectedDates.length ? 1 : 0,
              pointerEvents: selectedDates.length ? "auto" : "none",
            }}
          ></div>
        </section>
      </main>

      {isStationModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel" style={{ width: "400px" }}>
            <div className="modal-header">
              <h3>获取历史辐照度 - 选择场站</h3>
              <button onClick={() => setIsStationModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div style={{ padding: "0 20px 20px" }}>
              <p className="label">搜索或输入场站名称 (支持模糊匹配)</p>
              <input
                type="text"
                className="styled-select"
                placeholder="输入名称搜索..."
                value={stationSearchTerm}
                onChange={(e) => setStationSearchTerm(e.target.value)}
                autoFocus
                style={{ width: "100%", marginBottom: "6px" }}
              />
              <select
                className="styled-select"
                style={{ width: "100%", marginBottom: "10px" }}
                value={stationSearchTerm}
                onChange={(e) => setStationSearchTerm(e.target.value)}
              >
                <option value="">-- 选择或搜索场站 --</option>
                {availableStations.map((s) => (
                  <option key={s.name} value={s.name}>
                    {s.name} ({s.region || "未分区"})
                  </option>
                ))}
              </select>
              <div
                className="station-list-scroll"
                style={{
                  maxHeight: "250px",
                  overflowY: "auto",
                  border: "1px solid var(--border-color)",
                  borderRadius: "8px",
                  background: "rgba(0,0,0,0.05)",
                }}
              >
                {availableStations
                  .filter((s) =>
                    s.name
                      .toLowerCase()
                      .includes(stationSearchTerm.toLowerCase()),
                  )
                  .map((s) => (
                    <div
                      key={s.name}
                      className="station-item-row"
                      style={{
                        padding: "8px 12px",
                        cursor: "pointer",
                        borderBottom: "1px solid var(--border-color)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background:
                          stationSearchTerm === s.name
                            ? "rgba(var(--primary-rgb), 0.1)"
                            : "transparent",
                      }}
                      onClick={() => setStationSearchTerm(s.name)}
                    >
                      <span style={{ fontWeight: 500, fontSize: "13px" }}>
                        {s.name}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          opacity: 0.6,
                          background: "rgba(128,128,128,0.1)",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        {s.region}
                      </span>
                    </div>
                  ))}
                {availableStations.filter((s) =>
                  s.name
                    .toLowerCase()
                    .includes(stationSearchTerm.toLowerCase()),
                ).length === 0 &&
                  stationSearchTerm && (
                    <div
                      style={{
                        padding: "12px",
                        textAlign: "center",
                        fontSize: "12px",
                        opacity: 0.6,
                      }}
                    >
                      系统中无此预置场站
                      <br />
                      将尝试作为"自定义名称"搜索
                    </div>
                  )}
              </div>
            </div>
            <div className="modal-actions" style={{ padding: "0 20px 20px" }}>
              <button
                onClick={() => setIsStationManagerOpen(true)}
                style={{
                  marginRight: "auto",
                  background: "transparent",
                  border: "1px dashed var(--primary-color)",
                  color: "var(--primary-color)",
                }}
              >
                配置场站库
              </button>
              <button onClick={() => setIsStationModalOpen(false)}>取消</button>
              <button
                className="premium-button"
                onClick={() => {
                  executeFetchIrradiance(stationSearchTerm);
                  setIsStationModalOpen(false);
                }}
              >
                确认获取
              </button>
            </div>
          </div>
        </div>
      )}
      {isStationManagerOpen && (
        <div className="modal-overlay">
          <div
            className="modal-content glass-panel"
            style={{
              width: "700px",
              maxHeight: "95vh",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div className="modal-header">
              <h3>场站库管理</h3>
              <button onClick={() => setIsStationManagerOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div
              className="station-manager-body"
              style={{
                display: "grid",
                gridTemplateColumns: "1.2fr 1fr",
                gap: "20px",
                padding: "0 20px 20px",
                overflow: "hidden",
                flex: 1,
              }}
            >
              <div
                className="station-list-container"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                }}
              >
                <p className="label">
                  当前场站列表 ({availableStations.length})
                </p>
                <div
                  className="station-list-scroll"
                  style={{
                    flex: 1,
                    overflowY: "auto",
                    border: "1px solid var(--border-color)",
                    borderRadius: "8px",
                    background: "rgba(0,0,0,0.05)",
                  }}
                >
                  {availableStations.map((s) => (
                    <div
                      key={s.name}
                      className="station-row"
                      style={{
                        padding: "8px 12px",
                        borderBottom: "1px solid var(--border-color)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      {editingStationName === s.name ? (
                        <>
                          <input
                            type="text"
                            value={newStationName}
                            onChange={(e) => setNewStationName(e.target.value)}
                            autoFocus
                            onKeyDown={(e) =>
                              e.key === "Enter" &&
                              renameStation(s.name, newStationName)
                            }
                            style={{
                              flex: 1,
                              padding: "4px 8px",
                              borderRadius: "4px",
                              border: "1px solid var(--primary-color)",
                            }}
                          />
                          <div
                            className="station-actions"
                            style={{ display: "flex", gap: "8px" }}
                          >
                            <button
                              onClick={() =>
                                renameStation(s.name, newStationName)
                              }
                              title="保存"
                            >
                              <Check size={16} style={{ color: "#34a853" }} />
                            </button>
                            <button
                              onClick={() => setEditingStationName(null)}
                              title="取消"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              gap: "2px",
                              flex: 1,
                            }}
                          >
                            <span style={{ fontSize: "13px", fontWeight: 600 }}>
                              {s.name}
                            </span>
                            <span style={{ fontSize: "11px", opacity: 0.6 }}>
                              {s.region || "未设区域"} | {s.lon?.toFixed(4)},{" "}
                              {s.lat?.toFixed(4)}
                            </span>
                          </div>
                          <div
                            className="station-actions"
                            style={{ display: "flex", gap: "8px" }}
                          >
                            <button
                              onClick={() => {
                                setEditingStationName(s.name);
                                setNewStationName(s.name);
                              }}
                              title="重命名场站"
                            >
                              <FilePen size={14} />
                            </button>
                            <button
                              onClick={() => deleteStation(s.name)}
                              title="删除场站"
                            >
                              <Trash2 size={14} style={{ color: "#ff4d4f" }} />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <div
                className="station-import-container"
                style={{ display: "flex", flexDirection: "column" }}
              >
                <p className="label">批量导入/配置 (粘贴文本)</p>
                <p
                  style={{
                    fontSize: "11px",
                    opacity: 0.7,
                    marginBottom: "8px",
                  }}
                >
                  格式：场站,经度,纬度,区域
                  <br />
                  (支持以逗号或制表符分隔)
                </p>
                <textarea
                  placeholder="峙书,107.28,22.12,宁明..."
                  value={stationBatchInput}
                  onChange={(e) => setStationBatchInput(e.target.value)}
                  style={{
                    width: "100%",
                    flex: 1,
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "8px",
                    padding: "10px",
                    fontSize: "12px",
                    color: "#fff",
                    resize: "none",
                    fontFamily: "monospace",
                  }}
                />
                <button
                  className="premium-button"
                  onClick={importStations}
                  style={{ width: "100%", marginTop: "10px" }}
                >
                  确认导入/更新
                </button>
                <button
                  className="text-action-btn-mini"
                  onClick={exportStationsCSV}
                  style={{
                    width: "100%",
                    marginTop: "8px",
                    justifyContent: "center",
                    border: "1px solid rgba(255,255,255,0.1)",
                    padding: "8px",
                  }}
                >
                  <Download size={14} style={{ marginRight: "6px" }} />
                  导出场站库为 CSV
                </button>
                <p
                  style={{
                    fontSize: "10px",
                    opacity: 0.5,
                    marginTop: "8px",
                    textAlign: "center",
                  }}
                >
                  * 名称相同将自动覆盖原有配置
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {isPasteModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel">
            <div className="modal-header">
              <h3>粘贴数据导入</h3>
              <button onClick={() => setIsPasteModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <textarea
              className="paste-area"
              placeholder="在此处粘贴您的数据..."
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
            />
            <div className="modal-actions">
              <button onClick={() => setIsPasteModalOpen(false)}>取消</button>
              <button className="premium-button" onClick={handlePasteSubmit}>
                确认导入
              </button>
            </div>
          </div>
        </div>
      )}
      {isLogModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content log-modal large-glass">
            <div className="modal-header">
              <div className="header-left">
                <Activity size={20} className="pulse-icon" />
                <h3>系统运行日志</h3>
                <div className="log-type-tabs">
                  <button
                    className={logType === "access" ? "active" : ""}
                    onClick={() => {
                      setLogSearchTerm("");
                      fetchAccessLogs("access");
                    }}
                  >
                    访问
                  </button>
                  <button
                    className={logType === "error" ? "active" : ""}
                    onClick={() => {
                      setLogSearchTerm("");
                      fetchAccessLogs("error");
                    }}
                  >
                    告警
                  </button>
                </div>
              </div>
              <div className="header-actions">
                <div className="search-box-mini">
                  <input
                    type="text"
                    placeholder="搜索日志内容..."
                    value={logSearchTerm}
                    onChange={(e) => setLogSearchTerm(e.target.value)}
                  />
                </div>
                <button
                  className="icon-btn-text"
                  onClick={exportLogs}
                  title="导出当前日志"
                >
                  <Download size={16} /> 导出
                </button>
                <button
                  className="icon-btn"
                  onClick={() => setIsLogModalOpen(false)}
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="log-area coder-style">
              {accessLogs
                .filter((log) =>
                  log.toLowerCase().includes(logSearchTerm.toLowerCase()),
                )
                .map((log, i) => (
                  <div
                    key={i}
                    className={`log-line ${log.includes("ERROR") ? "error-line" : ""}`}
                  >
                    {log}
                  </div>
                ))}
              {accessLogs.length === 0 && (
                <div className="empty-mini">暂无当前类型的日志记录</div>
              )}
            </div>
          </div>
        </div>
      )}
      {isDataEditorOpen && (
        <div className="modal-overlay">
          <div className="modal-content log-modal large-glass">
            <div className="modal-header">
              <h3>编辑序列源数据</h3>
              <button
                className="icon-btn"
                onClick={() => setIsDataEditorOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <div
              className="editor-top-fields"
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "20px",
                padding: "0 20px",
                marginBottom: "15px",
              }}
            >
              <div>
                <p className="label">系列显示名称</p>
                <input
                  type="text"
                  className="styled-select"
                  value={editingSeriesName}
                  onChange={(e) => setEditingSeriesName(e.target.value)}
                />
              </div>
              <div>
                <p className="label">核心指标名称 (影响坐标轴分组)</p>
                <input
                  type="text"
                  className="styled-select"
                  value={editingMetricName}
                  onChange={(e) => setEditingMetricName(e.target.value)}
                />
              </div>
            </div>
            <p
              className="label"
              style={{ padding: "0 20px", marginBottom: "10px" }}
            >
              源数据点调整 (JSON 格式)
            </p>
            <textarea
              className="paste-area coder-style"
              style={{
                height: "400px",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
              value={editingDataText}
              onChange={(e) => setEditingDataText(e.target.value)}
            />
            <div className="modal-actions" style={{ padding: "20px" }}>
              <button onClick={() => setIsDataEditorOpen(false)}>取消</button>
              <button className="premium-button" onClick={saveEditedData}>
                应用修改
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getUserColor(index, metricName = "") {
  // 定义核心指标与其对应的固定颜色 (电力工业标准方案)
  // 注意：使用数组以确保匹配顺序，优先匹配更具体的关键词
  const fixedColorMap = [
    { key: "历史辐照度", color: "#a855f7" }, // 紫色 - 区别于实时辐照度
    { key: "A3主站", color: "#06b6d4" }, // 青色 - 区别于普通可用
    { key: "主站可用", color: "#06b6d4" },
    { key: "短波辐射", color: "#f97316" }, // 深橙色
    { key: "AGC", color: "#ef4444" }, // 红色
    { key: "指令", color: "#ef4444" },
    { key: "出清", color: "#db2777" }, // 玫红
    { key: "预测", color: "#20c997" }, // 碧绿
    { key: "超短期", color: "#20c997" },

    // 通用后缀匹配
    { key: "实际功率", color: "#3b82f6" }, // 亮蓝
    { key: "可用", color: "#22c55e" }, // 纯绿
    { key: "理论", color: "#0ea5e9" }, // 天蓝
    { key: "辐照", color: "#ffc107" }, // 金黄 (最后匹配，作为辐照度兜底)
    { key: "价格", color: "#8b5cf6" }, // 蓝紫
    { key: "负荷", color: "#f59e0b" }, // 琥珀色
  ];

  if (metricName) {
    for (const { key, color } of fixedColorMap) {
      if (metricName.includes(key)) return color;
    }
  }

  // 专业高对比度色板 (适配多场站、多指标叠加)
  const colors = [
    "#2c7be5",
    "#f5803e",
    "#27b768",
    "#d63384",
    "#6610f2",
    "#0dcaf0",
    "#ffc107",
    "#fd7e14",
    "#20c997",
    "#e83e8c",
    "#6f42c1",
    "#198754",
    "#dc3545",
    "#52616b",
    "#7d5a50",
    "#00ffab",
    "#ff4d4d",
    "#007bff",
    "#6c757d",
    "#17a2b8",
  ];
  return colors[index % colors.length];
}

export default App;

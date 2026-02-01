/**
 * Chart Studio - 饼图/环形图模块
 * 基于 Chart.js 实现，支持自定义颜色、数值、样式
 */

const COLOR_PALETTE = [
  "#6366F1",
  "#22C55E",
  "#F59E0B",
  "#EF4444",
  "#06B6D4",
  "#8B5CF6",
  "#EC4899",
  "#14B8A6",
  "#F97316",
  "#84CC16",
  "#3B82F6",
  "#A855F7",
];

const DEFAULT_DATA = [
  { label: "项目 A", value: 35, color: COLOR_PALETTE[0] },
  { label: "项目 B", value: 25, color: COLOR_PALETTE[1] },
  { label: "项目 C", value: 20, color: COLOR_PALETTE[2] },
  { label: "项目 D", value: 15, color: COLOR_PALETTE[3] },
  { label: "项目 E", value: 5, color: COLOR_PALETTE[4] },
];

export class PieChart {
  constructor(canvasId, app) {
    this.canvasId = canvasId;
    this.app = app;
    this.chart = null;
    this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));

    // 配置选项
    this.options = {
      type: "pie",
      cutout: 0,
      showLegend: true,
      legendPosition: "bottom", // top, bottom, left, right, inside
      rotation: 0,
      showValues: true,
      showPercentage: true,
      unit: "",
      showFloatingLabels: true,
      floatingLabelFontSize: 13,
      floatingLabelPadding: 8,
      floatingLabelBgColor: "#1E293B",
      floatingLabelBgOpacity: 0.9,
      textColor: this.app.getTheme() === "dark" ? "#F8FAFC" : "#0F172A",
    };

    this.init();
  }

  init() {
    this.createChart();
    this.renderDataList();
    this.bindEvents();
  }

  createChart() {
    const ctx = document.getElementById(this.canvasId);
    if (!ctx) return;

    const isDark = this.app.getTheme() === "dark";
    const defaultTextColor = isDark ? "#F8FAFC" : "#0F172A";
    const activeTextColor = this.options.textColor || defaultTextColor;

    // 图例配置
    const isInside = this.options.legendPosition === "inside";
    const legendConfig = {
      display: this.options.showLegend,
      position: isInside ? "chartArea" : this.options.legendPosition,
      labels: {
        color: isInside
          ? "#FFFFFF"
          : this.options.textColor || defaultTextColor,
        usePointStyle: true,
        pointStyle: "circle",
        font: { size: 12 },
      },
    };

    // 内部图例样式调节
    if (isInside) {
      legendConfig.backgroundColor = "rgba(0, 0, 0, 0.6)";
      legendConfig.padding = 10;
      legendConfig.borderRadius = 8;
    }

    const hexToRgba = (hex, alpha) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };

    const datalabelsConfig = {
      display: (ctx) => {
        return this.options.showFloatingLabels;
      },
      backgroundColor: hexToRgba(this.options.floatingLabelBgColor, this.options.floatingLabelBgOpacity),
      borderColor: "rgba(255, 255, 255, 0.1)",
      borderWidth: 1,
      borderRadius: 6,
      padding: {
        top: this.options.floatingLabelPadding,
        bottom: this.options.floatingLabelPadding,
        left: this.options.floatingLabelPadding * 1.5,
        right: this.options.floatingLabelPadding * 1.5,
      },
      color: "#FFFFFF", // 始终使用白色文字以配合深色底
      font: {
        weight: "bold",
        size: this.options.floatingLabelFontSize,
        family: "'Fira Sans', sans-serif",
      },
      textAlign: "left",
      formatter: (value, ctx) => {
        const results = [];
        const label = ctx.chart.data.labels[ctx.dataIndex];

        // 第一行：标签
        results.push(`${label}`);

        // 第二行：数值/百分比（去掉色块）
        if (this.options.showValues || this.options.showPercentage) {
            let valStr = "";
            if (this.options.showValues) {
                valStr += value;
                if (this.options.unit) valStr += ` ${this.options.unit}`;
            }
            
            if (this.options.showPercentage) {
                const total = ctx.dataset.data.reduce((acc, data) => acc + data, 0);
                const percentage = ((value * 100) / total).toFixed(1) + "%";
                if (this.options.showValues) valStr += ` (${percentage})`;
                else valStr += percentage;
            }
            results.push(valStr);
        }

        return results.join("\n");
      },
      anchor: "center",
      align: "center",
      offset: 0,
      listeners: {
        enter: (ctx) => {
          ctx.active = true;
          return true;
        },
        leave: (ctx) => {
          ctx.active = false;
          return true;
        },
      },
    };

    this.chart = new Chart(ctx, {
      type: this.options.type,
      data: {
        labels: this.data.map((d) => d.label),
        datasets: [
          {
            data: this.data.map((d) => d.value),
            backgroundColor: this.data.map((d) => d.color),
            borderColor: isDark ? "#0F172A" : "#FFFFFF",
            borderWidth: 2,
            hoverOffset: 15,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        rotation: this.options.rotation,
        cutout: `${this.options.cutout}%`,
        plugins: {
          legend: legendConfig,
          datalabels: datalabelsConfig,
          tooltip: {
            enabled: true,
            backgroundColor: isDark
              ? "rgba(30, 41, 59, 0.95)"
              : "rgba(255, 255, 255, 0.95)",
            titleColor: defaultTextColor,
            bodyColor: defaultTextColor,
            padding: 12,
          },
        },
      },
      plugins: [ChartDataLabels],
    });
  }

  renderDataList() {
    const container = document.getElementById("pie-data-list");
    if (!container) return;
    container.innerHTML = "";
    this.data.forEach((item, index) => {
      const itemEl = document.createElement("div");
      itemEl.className = "data-item";
      itemEl.innerHTML = `
                <input type="color" class="color-picker" value="${item.color}" data-index="${index}">
                <input type="text" class="label-input" value="${item.label}" data-index="${index}" placeholder="标签">
                <input type="number" class="value-input" value="${item.value}" data-index="${index}" min="0" step="1">
                <button class="delete-btn" data-index="${index}">×</button>
            `;
      container.appendChild(itemEl);
    });
  }

  bindEvents() {
    const dataList = document.getElementById("pie-data-list");
    const addBtn = document.getElementById("btn-add-pie-item");

    if (dataList) {
      dataList.addEventListener("input", (e) => {
        const index = parseInt(e.target.dataset.index);
        if (isNaN(index)) return;
        if (e.target.classList.contains("color-picker"))
          this.data[index].color = e.target.value;
        else if (e.target.classList.contains("label-input"))
          this.data[index].label = e.target.value;
        else if (e.target.classList.contains("value-input"))
          this.data[index].value = parseFloat(e.target.value) || 0;
        this.updateChart();
      });
      dataList.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-btn"))
          this.removeDataItem(parseInt(e.target.dataset.index));
      });
    }
    if (addBtn) addBtn.addEventListener("click", () => this.addDataItem());

    // Controls
    const styleType = document.getElementById("pie-style-type");
    const cutoutSlider = document.getElementById("pie-cutout");
    const rotationSlider = document.getElementById("pie-rotation");
    const legendCheckbox = document.getElementById("pie-show-legend");
    const legendPosSelect = document.getElementById("pie-legend-position");
    const valueCheckbox = document.getElementById("pie-show-values");
    const percentCheckbox = document.getElementById("pie-show-percentage");
    const textColorInput = document.getElementById("pie-text-color");

    if (styleType) {
      styleType.addEventListener("change", (e) => {
        this.options.type = e.target.value;
        this.options.cutout = e.target.value === "doughnut" ? 50 : 0;
        if (cutoutSlider) {
          cutoutSlider.value = this.options.cutout;
          document.getElementById("pie-cutout-value").textContent =
            `${this.options.cutout}%`;
        }
        this.recreateChart();
      });
    }

    if (cutoutSlider) {
      cutoutSlider.addEventListener("input", (e) => {
        this.options.cutout = parseInt(e.target.value);
        document.getElementById("pie-cutout-value").textContent =
          `${this.options.cutout}%`;
        this.chart.options.cutout = `${this.options.cutout}%`;
        this.chart.update();
      });
    }

    if (rotationSlider) {
      rotationSlider.addEventListener("input", (e) => {
        this.options.rotation = parseInt(e.target.value);
        document.getElementById("pie-rotation-value").textContent =
          `${this.options.rotation}°`;
        this.chart.options.rotation = this.options.rotation;
        this.chart.update();
      });
    }

    if (legendCheckbox) {
      legendCheckbox.addEventListener("change", (e) => {
        this.options.showLegend = e.target.checked;
        this.recreateChart();
      });
    }

    if (legendPosSelect) {
      legendPosSelect.addEventListener("change", (e) => {
        this.options.legendPosition = e.target.value;
        this.recreateChart();
      });
    }

    if (valueCheckbox) {
      valueCheckbox.addEventListener("change", (e) => {
        this.options.showValues = e.target.checked;
        this.recreateChart();
      });
    }

    if (percentCheckbox) {
      percentCheckbox.addEventListener("change", (e) => {
        this.options.showPercentage = e.target.checked;
        this.recreateChart();
      });
    }

    const unitInput = document.getElementById("pie-unit");
    if (unitInput) {
      unitInput.addEventListener("input", (e) => {
        this.options.unit = e.target.value;
        this.recreateChart();
      });
    }

    const floatingToggle = document.getElementById("pie-show-floating");
    if (floatingToggle) {
      floatingToggle.addEventListener("change", (e) => {
        this.options.showFloatingLabels = e.target.checked;
        this.recreateChart();
      });
    }

    const fontSizeSlider = document.getElementById("pie-label-font-size");
    if (fontSizeSlider) {
      fontSizeSlider.addEventListener("input", (e) => {
        this.options.floatingLabelFontSize = parseInt(e.target.value);
        document.getElementById("pie-label-font-size-val").textContent =
          `${this.options.floatingLabelFontSize}px`;
        this.recreateChart();
      });
    }

    const paddingSlider = document.getElementById("pie-label-padding");
    if (paddingSlider) {
      paddingSlider.addEventListener("input", (e) => {
        this.options.floatingLabelPadding = parseInt(e.target.value);
        document.getElementById("pie-label-padding-val").textContent =
          `${this.options.floatingLabelPadding}px`;
        this.recreateChart();
      });
    }

    const labelBgColorInput = document.getElementById("pie-label-bg-color");
    if (labelBgColorInput) {
      labelBgColorInput.addEventListener("input", (e) => {
        this.options.floatingLabelBgColor = e.target.value;
        this.recreateChart();
      });
    }

    const labelBgOpacitySlider = document.getElementById("pie-label-bg-opacity");
    if (labelBgOpacitySlider) {
      labelBgOpacitySlider.addEventListener("input", (e) => {
        this.options.floatingLabelBgOpacity = parseFloat(e.target.value) / 100;
        document.getElementById("pie-label-bg-opacity-val").textContent =
          `${e.target.value}%`;
        this.recreateChart();
      });
    }

    if (textColorInput) {
      textColorInput.addEventListener("input", (e) => {
        this.options.textColor = e.target.value;
        this.recreateChart();
      });
    }
  }

  addDataItem() {
    const colorIndex = this.data.length % COLOR_PALETTE.length;
    this.data.push({
      label: `项目 ${String.fromCharCode(65 + this.data.length)}`,
      value: 10,
      color: COLOR_PALETTE[colorIndex],
    });
    this.renderDataList();
    this.updateChart();
  }

  removeDataItem(index) {
    if (this.data.length <= 1) return;
    this.data.splice(index, 1);
    this.renderDataList();
    this.updateChart();
  }

  updateChart() {
    if (!this.chart) return;
    this.chart.data.labels = this.data.map((d) => d.label);
    this.chart.data.datasets[0].data = this.data.map((d) => d.value);
    this.chart.data.datasets[0].backgroundColor = this.data.map((d) => d.color);
    this.chart.update();
    if (this.app.saveToLocalStorage) this.app.saveToLocalStorage();
  }

  recreateChart() {
    if (this.chart) this.chart.destroy();
    this.createChart();
  }

  reset() {
    this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));
    this.options = {
      type: "pie",
      cutout: 0,
      showLegend: true,
      legendPosition: "bottom",
      rotation: 0,
      showValues: false,
      showPercentage: true,
      textColor: this.app.getTheme() === "dark" ? "#F8FAFC" : "#0F172A",
    };
    this.renderDataList();
    this.recreateChart();
  }

  setData(newData) {
    this.data = newData.map((item, index) => ({
      label: item.label || `项目 ${index + 1}`,
      value: parseFloat(item.value) || 0,
      color: item.color || COLOR_PALETTE[index % COLOR_PALETTE.length],
    }));
    this.renderDataList();
    this.updateChart();
  }

  getData() {
    return this.data;
  }
  updateTheme() {
    this.options.textColor =
      this.app.getTheme() === "dark" ? "#F8FAFC" : "#0F172A";
    const textColorInput = document.getElementById("pie-text-color");
    if (textColorInput) textColorInput.value = this.options.textColor;
    this.recreateChart();
  }
  onActivate() {
    if (this.chart) this.chart.resize();
  }
  getCanvas() {
    return document.getElementById(this.canvasId);
  }
}

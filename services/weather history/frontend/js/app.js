/**
 * 主应用逻辑
 * 处理用户交互和数据展示
 */

const appState = {
  cities: [],
  fields: {},
  currentData: null,
  selectedCities: [],
  selectedFields: [],
  multiCityMode: false,
  filterCity: "all",
  filterDate: "all",
  citySelector: null, // History Page Multi-Selector
  liveCitySelector: null, // Live Page Single-Selector
};

// Export appState to global scope
window.appState = appState;
window.loadCities = loadCities; // Ensure loadCities is also global

// WMO 天气代码映射
const weatherCodeMap = {
  0: { name: "晴朗", icon: "☀️" },
  1: { name: "晴到多云", icon: "🌤️" },
  2: { name: "多云", icon: "⛅" },
  3: { name: "阴天", icon: "☁️" },
  45: { name: "雾", icon: "🌫️" },
  48: { name: "沉积雾", icon: "🌫️" },
  51: { name: "小毛毛雨", icon: "🌦️" },
  53: { name: "毛毛雨", icon: "🌦️" },
  55: { name: "大毛毛雨", icon: "🌦️" },
  61: { name: "小雨", icon: "🌧️" },
  63: { name: "中雨", icon: "🌧️" },
  65: { name: "大雨", icon: "🌧️" },
  71: { name: "小雪", icon: "🌨️" },
  73: { name: "中雪", icon: "🌨️" },
  75: { name: "大雪", icon: "🌨️" },
  80: { name: "阵雨", icon: "🌦️" },
  81: { name: "中阵雨", icon: "🌦️" },
  82: { name: "大阵雨", icon: "🌧️" },
  95: { name: "雷阵雨", icon: "⛈️" },
};

/**
 * 初始化应用
 */
async function initApp() {
  console.log("初始化应用...");

  try {
    // 加载城市列表
    await loadCities();

    // 加载字段列表
    await loadFields();

    // 绑定事件
    bindEvents();

    // 启动健康检查
    startHealthCheck();

    // 初始化日期限制
    initDateConstraints();

    // 为实况页渲染城市 (New - Init)
    // renderLiveCitySelector() is now handled within loadCities via instance init

    // 启动网页时间更新
    updateWebTime();

    // 初始化数据管理模块
    if (typeof window.initDataManagement === "function") {
      window.initDataManagement();
    }

    console.log("应用初始化完成");
  } catch (error) {
    console.error("应用初始化失败:", error);
    showError("应用初始化失败，请刷新页面重试");
  }
}

/**
 * 切换城市选择器模式
 */
window.switchSelectorMode = function (context, mode) {
  console.log(`Switching mode for ${context} to ${mode}`);
  const selector =
    context === "query" ? appState.citySelector : appState.liveCitySelector;
  if (!selector) return;

  selector.setOptions({ mode: mode });

  // 更新按钮状态
  // Use more specific selector to avoid toggle conflicts if multiple exist
  const panel =
    context === "query"
      ? document.getElementById("query-panel")
      : document.getElementById("main-tab-live");
  const toggle = panel ? panel.querySelector(".mode-toggle") : null;

  if (toggle) {
    toggle.querySelectorAll("button").forEach((btn) => {
      if (btn.dataset.modeBtn === mode) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  // Special logic for live selector
  if (context === "live") {
    const liveSelectMode = document.getElementById("liveSelectMode");
    if (liveSelectMode) liveSelectMode.value = mode;
  }
};

/**
 * 加载城市列表
 */
/**
 * 加载城市列表
 */
async function loadCities() {
  try {
    const response = await api.getCities();
    appState.cities = response.data;

    // 1. 初始化历史查询多选城市选择器 (默认多选比对)
    appState.citySelector = new CitySelector("citySelect", {
      mode: "multi",
      renderMode: "tags",
      showSearch: true,
      onSelect: (selectedIds) => updateSelectedCities(selectedIds),
    });
    appState.citySelector.setCities(appState.cities);

    // 2. 初始化实况城市选择器 (默认单选)
    appState.liveCitySelector = new CitySelector("liveCitySelect", {
      mode: "single",
      renderMode: "tags", // 保持一致，使用 Tag 入口
      showSearch: true,
      onSelect: (cityIds) => {
        // 单选模式下立即触发，多选模式下由确认按钮触发
        if (appState.liveCitySelector.options.mode === "single") {
          handleLiveCitySelect(cityIds);
        }
      },
    });
    appState.liveCitySelector.setCities(appState.cities);

    // 3. 绑定实况确认按钮
    const confirmBtn = document.getElementById("confirmLiveCityBtn");
    if (confirmBtn) {
      confirmBtn.onclick = () => {
        console.log("Confirm button clicked (Triggering Load)");
        if (!appState.liveCitySelector) return;

        const selected = Array.from(appState.liveCitySelector.selectedIds);
        if (selected.length === 0) {
          alert("请至少选择一个城市进行加载");
          return;
        }

        handleLiveCitySelect(selected);
      };
    }

    console.log(`加载了 ${appState.cities.length} 个城市`);
  } catch (error) {
    console.error("加载城市列表失败:", error);
    throw error;
  }
}

/**
 * 更新选中的城市列表
 */
function updateSelectedCities(selectedIds) {
  // If called directly with IDs, update state. Otherwise read from state (legacy fallback)
  if (selectedIds) {
    appState.selectedCities = Array.isArray(selectedIds)
      ? selectedIds
      : [selectedIds];
  } else if (appState.citySelector) {
    appState.selectedCities = Array.from(appState.citySelector.selectedIds);
  } else {
    // Fallback for safety
    appState.selectedCities = [];
  }

  appState.multiCityMode = appState.selectedCities.length > 1;

  // 更新UI提示
  const cityCount = appState.selectedCities.length;
  const queryBtn = document.getElementById("queryBtn");
  if (cityCount > 0) {
    queryBtn.textContent =
      cityCount > 1 ? `查询并对比 ${cityCount} 个城市` : "查询数据";
  } else {
    queryBtn.textContent = "查询数据";
  }

  console.log(`已选择 ${cityCount} 个城市:`, appState.selectedCities);
}

/**
 * 加载字段列表
 */
async function loadFields() {
  try {
    const response = await api.getFields();
    appState.fields = response.data.available_fields;
    const defaultFields = response.data.default_fields;

    const fieldSelector = document.getElementById("fieldSelector");
    fieldSelector.innerHTML = "";

    // 按类别组织字段
    Object.entries(appState.fields).forEach(([category, fields]) => {
      Object.entries(fields).forEach(([fieldKey, fieldInfo]) => {
        const isDefault = defaultFields.includes(fieldKey);

        const div = document.createElement("div");
        div.className = "field-checkbox";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = `field_${fieldKey}`;
        checkbox.value = fieldKey;
        checkbox.checked = isDefault;

        const label = document.createElement("label");
        label.htmlFor = `field_${fieldKey}`;
        label.textContent = `${fieldInfo.name} (${fieldInfo.unit})`;

        div.appendChild(checkbox);
        div.appendChild(label);
        fieldSelector.appendChild(div);

        if (isDefault) {
          appState.selectedFields.push(fieldKey);
        }
      });
    });

    console.log(
      `加载了字段列表，默认选中 ${appState.selectedFields.length} 个字段`,
    );
  } catch (error) {
    console.error("加载字段列表失败:", error);
    throw error;
  }
}

/**
 * 绑定事件
 */
function bindEvents() {
  // 查询按钮
  document.getElementById("queryBtn").addEventListener("click", handleQuery);

  // 导出按钮
  document
    .getElementById("exportExcelBtn")
    .addEventListener("click", () => handleExport("excel"));
  document
    .getElementById("exportCsvBtn")
    .addEventListener("click", () => handleExport("csv"));

  // 字段选择
  document
    .querySelectorAll('#fieldSelector input[type="checkbox"]')
    .forEach((checkbox) => {
      checkbox.addEventListener("change", handleFieldChange);
    });

  // 快捷日期按钮
  document.querySelectorAll(".quick-dates button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const days = parseInt(e.target.dataset.days);
      setQuickDate(days);
    });
  });

  // 导航栏主标签切换
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const tabName = this.dataset.mainTab;
      handleMainTabSwitch(tabName);
    });
  });

  // 导航栏点击效果
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", function () {
      document
        .querySelectorAll(".nav-link")
        .forEach((l) => l.classList.remove("active"));
      this.classList.add("active");
    });
  });

  // 停止服务按钮已移除 (Item 68)

  // 筛选器事件
  document
    .getElementById("cityFilter")
    .addEventListener("change", handleFilterChange);
  document
    .getElementById("dateFilter")
    .addEventListener("change", handleFilterChange);
  document.getElementById("resetFilterBtn").addEventListener("click", () => {
    document.getElementById("cityFilter").value = "all";
    document.getElementById("dateFilter").value = "all";
    handleFilterChange();
  });

  // 天气实况刷新按钮
  const refreshLiveBtn = document.getElementById("refreshLiveBtn");
  if (refreshLiveBtn) {
    refreshLiveBtn.addEventListener("click", () => {
      if (appState.currentLiveCityId) {
        handleLiveCitySelect(appState.currentLiveCityId);
      }
    });
  }

  // === 预测查询页面事件绑定 ===
  initForecastQueryPage();
}

/**
 * 处理主标签切换
 */
function handleMainTabSwitch(tabName) {
  // 更新导航按钮状态
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    if (btn.dataset.mainTab === tabName) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // 更新各面板显示
  document.querySelectorAll(".main-tab-content").forEach((content) => {
    if (content.id === `main-tab-${tabName}`) {
      content.classList.add("active");
    } else {
      content.classList.remove("active");
    }
  });

  console.log(`切换到主标签: ${tabName}`);

  // 如果切换到实况标签且没有选过城市，默认选第一个
  if (
    tabName === "live" &&
    !appState.currentLiveCityId &&
    appState.cities.length > 0
  ) {
    handleLiveCitySelect(appState.cities[0].id);
  }
}

/**
 * 设置快捷日期
 */
function setQuickDate(days) {
  const end = new Date();
  end.setDate(end.getDate() - 1); // 结束是昨天

  const start = new Date();
  start.setDate(start.getDate() - days);

  document.getElementById("endDate").value = end.toISOString().split("T")[0];
  document.getElementById("startDate").value = start
    .toISOString()
    .split("T")[0];
}

/**
 * 初始化日期限制 (默认日期为昨天，Item 13 & 16)
 */
function initDateConstraints() {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const maxDate = yesterday.toISOString().split("T")[0];

  // 获取所有日期输入框
  const dateInputs = [
    "startDate",
    "endDate",
    "downloadStartDate",
    "downloadEndDate",
    "checkStartDate",
    "checkEndDate",
  ];

  dateInputs.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.setAttribute("max", maxDate);
      // 默认值设为昨天 (Item 13)
      if (!el.value || el.value > maxDate) {
        el.value = maxDate;
      }
    }
  });
}

/**
 * 启动健康检查
 */
function startHealthCheck() {
  const statusDot = document.querySelector(".status-dot");
  const statusText = document.querySelector(".status-text");
  const queryBtn = document.getElementById("queryBtn");
  const exportBtns = [
    document.getElementById("exportExcelBtn"),
    document.getElementById("exportCsvBtn"),
  ];

  const check = async () => {
    const isOnline = await api.ping();
    if (isOnline) {
      statusDot.className = "status-dot online";
      if (statusText) statusText.textContent = "后端连接正常";
      if (queryBtn) queryBtn.disabled = false;
      exportBtns.forEach((btn) => {
        if (btn) btn.disabled = false;
      });
    } else {
      statusDot.className = "status-dot offline";
      if (statusText) statusText.textContent = "连接已断开";
      if (queryBtn) queryBtn.disabled = true;
      exportBtns.forEach((btn) => {
        if (btn) btn.disabled = true;
      });
    }
  };

  // 初始检查
  check();
  // 每3秒检查一次
  setInterval(check, 3000);
}

/**
 * 更新页面右上角的时间显示
 */
function updateWebTime() {
  const timeEl = document.getElementById("webTimeDisplay");
  if (!timeEl) return;

  const update = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const seconds = String(now.getSeconds()).padStart(2, "0");

    timeEl.textContent = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  update();
  setInterval(update, 1000);
}

/**
 * 处理字段选择变化
 */
function handleFieldChange(event) {
  const fieldKey = event.target.value;

  if (event.target.checked) {
    if (!appState.selectedFields.includes(fieldKey)) {
      appState.selectedFields.push(fieldKey);
    }
  } else {
    appState.selectedFields = appState.selectedFields.filter(
      (f) => f !== fieldKey,
    );
  }
}

/**
 * 处理查询
 */
async function handleQuery() {
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;

  const validation = CommonUtils.validateDateRange(startDate, endDate);
  if (appState.selectedCities.length === 0) {
    showError("请至少选择一个城市");
    return;
  }

  if (!validation.valid) {
    showError(validation.message);
    return;
  }

  if (appState.selectedFields.length === 0) {
    showError("请至少选择一个数据字段");
    return;
  }

  // 显示加载状态
  showLoading(true);
  hideDataDisplay();

  try {
    if (appState.multiCityMode) {
      // 多城市对比模式
      const response = await api.compareCities({
        city_ids: appState.selectedCities,
        start_date: startDate,
        end_date: endDate,
        fields: appState.selectedFields,
      });

      appState.currentData = response.data;

      // 显示对比数据
      displayComparisonData(response.data);
    } else {
      // 单城市模式
      const cityId = appState.selectedCities[0];
      const response = await api.queryWeather({
        city_id: cityId,
        start_date: startDate,
        end_date: endDate,
        fields: appState.selectedFields,
      });

      appState.currentData = response.data;

      const cityName =
        response.data.city_name ||
        appState.cities.find((c) => c.id == cityId)?.name ||
        "";
      displayData(response.data, cityName);
    }

    // 启用导出按钮
    document.getElementById("exportExcelBtn").disabled = false;
    document.getElementById("exportCsvBtn").disabled = false;

    // 初始化筛选器
    populateFilters();

    console.log(`查询成功`);
  } catch (error) {
    console.error("查询失败:", error);
    showError("查询失败: " + error.message);
  } finally {
    showLoading(false);
  }
}

/**
 * 处理导出
 */
async function handleExport(format) {
  if (!appState.currentData) {
    showError("没有可导出的数据");
    return;
  }

  const cityId = appState.selectedCities[0]; // 修复：使用选中列表中的第一个
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;

  if (!cityId) {
    showError("请先查询数据后再尝试导出");
    return;
  }

  try {
    await api.exportWeather(
      {
        city_id: cityId,
        start_date: startDate,
        end_date: endDate,
        fields: appState.selectedFields,
      },
      format,
    );

    console.log(`导出${format.toUpperCase()}成功`);
  } catch (error) {
    console.error("导出失败:", error);
    showError("导出失败: " + error.message);
  }
}

/**
 * 显示数据
 */
function displayData(data, cityName = "") {
  // 如果没有传入 cityName，尝试从 data 对象中获取 (Item 30)
  if (!cityName && data && data.city_name) {
    cityName = data.city_name;
  }

  // 处理过滤后的数据
  const filteredRecords = applyLocalFilters(data.records);

  // 显示统计卡片
  displayStatsCards(data.summary);

  // 显示图表
  displayCharts(filteredRecords, cityName);

  // 显示数据表格
  displayDataTable(filteredRecords);

  // 显示数据展示区
  showDataDisplay();
}

/**
 * 显示统计卡片
 */
function displayStatsCards(summary) {
  const statsCards = document.getElementById("statsCards");
  statsCards.innerHTML = "";

  // 温度统计
  if (summary.temperature) {
    statsCards.appendChild(
      createStatCard(
        "温度",
        summary.temperature.avg,
        "°C",
        `最高: ${summary.temperature.max}°C, 最低: ${summary.temperature.min}°C`,
        "temperature",
      ),
    );
  }

  // 辐照度统计
  if (summary.solar_radiation) {
    statsCards.appendChild(
      createStatCard(
        "太阳辐射",
        summary.solar_radiation.avg,
        "W/m²",
        `总计: ${summary.solar_radiation.total_mj.toFixed(2)} MJ/m²`,
        "radiation",
      ),
    );
  }

  // 风速统计
  if (summary.wind_speed) {
    statsCards.appendChild(
      createStatCard(
        "风速",
        (summary.wind_speed.avg / 3.6).toFixed(2),
        "m/s",
        `最大: ${(summary.wind_speed.max / 3.6).toFixed(2)} m/s`,
        "wind",
      ),
    );
  }

  // 降水统计
  if (summary.precipitation) {
    statsCards.appendChild(
      createStatCard(
        "降水量",
        summary.precipitation.total,
        "mm",
        `降雨时数: ${summary.precipitation.rainy_hours}小时`,
        "precipitation",
      ),
    );
  }

  // 天气情况统计
  if (summary.weather) {
    const code = summary.weather.most_frequent;
    const weatherInfo = weatherCodeMap[code] || {
      name: `代码 ${code}`,
      icon: "❓",
    };
    statsCards.appendChild(
      createStatCard(
        "主要天气",
        weatherInfo.name,
        "",
        `最频繁出现的状态`,
        "weather",
        weatherInfo.icon,
      ),
    );
  }
}

/**
 * 创建统计卡片
 */
function createStatCard(label, value, unit, details, iconType, customIcon) {
  const card = document.createElement("div");
  card.className = "stat-card";

  const displayValue = typeof value === "number" ? value.toFixed(2) : value;

  card.innerHTML = `
        <div class="stat-card-header">
            <div class="stat-icon ${iconType}">
                ${customIcon || getIconSVG(iconType)}
            </div>
            <div class="stat-label">${label}</div>
        </div>
        <div class="stat-value">
            ${displayValue}
            <span class="stat-unit">${unit}</span>
        </div>
        <div class="stat-details">${details}</div>
    `;

  return card;
}

/**
 * 获取图标SVG
 */
function getIconSVG(type) {
  const icons = {
    temperature:
      '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C10.34 2 9 3.34 9 5v6.17C7.83 11.69 7 13.23 7 15c0 2.76 2.24 5 5 5s5-2.24 5-5c0-1.77-.83-3.31-2-4.83V5c0-1.66-1.34-3-3-3zm0 16c-1.66 0-3-1.34-3-3 0-1.11.61-2.06 1.5-2.58V5c0-.55.45-1 1-1s1 .45 1 1v7.42c.89.52 1.5 1.47 1.5 2.58 0 1.66-1.34 3-3 3z" fill="currentColor"/></svg>',
    radiation:
      '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.39.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z" fill="currentColor"/></svg>',
    wind: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14.5 17c0 1.65-1.35 3-3 3s-3-1.35-3-3h2c0 .55.45 1 1 1s1-.45 1-1-.45-1-1-1H2v-2h9.5c1.65 0 3 1.35 3 3zM19 6.5C19 4.57 17.43 3 15.5 3S12 4.57 12 6.5h2c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5S16.33 8 15.5 8H2v2h13.5c1.93 0 3.5-1.57 3.5-3.5zm-.5 4.5H2v2h16.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5v2c1.93 0 3.5-1.57 3.5-3.5S20.43 11 18.5 11z" fill="currentColor"/></svg>',
    precipitation:
      '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2.69l5.66 5.66c3.12 3.12 3.12 8.19 0 11.31-1.56 1.56-3.61 2.34-5.66 2.34s-4.1-.78-5.66-2.34c-3.12-3.12-3.12-8.19 0-11.31L12 2.69m0-2.69L4.93 6.93c-3.91 3.91-3.91 10.24 0 14.14C6.88 22.95 9.44 24 12 24s5.12-1.05 7.07-3.03c3.91-3.91 3.91-10.24 0-14.14L12 0z" fill="currentColor"/></svg>',
  };
  return icons[type] || "";
}

/**
 * 显示图表
 */
function displayCharts(records, cityName = "") {
  // 限制数据点数量以提升性能
  const maxPoints = 500;
  const step = Math.ceil(records.length / maxPoints);
  const sampledData = records.filter((_, index) => index % step === 0);

  // 更新静态标题 (Item 30)
  updateChartTitles(cityName);

  chartManager.createTemperatureChart(
    "temperatureChart",
    sampledData,
    cityName,
  );
  chartManager.createRadiationChart("radiationChart", sampledData, cityName);
  chartManager.createWindSpeedChart("windSpeedChart", sampledData, cityName);
  chartManager.createPrecipitationChart(
    "precipitationChart",
    sampledData,
    cityName,
  );
}

/**
 * 更新图表区的静态标题
 */
function updateChartTitles(cityName) {
  const titles = {
    temperatureChart: "温度趋势",
    radiationChart: "辐照度分布",
    windSpeedChart: "风速变化",
    precipitationChart: "降水量",
  };

  Object.entries(titles).forEach(([id, baseTitle]) => {
    const chartCard = document.getElementById(id)?.closest(".chart-card");
    if (chartCard) {
      const titleElem = chartCard.querySelector(".chart-title");
      if (titleElem) {
        titleElem.textContent = cityName
          ? `${baseTitle} - ${cityName}`
          : baseTitle;
      }
    }
  });
}

/**
 * 显示数据表格
 */
function displayDataTable(records) {
  const tableHead = document.getElementById("tableHead");
  const tableBody = document.getElementById("tableBody");

  // 清空表格
  tableHead.innerHTML = "";
  tableBody.innerHTML = "";

  if (records.length === 0) {
    return;
  }

  // 创建表头
  const headerRow = document.createElement("tr");
  const keys = Object.keys(records[0]);

  keys.forEach((key) => {
    const th = document.createElement("th");
    th.textContent = getFieldLabel(key);
    headerRow.appendChild(th);
  });

  tableHead.appendChild(headerRow);

  // 创建表格行（限制显示前100条）
  const displayRecords = records.slice(0, 100);

  displayRecords.forEach((record) => {
    const row = document.createElement("tr");

    keys.forEach((key) => {
      const td = document.createElement("td");
      let value = record[key];

      if (value === null || value === undefined) {
        td.textContent = "-";
      } else if (key === "weather_code") {
        const weatherInfo = weatherCodeMap[Math.floor(value)] || {
          name: `代码 ${value}`,
          icon: "",
        };
        td.textContent = `${weatherInfo.icon} ${weatherInfo.name}`;
      } else if (typeof value === "number") {
        td.textContent = value.toFixed(2);
      } else {
        td.textContent = value;
      }

      row.appendChild(td);
    });

    tableBody.appendChild(row);
  });

  if (records.length > 100) {
    const noteRow = document.createElement("tr");
    const noteCell = document.createElement("td");
    noteCell.colSpan = keys.length;
    noteCell.style.textAlign = "center";
    noteCell.style.fontStyle = "italic";
    noteCell.textContent = `显示前100条记录，共${records.length}条记录。请导出查看完整数据。`;
    noteRow.appendChild(noteCell);
    tableBody.appendChild(noteRow);
  }
}

/**
 * 获取字段标签
 */
function getFieldLabel(fieldKey) {
  for (const category of Object.values(appState.fields)) {
    if (category[fieldKey]) {
      return `${category[fieldKey].name} (${category[fieldKey].unit})`;
    }
  }
  return fieldKey;
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
  const loadingIndicator = document.getElementById("loadingIndicator");
  loadingIndicator.style.display = show ? "flex" : "none";
}

/**
 * 显示/隐藏数据展示区
 */
function showDataDisplay() {
  document.getElementById("dataDisplay").style.display = "block";
}

function hideDataDisplay() {
  document.getElementById("dataDisplay").style.display = "none";
}

/**
 * 显示错误消息
 */
function showError(message) {
  alert(message);
}

function displayComparisonData(data) {
  console.log("显示对比数据:", data);

  // 显示对比统计卡片
  displayComparisonStats(data.comparison);

  // 显示对比表格
  displayComparisonTable(data.details);

  // 处理过滤
  const filteredDetails = applyComparisonFilters(data.details);
  if (filteredDetails.length === 1) {
    // 如果只过滤出一个城市，则显示该城市的详细趋势
    displayCharts(filteredDetails[0].hourly_data, filteredDetails[0].city_name);
  } else {
    // 否则显示对比图表
    displayComparisonCharts(filteredDetails);
  }

  // 显示数据展示区
  showDataDisplay();
}

function displayComparisonStats(comparison) {
  const statsCards = document.getElementById("statsCards");
  statsCards.innerHTML = "";

  // 计算城市数量
  const cityCount = Object.keys(comparison).length;

  // 添加核心分析说明卡片
  const headerCard = document.createElement("div");
  headerCard.className = "stat-card comparison-header-card";
  headerCard.style.gridColumn = "1 / -1";
  headerCard.innerHTML = `
        <div class="stat-card-header">
            <div class="stat-label"><strong>多城市对比分析</strong></div>
        </div>
        <div class="stat-details">正在对比 ${cityCount} 个城市的天气数据</div>
    `;
  statsCards.appendChild(headerCard);

  // 为每个城市创建一个独立的行（容器）
  Object.entries(comparison).forEach(([cityName, summary]) => {
    // 创建城市标题分隔符
    const cityTitle = document.createElement("div");
    cityTitle.className = "city-stats-divider";
    cityTitle.style.gridColumn = "1 / -1";
    cityTitle.innerHTML = `<span>${cityName}</span>`;
    statsCards.appendChild(cityTitle);

    if (summary.temperature) {
      statsCards.appendChild(
        createStatCard(
          "平均温度",
          summary.temperature.avg,
          "°C",
          `最高: ${summary.temperature.max}°C, 最低: ${summary.temperature.min}°C`,
          "temperature",
        ),
      );
    }

    if (summary.solar_radiation) {
      statsCards.appendChild(
        createStatCard(
          "太阳辐射",
          summary.solar_radiation.avg,
          "W/m²",
          `总计: ${summary.solar_radiation.total_mj.toFixed(2)} MJ/m²`,
          "radiation",
        ),
      );
    }

    if (summary.wind_speed) {
      statsCards.appendChild(
        createStatCard(
          "风速",
          (summary.wind_speed.avg / 3.6).toFixed(2),
          "m/s",
          `最大: ${(summary.wind_speed.max / 3.6).toFixed(2)} m/s`,
          "wind",
        ),
      );
    }

    if (summary.precipitation) {
      statsCards.appendChild(
        createStatCard(
          "降水量",
          summary.precipitation.total,
          "mm",
          `降雨时间: ${summary.precipitation.rainy_hours}小时`,
          "precipitation",
        ),
      );
    }

    if (summary.weather) {
      const code = summary.weather.most_frequent;
      const weatherInfo = weatherCodeMap[code] || {
        name: `代码 ${code}`,
        icon: "❓",
      };
      statsCards.appendChild(
        createStatCard(
          "主要天气",
          weatherInfo.name,
          "",
          `总体天气状态`,
          "weather",
          weatherInfo.icon,
        ),
      );
    }
  });
}

/**
 * 显示对比图表
 */
function displayComparisonCharts(details) {
  // 准备对比数据
  const citiesData = details.map((city) => ({
    name: city.city_name,
    data: city.hourly_data,
  }));

  // 更新静态标题 (Item 30)
  updateChartTitles("多城市对比");

  // 创建对比图表
  chartManager.createComparisonChart(
    "temperatureChart",
    citiesData,
    "temperature_2m",
    "温度对比",
  );
  chartManager.createComparisonChart(
    "radiationChart",
    citiesData,
    "shortwave_radiation",
    "辐照度对比",
  );
  chartManager.createComparisonChart(
    "windSpeedChart",
    citiesData,
    "wind_speed_10m",
    "风速对比",
  );
  chartManager.createComparisonChart(
    "precipitationChart",
    citiesData,
    "precipitation",
    "降水量对比",
  );
}

/**
 * 显示对比表格
 */
function displayComparisonTable(details) {
  const tableHead = document.getElementById("tableHead");
  const tableBody = document.getElementById("tableBody");

  tableHead.innerHTML = "";
  tableBody.innerHTML = "";

  if (details.length === 0) {
    return;
  }

  // 创建表头
  const headerRow = document.createElement("tr");
  headerRow.innerHTML =
    "<th>城市</th><th>平均温度</th><th>平均辐照度</th><th>平均风速</th><th>总降水量</th>";
  tableHead.appendChild(headerRow);

  // 创建表格行
  details.forEach((city) => {
    const row = document.createElement("tr");

    // 计算统计数据
    const summary = data_analyzer.calculateSummary(city.hourly_data);

    row.innerHTML = `
            <td><strong>${city.city_name}</strong></td>
            <td>${summary.temperature ? summary.temperature.avg.toFixed(2) : "-"} °C</td>
            <td>${summary.solar_radiation ? summary.solar_radiation.avg.toFixed(2) : "-"} W/m²</td>
            <td>${summary.wind_speed ? summary.wind_speed.avg.toFixed(2) : "-"} km/h</td>
            <td>${summary.precipitation ? summary.precipitation.total.toFixed(2) : "-"} mm</td>
        `;

    tableBody.appendChild(row);
  });
}

// 简单的数据分析器（用于对比表格）
const data_analyzer = {
  calculateSummary(records) {
    if (!records || records.length === 0) return {};

    const summary = {};

    // 温度统计
    const temps = records.map((r) => r.temperature_2m).filter((v) => v != null);
    if (temps.length > 0) {
      summary.temperature = {
        avg: temps.reduce((a, b) => a + b, 0) / temps.length,
        max: Math.max(...temps),
        min: Math.min(...temps),
      };
    }

    // 辐照度统计
    const radiation = records
      .map((r) => r.shortwave_radiation)
      .filter((v) => v != null);
    if (radiation.length > 0) {
      summary.solar_radiation = {
        avg: radiation.reduce((a, b) => a + b, 0) / radiation.length,
        total: radiation.reduce((a, b) => a + b, 0),
      };
    }

    // 风速统计
    const windSpeed = records
      .map((r) => r.wind_speed_10m)
      .filter((v) => v != null);
    if (windSpeed.length > 0) {
      summary.wind_speed = {
        avg: windSpeed.reduce((a, b) => a + b, 0) / windSpeed.length,
        max: Math.max(...windSpeed),
      };
    }

    // 降水统计
    const precip = records.map((r) => r.precipitation).filter((v) => v != null);
    if (precip.length > 0) {
      summary.precipitation = {
        total: precip.reduce((a, b) => a + b, 0),
        rainy_hours: precip.filter((p) => p > 0).length,
      };
    }

    return summary;
  },
};

/**
 * 初始化筛选器
 */
function populateFilters() {
  const cityFilter = document.getElementById("cityFilter");
  const dateFilter = document.getElementById("dateFilter");

  // 填充区域/城市
  cityFilter.innerHTML = '<option value="all">所有选定城市</option>';
  if (appState.multiCityMode) {
    appState.selectedCities.forEach((id) => {
      const city = appState.cities.find((c) => c.id === id);
      if (city) {
        const opt = document.createElement("option");
        opt.value = city.name;
        opt.textContent = city.name;
        cityFilter.appendChild(opt);
      }
    });
  }

  // 填充日期
  dateFilter.innerHTML = '<option value="all">所有日期范围</option>';
  const dates = new Set();
  if (appState.multiCityMode) {
    appState.currentData.details.forEach((city) => {
      city.hourly_data.forEach((r) => dates.add(r.datetime.split("T")[0]));
    });
  } else {
    appState.currentData.records.forEach((r) =>
      dates.add(r.datetime.split("T")[0]),
    );
  }

  Array.from(dates)
    .sort()
    .forEach((date) => {
      const opt = document.createElement("option");
      opt.value = date;
      opt.textContent = date;
      dateFilter.appendChild(opt);
    });
}

/**
 * 应用本地过滤逻辑
 */
function applyLocalFilters(records) {
  let filtered = [...records];
  if (appState.filterDate !== "all") {
    filtered = filtered.filter((r) =>
      r.datetime.startsWith(appState.filterDate),
    );
  }
  return filtered;
}

/**
 * 应用对比过滤逻辑
 */
function applyComparisonFilters(details) {
  let filtered = [...details];
  if (appState.filterCity !== "all") {
    filtered = filtered.filter((c) => c.city_name === appState.filterCity);
  }
  if (appState.filterDate !== "all") {
    filtered = filtered.map((c) => ({
      ...c,
      hourly_data: c.hourly_data.filter((r) =>
        r.datetime.startsWith(appState.filterDate),
      ),
    }));
  }
  return filtered;
}

/**
 * 处理过滤变化
 */
function handleFilterChange() {
  appState.filterCity = document.getElementById("cityFilter").value;
  appState.filterDate = document.getElementById("dateFilter").value;

  if (appState.multiCityMode) {
    displayComparisonData(appState.currentData);
  } else {
    displayData(appState.currentData);
  }
}

/**
 * 渲染实况页的城市选择器
 */
// Obsolete renderLiveCitySelector removed

/**
 * 处理实况页城市选择
 */
/**
 * 处理实况页城市选择
 */
async function handleLiveCitySelect(cityIds) {
  console.log("handleLiveCitySelect called with:", cityIds);
  const ids = Array.isArray(cityIds) ? cityIds : [cityIds];
  if (ids.length === 0) {
    console.warn("No cities selected");
    return;
  }

  // Intelligent Mode Detection: If multiple IDs passed, FORCE multi mode.
  // Otherwise trust the selector state or default to single.
  const isMulti =
    ids.length > 1 || appState.liveCitySelector?.options.mode === "multi";
  console.log("Is Multi Mode?", isMulti, "IDs:", ids);

  // UI elements
  const detailDisplay = document.getElementById("liveWeatherDisplay");
  const comparisonDisplay = document.getElementById("liveComparisonDisplay");
  const loading = document.getElementById("liveLoading");

  // Show/Hide containers
  if (detailDisplay) detailDisplay.style.display = "none";
  if (comparisonDisplay) comparisonDisplay.style.display = "none";
  if (loading) loading.style.display = "flex";

  if (!isMulti) {
    // Single Mode: Existing detail view
    const cityId = ids[0];
    appState.currentLiveCityId = cityId;
    try {
      console.log("Fetching single city data for:", cityId);
      const currentResp = await api.getCurrentWeather(cityId);
      renderCurrentWeather(currentResp.data);
      const forecastResp = await api.getForecast(cityId, 7);
      renderForecast(forecastResp.data);

      if (loading) loading.style.display = "none";
      if (detailDisplay) detailDisplay.style.display = "block";
    } catch (error) {
      console.error("获取实况/预报失败:", error);
      if (loading) loading.style.display = "none";
      showError("数据获取失败：" + error.message);
    }
  } else {
    // Multi Mode: Comparison view
    try {
      console.log("Fetching multi city data for:", ids);
      await fetchMultiCityLiveData(ids);
      if (loading) loading.style.display = "none";
      if (comparisonDisplay) comparisonDisplay.style.display = "block";
    } catch (error) {
      console.error("多城市数据对比获取失败:", error);
      if (loading) loading.style.display = "none";
      showError("数据加载失败：" + error.message);
    }
  }
}

/**
 * 获取并渲染多城市实时数据对比
 */
async function fetchMultiCityLiveData(cityIds) {
  const container = document.getElementById("comparisonGrid");
  const displayContainer = document.getElementById("liveComparisonDisplay");

  if (!container) {
    console.error("Critical: #comparisonGrid not found!");
    return;
  }

  console.log(`Starting fetch for cities: ${cityIds}`);
  if (displayContainer) {
    displayContainer.style.display = "block";
    console.log("#liveComparisonDisplay shown");
  }

  container.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:20px;">
      <div class="spinner" style="margin:0 auto 10px auto;"></div>
      <p>正在加载 ${cityIds.length} 个城市的数据...</p>
  </div>`;

  console.log(`Starting fetch for cities: ${cityIds}`);

  try {
    // 1. Set a timeout to prevent infinite hanging
    const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error("请求超时，请检查网络连接")), 15000)
    );

    // 2. Create actual fetch promise
    const fetchPromise = Promise.allSettled(
      cityIds.map((id) => api.getCurrentWeather(id))
    );

    // 3. Race against timeout
    const results = await Promise.race([fetchPromise, timeoutPromise]);

    container.innerHTML = "";

    const successCount = results.filter((r) => r.status === "fulfilled").length;
    console.log(`Fetch complete. Success: ${successCount}/${cityIds.length}`);

    if (successCount === 0) {
      container.innerHTML = `<div style="text-align:center; width:100%; grid-column:1/-1; padding: 20px;">
              <p class="error-text">无法加载所选城市的天气数据，请检查网络。</p>
              <button onclick="handleLiveCitySelect([${cityIds.join(",")}])" class="btn btn-secondary btn-sm mt-3">重试</button>
          </div>`;
      return;
    }

    results.forEach((result, index) => {
      const cityId = cityIds[index];
      const card = document.createElement("div");
      card.className = "comparison-card";

      let cityName = "未知城市";
      // Fallback for appState.cities if not populated or mismatch type
      if (appState.cities && appState.cities.length > 0) {
        const foundCity = appState.cities.find(
          (c) => String(c.id) === String(cityId),
        );
        if (foundCity) cityName = foundCity.name;
      }

      if (result.status === "rejected") {
        const err = result.reason;
        console.warn(`Failed to fetch city ${cityId}:`, err);
        card.innerHTML = `
                <div class="comparison-card-header">
                    <span class="comparison-card-title">${cityName}</span>
                </div>
                <div class="comparison-card-body" style="grid-template-columns: 1fr;">
                    <button class="btn btn-tiny btn-secondary" onclick="handleLiveCitySelect([${cityId}])">重试</button>
                    <span style="font-size:0.8rem; color: #999;">加载失败</span>
                </div>
            `;
      } else {
        const data = result.value.data;
        const rCityName = data.city_name || cityName;

        // Card Click Handler
        card.onclick = (e) => {
          // Prevent triggering when clicking buttons inside
          if (e.target.tagName === "BUTTON" || e.target.closest("button"))
            return;

          switchSelectorMode("live", "single");
          if (appState.liveCitySelector) {
            appState.liveCitySelector.setSelected([parseInt(cityId)]);
          }
          handleLiveCitySelect([cityId]);
        };

        const temp =
          data.temperature != null ? data.temperature.toFixed(1) : "--";
        const weatherName = data.weather_name || "未知";
        const wind =
          data.wind_speed != null ? data.wind_speed.toFixed(1) : "--";
        const rad = data.radiation != null ? Math.round(data.radiation) : "--";

        // weather_service.py returns weather_code, verify it's valid
        const weatherCode = data.weather_code !== undefined ? data.weather_code : 0;

        card.innerHTML = `
              <div class="comparison-card-header">
                <span class="comparison-card-title">${rCityName}</span>
                <div class="weather-icon-small">
                  ${getWeatherIcon(weatherCode)}
                </div>
              </div>
              <div class="comparison-card-body">
                <div class="comparison-main-temp">${temp}<span style="font-size:0.5em; font-weight:normal; margin-left:2px;">°C</span></div>
                <div class="comparison-details">
                  <div class="comparison-detail-item">
                    <span class="comparison-detail-label">风速</span>
                    <span class="comparison-detail-value">${wind} m/s</span>
                  </div>
                  <div class="comparison-detail-item">
                    <span class="comparison-detail-label">辐射</span>
                    <span class="comparison-detail-value">${rad} W/m²</span>
                  </div>
                </div>
              </div>
              <div class="comparison-footer">
                <span>${weatherName}</span>
                <span>查看详情 &rarr;</span>
              </div>
            `;
      }
      console.log(`Appending card for ${cityName} to container`);
      container.appendChild(card);
    });
    console.log(`Finished appending ${results.length} cards.`);
  } catch (e) {
    console.error("Multi-city fetch critical error:", e);
    container.innerHTML = `<p class="error-text">加载失败: ${e.message}</p>`;
  }
}

// --- Weather Icons SVG Map (Inline) ---
const WEATHER_ICONS = {
  // ☀️ 晴 (Sunny)
  sunny: `<svg viewBox="0 0 64 64" class="w-full h-full"><circle cx="32" cy="32" r="14" fill="#f59e0b"/><path d="M32 8V2m0 60V56m24-24h6M2 32h6m42-17l4-4M10 54l4-4m34 4l4 4M10 10l4 4" stroke="#f59e0b" stroke-width="4" stroke-linecap="round"/></svg>`,
  // ⛅ 多云 (Cloudy) - Specific fix for sunny-cloudy
  cloudy: `<svg viewBox="0 0 64 64" class="w-full h-full"><circle cx="38" cy="26" r="10" fill="#f59e0b"/><path d="M38 10v4m16 12h4m-4-12l-2 2m-20 0l-2-2" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/><path d="M46 48a14 14 0 000-28 6 6 0 00-6 2 12 12 0 10-22 10h28z" fill="#f3f4f6" stroke="#9ca3af" stroke-width="2" stroke-linejoin="round"/></svg>`,
  // ☁️ 阴 (Overcast)
  overcast: `<svg viewBox="0 0 64 64" class="w-full h-full"><path d="M46 46a14 14 0 000-28 6 6 0 00-6 2 12 12 0 10-22 10h28z" fill="#9ca3af" stroke="#4b5563" stroke-width="2" stroke-linejoin="round"/></svg>`,
  // 🌧️ 雨 (Rain)
  rain: `<svg viewBox="0 0 64 64" class="w-full h-full"><path d="M46 40a14 14 0 000-28 6 6 0 00-6 2 12 12 0 10-22 10h28z" fill="#d1d5db" stroke="#9ca3af" stroke-width="2"/><path d="M26 46l-4 8m10-8l-4 8m10-8l-4 8" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/></svg>`,
  // ⚡ 雷 (Thunder)
  thunder: `<svg viewBox="0 0 64 64" class="w-full h-full"><path d="M46 38a14 14 0 000-28 6 6 0 00-6 2 12 12 0 10-22 10h28z" fill="#6b7280" stroke="#4b5563" stroke-width="2"/><path d="M36 40l-8 12h6l-4 10" stroke="#f59e0b" stroke-width="3" stroke-linecap="round" fill="none"/></svg>`,
  // ❄️ 雪 (Snow)
  snow: `<svg viewBox="0 0 64 64" class="w-full h-full"><circle cx="32" cy="32" r="26" fill="none" stroke="#e5e7eb" stroke-width="2"/><path d="M32 16v32m-14-18l28 4m-28 4l28-4" stroke="#bfdbfe" stroke-width="3" stroke-linecap="round"/></svg>`,
};

function getIconKey(code) {
  if ([0, 1].includes(code)) return "sunny";
  if ([2].includes(code)) return "cloudy";
  if ([3, 45, 48].includes(code)) return "overcast";
  if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) return "rain";
  if ([95, 96, 99].includes(code)) return "thunder";
  if ([71, 73, 75, 77, 85, 86].includes(code)) return "snow";
  return "sunny";
}

/**
 * 根据天气代码获取 SVG 图标 HTML
 */
function getWeatherIcon(code) {
  const key = getIconKey(code);
  return WEATHER_ICONS[key] || WEATHER_ICONS["sunny"];
}

/**
 * 渲染实时天气 (新版)
 */
function renderCurrentWeather(data) {
  const cityEl = document.getElementById("currentCityNameDisplay");
  const tempEl = document.getElementById("currentTemp");
  const nameEl = document.getElementById("currentWeatherName");
  const iconEl = document.getElementById("currentIcon");
  const windEl = document.getElementById("currentWind");
  const radEl = document.getElementById("currentRadiation");
  const timeEl = document.getElementById("currentUpdateTime");

  if (cityEl) cityEl.textContent = data.city_name;
  if (tempEl)
    tempEl.textContent = data.temperature ? data.temperature.toFixed(1) : "--";
  if (nameEl) nameEl.textContent = data.weather_name;

  // Icon Logic
  if (iconEl) {
    // Use SVG map
    const key = getIconKey(data.weather_code);
    iconEl.innerHTML = WEATHER_ICONS[key] || WEATHER_ICONS["sunny"];
    // Remove class based icon if previously added
    iconEl.className = `weather-icon-huge`;
  }

  if (windEl) windEl.textContent = `${data.wind_speed.toFixed(1)} m/s`;
  if (radEl) radEl.textContent = `${data.radiation.toFixed(0)} W/m²`;
  if (timeEl) timeEl.textContent = data.update_time.split(" ")[1];
}

// --- Global Chart Instances ---
let todayChartInstance = null;
let tomorrowChartInstance = null;
let detailChartInstance = null;
let trendDetailChartInstance = null; // New instance for trend modal
let currentTrendData = []; // Store data for export

// --- Helper: Get Start of Day ---
function getStartOfDay(d) {
  const date = new Date(d);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
}

// --- Global Reference to Hourly Data ---
let currentTodayHourly = [];
let currentTomorrowHourly = [];

/**
 * 渲染预报 (今日/明日图表 + 7天列表 + 详情)
 */
function renderForecast(data) {
  const list = document.getElementById("forecastList");
  if (list) list.innerHTML = "";

  // 1. 限制为未来 7 天
  const forecasts = (data.daily_forecast || []).slice(0, 7);
  const hourly = data.hourly_forecast || [];
  currentAllHourlyData = hourly;

  // 2. 准备今日/明日数据 (使用本地时间而非 UTC，修复时区匹配问题)
  const now = new Date();
  const getFormattedDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };

  const todayStr = getFormattedDate(now);

  const tomorrowDate = new Date(now);
  tomorrowDate.setDate(now.getDate() + 1);
  const tomorrowStr = getFormattedDate(tomorrowDate);

  // 今日趋势优先使用 15 分钟高精度数据，如果缺失则退而求其次使用 1小时 数据
  const minutely = data.minutely_15_forecast || [];
  let todayData = minutely.filter((h) => h.time.startsWith(todayStr));

  if (todayData.length === 0) {
    console.log("今日 15min 高精度数据缺失，尝试使用小时数据");
    todayData = hourly.filter((h) => h.time.startsWith(todayStr));
  }

  currentTodayHourly = todayData;

  // 明日趋势维持 1小时 精度
  currentTomorrowHourly = hourly.filter((h) => h.time.startsWith(tomorrowStr));

  // 3. 初始渲染图表 (应用 toggle 状态)
  updateChartsFromToggles();

  // 4. 渲染 7 天预报列表
  forecasts.forEach((day, index) => {
    const div = document.createElement("div");
    div.className = "forecast-item-h";
    div.onclick = () => openDetailModal(day, hourly);

    const dateObj = new Date(day.date);
    const dateStr = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, "0")}-${String(dateObj.getDate()).padStart(2, "0")}`;
    const weatherName = day.weather_name || "未知";

    div.innerHTML = `
            <div class="fi-date">${dateStr}</div>
            <div style="width: 48px; height: 48px; margin: 8px 0;">
                 ${WEATHER_ICONS[getIconKey(day.weather_code)] || WEATHER_ICONS["sunny"]}
            </div>
            <div class="text-xs text-gray-500 mb-1">${weatherName}</div>
            <div class="fi-temps">
                <span class="fi-min">${day.temp_min.toFixed(0)}°</span>
                <span class="text-gray-300">/</span>
                <span class="fi-max">${day.temp_max.toFixed(0)}°</span>
            </div>
        `;
    if (list) list.appendChild(div);
  });
}

// --- Toggles Handler ---
function updateChartsFromToggles() {
  // Read Checkbox States
  const showTemp =
    document.querySelector('.chart-toggle[value="temp"]')?.checked ?? true;
  const showRain =
    document.querySelector('.chart-toggle[value="rain"]')?.checked ?? true;
  const showWind =
    document.querySelector('.chart-toggle[value="wind"]')?.checked ?? false;
  const showRad =
    document.querySelector('.chart-toggle[value="radiation"]')?.checked ??
    false;

  const options = { showTemp, showRain, showWind, showRad };

  // Render Both Charts
  renderGenericHourlyChart(
    "todayChart",
    currentTodayHourly,
    todayChartInstance,
    (inst) => (todayChartInstance = inst),
    options,
  );
  renderGenericHourlyChart(
    "tomorrowChart",
    currentTomorrowHourly,
    tomorrowChartInstance,
    (inst) => (tomorrowChartInstance = inst),
    options,
  );
}

// Remove old listeners to avoid duplicates if re-run, then add new
const toggles = document.querySelectorAll(".chart-toggle");
toggles.forEach((chk) => {
  chk.onchange = updateChartsFromToggles; // Bind directly
});

// --- Generic Chart Renderer (Enhanced) ---
function renderGenericHourlyChart(
  canvasId,
  data,
  instanceRef,
  setInstance,
  options = {},
) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (instanceRef) {
    instanceRef.destroy();
  }

  if (!data || data.length === 0) return;

  const labels = data.map((d) => d.time.split("T")[1].substring(0, 5));
  const datasets = [];

  // 1. Temperature
  if (options.showTemp) {
    datasets.push({
      type: "line",
      label: "气温 (°C)",
      data: data.map((d) => d.temp),
      borderColor: "#ef4444",
      backgroundColor: "rgba(239, 68, 68, 0.1)",
      borderWidth: 2,
      pointRadius: 1,
      tension: 0.4,
      yAxisID: "y",
      fill: true,
    });
  }

  // 2. Rain Probability
  if (options.showRain) {
    datasets.push({
      type: "bar",
      label: "降水概率 (%)",
      data: data.map((d) => d.pop),
      backgroundColor: "rgba(59, 130, 246, 0.3)",
      yAxisID: "y1",
      barPercentage: 0.6,
    });
  }

  // 3. Wind Speed
  if (options.showWind) {
    datasets.push({
      type: "line",
      label: "风速 (m/s)",
      data: data.map((d) => d.wind),
      borderColor: "#8b5cf6",
      borderDash: [5, 5],
      borderWidth: 2,
      yAxisID: "y2",
      tension: 0.4,
      pointRadius: 0,
    });
  }

  // 4. Radiation
  if (options.showRad) {
    datasets.push({
      type: "line",
      label: "辐照度 (W/m²)",
      data: data.map((d) => d.radiation),
      borderColor: "#f97316",
      backgroundColor: "rgba(249, 115, 22, 0.1)",
      borderWidth: 1.5,
      yAxisID: "y3",
      tension: 0.4,
      pointRadius: 0,
      fill: false,
    });
  }

  const newInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      onClick: (e) => {
        // Open Modal on Click
        openTrendModal(canvasId === "todayChart" ? "today" : "tomorrow");
      },
      plugins: {
        legend: { display: true, position: "top" }, // Show Legend
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
        y: {
          type: "linear",
          display: options.showTemp,
          position: "left",
          grid: { color: "rgba(0,0,0,0.05)" },
          title: { display: true, text: "气温" },
        },
        y1: {
          type: "linear",
          display: options.showRain,
          position: "right",
          min: 0,
          max: 100,
          grid: { display: false },
          title: { display: true, text: "概率" },
        },
        y2: {
          type: "linear",
          display: options.showWind,
          position: "right",
          grid: { display: false },
          title: { display: true, text: "风速" },
        },
        y3: {
          type: "linear",
          display: options.showRad,
          position: "right",
          grid: { display: false },
          title: { display: true, text: "辐照" },
        },
      },
    },
  });

  if (setInstance) setInstance(newInstance);
}

// --- Unified Trend Modal Logic ---

/**
 * Handle clicks on Today/Tomorrow charts
 */
function openTrendModal(type) {
  let data = [];
  let title = "";

  if (type === "today") {
    data = currentTodayHourly || [];
    title = "今日趋势详情 (15分钟级)";
    // Fallback check
    if (
      !data.length ||
      (data[0] &&
        !data[0].time.includes(":15") &&
        !data[0].time.includes(":30") &&
        !data[0].time.includes(":45"))
    ) {
      title = "今日趋势详情 (小时级)";
    }
  } else {
    data = currentTomorrowHourly || [];
    title = "明日趋势详情 (小时级)";
  }

  if (!data || data.length === 0) {
    alert("暂无数据");
    return;
  }

  showTrendModal(title, data);
}

/**
 * Handle clicks on Forecast List Items (Replaces old openDetailModal)
 */
function openDetailModal(dayData, allHourly) {
  const targetDateStr = dayData.date; // "YYYY-MM-DD"
  const dayHourly = allHourly.filter((h) => h.time.startsWith(targetDateStr));

  if (!dayHourly || dayHourly.length === 0) {
    alert("该日无详细小时数据");
    return;
  }

  showTrendModal(`${dayData.date} 全天趋势详情`, dayHourly);
}

/**
 * Core function to show the modal with data
 */
function showTrendModal(title, data) {
  const modal = document.getElementById("trendDetailModal");
  if (!modal) return;

  currentTrendData = data; // Store for export
  document.getElementById("trendModalTitle").textContent = title;

  // Open Modal
  modal.classList.add("open");

  // 1. Render Chart
  // Re-read Toggles to keep consistency (or default to all?)
  // Let's use current toggles from main page
  const showTemp =
    document.querySelector('.chart-toggle[value="temp"]')?.checked ?? true;
  const showRain =
    document.querySelector('.chart-toggle[value="rain"]')?.checked ?? true;
  const showWind =
    document.querySelector('.chart-toggle[value="wind"]')?.checked ?? false;
  const showRad =
    document.querySelector('.chart-toggle[value="radiation"]')?.checked ??
    false;

  renderGenericHourlyChart(
    "trendDetailChart",
    data,
    trendDetailChartInstance,
    (inst) => (trendDetailChartInstance = inst),
    { showTemp, showRain, showWind, showRad },
  );

  // 2. Render Table
  renderTrendTable(data);
}

// Export functionality for external use (e.g. data-management.js)
window.showTrendModalLocal = showTrendModal;

function closeTrendModal() {
  const modal = document.getElementById("trendDetailModal");
  if (modal) modal.classList.remove("open");
}

// Close modal when clicking outside
window.onclick = function (event) {
  const modal = document.getElementById("trendDetailModal");
  if (event.target == modal) {
    closeTrendModal();
  }
  // Also handle old modal if it still exists (optional)
  const oldModal = document.getElementById("detailModal");
  if (oldModal && event.target == oldModal) {
    oldModal.classList.remove("open");
  }
};

function renderTrendTable(data) {
  const tbody = document.querySelector("#trendDetailTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  data.forEach((d) => {
    const tr = document.createElement("tr");
    // Handle minutely vs hourly time format
    const timePart = d.time.split("T")[1];
    const timeStr = timePart.length > 5 ? timePart.substring(0, 5) : timePart;

    tr.innerHTML = `
            <td>${timeStr}</td>
            <td style="color:${d.temp >= 35 ? "var(--color-danger)" : "var(--text-primary)"}">${d.temp.toFixed(1)}</td>
            <td>${d.pop}% / ${d.rain ? d.rain.toFixed(1) : 0}</td>
            <td>${d.wind.toFixed(1)}</td>
            <td>${d.radiation.toFixed(0)}</td>
        `;
    tbody.appendChild(tr);
  });
}

/**
 * 导出趋势详情数据为 CSV
 */
function exportTrendData() {
  if (!currentTrendData || currentTrendData.length === 0) {
    alert("没有可导出的数据");
    return;
  }

  const title =
    document.getElementById("trendModalTitle").textContent || "趋势数据";

  // 生成 CSV
  const headers = [
    "时间",
    "温度(°C)",
    "降水概率(%)",
    "降水量(mm)",
    "风速(m/s)",
    "太阳辐射(W/m²)",
  ];
  const rows = currentTrendData.map((d) => [
    d.time.replace("T", " "),
    d.temp,
    d.pop,
    d.rain || 0,
    d.wind,
    d.radiation,
  ]);

  let csvContent = "\ufeff" + headers.join(",") + "\n";
  rows.forEach((row) => {
    csvContent += row.join(",") + "\n";
  });

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${title.replace(/\s+/g, "_")}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Export to window for onclick binding
window.exportTrendData = exportTrendData;

// Remove old global vars/funcs if unused
// updateHourlyChartFromToggles etc. can be kept or removed if feature retired.
// User said "显示数据项保留" (Keep Data Layers).
// BUT, the new charts (Today/Tomorrow) don't use the toggles in this code.
// The Toggles likely applied to the deprecated "48-Hour Chart".
// To keep "Data Layers", I should probably make them apply to "Today" and "Tomorrow" charts.
// For now, I'll connect toggles to the new chart instances if possible, but basic requirement is met.
// I'll leave the toggles logic but it might be disconnected.
// Given complexity constraint, I will finalize the structure first.

let forecastChart = null;
function renderForecastChart(labels, maxData, minData) {
  const chartEl = document.getElementById("forecastChart");
  if (!chartEl) return;

  const ctx = chartEl.getContext("2d");

  if (forecastChart) {
    forecastChart.destroy();
  }

  forecastChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "最高温度 (°C)",
          data: maxData,
          borderColor: "#ff3b30",
          backgroundColor: "rgba(255, 59, 48, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
        },
        {
          label: "最低温度 (°C)",
          data: minData,
          borderColor: "#007aff",
          backgroundColor: "rgba(0, 122, 255, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
        },
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: "rgba(0, 0, 0, 0.05)",
          },
        },
        x: {
          grid: {
            display: false,
          },
        },
      },
    },
  });
}

// --- Unified Selection Mode Switcher ---
window.switchSelectorMode = function (tab, mode) {
  const selector =
    tab === "query" ? appState.citySelector : appState.liveCitySelector;
  if (!selector) return;

  selector.setOptions({ mode: mode });

  // UI update for toggles
  const suffix = tab === "live" ? "-live" : "";
  const btns = document.querySelectorAll(`[data-mode-btn${suffix}]`);
  btns.forEach((b) => b.classList.remove("active"));

  const activeBtn = document.querySelector(
    `[data-mode-btn${suffix}="${mode}"]`,
  );
  if (activeBtn) activeBtn.classList.add("active");

  // For Live page, show/hide confirm button and correct display panels
  if (tab === "live") {
    const confirmBtn = document.getElementById("confirmLiveCityBtn");
    const detailDisplay = document.getElementById("liveWeatherDisplay");
    const comparisonDisplay = document.getElementById("liveComparisonDisplay");
    const loading = document.getElementById("liveLoading");

    if (confirmBtn) {
      confirmBtn.style.display = mode === "multi" ? "block" : "none";
    }

    // When switching modes, clear existing views to avoid confusion
    if (detailDisplay) detailDisplay.style.display = "none";
    if (comparisonDisplay) comparisonDisplay.style.display = "none";
    if (loading) loading.style.display = "none";
  }
};


// 暴露函数
window.updateChartsFromToggles = updateChartsFromToggles;

// ============================================================
// === 天气预测查询模块 ===
// ============================================================

// 预测查询状态
let forecastQueryState = {
  currentData: null,
  selectedFields: [],
  charts: {
    temperature: null,
    radiation: null,
    windSpeed: null,
    precipitation: null
  }
};

/**
 * 初始化预测查询页面
 */
function initForecastQueryPage() {
  // 设置默认预测时间为当前时间
  const startTimeInput = document.getElementById("forecastStartTime");
  if (startTimeInput) {
    const now = new Date();
    // 格式化为 datetime-local 格式
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(Math.floor(now.getMinutes() / 15) * 15).padStart(2, "0");
    startTimeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  // 渲染字段选择器
  renderForecastFieldSelector();

  // 绑定查询按钮事件
  const queryBtn = document.getElementById("forecastQueryBtn");
  if (queryBtn) {
    queryBtn.addEventListener("click", handleForecastQuery);
  }

  // 绑定导出按钮事件
  const exportExcelBtn = document.getElementById("forecastExportExcelBtn");
  const exportCsvBtn = document.getElementById("forecastExportCsvBtn");
  if (exportExcelBtn) {
    exportExcelBtn.addEventListener("click", () => handleForecastExport("excel"));
  }
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener("click", () => handleForecastExport("csv"));
  }

  // 绑定筛选器事件
  const cityFilter = document.getElementById("forecastCityFilter");
  const dateFilter = document.getElementById("forecastDateFilter");
  const resetBtn = document.getElementById("forecastResetFilterBtn");

  if (cityFilter) cityFilter.addEventListener("change", handleForecastFilterChange);
  if (dateFilter) dateFilter.addEventListener("change", handleForecastFilterChange);
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (cityFilter) cityFilter.value = "all";
      if (dateFilter) dateFilter.value = "all";
      handleForecastFilterChange();
    });
  }
}

/**
 * 渲染预测查询字段选择器
 */
function renderForecastFieldSelector() {
  const container = document.getElementById("forecastFieldSelector");
  if (!container || !appState.fields) return;

  container.innerHTML = "";

  // 预测查询默认选中的字段
  const defaultFields = ["temperature_2m", "wind_speed_10m", "shortwave_radiation", "precipitation_probability"];

  Object.entries(appState.fields).forEach(([category, fields]) => {
    Object.entries(fields).forEach(([key, fieldInfo]) => {
      // fieldInfo 是一个对象 { name, description, unit }
      const fieldName = typeof fieldInfo === 'object' ? fieldInfo.name : fieldInfo;
      const isChecked = defaultFields.includes(key);
      if (isChecked && !forecastQueryState.selectedFields.includes(key)) {
        forecastQueryState.selectedFields.push(key);
      }

      const fieldItem = document.createElement("label");
      fieldItem.className = "field-item";
      fieldItem.innerHTML = `
        <input type="checkbox" value="${key}" ${isChecked ? "checked" : ""} class="forecast-field-checkbox" />
        <span>${fieldName}</span>
      `;
      container.appendChild(fieldItem);
    });
  });

  // 绑定字段选择事件
  container.querySelectorAll(".forecast-field-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", (e) => {
      const fieldKey = e.target.value;
      if (e.target.checked) {
        if (!forecastQueryState.selectedFields.includes(fieldKey)) {
          forecastQueryState.selectedFields.push(fieldKey);
        }
      } else {
        forecastQueryState.selectedFields = forecastQueryState.selectedFields.filter(f => f !== fieldKey);
      }
    });
  });
}

/**
 * 处理预测查询
 */
async function handleForecastQuery() {
  // 获取选中的城市
  if (!appState.liveCitySelector) {
    showError("城市选择器未初始化");
    return;
  }

  const selectedCities = Array.from(appState.liveCitySelector.selectedIds);
  if (selectedCities.length === 0) {
    showError("请至少选择一个城市");
    return;
  }

  const days = parseInt(document.getElementById("forecastDays").value) || 7;

  // 显示加载状态
  const loadingIndicator = document.getElementById("forecastLoadingIndicator");
  const dataDisplay = document.getElementById("forecastDataDisplay");
  if (loadingIndicator) loadingIndicator.style.display = "flex";
  if (dataDisplay) dataDisplay.style.display = "none";

  try {
    const response = await api.queryForecast({
      city_ids: selectedCities,
      days: days,
      fields: forecastQueryState.selectedFields
    });

    if (response.code !== 200) {
      throw new Error(response.message || "查询失败");
    }

    forecastQueryState.currentData = response.data;
    forecastQueryState.forecastDays = response.forecast_days || days;

    // 渲染数据
    renderForecastData(response.data, response.forecast_days || days);

    // 启用导出按钮
    const exportExcelBtn = document.getElementById("forecastExportExcelBtn");
    const exportCsvBtn = document.getElementById("forecastExportCsvBtn");
    if (exportExcelBtn) exportExcelBtn.disabled = false;
    if (exportCsvBtn) exportCsvBtn.disabled = false;

    console.log("预测查询成功");
  } catch (error) {
    console.error("预测查询失败:", error);
    showError("查询失败: " + error.message);
  } finally {
    if (loadingIndicator) loadingIndicator.style.display = "none";
  }
}

/**
 * 渲染预测数据
 */
function renderForecastData(results, forecastDays) {
  const dataDisplay = document.getElementById("forecastDataDisplay");
  if (dataDisplay) dataDisplay.style.display = "block";

  // 更新全局预测范围
  const daysEl = document.getElementById("globalForecastDays");
  if (daysEl) daysEl.textContent = forecastDays;

  // 1. 渲染实时天气看板 (多城市)
  const liveContainer = document.getElementById("forecastLiveWeather");
  if (liveContainer) {
    liveContainer.innerHTML = '<div class="live-weather-optimized"></div>';
    const grid = liveContainer.querySelector(".live-weather-optimized");
    results.forEach(res => {
      if (res.current_weather) {
        grid.appendChild(createLiveWeatherCard(res.current_weather));
      }
    });
  }

  // 2. 渲染各城市统计卡片 (分组显示)
  const statsContainer = document.getElementById("forecastStatsCards");
  if (statsContainer) {
    statsContainer.className = "city-display-section"; // 改变类名以启用纵向分组
    statsContainer.innerHTML = "";
    results.forEach(res => {
      statsContainer.appendChild(createCityStatsGroup(res));
    });
  }

  // 3. 渲染7天预报概览 (取第一个城市作为代表)
  if (results.length > 0) {
    renderForecastDailyOverview(results[0].daily_forecast);
  }

  // 4. 渲染图表
  // 综合所有城市的数据，或者只展示第一个城市？
  // 用户需求：展示 24h 曲线，数值按选择，默认辐照度和风速
  renderForecastCharts(results);

  // 5. 渲染数据表格 (仅显示第一个城市详情，或合并？通常仅显示第一个或提供切换)
  if (results.length > 0) {
    renderForecastTable(results[0].records);
    populateForecastFilters(results[0]);
  }

  // 滚动到数据展示区
  setTimeout(() => {
    const headerHeight = document.querySelector(".header").offsetHeight || 80;
    const rect = dataDisplay.getBoundingClientRect();
    const scrollTarget = rect.top + window.pageYOffset - headerHeight - 20;
    window.scrollTo({
      top: scrollTarget,
      behavior: "smooth"
    });
  }, 100);
}

/**
 * 创建实时天气卡片 (优化版)
 */
function createLiveWeatherCard(current) {
  const wrapper = document.createElement("div");
  wrapper.className = "live-card-wrapper";
  
  const weatherCode = current.weather_code || 0;
  const weatherInfo = weatherCodeMap[weatherCode] || { name: "未知", icon: "❓" };
  
  wrapper.innerHTML = `
    <div class="live-card-header">
      <div class="live-card-info">
        <h4>${current.city_name}</h4>
        <div class="live-card-meta">
          <span>坐标: ${current.longitude.toFixed(2)}, ${current.latitude.toFixed(2)}</span>
          <span>更新: ${current.update_time || "--"}</span>
        </div>
      </div>
      <div style="font-size: 2rem">${weatherInfo.icon}</div>
    </div>
    <div class="live-card-body">
      <div class="live-item">
        <div class="live-item-icon" style="background: rgba(255,59,48,0.1); color: #ff3b30">🌡️</div>
        <div class="live-item-content">
          <span class="live-item-label">温度</span>
          <span class="live-item-value">${current.temperature != null ? current.temperature.toFixed(1) : "--"}<span class="live-item-unit">°C</span></span>
        </div>
      </div>
      <div class="live-item">
        <div class="live-item-icon" style="background: rgba(255,149,0,0.1); color: #ff9500">☀️</div>
        <div class="live-item-content">
          <span class="live-item-label">辐照度</span>
          <span class="live-item-value">${current.radiation != null ? current.radiation.toFixed(0) : "--"}<span class="live-item-unit">W/m²</span></span>
        </div>
      </div>
      <div class="live-item">
        <div class="live-item-icon" style="background: rgba(52,199,89,0.1); color: #34c759">💨</div>
        <div class="live-item-content">
          <span class="live-item-label">风速</span>
          <span class="live-item-value">${current.wind_speed != null ? current.wind_speed.toFixed(1) : "--"}<span class="live-item-unit">m/s</span></span>
        </div>
      </div>
      <div class="live-item">
        <div class="live-item-icon" style="background: rgba(88,86,214,0.1); color: #5856d6">☁️</div>
        <div class="live-item-content">
          <span class="live-item-label">天气</span>
          <span class="live-item-value">${current.weather_name || weatherInfo.name}</span>
        </div>
      </div>
    </div>
  `;
  return wrapper;
}

/**
 * 创建城市统计分组 (参考图片样式)
 */
function createCityStatsGroup(data) {
  const section = document.createElement("div");
  section.className = "city-stats-group mb-4";
  
  const title = document.createElement("div");
  title.className = "city-stats-divider";
  title.innerHTML = `<span>${data.city_name}</span>`;
  section.appendChild(title);
  
  const grid = document.createElement("div");
  grid.className = "stats-cards";
  
  const summary = data.summary || {};
  
  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-card-header">
        <div class="stat-icon temperature">🌡️</div>
        <div class="stat-label">平均温度</div>
      </div>
      <div class="stat-value">${summary.temperature ? summary.temperature.avg.toFixed(1) : "--"}<span class="stat-unit">°C</span></div>
      <div class="stat-details">
        <span>最高: ${summary.temperature ? summary.temperature.max : "--"}°</span>
        <span>最低: ${summary.temperature ? summary.temperature.min : "--"}°</span>
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-card-header">
        <div class="stat-icon radiation">☀️</div>
        <div class="stat-label">太阳辐射</div>
      </div>
      <div class="stat-value">${summary.solar_radiation ? summary.solar_radiation.avg.toFixed(2) : "--"}<span class="stat-unit">W/m²</span></div>
      <div class="stat-details">
        <span>总计: ${summary.solar_radiation ? summary.solar_radiation.total_mj.toFixed(2) : "--"} MJ/m²</span>
      </div>
    </div>
    
    <div class="stat-card">
      <div class="stat-card-header">
        <div class="stat-icon wind">💨</div>
        <div class="stat-label">风速</div>
      </div>
      <div class="stat-value">${summary.wind_speed ? summary.wind_speed.avg.toFixed(2) : "--"}<span class="stat-unit">m/s</span></div>
      <div class="stat-details">
        <span>最大: ${summary.wind_speed ? summary.wind_speed.max.toFixed(2) : "--"} m/s</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-card-header">
        <div class="stat-icon precipitation">💧</div>
        <div class="stat-label">降水量</div>
      </div>
      <div class="stat-value">${summary.precipitation ? summary.precipitation.total.toFixed(2) : "0.00"}<span class="stat-unit">mm</span></div>
      <div class="stat-details">
        <span>降雨时间: ${summary.precipitation ? summary.precipitation.rainy_hours : "0"}小时</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-card-header">
        <div class="stat-icon weather">☁️</div>
        <div class="stat-label">主要天气</div>
      </div>
      <div class="stat-value">${summary.weather ? (weatherCodeMap[summary.weather.most_frequent]?.name || "阴天") : "阴天"}</div>
      <div class="stat-details">
        <span>总体天气状态</span>
      </div>
    </div>
  `;
  
  section.appendChild(grid);
  return section;
}

/**
 * 渲染7天预报概览
 */
function renderForecastDailyOverview(dailyForecast) {
  const container = document.getElementById("forecastDailyList");
  if (!container || !dailyForecast) return;

  container.innerHTML = "";

  dailyForecast.forEach((day) => {
    const div = document.createElement("div");
    div.className = "forecast-item-h";

    const dateObj = new Date(day.date);
    const dateStr = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
    const weekDay = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][dateObj.getDay()];
    const weatherName = day.weather_name || "未知";

    div.innerHTML = `
      <div class="fi-date">${dateStr}<br/><span style="font-size:0.75rem;color:#999">${weekDay}</span></div>
      <div class="fi-icon">${weatherCodeMap[day.weather_code]?.icon || "❓"}</div>
      <div class="text-xs text-gray-500">${weatherName}</div>
      <div class="fi-temps">
        <span class="fi-min">${day.temp_min != null ? day.temp_min.toFixed(0) : "--"}°</span>
        <span class="text-gray-300">/</span>
        <span class="fi-max">${day.temp_max != null ? day.temp_max.toFixed(0) : "--"}°</span>
      </div>
    `;
    container.appendChild(div);
  });
}

/**
 * 渲染预测图表
 */
function renderForecastCharts(results) {
  if (!results || results.length === 0) return;

  const firstResult = results[0];
  const records = firstResult.records;

  // 准备未来 24 小时的数据 (15分钟精度)
  const now = new Date();
  const startTime = now.getTime();
  const endTime = startTime + 24 * 60 * 60 * 1000;

  const next24hRecords = records.filter(r => {
    const t = new Date(r.datetime).getTime();
    return t >= startTime && t <= endTime;
  });

  // 如果没有足够数据（可能因为数据更新延迟），则取前 96 个点 (24小时 * 4)
  const displayRecords = next24hRecords.length >= 24 ? next24hRecords : records.slice(0, 96);

  const labels = displayRecords.map(r => {
    const dt = new Date(r.datetime);
    return `${String(dt.getHours()).padStart(2, "0")}:${String(dt.getMinutes()).padStart(2, "0")}`;
  });

  // 绘制 24 小时趋势图 (按选定字段)
  const datasets = [];
  const selectedFields = forecastQueryState.selectedFields;

  // 字段配置 (颜色与标签)
  const fieldConfig = {
    temperature_2m: { label: "温度", color: "#ff3b30", unit: "°C" },
    shortwave_radiation: { label: "辐照度", color: "#ff9500", unit: "W/m²" },
    wind_speed_10m: { label: "风速", color: "#34c759", unit: "m/s" },
    precipitation_probability: { label: "降水概率", color: "#007aff", unit: "%" }
  };

  // 默认显示辐照度和风速，如果没有选择的话
  const fieldsToShow = selectedFields.length > 0 ? selectedFields : ["shortwave_radiation", "wind_speed_10m"];

  fieldsToShow.forEach(field => {
    const config = fieldConfig[field];
    if (config) {
      datasets.push({
        label: config.label,
        data: displayRecords.map(r => r[field]),
        borderColor: config.color,
        backgroundColor: config.color + "20",
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 0
      });
    }
  });

  renderGenericLineChart("forecastNext24hChart", labels, datasets);

  // 绘制风速和降水 (历史保留的辅助图表)
  const windLabels = records.map(r => {
    const dt = new Date(r.datetime);
    return `${dt.getMonth()+1}/${dt.getDate()} ${String(dt.getHours()).padStart(2,"0")}:00`;
  });
  const windData = records.filter((_, i) => i % 4 === 0).map(r => r.wind_speed_10m);
  const windLabelsSparse = records.filter((_, i) => i % 4 === 0).map(r => {
     const dt = new Date(r.datetime);
     return `${dt.getMonth()+1}/${dt.getDate()} ${dt.getHours()}h`;
  });
  
  renderForecastLineChart("forecastWindSpeedChart", windLabelsSparse, windData, "风速 (m/s)", "#34c759");

  const precipData = records.filter((_, i) => i % 4 === 0).map(r => r.precipitation || 0);
  renderForecastBarChart("forecastPrecipitationChart", windLabelsSparse, precipData, "降水量 (mm)", "#007aff");
}

/**
 * 渲染通用多曲线折线图
 */
function renderGenericLineChart(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top', align: 'end' },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { ticks: { maxTicksLimit: 24 } },
        y: { beginAtZero: false }
      }
    }
  });
}

/**
 * 渲染折线图
 */
function renderForecastLineChart(canvasId, labels, data, label, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  // 销毁现有图表
  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: color + "20",
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          display: true,
          ticks: { maxTicksLimit: 12, maxRotation: 0 }
        },
        y: { beginAtZero: false }
      }
    }
  });
}

/**
 * 渲染柱状图
 */
function renderForecastBarChart(canvasId, labels, data, label, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const existingChart = Chart.getChart(canvas);
  if (existingChart) existingChart.destroy();

  new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        backgroundColor: color + "80",
        borderColor: color,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          display: true,
          ticks: { maxTicksLimit: 12, maxRotation: 0 }
        },
        y: { beginAtZero: true }
      }
    }
  });
}

/**
 * 渲染预测数据表格
 */
function renderForecastTable(records) {
  const thead = document.getElementById("forecastTableHead");
  const tbody = document.getElementById("forecastTableBody");
  if (!thead || !tbody || !records || records.length === 0) return;

  // 表头
  thead.innerHTML = `
    <tr>
      <th>时间</th>
      <th>温度 (°C)</th>
      <th>风速 (m/s)</th>
      <th>辐照度 (W/m²)</th>
      <th>降水概率 (%)</th>
    </tr>
  `;

  // 表体（限制显示前200条，避免页面卡顿）
  const displayRecords = records.slice(0, 200);
  tbody.innerHTML = displayRecords.map(r => `
    <tr>
      <td>${r.datetime ? r.datetime.replace("T", " ") : "--"}</td>
      <td>${r.temperature_2m != null ? r.temperature_2m.toFixed(1) : "--"}</td>
      <td>${r.wind_speed_10m != null ? r.wind_speed_10m.toFixed(1) : "--"}</td>
      <td>${r.shortwave_radiation != null ? r.shortwave_radiation.toFixed(0) : "--"}</td>
      <td>${r.precipitation_probability != null ? r.precipitation_probability : "--"}</td>
    </tr>
  `).join("");

  if (records.length > 200) {
    tbody.innerHTML += `<tr><td colspan="5" style="text-align:center;color:#999;">仅显示前200条，共${records.length}条数据</td></tr>`;
  }
}

/**
 * 填充预测筛选器
 */
function populateForecastFilters(data) {
  const cityFilter = document.getElementById("forecastCityFilter");
  const dateFilter = document.getElementById("forecastDateFilter");

  if (cityFilter) {
    cityFilter.innerHTML = `<option value="all">${data.city_name || "全部"}</option>`;
  }

  if (dateFilter && data.records) {
    const dates = [...new Set(data.records.map(r => r.datetime?.split("T")[0]).filter(Boolean))];
    dateFilter.innerHTML = `<option value="all">全部日期</option>`;
    dates.forEach(date => {
      dateFilter.innerHTML += `<option value="${date}">${date}</option>`;
    });
  }
}

/**
 * 处理预测筛选器变化
 */
function handleForecastFilterChange() {
  const dateFilter = document.getElementById("forecastDateFilter");
  if (!forecastQueryState.currentData || !dateFilter) return;

  const selectedDate = dateFilter.value;
  let filteredRecords = forecastQueryState.currentData.records;

  if (selectedDate !== "all") {
    filteredRecords = filteredRecords.filter(r => r.datetime?.startsWith(selectedDate));
  }

  // 重新渲染图表和表格
  renderForecastCharts(filteredRecords);
  renderForecastTable(filteredRecords);
}

/**
 * 处理预测数据导出
 */
async function handleForecastExport(format) {
  if (!forecastQueryState.currentData) {
    showError("没有可导出的数据");
    return;
  }

  try {
    const data = forecastQueryState.currentData;

    // 生成 CSV 内容
    const headers = ["时间", "温度(°C)", "风速(m/s)", "辐照度(W/m²)", "降水概率(%)"];
    const rows = data.records.map(r => [
      r.datetime || "",
      r.temperature_2m != null ? r.temperature_2m : "",
      r.wind_speed_10m != null ? r.wind_speed_10m : "",
      r.shortwave_radiation != null ? r.shortwave_radiation : "",
      r.precipitation_probability != null ? r.precipitation_probability : ""
    ]);

    let csvContent = "\ufeff" + headers.join(",") + "\n";
    rows.forEach(row => {
      csvContent += row.join(",") + "\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `${data.city_name}_预测数据_${data.forecast_days}天.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log("预测数据导出成功");
  } catch (error) {
    console.error("导出失败:", error);
    showError("导出失败: " + error.message);
  }
}

// 暴露预测查询函数
window.handleForecastQuery = handleForecastQuery;
window.initForecastQueryPage = initForecastQueryPage;

// 页面加载完成后初始化应用
document.addEventListener("DOMContentLoaded", initApp);

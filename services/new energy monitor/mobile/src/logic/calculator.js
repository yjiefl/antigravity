/**
 * 新能源出力核心计算逻辑 (S.O.L.I.D 原则)
 */

export const STATIONS = [
  { name: "驮堪光伏电站", ac: 32.32, dc: 43.15, date: "2022-08-30", city: "天等", type: "PV", lat: 23.08, lon: 107.12 },
  { name: "弄滩光伏电站", ac: 290.00, dc: 403.88, date: "2022-12-20", city: "江州", type: "PV", lat: 22.39, lon: 107.41 },
  { name: "峙书光伏电站", ac: 100.00, dc: 141.40, date: "2022-12-23", city: "宁明", type: "PV", lat: 22.13, lon: 107.07 },
  { name: "浦峙光伏电站", ac: 90.00, dc: 126.00, date: "2022-12-31", city: "宁明", type: "PV", lat: 22.13, lon: 107.07 },
  { name: "康宁光伏电站", ac: 140.00, dc: 194.70, date: "2023-01-17", city: "宁明", type: "PV", lat: 22.13, lon: 107.07 },
  { name: "强胜光伏电站", ac: 100.00, dc: 140.36, date: "2023-04-07", city: "江州", type: "PV", lat: 22.39, lon: 107.41 },
  { name: "寨安光伏电站", ac: 50.00, dc: 69.66, date: "2023-04-09", city: "宁明", type: "PV", lat: 22.13, lon: 107.07 },
  { name: "樟木光伏电站", ac: 337.93, dc: 473.10, date: "2023-05-19", city: "贵港", type: "PV", lat: 23.11, lon: 109.60 },
  { name: "岑凡光伏电站", ac: 79.25, dc: 110.16, date: "2023-05-29", city: "扶绥", type: "PV", lat: 22.57, lon: 107.90 },
  { name: "守旗光伏电站", ac: 183.5, dc: 255.07, date: "2023-05-30", city: "扶绥", type: "PV", lat: 22.57, lon: 107.90 },
  { name: "榕木光伏电站", ac: 114.98, dc: 197.05, date: "2023-07-20", city: "贵港", type: "PV", lat: 23.11, lon: 109.60 },
  { name: "派岸光伏电站", ac: 145.00, dc: 203.00, date: "2023-07-26", city: "江州", type: "PV", lat: 22.39, lon: 107.41 }
];

/**
 * 计算光伏出力
 * @param {Object} params 
 * @returns {Object} 计算结果
 */
export function calculatePower(params) {
  const { 
    irradiance, 
    ambientTemp, 
    basePR, 
    dcCapacity, 
    acLimit, 
    degradationRate = 0.5, 
    startDate 
  } = params;

  // 1. 理论 DC 潜力 (W/m² 转换为比例)
  const potentialDC = dcCapacity * (irradiance / 1000);

  // 2. 环境温度 -> 电池温度 (简化模型: T_cell = T_amb + (Irradiance/800)*25)
  const cellTemp = ambientTemp + (irradiance / 800) * 25;
  const deltaT = cellTemp - 25;
  const tempCoeff = -0.004; // -0.4% per °C
  const tempLossFactor = deltaT * tempCoeff;

  // 3. 计算衰减 (基于投运日期)
  let degradation = 0;
  if (startDate) {
    const age = (new Date() - new Date(startDate)) / (1000 * 60 * 60 * 24 * 365.25);
    degradation = (age * degradationRate) / 100;
  }

  // 4. 综合效率 (PR * 温度损耗系数 * 衰减系数)
  const basePrDecimal = basePR / 100;
  const degradationFactor = 1 - degradation;
  const totalPR = basePrDecimal * (1 + tempLossFactor) * degradationFactor;

  // 5. AC 侧理论出力
  const potentialAC = potentialDC * totalPR;

  // 6. 截峰限制
  const finalAC = Math.min(Math.max(potentialAC, 0), acLimit);

  return {
    dcPotential: potentialDC,
    cellTemp,
    tempLossPct: tempLossFactor * 100,
    totalPRPct: totalPR * 100,
    potentialAC,
    finalAC,
    isClipping: potentialAC > acLimit
  };
}

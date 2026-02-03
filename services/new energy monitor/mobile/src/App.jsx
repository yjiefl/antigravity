import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CloudRain, 
  Settings, 
  MapPin, 
  Info,
  ChevronDown,
  Sun,
  Thermometer,
  Zap,
  TrendingUp,
  RefreshCw,
  Wind,
  CheckCircle,
  Lock,
  Calculator,
  Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ComposedChart,
  AreaChart,
  Area, 
  Line,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { STATIONS, calculatePower } from './logic/calculator';

// ... (Constants kept same)

// --- View Components ---
// ... (LoginView kept same)

// Monitor: Now has AC Capacity, Ratio, Controls for Subs
// ... (MonitorView kept same, but need to be careful with file replacement boundaries)

// Logic View: Redesigned with 4 cards
const LogicView = ({ station, currentParams }) => {
    // 1. Calculate current state metrics for cards
    const results = calculatePower({
      ...currentParams,
      dcCapacity: station.dc,
      acLimit: station.ac,
      startDate: station.date,
      degradationRate: currentParams.degRate
    });

    const dcInput = station.dc * (currentParams.irradiance / 1000);
    const afterEfficiency = results.dcPotential; // This is DC power after losses (Temp, PR, Deg)
    
    // 2. Generate Curve Data (Comparison)
    const curveData = [];
    for(let i=0; i<=1300; i+=50) {
        // Calculate potential without AC limit comparison first
        // We reuse calculatePower but need to extract intermediate values or simulate it
        // Simulating:
        const irrStandard = i / 1000;
        const tempLoss = 1 + ((-0.0035) * (currentParams.ambientTemp + (i/800)*25 - 25)); // Simplified approximate temp model or reuse calculator logic
        // To be precise, let's just use `calculatePower` but check its return if it offers unclipped power
        
        const res = calculatePower({ 
            ...currentParams, 
            irradiance: i, 
            dcCapacity: station.dc, 
            acLimit: 99999, // High limit to get unclipped
            startDate: station.date, 
            degradationRate: currentParams.degRate 
        });
        
        const actualRes = calculatePower({ 
            ...currentParams, 
            irradiance: i, 
            dcCapacity: station.dc, 
            acLimit: station.ac, 
            startDate: station.date, 
            degradationRate: currentParams.degRate 
        });

        curveData.push({ 
            irr: i, 
            potential: res.finalAC, 
            actual: actualRes.finalAC 
        });
    }

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-bold">核心计算逻辑</h2>
            
            {/* 4 Cards Layout */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 auto-rows-fr">
                {/* Card 1: DC Input */}
                <div className="bg-white/5 p-4 rounded-xl text-white shadow-sm border border-white/5 flex flex-col justify-between h-full min-h-[120px]">
                    <div className="mb-4">
                        <div className="text-xs font-bold text-blue-400 mb-1">DC 理论输入</div>
                        <div className="text-[10px] text-gray-400 opacity-80">Station Capacity × Irradiance</div>
                    </div>
                    <div className="text-2xl font-black whitespace-nowrap">{dcInput.toFixed(2)} <span className="text-sm font-normal text-gray-500">MW</span></div>
                </div>
                
                {/* Card 2: Efficiency */}
                <div className="bg-white/5 p-4 rounded-xl text-white shadow-sm border border-white/5 flex flex-col justify-between h-full min-h-[120px]">
                    <div className="mb-4">
                        <div className="text-xs font-bold text-emerald-400 mb-1">应用综合效率</div>
                        <div className="text-[10px] text-gray-400 opacity-80">× (Base PR - Temp Loss)</div>
                    </div>
                    <div className="text-2xl font-black whitespace-nowrap">{afterEfficiency.toFixed(2)} <span className="text-sm font-normal text-gray-500">MW</span></div>
                </div>

                {/* Card 3: Inverter Limit */}
                <div className="bg-white/5 p-4 rounded-xl text-white shadow-sm border border-white/5 flex flex-col justify-between h-full min-h-[120px]">
                    <div className="mb-4">
                        <div className="text-xs font-bold text-orange-400 mb-1">逆变器限制</div>
                        <div className="text-[10px] text-gray-400 opacity-80">Limit Output to AC (Max)</div>
                    </div>
                    <div className="text-2xl font-black whitespace-nowrap">{station.ac} <span className="text-sm font-normal text-gray-500">MW</span></div>
                </div>

                {/* Card 4: Final Output */}
                <div className="bg-blue-600 p-4 rounded-xl text-white shadow-lg shadow-blue-600/30 flex flex-col justify-between h-full min-h-[120px]">
                    <div className="mb-4">
                        <div className="text-xs font-bold text-blue-200 mb-1">发电功率 (GENERATION)</div>
                        <div className="text-[10px] text-blue-100/60">Final AC Output</div>
                    </div>
                    <div className="text-2xl font-black whitespace-nowrap">{results.finalAC.toFixed(2)} <span className="text-sm font-normal text-blue-200">MW</span></div>
                </div>
            </div>

            {/* P-V Curve Chart */}
            <div className="glass-panel p-6 text-white">
              <div className="flex items-center justify-between mb-8">
                 <div className="text-lg font-bold text-white">功率输出曲线 (P-V Curve)</div>
                 <div className="flex items-center gap-4 text-xs">
                     <div className="flex items-center gap-2">
                         <div className="w-3 h-3 border-2 border-dashed border-gray-400 rounded-sm"></div>
                         <span className="text-gray-400">理论潜力 (无限制)</span>
                     </div>
                     <div className="flex items-center gap-2">
                         <div className="w-3 h-3 bg-blue-600 rounded-sm"></div>
                         <span className="font-bold text-blue-400">实际有功功率 (MW)</span>
                     </div>
                 </div>
              </div>
              
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                 <ComposedChart data={curveData} margin={{top: 10, right: 10, left: -20, bottom: 0}}>
                     <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                     <XAxis 
                        dataKey="irr" 
                        stroke="#6b7280" 
                        fontSize={10} 
                        axisLine={false} 
                        tickLine={false} 
                        label={{ value: '辐照度 (W/m²)', position: 'insideBottom', offset: -10, fill: '#6b7280', fontSize: 10 }} 
                     />
                     <YAxis 
                        stroke="#6b7280" 
                        fontSize={10} 
                        axisLine={false} 
                        tickLine={false} 
                        label={{ value: '功率 (MW)', position: 'insideLeft', angle: -90, offset: 20, fill: '#6b7280', fontSize: 10 }} 
                     />
                     <Tooltip 
                         contentStyle={{ backgroundColor: '#16161a', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '12px' }}
                         itemStyle={{ color: '#fff' }}
                         labelFormatter={(val) => `${val} W/m²`}
                     />
                     <Line type="monotone" dataKey="potential" stroke="#6b7280" strokeWidth={2} strokeDasharray="5 5" dot={false} name="理论潜力" />
                     <Area type="monotone" dataKey="actual" stroke="#3b82f6" strokeWidth={3} fill="#3b82f6" fillOpacity={0.1} name="实际功率" />
                 </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Algorithm Description */}
            <div className="glass-panel p-6">
                <h3 className="text-sm font-bold text-white mb-4">核心算法说明</h3>
                <div className="space-y-2 text-xs text-gray-400">
                    <p>1. <span className="text-energy-primary">理论直流功率</span> = 直流容量 × (当前辐照度 / STC辐照度)</p>
                    <p>2. <span className="text-energy-primary">温度修正</span> = 1 + 温度系数 × (当前组件温度 - 25℃)</p>
                    <p>3. <span className="text-energy-primary">老化修正</span> = (1 - 年衰减率) ^ 运行年限</p>
                    <p>4. <span className="text-energy-primary">最终交流功率</span> = min(修正后直流功率 × 综合效率, 交流逆变器上限)</p>
                </div>
            </div>
        </div>
    );
};

// --- Constants ---
const WEATHER_CODES = {
  0: '晴朗无云', 1: '大致晴朗', 2: '局部多云', 3: '阴天',
  45: '雾', 48: '白霜雾',
  51: '毛毛雨 (轻)', 53: '毛毛雨 (中)', 55: '毛毛雨 (密)',
  56: '冻雨 (轻)', 57: '冻雨 (密)',
  61: '小雨', 63: '中雨', 65: '大雨',
  66: '冻雨 (轻)', 67: '冻雨 (大)',
  71: '小雪', 73: '中雪', 75: '大雪',
  77: '雪粒',
  80: '阵雨 (轻)', 81: '阵雨 (中)', 82: '阵雨 (暴)',
  85: '阵雪 (轻)', 86: '阵雪 (大)',
  95: '雷雨', 96: '雷雨伴冰雹 (轻)', 99: '雷雨伴冰雹 (重)'
};

// --- Main App Component ---
const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('monitor');
  const [currentStationIdx, setCurrentStationIdx] = useState(0);
  const [weather, setWeather] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isAutoMode, setIsAutoMode] = useState(true); 
  const [showToast, setShowToast] = useState(false);
  
  // Manual simulation params
  const [simParams, setSimParams] = useState({
    irradiance: 800,
    ambientTemp: 25,
    basePR: 85,
    degRate: 0.5
  });

  const [effectiveParams, setEffectiveParams] = useState(simParams);
  const station = STATIONS[currentStationIdx];

  // 1. Fetch Weather
  const fetchWeather = async () => {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${station.lat}&longitude=${station.lon}&current=temperature_2m,weather_code,shortwave_radiation,wind_speed_10m&minutely_15=shortwave_radiation,temperature_2m,wind_speed_10m&hourly=shortwave_radiation,temperature_2m&forecast_days=2&timezone=auto`;
      const resp = await fetch(url);
      const data = await resp.json();
      setWeather(data);
      setLastUpdated(new Date());
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    } catch (e) {
      console.error("Weather fetch failed", e);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, [currentStationIdx]);

  // 2. Sync Logic
  useEffect(() => {
    if (isAutoMode && weather?.current) {
      setEffectiveParams(prev => ({
        ...prev,
        irradiance: weather.current.shortwave_radiation || 0,
        ambientTemp: weather.current.temperature_2m || 0,
        basePR: simParams.basePR,
        degRate: simParams.degRate
      }));
    } else {
      setEffectiveParams(simParams);
    }
  }, [isAutoMode, weather, simParams]);

  // 3. Calculate Results
  const results = calculatePower({
    ...effectiveParams,
    dcCapacity: station.dc,
    acLimit: station.ac,
    startDate: station.date,
    degradationRate: effectiveParams.degRate
  });

  if (!isLoggedIn) {
     return <LoginView onLogin={setIsLoggedIn} />;
  }

  const renderContent = () => {
    switch(activeTab) {
      case 'monitor': 
        return <MonitorView 
                  station={station} 
                  results={results} 
                  weather={weather} 
                  isAutoMode={isAutoMode}
                  setIsAutoMode={setIsAutoMode}
                  allStations={STATIONS}
                  currentStationIdx={currentStationIdx}
                  onStationChange={setCurrentStationIdx}
                  currentParams={effectiveParams}
                  manualParams={simParams}
                  onUpdateParams={setSimParams}
               />;
      case 'logic':
        return <LogicView 
                  station={station}
                  currentParams={effectiveParams}
               />;
      case 'weather': 
        return <WeatherView 
                  station={station} 
                  weatherData={weather} 
                  onRefresh={fetchWeather} 
                  lastUpdated={lastUpdated}
               />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-energy-dark text-gray-100 font-sans selection:bg-energy-primary/30 flex flex-col md:flex-row overflow-hidden">
      
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 glass-panel border-r border-white/5 m-4 mr-0 rounded-3xl">
        <div className="p-6">
           <div className="flex items-center gap-2 text-energy-primary mb-1">
             <Activity className="w-6 h-6" />
             <span className="font-bold text-lg tracking-tight">Energy Monitor</span>
           </div>
           <div className="text-[10px] text-gray-500 uppercase tracking-widest pl-8">Pro Dashboard</div>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          <SidebarBtn icon={<Activity />} label="监控台" active={activeTab === 'monitor'} onClick={() => setActiveTab('monitor')} />
          <SidebarBtn icon={<CloudRain />} label="气象预测" active={activeTab === 'weather'} onClick={() => setActiveTab('weather')} />
          <SidebarBtn icon={<Calculator />} label="计算逻辑" active={activeTab === 'logic'} onClick={() => setActiveTab('logic')} />
        </nav>

        <div className="p-6">
           <div className="bg-white/5 rounded-xl p-4">
              <div className="text-xs text-gray-400 mb-2">当前模式</div>
              <div className="flex items-center gap-2">
                 <div className={`w-2 h-2 rounded-full ${isAutoMode ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`} />
                 <span className="font-bold text-sm">{isAutoMode ? '实时数据驱动' : '手动模拟模式'}</span>
              </div>
           </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 relative h-screen overflow-y-auto no-scrollbar">
        <AnimatePresence>
          {showToast && (
            <motion.div 
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 20 }}
              exit={{ opacity: 0, y: -50 }}
              className="absolute top-0 left-0 right-0 z-50 flex justify-center pointer-events-none"
            >
               <div className="bg-emerald-500/90 text-white backdrop-blur px-4 py-2 rounded-full shadow-2xl flex items-center gap-2 text-sm font-bold">
                 <CheckCircle className="w-4 h-4" />
                 数据已更新 ({lastUpdated?.toLocaleTimeString()})
               </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="max-w-3xl mx-auto w-full p-4 md:p-8 pb-24 md:pb-8">
           <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {renderContent()}
            </motion.div>
           </AnimatePresence>
        </div>
      </main>

      {/* Mobile Nav */}
      <nav className="md:hidden fixed bottom-6 left-6 right-6 h-20 glass-panel flex items-center justify-around px-4 z-50 backdrop-blur-xl bg-black/40 border border-white/10">
        <TabButton icon={<Activity />} label="监控" active={activeTab === 'monitor'} onClick={() => setActiveTab('monitor')} />
        <TabButton icon={<CloudRain />} label="天气" active={activeTab === 'weather'} onClick={() => setActiveTab('weather')} />
        <TabButton icon={<Calculator />} label="逻辑" active={activeTab === 'logic'} onClick={() => setActiveTab('logic')} />
      </nav>

    </div>
  );
};

// --- View Components ---

const LoginView = ({ onLogin }) => {
    const [pwd, setPwd] = useState('');
    const [err, setErr] = useState('');
    const [locked, setLocked] = useState(false);

    useEffect(() => {
        checkLockout();
    }, []);

    const checkLockout = () => {
        const lockoutTime = localStorage.getItem('login_lockout_until');
        if (lockoutTime && new Date().getTime() < parseInt(lockoutTime)) {
             setLocked(true);
             const remaining = Math.ceil((parseInt(lockoutTime) - new Date().getTime()) / 60000);
             setErr(`系统已锁定，请能在 ${remaining} 分钟后重试`);
             return true;
        }
        setLocked(false);
        return false;
    };

    const recordAttempt = () => {
        let attempts = parseInt(localStorage.getItem('login_attempts') || '0');
        attempts += 1;
        localStorage.setItem('login_attempts', attempts.toString());

        if (attempts >= 10) {
            const lockoutUntil = new Date().getTime() + (120 * 60 * 1000); // 120 minutes
            localStorage.setItem('login_lockout_until', lockoutUntil.toString());
            checkLockout();
        }
    };

    const check = (e) => {
        e.preventDefault();
        if (checkLockout()) return;

        if(pwd === 'nengjianjikong') {
            localStorage.removeItem('login_attempts');
            localStorage.removeItem('login_lockout_until');
            onLogin(true);
        } else {
            recordAttempt();
            const attempts = parseInt(localStorage.getItem('login_attempts') || '0');
            const left = 10 - attempts;
            setErr(left > 0 ? `密钥错误，还剩 ${left} 次尝试机会` : '错误次数过多，系统锁定');
            setPwd('');
        }
    };

    return (
        <div className="min-h-screen bg-energy-dark flex items-center justify-center p-4">
            <div className="glass-panel p-8 w-full max-w-sm text-center relative overflow-hidden">
                {locked && <div className="absolute inset-0 bg-red-500/10 z-0 animate-pulse pointer-events-none" />}
                
                <div className="mb-6 flex justify-center relative z-10">
                    <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${locked ? 'bg-red-500/20 text-red-500' : 'bg-energy-primary/20 text-energy-primary'}`}>
                        <Lock className="w-8 h-8" />
                    </div>
                </div>
                <h1 className="text-2xl font-bold text-white mb-2 relative z-10">欢迎登录</h1>
                <p className="text-gray-400 text-sm mb-6 relative z-10">新一代能源集控监控平台</p>
                
                <form onSubmit={check} className="space-y-4 relative z-10">
                    <input 
                        type="password" 
                        placeholder={locked ? "系统已锁定" : "请输入访问密钥"}
                        value={pwd}
                        disabled={locked}
                        onChange={e => {setPwd(e.target.value); if(!locked) setErr('');}}
                        className={`w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none transition-colors text-center font-bold ${locked ? 'cursor-not-allowed opacity-50' : 'focus:border-energy-primary'}`}
                    />
                    {err && <div className="text-red-400 text-xs font-bold animate-pulse">{err}</div>}
                    <button 
                        type="submit" 
                        disabled={locked}
                        className={`w-full font-bold py-3 rounded-xl transition-all ${locked ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-energy-primary text-white hover:bg-blue-600 active:scale-95'}`}
                    >
                        {locked ? '锁定中' : '进入系统'}
                    </button>
                </form>
            </div>
        </div>
    );
};

// Monitor: Now has AC Capacity, Ratio, Controls for Subs
const MonitorView = ({ station, results, weather, isAutoMode, setIsAutoMode, allStations, currentStationIdx, onStationChange, currentParams, manualParams, onUpdateParams }) => {
  if (!results) return null;
  const powerPct = (results.finalAC / station.ac) * 100;
  
  // Calculate specific metrics
  const ratio = (station.dc / station.ac).toFixed(2);

  const updateParam = (key, val) => {
    onUpdateParams(prev => ({ ...prev, [key]: val }));
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between">
         <div className="relative group">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">当前监控电站</h2>
            <div className="flex items-center gap-2 cursor-pointer">
              <h1 className="text-2xl font-extrabold text-white">{station.name}</h1>
              <ChevronDown className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" />
            </div>
            <select 
               className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
               value={currentStationIdx}
               onChange={(e) => onStationChange(Number(e.target.value))}
            >
               {allStations.map((s, idx) => <option key={idx} value={idx}>{s.name} ({s.city})</option>)}
            </select>
         </div>
         <div 
            onClick={() => setIsAutoMode(!isAutoMode)}
            className={`cursor-pointer px-3 py-1.5 rounded-full border text-xs font-bold flex items-center gap-2 transition-all ${isAutoMode ? 'bg-green-500/10 border-green-500 text-green-400' : 'bg-amber-500/10 border-amber-500 text-amber-400'}`}
         >
            <div className={`w-2 h-2 rounded-full ${isAutoMode ? 'bg-green-500' : 'bg-amber-500'}`} />
            {isAutoMode ? '实时' : '模拟'}
         </div>
      </div>

      {/* Main Gauge */}
      <div className="glass-panel p-8 text-center relative overflow-hidden group border-t-4 border-t-energy-primary">
         <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-energy-primary/5 to-transparent pointer-events-none" />
         
         <div className="text-gray-400 text-sm font-bold uppercase tracking-wider mb-4">实时发电功率</div>
         <div className="flex items-baseline justify-center gap-2 mb-4">
           <span className="text-7xl md:text-8xl font-black text-white tracking-tighter drop-shadow-2xl">{results.finalAC.toFixed(1)}</span>
           <span className="text-2xl font-bold text-energy-primary">MW</span>
         </div>
         <div className="relative h-4 w-full bg-white/5 rounded-full overflow-hidden">
            <motion.div 
               initial={{ width: 0 }}
               animate={{ width: `${powerPct}%` }}
               transition={{ type: "spring", stiffness: 50 }}
               className={`h-full rounded-full ${results.isClipping ? 'bg-red-500' : 'bg-energy-primary'} shadow-[0_0_20px_rgba(59,130,246,0.6)]`}
            />
         </div>
         <div className="flex justify-between mt-2 text-xs font-bold text-gray-500">
             <span>0 MW</span>
             <span>{station.ac} MW (由逆变器限幅)</span>
         </div>
         {results.isClipping && (
           <div className="mt-4 inline-flex items-center gap-2 text-red-400 bg-red-500/10 px-3 py-1 rounded-lg animate-pulse">
               <Info className="w-4 h-4" />
               <span className="text-xs font-bold">功率限幅中 (CLIPPING ACTIVE)</span>
           </div>
         )}
      </div>

      {/* Metrics Grid - Added AC Capacity and Ratio */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
         <StatCard icon={<Sun className="text-amber-400"/>} label="辐照度" value={currentParams.irradiance} unit="W/m²" />
         <StatCard icon={<Thermometer className="text-red-400"/>} label="环境温度" value={currentParams.ambientTemp} unit="°C" />
         <StatCard icon={<Zap className="text-purple-400"/>} label="理论直流功率" value={results.dcPotential.toFixed(1)} unit="MW" />
         <StatCard icon={<Activity className="text-emerald-400"/>} label="系统效率 (PR)" value={results.totalPRPct.toFixed(1)} unit="%" />
      </div>

      <div className="grid grid-cols-2 gap-4">
          <StatCard icon={<Cpu className="text-blue-400" />} label="交流侧容量 (AC)" value={station.ac} unit="MW" />
          <StatCard icon={<TrendingUp className="text-pink-400" />} label="容配比 (DC/AC)" value={ratio} unit=": 1" />
      </div>

     {/* Controls (Merged into Monitor) */}
     <div className="glass-panel p-6 space-y-6">
         <div className="flex items-center gap-2 mb-4 pb-2 border-b border-white/5">
            <Settings className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-bold text-gray-200">参数配置</span>
         </div>

         <div className={`space-y-6 transition-all ${isAutoMode ? 'opacity-50 grayscale pointer-events-none' : ''}`}>
            <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] uppercase font-bold text-gray-500">环境参数 {isAutoMode && '(实时锁定)'}</span>
            </div>
            <SliderControl label="模拟辐照度" value={isAutoMode ? currentParams.irradiance : manualParams.irradiance} min={0} max={1300} step={10} unit="W/m²" color="bg-amber-400" onChange={(v) => updateParam('irradiance', v)} />
            <SliderControl label="模拟环境温度" value={isAutoMode ? currentParams.ambientTemp : manualParams.ambientTemp} min={-10} max={50} step={1} unit="°C" color="bg-red-400" onChange={(v) => updateParam('ambientTemp', v)} />
         </div>

         <div className="space-y-6 pt-4 border-t border-white/5">
             <span className="text-[10px] uppercase font-bold text-gray-500 block mb-2">系统参数 (始终可调)</span>
             <SliderControl label="基础系统效率 (PR)" value={manualParams.basePR} min={50} max={98} step={1} unit="%" color="bg-energy-primary" onChange={(v) => updateParam('basePR', v)} />
             <SliderControl label="年衰减率" value={manualParams.degRate} min={0} max={3} step={0.1} unit="%" color="bg-purple-400" onChange={(v) => updateParam('degRate', v)} />
         </div>
      </div>
      
      {/* Footer Info */}
      <div className="grid grid-cols-2 gap-4 text-center opacity-60">
          <div className="bg-white/5 rounded-xl p-3">
             <div className="text-lg font-bold text-white">{station.dc} MWp</div>
             <div className="text-[10px] uppercase">直流侧容量</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3">
             <div className="text-lg font-bold text-white">{station.city}</div>
             <div className="text-[10px] uppercase">地理位置</div>
          </div>
      </div>
    </div>
  );
};



// Weather View: Now with Weather Description
const WeatherView = ({ station, weatherData, onRefresh, lastUpdated }) => {
    if (!weatherData) return <div className="p-8 text-center text-gray-500 animate-pulse">正在获取气象卫星数据...</div>;

    const current = weatherData.current;
    
    // Process Data
    const minutely15 = weatherData.minutely_15;
    const todayData = [];
    if(minutely15) {
        for(let i=0; i<Math.min(96, minutely15.time.length); i++) {
             const irr = minutely15.shortwave_radiation[i];
             const temp = minutely15.temperature_2m[i];
             const wind = minutely15.wind_speed_10m ? minutely15.wind_speed_10m[i] : (current.wind_speed_10m || 0);
             const timeStr = new Date(minutely15.time[i]).getHours() + ':' + ('0'+new Date(minutely15.time[i]).getMinutes()).slice(-2);
             
             const res = calculatePower({
                irradiance: irr,
                ambientTemp: temp,
                basePR: 85,
                dcCapacity: station.dc,
                acLimit: station.ac,
                startDate: station.date
             });

             todayData.push({ 
                 time: timeStr, 
                 power: res.finalAC, 
                 irr: irr, 
                 temp: temp,
                 wind: wind 
             });
        }
    }
    
    const hourly = weatherData.hourly;
    const tmrData = [];
    if(hourly) {
        for(let i=24; i<48; i++) {
             const irr = hourly.shortwave_radiation[i];
             const temp = hourly.temperature_2m[i];
             const timeStr = new Date(hourly.time[i]).getHours() + ':00';

             const res = calculatePower({
                irradiance: irr,
                ambientTemp: temp,
                basePR: 85,
                dcCapacity: station.dc,
                acLimit: station.ac,
                startDate: station.date
             });

             tmrData.push({ 
                 time: timeStr, 
                 power: res.finalAC, 
                 irr: irr,
                 temp: temp
             });
        }
    }

    const weatherDesc = WEATHER_CODES[current.weather_code] || `未知 (${current.weather_code})`;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold">气象中心</h2>
                  {lastUpdated && <p className="text-xs text-gray-500">更新于: {lastUpdated.toLocaleTimeString()}</p>}
                </div>
                <button onClick={onRefresh} className="p-3 bg-blue-600 rounded-xl hover:bg-blue-500 active:scale-95 transition-all shadow-lg shadow-blue-600/20">
                    <RefreshCw className="w-5 h-5 text-white" />
                </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                 <WeatherTile icon={<Sun className="text-amber-400"/>} value={current.shortwave_radiation} unit="W/m²" label="辐照度" />
                 <WeatherTile icon={<Wind className="text-blue-400"/>} value={current.wind_speed_10m} unit="km/h" label="风速" />
                 <WeatherTile icon={<Thermometer className="text-red-400"/>} value={current.temperature_2m} unit="°C" label="温度" />
                 <WeatherTile icon={<CloudRain className="text-gray-400"/>} value={weatherDesc} unit="" label="当前天气" />
            </div>

            <ChartSection 
                title="今日短期功率预测 (15min级)" 
                data={todayData} 
                primaryColor="#f59e0b" 
                secondaryColor="#fbbf24"
                showWind={true}
            />
            <ChartSection 
                title="明日全天功率预测 (小时级)" 
                data={tmrData} 
                primaryColor="#3b82f6" 
                secondaryColor="#93c5fd"
            />
        </div>
    );
};

// --- Shared Helper Components ---

const SidebarBtn = ({ icon, label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${active ? 'bg-energy-primary text-white shadow-lg shadow-energy-primary/20' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
  >
    {React.cloneElement(icon, { className: "w-5 h-5" })}
    <span className="font-bold text-sm">{label}</span>
  </button>
);

const TabButton = ({ icon, label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`flex flex-col items-center justify-center transition-all ${active ? 'text-energy-primary scale-110' : 'text-gray-500'}`}
  >
    {React.cloneElement(icon, { className: "w-6 h-6 mb-1" })}
    <span className="text-[10px] font-bold uppercase">{label}</span>
    {active && <motion.div layoutId="tab-indicator" className="w-1 h-1 rounded-full bg-energy-primary mt-1" />}
  </button>
);

const WeatherTile = ({ icon, value, unit, label }) => (
    <div className="glass-panel p-4 flex items-center gap-4">
        <div className="text-2xl">{icon}</div>
        <div>
            <div className={`font-bold ${typeof value === 'string' ? 'text-sm' : 'text-xl'}`}>{value} <span className="text-xs text-gray-500">{unit}</span></div>
            <div className="text-[10px] font-bold text-gray-500 uppercase">{label}</div>
        </div>
    </div>
);

const ChartSection = ({ title, data, primaryColor, secondaryColor, showWind }) => (
    <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-bold text-gray-500 uppercase">{title}</div>
            <div className="flex items-center gap-4 text-[10px] font-bold">
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full" style={{backgroundColor: primaryColor}} />
                    <span>功率 (MW)</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-sm opacity-50" style={{backgroundColor: secondaryColor}} />
                    <span>辐照度 (W/m²)</span>
                </div>
            </div>
        </div>
        <div className="h-72">
           <ResponsiveContainer width="100%" height="100%">
               <ComposedChart data={data}>
                   <defs>
                       <linearGradient id={`grad${primaryColor}`} x1="0" y1="0" x2="0" y2="1">
                           <stop offset="5%" stopColor={primaryColor} stopOpacity={0.3}/>
                           <stop offset="95%" stopColor={primaryColor} stopOpacity={0}/>
                       </linearGradient>
                   </defs>
                   <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                   <XAxis dataKey="time" stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} interval={6} />
                   <YAxis yAxisId="left" stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} label={{ value: 'MW', position: 'insideTopLeft', offset: 0, fill: '#6b7280', fontSize: 8 }} />
                   <YAxis yAxisId="right" orientation="right" stroke="#6b7280" fontSize={10} axisLine={false} tickLine={false} domain={[0, 1400]} label={{ value: 'W/m²', position: 'insideTopRight', offset: 0, fill: '#6b7280', fontSize: 8 }} />
                   <Tooltip 
                       contentStyle={{ backgroundColor: '#16161a', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '12px' }}
                       labelFormatter={(label) => `时间: ${label}`}
                       formatter={(value, name) => {
                           if(name === 'power') return [`${value.toFixed(1)} MW`, '预测功率'];
                           if(name === 'irr') return [`${value} W/m²`, '辐照度'];
                           if(name === 'temp') return [`${value}°C`, '气温'];
                           if(name === 'wind') return [`${value} km/h`, '风速'];
                           return [value, name];
                       }}
                   />
                   <Bar yAxisId="right" dataKey="irr" fill={secondaryColor} opacity={0.3} barSize={4} radius={[2, 2, 0, 0]} />
                   <Area yAxisId="left" type="monotone" dataKey="power" stroke={primaryColor} fill={`url(#grad${primaryColor})`} strokeWidth={3} />
               </ComposedChart>
           </ResponsiveContainer>
        </div>
    </div>
);

const SliderControl = ({ label, value, min, max, step, unit, color, onChange }) => (
  <div className="space-y-4">
    <div className="flex justify-between items-end">
        <label className="text-xs font-bold text-gray-500 uppercase tracking-widest">{label}</label>
        <div className="text-xl font-bold text-white">{value} <span className="text-xs text-gray-500 uppercase">{unit}</span></div>
    </div>
    <div className="relative h-6 flex items-center">
        <div className="absolute w-full h-1.5 bg-white/5 rounded-full" />
        <input 
            type="range" min={min} max={max} step={step} value={value} 
            onChange={(e) => onChange(parseFloat(e.target.value))}
            className="w-full appearance-none bg-transparent cursor-pointer z-10 relative
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-lg
                [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-energy-primary"
        />
    </div>
  </div>
);

const StatCard = ({ icon, label, value, unit }) => (
    <div className="glass-panel p-4 flex flex-col items-center justify-center text-center hover:bg-white/10 transition-colors">
        <div className="mb-2 bg-white/5 p-2 rounded-full">{icon}</div>
        <div className="text-lg font-bold text-white leading-none mb-1">{value} <span className="text-xs text-gray-400 font-normal">{unit}</span></div>
        <div className="text-[10px] font-bold text-gray-500 uppercase">{label}</div>
    </div>
);

export default App;

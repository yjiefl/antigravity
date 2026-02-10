const express = require('express');
const path = require('path');
const morgan = require('morgan');
const cors = require('cors');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3001;
const DB_PATH = path.join(__dirname, 'data.db');
const LOG_DIR = path.join(__dirname, '../logs');
const ACCESS_LOG = path.join(LOG_DIR, 'access.log');
const ERROR_LOG = path.join(LOG_DIR, 'error.log');

// 确保日志目录存在
try {
	if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
} catch (e) {
	console.error('无法创建或访问日志目录:', e.message);
}

const logToError = (msg) => {
	const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
	const line = `[${timestamp}] ERROR: ${msg}\n`;
	console.error(line);
	try {
		fs.appendFileSync(ERROR_LOG, line);
	} catch (e) {
		// 忽略写入失败
	}
};

// 初始化数据库
const db = new sqlite3.Database(DB_PATH, (err) => {
	if (err) {
		console.error('❌ 数据库连接失败:', err.message);
	} else {
		console.log('✅ 已连接到 SQLite 数据库');
		// 存单表
		db.run(`CREATE TABLE IF NOT EXISTS snapshots (
			id TEXT PRIMARY KEY,
			name TEXT,
			data TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`);
		// 场站配置表
		db.run(`CREATE TABLE IF NOT EXISTS stations (
			name TEXT PRIMARY KEY,
			lon REAL,
			lat REAL,
			region TEXT,
			azimuth REAL DEFAULT 0,
			tilt REAL DEFAULT 0
		)`, () => {
			// 仅在场站表为空时插入预设数据，防止用户删除后被重新填充
			db.get("SELECT COUNT(*) as count FROM stations", [], (err, row) => {
				if (err || (row && row.count > 0)) return; // 已有数据则跳过
				console.log('📦 场站表为空，正在插入预设数据...');
				const initialStations = [
					['峙书', 107.2879, 22.1235, '崇左宁明'],
					['守旗', 107.6518, 22.4539, '崇左扶绥'],
					['弄滩', 107.2668, 22.2477, '崇左江州'],
					['派岸', 107.272, 22.3027, '崇左江州'],
					['寨安', 107.0092, 22.0386, '崇左宁明'],
					['强胜', 107.5495, 22.3185, '崇左江州'],
					['康宁', 107.2714, 22.087, '崇左宁明'],
					['驮堪', 107.2574, 23.1326, '崇左天等'],
					['浦峙', 107.3855, 22.1573, '崇左宁明'],
					['岑凡', 107.8472, 22.3392, '崇左扶绥'],
					['樟木', 109.3785, 23.379, '贵港'],
					['榕木', 109.494, 22.9408, '贵港'],
					['那小', 107.4159, 22.1853, '崇左']
				];
				initialStations.forEach(s => {
					db.run("INSERT OR IGNORE INTO stations (name, lon, lat, region, azimuth, tilt) VALUES (?,?,?,?,?,?)", [...s, 0, 0]);
				});
			});
		});
	}
});

// 中间件
app.use(cors());
app.use(express.json({ limit: '50mb' })); 

// 网站访问日志记录
app.use(morgan('dev')); 

// 自定义操作日志函数 (带容错)
const logAction = (req, action, details = '') => {
	const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
	const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
	const line = `[${timestamp}] ${ip} - ${action} ${details}\n`;
	console.log(line);
	try {
		// 仅在目录存在时尝试写入
		if (fs.existsSync(LOG_DIR)) {
			fs.appendFileSync(ACCESS_LOG, line);
		}
	} catch (e) {
		// 忽略写入失败
	}
};



// --- API 接口 ---

app.get('/api/health', (req, res) => {
	logAction(req, 'Health Check');
	res.json({ ok: true, status: 'online', time: new Date() });
});

// 获取支持的所有场站列表
app.get('/api/stations', (req, res) => {
	db.all("SELECT * FROM stations ORDER BY name ASC", [], (err, rows) => {
		if (err) return res.status(500).json({ error: err.message });
		res.json(rows);
	});
});

// 保存/导入场站
app.post('/api/stations', (req, res) => {
	const stations = Array.isArray(req.body) ? req.body : [req.body];
	logAction(req, 'Save Stations', `Count: ${stations.length}`);

	db.serialize(() => {
		db.run("BEGIN TRANSACTION");
		const stmt = db.prepare("INSERT OR REPLACE INTO stations (name, lon, lat, region, azimuth, tilt) VALUES (?, ?, ?, ?, ?, ?)");
		stations.forEach(s => {
			stmt.run([s.name.trim(), s.lon, s.lat, (s.region || '').trim(), s.azimuth || 0, s.tilt || 0]);
		});
		stmt.finalize();
		db.run("COMMIT", (err) => {
			if (err) {
				console.error("Transaction commit failed:", err);
				// 尝试回滚
				db.run("ROLLBACK");
				return res.status(500).json({ error: "Database transaction failed: " + err.message });
			}
			res.json({ success: true, count: stations.length });
		});
	});
});

app.delete('/api/stations/:name', (req, res) => {
	logAction(req, 'Delete Station', `Name: ${req.params.name}`);
	db.run("DELETE FROM stations WHERE name = ?", [req.params.name], function(err) {
		if (err) return res.status(500).json({ error: err.message });
		res.json({ success: true });
	});
});

// Promise-based helpers for sqlite3
function dbGetAsync(sql, params) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

function dbRunAsync(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve(this);
        });
    });
}

// 更新场站名称
app.put('/api/stations/:oldName', async (req, res) => {
	const { oldName } = req.params;
	const { newName } = req.body;

	if (!newName || oldName === newName) {
		return res.status(400).json({ error: '新名称无效或与旧名称相同' });
	}

	logAction(req, 'Rename Station', `From: ${oldName}, To: ${newName}`);

	try {
		// 1. 检查新名称是否已存在
		const existingNew = await dbGetAsync("SELECT name FROM stations WHERE name = ?", [newName]);
		if (existingNew) {
			return res.status(409).json({ error: `名称 "${newName}" 已存在，无法重命名` });
		}

		// 2. 检查旧场站是否存在
		const station = await dbGetAsync("SELECT * FROM stations WHERE name = ?", [oldName]);
		if (!station) {
			return res.status(404).json({ error: `未找到要重命名的场站 "${oldName}"` });
		}

		// 3. 执行事务
		await dbRunAsync("BEGIN TRANSACTION");
		try {
			// Create new record
			await dbRunAsync(
				"INSERT INTO stations (name, lon, lat, region, azimuth, tilt) VALUES (?, ?, ?, ?, ?, ?)",
				[newName, station.lon, station.lat, station.region, station.azimuth, station.tilt]
			);
			
			// Delete old record
			await dbRunAsync("DELETE FROM stations WHERE name = ?", [oldName]);
			
			// Commit
			await dbRunAsync("COMMIT");
			
			res.json({ success: true, message: `场站已从 ${oldName} 重命名为 ${newName}` });
		} catch (transactionError) {
			await dbRunAsync("ROLLBACK");
			// Rethrow to be caught by the outer catch block
			throw transactionError;
		}
	} catch (err) {
		console.error(`重命名场站 "${oldName}" 到 "${newName}" 失败:`, err);
		res.status(500).json({ error: `数据库操作失败: ${err.message}` });
	}
});


// 获取历史辐照度数据
app.get('/api/weather/irradiance', async (req, res) => {
	const { stationName, date } = req.query;
	if (!stationName || !date) return res.status(400).json({ error: '缺少场站名称或日期参数' });

	db.get("SELECT * FROM stations WHERE name = ?", [stationName], async (err, coords) => {
		if (err) {
			logToError(`Database error fetching station ${stationName}: ${err.message}`);
			return res.status(500).json({ error: '数据库查询失败' });
		}
		if (!coords) {
			logAction(req, 'Weather Data Failed', `Station not found: ${stationName}`);
			return res.status(404).json({ error: `未找到场站 "${stationName}" 的坐标映射，请先在场站管理中配置` });
		}

		if (!coords.lat || !coords.lon) {
			logAction(req, 'Weather Data Failed', `Coords missing for: ${stationName}`);
			return res.status(400).json({ error: `场站 "${stationName}" 缺少有效的经纬度信息` });
		}

		logAction(req, 'Fetch Weather Data', `Station: ${stationName} (${coords.lat}, ${coords.lon}), Date: ${date}`);
		try {
			const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${coords.lat}&longitude=${coords.lon}&start_date=${date}&end_date=${date}&hourly=shortwave_radiation&timezone=auto`;
			
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
			
			const response = await fetch(url, {
				headers: { 'User-Agent': 'AntigravityDataAnalyzer/1.1' },
				signal: controller.signal
			});
			clearTimeout(timeoutId);

			if (!response.ok) {
				const errText = await response.text();
				logToError(`Open-Meteo API Error (${response.status}): ${errText}`);
				return res.status(response.status).json({ error: `天气服务请求失败 (HTTP ${response.status})` });
			}

			const data = await response.json();
			if (!data || !data.hourly) {
				logToError(`Open-Meteo returned invalid data format: ${JSON.stringify(data)}`);
				return res.status(502).json({ error: '天气服务返回了无效的数据格式' });
			}

			const result = [];
			const times = data.hourly.time || [];
			const values = data.hourly.shortwave_radiation || [];
			
			for (let i = 0; i < times.length; i++) {
					// Open-Meteo 返回的是本地 ISO 格式 (例如 2026-02-10T07:00)
					// 强制在末尾附加 +08:00 以确保 JS 引擎将其解析为中国时间
					const currentTime = new Date(times[i] + "+08:00");
					const currentVal = values[i];
					const nextVal = (i < times.length - 1) ? values[i + 1] : currentVal;
					for (let j = 0; j < 4; j++) {
						const interpolatedTime = new Date(currentTime.getTime() + j * 15 * 60000);
						const weight = j / 4;
						const interpolatedVal = currentVal + (nextVal - currentVal) * weight;
						result.push({ time: interpolatedTime, value: parseFloat(interpolatedVal.toFixed(2)) });
					}
				}
				res.json({ stationName, date, data: result, region: coords.region });
			} catch (err) {
			console.error('Fetch error:', err);
			const msg = err.name === 'AbortError' ? '请求超时' : err.message;
			res.status(500).json({ error: '获取天气数据失败: ' + msg });
		}
	});
});

// 获取所有存单
app.get('/api/snapshots', (req, res) => {
	logAction(req, 'Get Snapshots');
	db.all("SELECT * FROM snapshots ORDER BY created_at DESC", [], (err, rows) => {
		if (err) return res.status(500).json({ error: err.message });
		const records = rows.map(row => ({ ...JSON.parse(row.data), id: row.id, name: row.name }));
		res.json(records);
	});
});

// 保存存单
app.post('/api/snapshots', (req, res) => {
	const record = req.body;
	const id = record.id || Date.now().toString();
	const name = record.name || '未命名记录';
	logAction(req, 'Save Snapshot', `Name: ${name}`);
	db.run("INSERT OR REPLACE INTO snapshots (id, name, data) VALUES (?, ?, ?)", [id, name, JSON.stringify(record)], (err) => {
		if (err) return res.status(500).json({ error: err.message });
		res.json({ success: true, id });
	});
});

app.delete('/api/snapshots/:id', (req, res) => {
	logAction(req, 'Delete Snapshot', `ID: ${req.params.id}`);
	db.run("DELETE FROM snapshots WHERE id = ?", [req.params.id], (err) => {
		if (err) return res.status(500).json({ error: err.message });
		res.json({ success: true });
	});
});

app.delete('/api/snapshots', (req, res) => {
	logAction(req, 'Clear All Snapshots');
	db.run("DELETE FROM snapshots", [], (err) => {
		if (err) return res.status(500).json({ error: err.message });
		res.json({ success: true });
	});
});

app.get('/api/logs', (req, res) => {
	const type = req.query.type || 'access';
	const targetFile = type === 'error' ? ERROR_LOG : ACCESS_LOG;
	if (fs.existsSync(targetFile)) {
		const logs = fs.readFileSync(targetFile, 'utf8').split('\n').filter(Boolean).slice(-500);
		res.json({ logs });
	} else {
		res.json({ logs: [] });
	}
});

if (process.env.NODE_ENV === 'production') {
	const frontendDist = path.join(__dirname, '../frontend/dist');
	if (fs.existsSync(frontendDist)) {
		app.use(express.static(frontendDist));
		app.get('*', (req, res) => res.sendFile(path.join(frontendDist, 'index.html')));
	}
}

app.listen(PORT, () => {
	console.log(`🚀 后端服务已启动: http://localhost:${PORT}`);
});

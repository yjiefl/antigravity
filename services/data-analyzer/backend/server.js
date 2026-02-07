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
const LOG_DIR = path.join(__dirname, '../log');
const ACCESS_LOG = path.join(LOG_DIR, 'access.log');
const ERROR_LOG = path.join(LOG_DIR, 'error.log');

// 确保日志目录存在
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

const logToError = (msg) => {
	const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
	fs.appendFileSync(ERROR_LOG, `[${timestamp}] ERROR: ${msg}\n`);
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
			// 预设数据 (按照用户最新要求的 场站,经度,纬度 格式)
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
	}
});

// 中间件
app.use(cors());
app.use(express.json({ limit: '50mb' })); 

// 网站访问日志记录到文件
const accessLogStream = fs.createWriteStream(ACCESS_LOG, { flags: 'a' });
app.use(morgan('combined', { stream: accessLogStream }));
app.use(morgan('dev')); 

// 自定义操作日志函数
const logAction = (req, action, details = '') => {
	const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
	const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
	const logMessage = `[${timestamp}] IP: ${ip} | ACTION: ${action} | DETAILS: ${details}\n`;
	fs.appendFileSync(ACCESS_LOG, logMessage);
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
	
	const stmt = db.prepare("INSERT OR REPLACE INTO stations (name, lon, lat, region, azimuth, tilt) VALUES (?, ?, ?, ?, ?, ?)");
	stations.forEach(s => {
		stmt.run([s.name, s.lon, s.lat, s.region || '', s.azimuth || 0, s.tilt || 0]);
	});
	stmt.finalize();
	res.json({ success: true });
});

app.delete('/api/stations/:name', (req, res) => {
	logAction(req, 'Delete Station', `Name: ${req.params.name}`);
	db.run("DELETE FROM stations WHERE name = ?", [req.params.name], function(err) {
		if (err) return res.status(500).json({ error: err.message });
		res.json({ success: true });
	});
});

// 获取历史辐照度数据
app.get('/api/weather/irradiance', (req, res) => {
	const { stationName, date } = req.query;
	if (!stationName || !date) return res.status(400).json({ error: '缺少场站名称或日期参数' });

	db.get("SELECT * FROM stations WHERE name = ?", [stationName], async (err, coords) => {
		if (err || !coords) {
			logAction(req, 'Weather Data Failed', `Not found: ${stationName}`);
			return res.status(404).json({ error: `未找到场站 "${stationName}" 的坐标映射` });
		}

		logAction(req, 'Fetch Weather Data', `Station: ${stationName}, Date: ${date}`);
		try {
			const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${coords.lat}&longitude=${coords.lon}&start_date=${date}&end_date=${date}&hourly=shortwave_radiation&timezone=auto`;
			const response = await fetch(url);
			const data = await response.json();

			if (data.hourly) {
				const result = [];
				const times = data.hourly.time;
				const values = data.hourly.shortwave_radiation;
				for (let i = 0; i < times.length; i++) {
					const currentTime = new Date(times[i]);
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
			} else {
				res.status(502).json({ error: '天气 API 未返回数据', details: data });
			}
		} catch (err) {
			res.status(500).json({ error: '获取天气数据失败: ' + err.message });
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

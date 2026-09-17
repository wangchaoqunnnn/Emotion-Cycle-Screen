#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪周期选股系统 - V2.0 后端服务
Flask + SQLite，提供REST API，支持多用户，集成AKShare数据采集

使用方法：
  pip install flask akshare pandas
  python server.py
  默认监听 http://127.0.0.1:5000
"""

import os
import json
import uuid
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emotion_screener.db')

# ==================== 数据库 ====================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            limit_up INTEGER DEFAULT 0,
            limit_down INTEGER DEFAULT 0,
            up_count INTEGER DEFAULT 0,
            down_count INTEGER DEFAULT 0,
            red_rate REAL DEFAULT 0,
            seal_rate REAL DEFAULT 0,
            promote_rate REAL DEFAULT 0,
            first_promote REAL DEFAULT 0,
            max_board INTEGER DEFAULT 0,
            ever_limit INTEGER DEFAULT 0,
            sealed INTEGER DEFAULT 0,
            temperature INTEGER DEFAULT 0,
            stage TEXT DEFAULT 'warm',
            UNIQUE(user_id, date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT DEFAULT '',
            board INTEGER DEFAULT 1,
            change REAL DEFAULT 0,
            price REAL DEFAULT 0,
            turnover REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            seal_amount REAL DEFAULT 0,
            concept TEXT DEFAULT '',
            volume_ratio REAL DEFAULT 1,
            main_inflow REAL DEFAULT 0,
            market_cap REAL DEFAULT 0,
            UNIQUE(user_id, date, code),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT DEFAULT '',
            price REAL DEFAULT 0,
            qty INTEGER DEFAULT 0,
            fee REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            note TEXT DEFAULT '',
            stage TEXT DEFAULT 'unknown',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            strategy TEXT DEFAULT 'warm',
            filters_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT UNIQUE NOT NULL,
            data_json TEXT DEFAULT '{}',
            note TEXT DEFAULT '',
            conclusion TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_snapshots_user ON snapshots(user_id);
        CREATE INDEX IF NOT EXISTS idx_stocks_user ON stocks(user_id, date);
        CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);
    ''')
    db.commit()
    db.close()
    print(f"[数据库] 初始化完成: {DATABASE}")

# ==================== 认证 ====================
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            return jsonify({'error': '缺少API Key'}), 401
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE api_key = ?', (api_key,)).fetchone()
        if not user:
            return jsonify({'error': '无效的API Key'}), 401
        g.user_id = user['id']
        g.username = user['username']
        return f(*args, **kwargs)
    return decorated

# ==================== 工具函数 ====================
SNAPSHOT_FIELD_MAP = {
    'limitUp': 'limit_up', 'limitDown': 'limit_down',
    'upCount': 'up_count', 'downCount': 'down_count',
    'redRate': 'red_rate', 'sealRate': 'seal_rate',
    'promoteRate': 'promote_rate', 'firstPromote': 'first_promote',
    'maxBoard': 'max_board', 'everLimit': 'ever_limit',
}
STOCK_FIELD_MAP = {
    'sealAmount': 'seal_amount', 'volumeRatio': 'volume_ratio',
    'mainInflow': 'main_inflow', 'marketCap': 'market_cap',
}

def normalize_snapshot(snap):
    """将前端camelCase字段映射为后端snake_case"""
    result = dict(snap)
    for camel, snake in SNAPSHOT_FIELD_MAP.items():
        if camel in result and snake not in result:
            result[snake] = result[camel]
    return result

def normalize_stock(stock):
    """将前端camelCase字段映射为后端snake_case"""
    result = dict(stock)
    for camel, snake in STOCK_FIELD_MAP.items():
        if camel in result and snake not in result:
            result[snake] = result[camel]
    return result

def snapshot_to_camel(snap):
    """将后端snake_case快照转换为前端camelCase格式"""
    result = {}
    reverse_map = {v: k for k, v in SNAPSHOT_FIELD_MAP.items()}
    for key, val in snap.items():
        if key in reverse_map:
            result[reverse_map[key]] = val
        elif key == 'user_id':
            continue
        else:
            result[key] = val
    return result

def stock_to_camel(stock):
    """将后端snake_case股票转换为前端camelCase格式"""
    result = {}
    reverse_map = {v: k for k, v in STOCK_FIELD_MAP.items()}
    for key, val in stock.items():
        if key in reverse_map:
            result[reverse_map[key]] = val
        elif key == 'user_id':
            continue
        else:
            result[key] = val
    return result

# ==================== 路由 ====================
@app.route('/')
def index():
    # 自动获取或创建demo用户的API Key，注入到HTML中
    db = get_db()
    row = db.execute("SELECT api_key FROM users WHERE username = 'demo' LIMIT 1").fetchone()
    if not row:
        # 自动创建demo用户
        import uuid, hashlib as hl
        api_key = hl.sha256(f"demo{uuid.uuid4()}".encode()).hexdigest()[:32]
        db.execute("INSERT INTO users (username, api_key) VALUES ('demo', ?)", (api_key,))
        db.commit()
    else:
        api_key = row['api_key']
    # 读取HTML并注入API Key
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    inject = f'<script>window.__SERVER_API_KEY__ = "{api_key}";window.__SERVER_ORIGIN__ = window.location.origin;</script>'
    html = html.replace('</head>', inject + '\n</head>')
    from flask import Response
    return Response(html, mimetype='text/html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Emotion Cycle Screener API', 'version': '2.0'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    api_key = hashlib.sha256(f"{username}{uuid.uuid4()}".encode()).hexdigest()[:32]
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, api_key) VALUES (?, ?)', (username, api_key))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400
    return jsonify({'username': username, 'api_key': api_key, 'message': '注册成功，请保存API Key'})

# --- 情绪快照 ---
@app.route('/api/snapshots', methods=['GET'])
@require_auth
def get_snapshots():
    db = get_db()
    rows = db.execute('SELECT * FROM snapshots WHERE user_id = ? ORDER BY date', (g.user_id,)).fetchall()
    return jsonify([snapshot_to_camel(dict(r)) for r in rows])

@app.route('/api/snapshots', methods=['POST'])
@require_auth
def save_snapshot():
    data = request.get_json() or {}
    date = data.get('date')
    if not date:
        return jsonify({'error': '日期不能为空'}), 400
    db = get_db()
    fields = ['limit_up','limit_down','up_count','down_count','red_rate','seal_rate',
              'promote_rate','first_promote','max_board','ever_limit','sealed','temperature','stage']
    values = {f: data.get(f, 0) for f in fields}
    values['user_id'] = g.user_id
    values['date'] = date
    placeholders = ', '.join(['?'] * (len(fields) + 2))
    columns = 'user_id, date, ' + ', '.join(fields)
    updates = ', '.join([f"{f}=excluded.{f}" for f in fields])
    db.execute(f'INSERT INTO snapshots ({columns}) VALUES ({placeholders}) ON CONFLICT(user_id, date) DO UPDATE SET {updates}',
                 [values['user_id'], values['date']] + [values[f] for f in fields])
    db.commit()
    return jsonify({'message': '快照已保存', 'date': date})

@app.route('/api/snapshots/batch', methods=['POST'])
@require_auth
def batch_snapshots():
    data = request.get_json() or {}
    snapshots = data.get('snapshots', [])
    db = get_db()
    count = 0
    for snap in snapshots:
        snap = normalize_snapshot(snap)
        date = snap.get('date')
        if not date:
            continue
        fields = ['limit_up','limit_down','up_count','down_count','red_rate','seal_rate',
                  'promote_rate','first_promote','max_board','ever_limit','sealed','temperature','stage']
        values = {f: snap.get(f, 0) for f in fields}
        placeholders = ', '.join(['?'] * (len(fields) + 2))
        columns = 'user_id, date, ' + ', '.join(fields)
        updates = ', '.join([f"{f}=excluded.{f}" for f in fields])
        db.execute(f'INSERT INTO snapshots ({columns}) VALUES ({placeholders}) ON CONFLICT(user_id, date) DO UPDATE SET {updates}',
                     [g.user_id, date] + [values[f] for f in fields])
        count += 1
    db.commit()
    return jsonify({'message': f'批量保存成功', 'count': count})

# --- 涨停股票 ---
@app.route('/api/stocks', methods=['GET'])
@require_auth
def get_stocks():
    date = request.args.get('date')
    db = get_db()
    if date:
        rows = db.execute('SELECT * FROM stocks WHERE user_id = ? AND date = ? ORDER BY board DESC, code', (g.user_id, date)).fetchall()
    else:
        rows = db.execute('SELECT * FROM stocks WHERE user_id = ? ORDER BY date DESC, board DESC', (g.user_id,)).fetchall()
    return jsonify([stock_to_camel(dict(r)) for r in rows])

@app.route('/api/stocks', methods=['POST'])
@require_auth
def save_stocks():
    data = request.get_json() or {}
    stocks = data.get('stocks', [])
    date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    # 先删除该日期旧数据
    db.execute('DELETE FROM stocks WHERE user_id = ? AND date = ?', (g.user_id, date))
    count = 0
    for s in stocks:
        s = normalize_stock(s)
        code = s.get('code')
        if not code:
            continue
        db.execute('''INSERT INTO stocks (user_id, date, code, name, board, change, price, turnover, amount, seal_amount, concept, volume_ratio, main_inflow, market_cap)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (g.user_id, date, code, s.get('name',''), s.get('board',1), s.get('change',0),
                    s.get('price',0), s.get('turnover',0), s.get('amount',0), s.get('seal_amount',0),
                    s.get('concept',''), s.get('volume_ratio',1), s.get('main_inflow',0), s.get('market_cap',0)))
        count += 1
    db.commit()
    return jsonify({'message': '涨停股票已保存', 'date': date, 'count': count})

# --- 交易记录 ---
@app.route('/api/trades', methods=['GET'])
@require_auth
def get_trades():
    db = get_db()
    rows = db.execute('SELECT * FROM trades WHERE user_id = ? ORDER BY date DESC, created_at DESC', (g.user_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/trades', methods=['POST'])
@require_auth
def add_trade():
    data = request.get_json() or {}
    trade_id = data.get('id') or str(uuid.uuid4())
    db = get_db()
    db.execute('''INSERT OR REPLACE INTO trades (id, user_id, date, type, code, name, price, qty, fee, amount, note, stage)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
               (trade_id, g.user_id, data.get('date',''), data.get('type','buy'), data.get('code',''),
                data.get('name',''), data.get('price',0), data.get('qty',0), data.get('fee',0),
                data.get('amount',0), data.get('note',''), data.get('stage','unknown')))
    db.commit()
    return jsonify({'message': '交易记录已保存', 'id': trade_id})

@app.route('/api/trades/<trade_id>', methods=['DELETE'])
@require_auth
def delete_trade(trade_id):
    db = get_db()
    db.execute('DELETE FROM trades WHERE id = ? AND user_id = ?', (trade_id, g.user_id))
    db.commit()
    return jsonify({'message': '交易记录已删除'})

# --- 选股条件 ---
@app.route('/api/conditions', methods=['GET'])
@require_auth
def get_conditions():
    db = get_db()
    rows = db.execute('SELECT * FROM conditions WHERE user_id = ? ORDER BY created_at DESC', (g.user_id,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['filters'] = json.loads(d.pop('filters_json', '{}'))
        result.append(d)
    return jsonify(result)

@app.route('/api/conditions', methods=['POST'])
@require_auth
def save_condition():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '条件名称不能为空'}), 400
    filters_json = json.dumps(data.get('filters', {}), ensure_ascii=False)
    db = get_db()
    db.execute('''INSERT INTO conditions (user_id, name, strategy, filters_json) VALUES (?, ?, ?, ?)
                  ON CONFLICT(user_id, name) DO UPDATE SET strategy=excluded.strategy, filters_json=excluded.filters_json''',
               (g.user_id, name, data.get('strategy','warm'), filters_json))
    db.commit()
    return jsonify({'message': '选股条件已保存', 'name': name})

@app.route('/api/conditions/<int:cond_id>', methods=['DELETE'])
@require_auth
def delete_condition(cond_id):
    db = get_db()
    db.execute('DELETE FROM conditions WHERE id = ? AND user_id = ?', (cond_id, g.user_id))
    db.commit()
    return jsonify({'message': '选股条件已删除'})

# --- 复盘记录 ---
@app.route('/api/reviews', methods=['GET'])
@require_auth
def get_reviews():
    db = get_db()
    rows = db.execute('SELECT * FROM reviews WHERE user_id = ? ORDER BY date DESC', (g.user_id,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d['data'] = json.loads(d.pop('data_json', '{}'))
        result.append(d)
    return jsonify(result)

@app.route('/api/reviews', methods=['POST'])
@require_auth
def save_review():
    data = request.get_json() or {}
    date = data.get('date')
    if not date:
        return jsonify({'error': '日期不能为空'}), 400
    data_json = json.dumps(data.get('data', {}), ensure_ascii=False)
    db = get_db()
    db.execute('''INSERT INTO reviews (user_id, date, data_json, note, conclusion) VALUES (?, ?, ?, ?, ?)
                  ON CONFLICT(date) DO UPDATE SET data_json=excluded.data_json, note=excluded.note, conclusion=excluded.conclusion''',
               (g.user_id, date, data_json, data.get('note',''), data.get('conclusion','')))
    db.commit()
    return jsonify({'message': '复盘记录已保存', 'date': date})

# --- 导出导入 ---
@app.route('/api/export', methods=['GET'])
@require_auth
def export_data():
    db = get_db()
    snapshots = [dict(r) for r in db.execute('SELECT * FROM snapshots WHERE user_id = ? ORDER BY date', (g.user_id,)).fetchall()]
    stocks = [dict(r) for r in db.execute('SELECT * FROM stocks WHERE user_id = ? ORDER BY date, board DESC', (g.user_id,)).fetchall()]
    trades = [dict(r) for r in db.execute('SELECT * FROM trades WHERE user_id = ? ORDER BY date DESC', (g.user_id,)).fetchall()]
    conditions = []
    for r in db.execute('SELECT * FROM conditions WHERE user_id = ?', (g.user_id,)).fetchall():
        d = dict(r)
        d['filters'] = json.loads(d.pop('filters_json', '{}'))
        conditions.append(d)
    reviews = []
    for r in db.execute('SELECT * FROM reviews WHERE user_id = ?', (g.user_id,)).fetchall():
        d = dict(r)
        d['data'] = json.loads(d.pop('data_json', '{}'))
        reviews.append(d)
    return jsonify({
        'exported_at': datetime.now().isoformat(),
        'username': g.username,
        'snapshots': snapshots,
        'stocks': stocks,
        'trades': trades,
        'conditions': conditions,
        'reviews': reviews
    })

@app.route('/api/import', methods=['POST'])
@require_auth
def import_data():
    data = request.get_json() or {}
    db = get_db()
    count = {'snapshots': 0, 'stocks': 0, 'trades': 0, 'conditions': 0, 'reviews': 0}

    for snap in data.get('snapshots', []):
        date = snap.get('date')
        if not date: continue
        fields = ['limit_up','limit_down','up_count','down_count','red_rate','seal_rate',
                  'promote_rate','first_promote','max_board','ever_limit','sealed','temperature','stage']
        values = [snap.get(f, 0) for f in fields]
        placeholders = ', '.join(['?'] * (len(fields) + 2))
        columns = 'user_id, date, ' + ', '.join(fields)
        updates = ', '.join([f"{f}=excluded.{f}" for f in fields])
        db.execute(f'INSERT INTO snapshots ({columns}) VALUES ({placeholders}) ON CONFLICT(user_id, date) DO UPDATE SET {updates}',
                     [g.user_id, date] + values)
        count['snapshots'] += 1

    for s in data.get('stocks', []):
        code = s.get('code')
        date = s.get('date') or datetime.now().strftime('%Y-%m-%d')
        if not code: continue
        db.execute('''INSERT OR IGNORE INTO stocks (user_id, date, code, name, board, change, price, turnover, amount, seal_amount, concept, volume_ratio, main_inflow, market_cap)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (g.user_id, date, code, s.get('name',''), s.get('board',1), s.get('change',0),
                    s.get('price',0), s.get('turnover',0), s.get('amount',0), s.get('seal_amount',0),
                    s.get('concept',''), s.get('volume_ratio',1), s.get('main_inflow',0), s.get('market_cap',0)))
        count['stocks'] += 1

    for t in data.get('trades', []):
        tid = t.get('id') or str(uuid.uuid4())
        db.execute('''INSERT OR REPLACE INTO trades (id, user_id, date, type, code, name, price, qty, fee, amount, note, stage)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (tid, g.user_id, t.get('date',''), t.get('type','buy'), t.get('code',''),
                    t.get('name',''), t.get('price',0), t.get('qty',0), t.get('fee',0),
                    t.get('amount',0), t.get('note',''), t.get('stage','unknown')))
        count['trades'] += 1

    db.commit()
    return jsonify({'message': '数据导入成功', 'count': count})

# --- AKShare数据采集 ---
@app.route('/api/fetch', methods=['POST'])
@require_auth
def fetch_data():
    """从AKShare获取最新行情数据并保存到数据库"""
    try:
        import akshare as ak
        import pandas as pd
    except ImportError:
        return jsonify({'error': '请先安装 akshare: pip install akshare pandas'}), 500

    data = request.get_json() or {}
    days = data.get('days', 5)
    today = datetime.now().strftime('%Y-%m-%d')

    # 获取最近交易日
    try:
        trade_dates = ak.tool_trade_date_hist_sina()
        trade_dates = trade_dates[trade_dates['trade_date'] <= today]
        recent_dates = trade_dates.tail(days)['trade_date'].tolist()
    except Exception as e:
        return jsonify({'error': f'获取交易日历失败: {str(e)}'}), 500

    db = get_db()
    result = {'dates': [], 'stocks_count': 0}

    for date_str in recent_dates:
        date_str = str(date_str)[:10]
        try:
            # 涨停股池
            zt_df = ak.stock_zt_pool_em(date=date_str)
            if zt_df is not None and len(zt_df) > 0:
                limit_up = len(zt_df)
                max_board = int(zt_df['连板数'].max()) if '连板数' in zt_df.columns else 1
                # 保存股票
                stocks = []
                for _, row in zt_df.iterrows():
                    stock = {
                        'code': str(row.get('代码', '')),
                        'name': str(row.get('名称', '')),
                        'board': int(row.get('连板数', 1)),
                        'change': float(row.get('涨跌幅', 10)),
                        'price': float(row.get('最新价', 0)),
                        'turnover': float(row.get('换手率', 0)),
                        'amount': float(row.get('成交额', 0)) / 1e8 if row.get('成交额', 0) else 0,
                        'seal_amount': float(row.get('封单金额', 0)) / 1e4 if row.get('封单金额', 0) else 0,
                        'concept': str(row.get('所属行业', '')),
                        'volume_ratio': float(row.get('量比', 1)),
                    }
                    stocks.append(stock)
                    db.execute('''INSERT OR IGNORE INTO stocks (user_id, date, code, name, board, change, price, turnover, amount, seal_amount, concept, volume_ratio, main_inflow, market_cap)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (g.user_id, date_str, stock['code'], stock['name'], stock['board'], stock['change'],
                                stock['price'], stock['turnover'], stock['amount'], stock['seal_amount'],
                                stock['concept'], stock['volume_ratio'], 0, 0))
                result['stocks_count'] += len(stocks)
            else:
                limit_up = 0
                max_board = 0

            # 跌停股池
            try:
                dt_df = ak.stock_zt_pool_dtgc_em(date=date_str)
                limit_down = len(dt_df) if dt_df is not None else 0
            except:
                limit_down = 0

            # 市场广度
            try:
                sh_df = ak.stock_zh_index_spot_em()
                total = len(sh_df)
                up = len(sh_df[sh_df['涨跌幅'] > 0])
                down = len(sh_df[sh_df['涨跌幅'] < 0])
                red_rate = round(up / total * 100, 1) if total > 0 else 50
            except:
                up = down = 0
                red_rate = 50

            # 估算封板率和晋级率
            seal_rate = 60 + (max_board * 2) if limit_up > 0 else 70
            promote_rate = round((max_board / max(limit_up, 1)) * 100, 1)

            # 温度计算（简化版）
            temp = min(100, int(
                limit_up / 150 * 20 +
                max(0, 100 - limit_down / 30 * 100) * 0.15 +
                red_rate * 0.2 +
                seal_rate * 0.15 +
                promote_rate * 0.15 +
                min(100, max_board / 7 * 100) * 0.15
            ))

            # 阶段判定
            if temp < 30: stage = 'ice'
            elif temp < 45: stage = 'repair' if temp > 35 else 'ebb'
            elif temp < 65: stage = 'warm'
            elif temp < 80: stage = 'hot'
            else: stage = 'hot'

            # 保存快照
            fields = ['limit_up','limit_down','up_count','down_count','red_rate','seal_rate',
                      'promote_rate','first_promote','max_board','ever_limit','sealed','temperature','stage']
            values = [limit_up, limit_down, up, down, red_rate, seal_rate,
                      promote_rate, promote_rate * 0.8, max_board, int(limit_up * 1.5), limit_up, temp, stage]
            placeholders = ', '.join(['?'] * (len(fields) + 2))
            columns = 'user_id, date, ' + ', '.join(fields)
            updates = ', '.join([f"{f}=excluded.{f}" for f in fields])
            db.execute(f'INSERT INTO snapshots ({columns}) VALUES ({placeholders}) ON CONFLICT(user_id, date) DO UPDATE SET {updates}',
                         [g.user_id, date_str] + values)
            result['dates'].append({'date': date_str, 'limit_up': limit_up, 'temperature': temp, 'stage': stage})

        except Exception as e:
            result['dates'].append({'date': date_str, 'error': str(e)})
            continue

    db.commit()
    return jsonify({'message': '数据采集完成', 'result': result})


# --- 实时行情（当日盘中/收盘即时数据） ---
@app.route('/api/realtime', methods=['GET'])
@require_auth
def realtime():
    """实时获取当日市场情绪数据（涨停/跌停/红盘率/封板率/晋级率 + 涨停股列表）"""
    try:
        import akshare as ak
    except ImportError:
        return jsonify({'error': '请先安装 akshare: pip install akshare'}), 500

    now = datetime.now()
    today_compact = now.strftime('%Y%m%d')
    today_iso = now.strftime('%Y-%m-%d')
    # 判断交易时段
    hm = now.hour * 60 + now.minute
    is_trading = (570 <= hm <= 690) or (780 <= hm <= 900)
    market_status = '交易中' if is_trading else '已收盘'

    result = {
        'date': today_iso, 'time': now.strftime('%H:%M:%S'),
        'marketStatus': market_status, 'isTrading': is_trading,
    }
    errors = []

    # 1. 涨停池
    limit_up = 0; max_board = 0; stocks = []
    try:
        zt = ak.stock_zt_pool_em(date=today_compact)
        if zt is not None and len(zt) > 0:
            limit_up = len(zt)
            max_board = int(zt['连板数'].max()) if '连板数' in zt.columns else 1
            for _, row in zt.iterrows():
                seal_yi = float(row.get('封板资金', 0)) / 1e8
                stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'board': int(row.get('连板数', 1)),
                    'change': float(row.get('涨跌幅', 10)),
                    'price': float(row.get('最新价', 0)),
                    'turnover': float(row.get('换手率', 0)),
                    'amount': float(row.get('成交额', 0)) / 1e8,
                    'sealAmount': round(seal_yi, 2),
                    'concept': str(row.get('所属行业', '')),
                    'volumeRatio': 1.0,
                    'firstSeal': str(row.get('首次封板时间', '')),
                    'breakCount': int(row.get('炸板次数', 0)),
                })
    except Exception as e:
        errors.append(f'涨停池: {e}')

    # 2. 跌停池
    limit_down = 0
    try:
        dt = ak.stock_zt_pool_dtgc_em(date=today_compact)
        limit_down = len(dt) if dt is not None else 0
    except Exception as e:
        errors.append(f'跌停池: {e}')

    # 3. 炸板池（计算封板率）
    broken = 0
    try:
        zb = ak.stock_zt_pool_zbgc_em(date=today_compact)
        broken = len(zb) if zb is not None else 0
    except Exception as e:
        errors.append(f'炸板池: {e}')

    # 封板率 = 涨停 / (涨停 + 炸板)
    seal_rate = round(limit_up / (limit_up + broken) * 100, 1) if (limit_up + broken) > 0 else 0

    # 4. 市场广度（乐咕乐股，轻量）
    up_count = down_count = 0; red_rate = 50.0
    try:
        act = ak.stock_market_activity_legu()
        d = dict(zip(act['item'], act['value']))
        up_count = int(float(d.get('上涨', 0)))
        down_count = int(float(d.get('下跌', 0)))
        total_breadth = up_count + down_count + int(float(d.get('平盘', 0)))
        red_rate = round(up_count / total_breadth * 100, 1) if total_breadth > 0 else 50.0
    except Exception as e:
        errors.append(f'市场广度: {e}')

    # 5. 晋级率 = 今日连板数 / 昨日涨停数
    promote_rate = 0.0
    try:
        lianban = len([s for s in stocks if s['board'] >= 2])
        # 从数据库取昨日涨停数
        db = get_db()
        row = db.execute('SELECT limit_up FROM snapshots WHERE user_id=? ORDER BY date DESC LIMIT 1',
                        (g.user_id,)).fetchone()
        prev_limit_up = row['limit_up'] if row else limit_up
        promote_rate = round(lianban / prev_limit_up * 100, 1) if prev_limit_up > 0 else 0
    except Exception as e:
        errors.append(f'晋级率: {e}')

    # 6. 温度计算（与前端一致的加权模型）
    # 涨停家数20% 跌停15% 红盘率20% 封板率15% 晋级率15% 最高连板15%
    lu_score = min(100, limit_up / 120 * 100)
    ld_score = max(0, 100 - limit_down / 20 * 100)
    temp = int(lu_score * 0.20 + ld_score * 0.15 + red_rate * 0.20 +
               seal_rate * 0.15 + promote_rate * 0.15 +
               min(100, max_board / 7 * 100) * 0.15)

    if temp < 30: stage = 'ice'
    elif temp < 45: stage = 'repair' if temp > 35 else 'ebb'
    elif temp < 65: stage = 'warm'
    elif temp < 80: stage = 'hot'
    else: stage = 'hot'

    stage_names = {'ice': '冰点', 'repair': '修复', 'warm': '升温', 'hot': '高潮', 'ebb': '退潮'}

    result.update({
        'limitUp': limit_up, 'limitDown': limit_down,
        'upCount': up_count, 'downCount': down_count,
        'redRate': red_rate, 'sealRate': seal_rate,
        'promoteRate': promote_rate, 'maxBoard': max_board,
        'everLimit': limit_up + broken, 'sealed': limit_up,
        'temperature': temp, 'stage': stage,
        'stageName': stage_names.get(stage, stage),
        'broken': broken,
        'stocks': sorted(stocks, key=lambda x: (-x['board'], x['code'])),
        'errors': errors if errors else None,
    })
    return jsonify(result)


# ==================== 启动 ====================
if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("  情绪周期选股系统 V2.0 后端服务")
    print("  API地址: http://127.0.0.1:5000")
    print("  健康检查: http://127.0.0.1:5000/api/health")
    print("  注册用户: POST /api/auth/register {username: 'xxx'}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)

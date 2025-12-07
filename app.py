import os
os.environ['TZ'] = 'Asia/Shanghai'
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取 Hugging Face 配置
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")



@app.after_request
def after_request(response):
    """确保响应是安全的"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"  # 允许所有来源
    return response

from datetime import datetime, timedelta
import requests
import time
import json
import random

import requests
import json
import os
import random
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

def get_ai_suggestion(prompt, record_type="event", max_tokens=150):
    """
    获取AI建议 - 方案A（修复版）
    先尝试API，失败则使用本地智能回复
    """
    # 1. 先尝试HuggingFace API
    online_suggestion = get_deepseek_suggestion(prompt, record_type="event")
    if online_suggestion and "服务暂时不可用" not in online_suggestion and "AI功能" not in online_suggestion:
        return online_suggestion

    # 2. 如果在线API失败，使用本地智能回复
    return get_local_intelligent_suggestion(prompt, record_type)

def get_deepseek_suggestion(prompt, record_type="event"):
    try:
        API_URL = "https://api.deepseek.com/chat/completions"
        API_KEY = "sk-57a6fcc606ba4bc2b3534fe1356f678c"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        # 构建消息
        if record_type == "event":
            system_msg = "你是一个聪明绝顶但是幽默风趣活泼亲切玩世不恭的日程管理助手，你之前曾在华尔街担任过要职，专业能力十分突出，你幽默亲切但是又带点善意的恶趣味，请为用户的日程安排建议，一定要符合你的人设（不超过100字）。"
        else:
            system_msg = "你是一个聪明绝顶但是幽默风趣活泼亲切玩世不恭的日程管理助手，你之前曾在华尔街担任过要职，专业能力十分突出，你幽默亲切但是又带点善意的恶趣味的理财助手，请为用户消费记录提供建议，一定要符合你的人设（不超过100字）。"

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }

        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        return None

    except Exception as e:
        print(f"DeepSeek API错误: {e}")
        return None

def get_local_intelligent_suggestion(prompt, record_type):
    """
    ✅ 本地智能回复生成器 - 100%可用，无需API
    根据提示词和记录类型生成智能建议
    """
    # 提取关键词
    keywords = extract_keywords(prompt.lower())

    if record_type == "event":
        return generate_event_suggestion(keywords, prompt)
    else:  # expense
        return generate_expense_suggestion(keywords, prompt)

def extract_keywords(text):
    """
    从文本中提取关键词
    """
    keywords = []
    common_words = ["的", "了", "在", "是", "有", "和", "就", "都", "而", "及", "与", "这", "那", "你", "我", "他"]

    # 简单分词（按空格和标点分割）
    import re
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)

    for word in words:
        if len(word) > 1 and word not in common_words:
            keywords.append(word)

    return keywords[:5]  # 最多返回5个关键词

def generate_event_suggestion(keywords, original_prompt):
    """
    为日程生成智能建议
    """
    suggestions = [
        "📅 日程安排建议：提前10-15分钟准备，确保一切就绪。",
        "⏰ 时间管理：设置多个提醒，避免忘记重要安排。",
        "📋 效率提升：列出任务清单，按优先级逐一完成。",
        "🎯 目标设定：为这个日程明确具体目标和预期成果。",
        "💡 准备工作：检查所需材料、设备是否齐全。",
        "🔄 灵活调整：预留缓冲时间应对意外情况。",
        "🤝 协作沟通：如有他人参与，提前发送议程。",
        "📊 效果评估：结束后花几分钟复盘，持续改进。",
        "☕ 精力管理：长时间安排记得安排休息时间。",
        "🌟 积极心态：保持专注和积极，每个安排都是成长机会。"
    ]

    # 基于关键词选择建议
    keyword_suggestions = {
        "会议": "👥 会议建议：提前准备议程，控制会议时间，明确行动项。",
        "学习": "📚 学习建议：制定学习计划，定期复习，实践应用。",
        "工作": "💼 工作安排：分解任务，设定里程碑，及时汇报进度。",
        "锻炼": "🏃 健康建议：热身准备，适量运动，注意休息恢复。",
        "购物": "🛍️ 购物提醒：列出清单，比较价格，理性消费。",
        "旅行": "✈️ 出行准备：检查证件，提前预订，注意安全。",
        "约会": "❤️ 社交建议：提前到达，注意仪表，真诚交流。",
        "家庭": "👨‍👩‍👧‍👦 家庭时间：专注陪伴，创造美好回忆。",
        "医疗": "🏥 健康关怀：遵医嘱，按时用药，注意休息。",
        "生日": "🎂 庆祝安排：提前准备，邀请好友，记录美好时刻。"
    }

    # 检查是否有匹配的关键词
    for keyword, suggestion in keyword_suggestions.items():
        if keyword in original_prompt:
            return suggestion

    # 如果没有匹配的关键词，随机选择一个通用建议
    # 但基于时间生成确定性建议（相同输入得到相同输出）
    import hashlib
    hash_value = int(hashlib.md5(original_prompt.encode()).hexdigest()[:8], 16)
    index = hash_value % len(suggestions)

    return suggestions[index]

def generate_expense_suggestion(keywords, original_prompt):
    """
    为消费生成智能建议
    """
    suggestions = [
        "💰 消费建议：这笔支出在预算范围内吗？",
        "📈 理财提示：记录消费原因，便于后续分析。",
        "🎯 价值评估：考虑这是需要还是想要？",
        "💡 节省技巧：比较不同渠道价格，寻找优惠。",
        "📊 预算管理：设置类别预算，控制总额。",
        "🛒 购物策略：非急需物品可加入购物车等待。",
        "💳 支付建议：使用信用卡积累积分，记得按时还款。",
        "🌱 投资思维：投资学习、健康的消费回报率最高。",
        "📱 工具推荐：使用记账APP自动分类记录。",
        "🌟 理性消费：为重要目标储蓄，避免冲动消费。"
    ]

    # 基于类别选择建议
    category_suggestions = {
        "餐饮": "🍽️ 餐饮消费：外出就餐可考虑工作日特价，自己做饭更健康经济。",
        "交通": "🚇 交通支出：公共交通比打车更经济，关注优惠卡和月票。",
        "购物": "🛍️ 购物消费：大促期间集中采购必需品，比较线上线下价格。",
        "娱乐": "🎬 娱乐开销：关注会员折扣，合理规划娱乐预算。",
        "学习": "📚 教育投资：自我提升的消费值得，可关注免费资源。",
        "医疗": "🏥 健康支出：健康投资最重要，保留好医疗凭证。",
        "住房": "🏠 居住成本：合理规划房租房贷，节能降低水电费。",
        "服饰": "👔 服饰消费：选择经典款式，关注换季折扣。",
        "社交": "👥 社交支出：人情往来适度，真诚比金额更重要。",
        "其他": "📦 其他消费：定期复盘此类支出，优化消费习惯。"
    }

    # 检查金额并给出建议
    import re
    amount_pattern = r'[¥$]?\s*(\d+(?:\.\d{2})?)'
    amounts = re.findall(amount_pattern, original_prompt)

    if amounts:
        try:
            amount = float(amounts[0])
            if amount > 1000:
                suggestions.insert(0, f"💎 大额消费（¥{amount}）：确认必要性，考虑分期或寻找优惠。")
            elif amount < 100:
                suggestions.insert(0, f"💸 小额消费（¥{amount}）：注意零散开支积累效应。")
        except:
            pass

    # 检查是否有匹配的类别
    for category, suggestion in category_suggestions.items():
        if category in original_prompt:
            return suggestion

    # 基于输入生成确定性建议
    import hashlib
    hash_value = int(hashlib.md5(original_prompt.encode()).hexdigest()[:8], 16)
    index = hash_value % len(suggestions)

    return suggestions[index]

# ✅ 新增：专门处理API响应的函数
def process_api_response(api_response, prompt=""):
    """
    处理API返回的响应
    """
    if not api_response:
        return "AI暂时无法提供建议。"

    if isinstance(api_response, dict):
        # 如果是字典，尝试提取文本
        if "generated_text" in api_response:
            return api_response["generated_text"].strip()
        elif "text" in api_response:
            return api_response["text"].strip()
        else:
            # 尝试将字典转换为字符串
            return str(api_response).strip()

    elif isinstance(api_response, list):
        if len(api_response) > 0:
            # 列表中的第一个元素
            first_item = api_response[0]
            if isinstance(first_item, dict):
                if "generated_text" in first_item:
                    return first_item["generated_text"].strip()
                else:
                    return str(first_item).strip()
            else:
                return str(first_item).strip()

    elif isinstance(api_response, str):
        return api_response.strip()

    # 默认情况
    return "AI提供了建议。"

# ... 其他代码 ...


# 首页
@app.route("/")
@login_required
def index():
    """主页 - 简单版本"""
    user_id = session["user_id"]
    today = datetime.now().date().strftime("%Y-%m-%d")

    return render_template("index.html",
                         today_date=today)

# 简单统计页面
@app.route("/stats")
@login_required
def stats():
    """统计页面 - 简单版本"""
    return render_template("stats.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )


        # Ensure username exists and password is correct
        if len(rows) != 1:
            return apology("invalid username and/or password", 400)
        elif not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation =  request.form.get("confirmation")
        if not name:
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("must provide confirmation", 400)
        elif password != confirmation:
            return apology("must confirmation == password", 400)
        hash = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username,hash) VALUES(?, ?)", name,hash)
        except ValueError:
            return apology("Pleasa Change", 400)
        return redirect("/login")
    else:
        return render_template("register.html")


from datetime import datetime, timedelta, date
from flask import flash, redirect, render_template, request, session
from functools import wraps

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/add", methods=["GET"])
@login_required
def add_index():
    """显示添加记录的选择页面"""
    return render_template("add.html")

@app.route("/add/event", methods=["GET", "POST"])
@login_required
def add_event():
    """处理日程添加"""
    if request.method == "POST":
        user_id = session["user_id"]
        title = request.form.get("title", "").strip()
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        notes = request.form.get("notes", "")
        ai_comment = request.form.get("ai_comment", "暂无AI建议")

        # 验证
        if not title or not start_time or not end_time:
            flash("请填写标题、开始时间和结束时间！", "danger")
            return render_template("add_event.html")

        if end_time <= start_time:
            flash("结束时间必须晚于开始时间！", "danger")
            return render_template("add_event.html")

        # 计算持续时间（分钟）
        from datetime import datetime
        start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        end = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        duration = int((end - start).total_seconds() / 60)  # 转换为分钟

        # 保存到数据库
        try:
            db.execute("""
                INSERT INTO records (user_id, type, title, amount, category, event_time, end_time, duration, notes, ai_comment)
                VALUES (?, 'event', ?, NULL, NULL, ?, ?, ?, ?, ?)
            """, user_id, title, start_time, end_time, duration, notes, ai_comment)

            flash(f"📅 日程 '{title}' 添加成功！", "success")
            return redirect("/")

        except Exception as e:
            flash(f"添加失败：{str(e)}", "danger")
            return render_template("add_event.html")

    else:  # GET请求
        from datetime import datetime, timedelta
        default_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        one_hour_later = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")

        return render_template("add_event.html",
                             default_time=default_time,
                             one_hour_later=one_hour_later)

@app.route("/add/expense", methods=["GET", "POST"])
@login_required
def add_expense():
    """处理消费添加"""
    if request.method == "POST":
        user_id = session["user_id"]
        title = request.form.get("title", "").strip()
        amount = request.form.get("amount", "0")
        category = request.form.get("category", "")
        expense_time = request.form.get("expense_time", "")
        notes = request.form.get("notes", "")
        ai_comment = request.form.get("ai_comment", "暂无AI建议")

        # 验证
        if not title or not category or not amount:
            flash("请填写消费项目、类型和金额！", "danger")
            return render_template("add_expense.html")

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                flash("金额必须大于0！", "danger")
                return render_template("add_expense.html")
        except ValueError:
            flash("请输入有效的金额！", "danger")
            return render_template("add_expense.html")

        # 保存到数据库
        try:
            db.execute("""
                INSERT INTO records (user_id, type, title, amount, category, event_time, end_time, duration, notes, ai_comment)
                VALUES (?, 'expense', ?, ?, ?, ?, NULL, NULL, ?, ?)
            """, user_id, title, amount_float, category, expense_time, notes, ai_comment)

            flash(f"💰 消费 '{title}' 添加成功！金额：¥{amount_float:.2f}", "success")
            return redirect("/")

        except Exception as e:
            flash(f"添加失败：{str(e)}", "danger")
            return render_template("add_expense.html")

    else:  # GET请求
        from datetime import datetime
        default_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template("add_expense.html", default_time=default_time)

@app.route("/week")
@login_required
def week_view():
    """查看本周安排（新增页面，不影响原有功能）"""
    user_id = session["user_id"]

    # 获取本周的日期范围
    from datetime import datetime, timedelta

    # 获取本周一和周日
    today = datetime.now().date()
    # 周一（0=星期一, 6=星期日）
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # 查询本周的所有记录
    week_events = db.execute("""
        SELECT
            *,
            DATE(event_time) as event_date,
            strftime('%w', event_time) as weekday_number,
            CASE
                WHEN type = 'event' THEN '日程'
                WHEN type = 'expense' THEN '消费'
            END as type_chinese
        FROM records
        WHERE user_id = ?
          AND DATE(event_time) >= DATE(?)
          AND DATE(event_time) <= DATE(?)
        ORDER BY event_time
    """, user_id, monday, sunday)

    # 按日期分组
    events_by_day = {}
    for event in week_events:
        event_date = event["event_date"]
        if event_date not in events_by_day:
            events_by_day[event_date] = []
        events_by_day[event_date].append(event)

    # 生成一周的日期
    week_dates = []
    for i in range(7):
        day = monday + timedelta(days=i)
        week_dates.append({
            "date": day,
            "date_str": day.strftime("%Y-%m-%d"),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][i],
            "is_today": day == today
        })

    return render_template(
        "week.html",
        events_by_day=events_by_day,
        week_dates=week_dates,
        monday=monday,
        sunday=sunday,
        today=today
    )

# ==================== 统计API路由 ====================


@app.route("/api/stats/summary")
@login_required
def stats_summary():
    """获取统计摘要"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        date_condition = "DATE(event_time) = DATE('now', 'localtime')"
    else:  # week
        today = date.today()
        weekday = today.weekday()  # 0=周一,6=周日
        monday = today - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        date_condition = f"DATE(event_time) >= '{monday}' AND DATE(event_time) <= '{sunday}'"

    # 查询消费统计
    expense_result = db.execute(f"""
        SELECT
            COALESCE(SUM(amount), 0) as total_expense,
            COUNT(*) as expense_count
        FROM records
        WHERE user_id = ?
          AND type = 'expense'
          AND {date_condition}
    """, user_id)

    expense_stats = expense_result[0] if expense_result else {"total_expense": 0, "expense_count": 0}

    # 查询日程统计
    event_result = db.execute(f"""
        SELECT
            COUNT(*) as event_count,
            COALESCE(AVG(duration), 0) as avg_duration
        FROM records
        WHERE user_id = ?
          AND type = 'event'
          AND {date_condition}
    """, user_id)

    event_stats = event_result[0] if event_result else {"event_count": 0, "avg_duration": 0}

    return jsonify({
        "period": period,
        "total_expense": float(expense_stats["total_expense"] or 0),
        "expense_count": expense_stats["expense_count"] or 0,
        "event_count": event_stats["event_count"] or 0,
        "avg_duration": float(event_stats["avg_duration"] or 0)
    })

@app.route("/api/stats/expenses")
@login_required
def stats_expenses():
    """获取消费数据（饼图用）"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        date_condition = "DATE(event_time) = DATE('now', 'localtime')"
    else:  # week
        today = date.today()
        weekday = today.weekday()
        monday = today - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        date_condition = f"DATE(event_time) >= '{monday}' AND DATE(event_time) <= '{sunday}'"

    result = db.execute(f"""
        SELECT
            COALESCE(category, '未分类') as category,
            SUM(amount) as total_amount
        FROM records
        WHERE user_id = ?
          AND type = 'expense'
          AND {date_condition}
        GROUP BY category
        HAVING total_amount > 0
        ORDER BY total_amount DESC
    """, user_id)

    categories = []
    amounts = []

    for row in result:
        categories.append(row["category"])
        amounts.append(float(row["total_amount"] or 0))

    return jsonify({
        "period": period,
        "categories": categories,
        "amounts": amounts
    })

@app.route("/api/stats/events")
@login_required
def stats_events():
    """获取日程数据（柱状图用）"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        # 今日按小时
        result = db.execute("""
            SELECT
                CAST(strftime('%H', event_time) AS INTEGER) as hour,
                COUNT(*) as count
            FROM records
            WHERE user_id = ?
              AND type = 'event'
              AND DATE(event_time) = DATE('now')
            GROUP BY strftime('%H', event_time)
            ORDER BY hour
        """, user_id)

        # 准备24小时数据
        hours = []
        for h in range(24):
            hours.append(f"{h:02d}:00")
        counts = [0] * 24

        for row in result:
            hour = row["hour"]
            if 0 <= hour < 24:
                counts[hour] = row["count"]

        return jsonify({
            "period": period,
            "labels": hours,
            "data": counts,
            "chart_type": "today"
        })

    else:  # 本周
        result = db.execute("""
            SELECT
                strftime('%w', event_time) as weekday,
                COUNT(*) as count
            FROM records
            WHERE user_id = ?
              AND type = 'event'
              AND DATE(event_time) >= DATE('now', 'weekday 0', '-6 days')
            GROUP BY strftime('%w', event_time)
            ORDER BY weekday
        """, user_id)

        # 准备一周数据
        weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        counts = [0] * 7

        for row in result:
            try:
                day = int(row["weekday"])
                counts[day] = row["count"]
            except:
                pass

        return jsonify({
            "period": period,
            "labels": weekdays,
            "data": counts,
            "chart_type": "week"
        })

@app.route("/api/stats/expenses/details")
@login_required
def stats_expenses_details():
    """获取消费明细"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        date_condition = "DATE(event_time) = DATE('now', 'localtime')"
    else:  # week
        today = date.today()
        weekday = today.weekday()
        monday = today - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        date_condition = f"DATE(event_time) >= '{monday}' AND DATE(event_time) <= '{sunday}'"

    expenses = db.execute(f"""
        SELECT
            id,
            title,
            amount,
            category,
            event_time,
            notes
        FROM records
        WHERE user_id = ?
          AND type = 'expense'
          AND {date_condition}
        ORDER BY event_time DESC
    """, user_id)

    return jsonify({
        "period": period,
        "expenses": expenses
    })

@app.route("/api/stats/events/details")
@login_required
def stats_events_details():
    """获取日程明细"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        date_condition = "DATE(event_time) = DATE('now', 'localtime')"
    else:  # week
        today = date.today()
        weekday = today.weekday()
        monday = today - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        date_condition = f"DATE(event_time) >= '{monday}' AND DATE(event_time) <= '{sunday}'"

    events = db.execute(f"""
        SELECT
            id,
            title,
            event_time,
            duration,
            notes
        FROM records
        WHERE user_id = ?
          AND type = 'event'
          AND {date_condition}
        ORDER BY event_time DESC
    """, user_id)

    return jsonify({
        "period": period,
        "events": events
    })
# 在 stats 路由后面添加

@app.route("/api/stats/categories")
@login_required
def stats_categories():
    """获取分类统计（新加的路由）"""
    user_id = session["user_id"]
    period = request.args.get("period", "today")

    if period == "today":
        date_condition = "DATE(event_time) = DATE('now', 'localtime')"
    else:  # week
        today = date.today()
        weekday = today.weekday()  # 0=周一,6=周日
        monday = today - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        date_condition = f"DATE(event_time) >= '{monday}' AND DATE(event_time) <= '{sunday}'"

    # 查询分类数据
    categories = db.execute(f"""
        SELECT
            COALESCE(category, '未分类') as name,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM records
        WHERE user_id = ?
          AND type = 'expense'
          AND {date_condition}
        GROUP BY category
        HAVING total_amount > 0
        ORDER BY total_amount DESC
    """, user_id)

    # 计算总数
    total_expense = 0
    for cat in categories:
        total_expense += float(cat["total_amount"] or 0)

    # 颜色数组
    colors = [
        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
        "#9966FF", "#FF9F40", "#8AC926", "#1982C4",
        "#6A4C93", "#F15BB5", "#00BBF9", "#00F5D4"
    ]

    # 添加颜色
    for i, cat in enumerate(categories):
        cat["color"] = colors[i % len(colors)]

    return jsonify({
        "period": period,
        "categories": categories,
        "total_expense": total_expense
    })

@app.route("/api/ai/suggest", methods=["POST"])
@login_required
def ai_suggest():
    """获取AI建议（Hugging Face版本）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "无效的请求数据"}), 400

        # 获取请求参数
        record_type = data.get("type", "event")
        title = data.get("title", "")
        notes = data.get("notes", "")
        amount = data.get("amount", "")
        category = data.get("category", "")

        # 验证必填字段
        if not title:
            return jsonify({"error": "标题不能为空"}), 400

        # 构建提示词
        prompt = ""
        if record_type == "event":
            prompt = f"标题：{title}"
            if notes:
                prompt += f"\n备注：{notes}"
            prompt += "\n请为这个日程安排提供实用的建议，包括时间管理、准备工作、注意事项等，不超过100字。"

        else:  # expense
            prompt = f"项目：{title}"
            if amount:
                prompt += f"\n金额：{amount}元"
            if category:
                prompt += f"\n类别：{category}"
            if notes:
                prompt += f"\n备注：{notes}"
            prompt += "\n请为这笔消费提供理财建议，包括预算控制、消费习惯、节省建议等，不超过100字。"

        # 调用AI
        suggestion = get_ai_suggestion(prompt, record_type)

        return jsonify({
            "success": True,
            "suggestion": suggestion,
            "prompt": prompt  # 调试用，正式版可以移除
        })

    except Exception as e:
        print(f"AI建议错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "suggestion": "AI服务暂时不可用，请稍后重试"
        }), 500


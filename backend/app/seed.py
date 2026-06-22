from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from .auth import hash_password
from .models import AuthUser, Contact, Customer, CustomerActivity, InventoryMovement, LeadStage, OrderApprovalRequest, OrderApprovalStatus, OrderItem, OrderStatus, Organization, Product, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem


DEMO_AUTH_EMAIL = "demo@smart-crm.local"
DEMO_AUTH_PASSWORD = "SmartCRM@2026"


def ensure_auth_seed(session: Session) -> None:
    organization = session.exec(select(Organization).where(Organization.slug == "szu-ai-crm-course")).first()
    if not organization:
        organization = Organization(name="深大 AI CRM 课程组", slug="szu-ai-crm-course", plan="course", status="active")
        session.add(organization)
        session.flush()

    auth_users = [
        ("李伟超", DEMO_AUTH_EMAIL, "18600002048", "管理员", "CRM 运营管理员", "客户增长中心"),
        ("王蕾", "manager@smart-crm.local", "18600002049", "销售经理", "销售团队主管", "客户增长中心"),
        ("赵可", "sales@smart-crm.local", "18600002050", "销售", "客户经理", "华南销售组"),
        ("刘涵", "support@smart-crm.local", "18600002051", "支持", "实施支持工程师", "客户成功中心"),
        ("孙梦琪", "audit@smart-crm.local", "18600002052", "审计员", "项目审计专员", "质量与审计组"),
    ]
    for full_name, email, phone, role, position, department in auth_users:
        if session.exec(select(AuthUser).where(AuthUser.email == email)).first():
            continue
        session.add(
            AuthUser(
                organization_id=organization.id,
                full_name=full_name,
                email=email,
                phone=phone,
                role=role,
                position=position,
                department=department,
                location="深圳 · 南山",
                status="active",
                password_hash=hash_password(DEMO_AUTH_PASSWORD),
            )
        )


def seed_data(session: Session) -> None:
    ensure_auth_seed(session)
    existing_customer = session.exec(select(Customer)).first()
    if existing_customer:
        session.commit()
        return

    today = date.today()
    now = datetime.utcnow()

    customers = [
        Customer(name="李强", company="星海装备", industry="工业制造", city="上海", contact_person="李强", phone="13800001111", email="liqiang@xinghai.com", source="展会", level="A"),
        Customer(name="陈敏", company="云川医疗", industry="医疗器械", city="杭州", contact_person="陈敏", phone="13900002222", email="chenmin@yunchuan.com", source="老客户转介绍", level="S"),
        Customer(name="王凯", company="北辰教育科技", industry="教育信息化", city="深圳", contact_person="王凯", phone="13700003333", email="wangkai@beichen.com", source="官网咨询", level="B"),
        Customer(name="孙伊", company="峰值数据", industry="软件服务", city="深圳", contact_person="孙伊", phone="13600004444", email="sunyi@fengzhi.cn", source="线上活动", level="A"),
        Customer(name="赵可", company="拓海医疗", industry="医疗健康", city="广州", contact_person="赵可", phone="13500005555", email="zhaoke@tuohai.com", source="行业会议", level="A"),
        Customer(name="吴青", company="永酌公司", industry="消费制造", city="佛山", contact_person="吴青", phone="13400006666", email="wuqing@yongzhuo.com", source="渠道伙伴", level="S"),
        Customer(name="韩澈", company="辰星物流", industry="供应链物流", city="东莞", contact_person="韩澈", phone="13300007777", email="hanche@chenxing.io", source="客户转介绍", level="B"),
        Customer(name="周宁", company="南山科技", industry="人工智能", city="深圳", contact_person="周宁", phone="13200008888", email="zhouning@nanshan.ai", source="校企合作", level="S"),
        Customer(name="林渡", company="星火教育", industry="教育培训", city="长沙", contact_person="林渡", phone="13100009999", email="lindu@xinghuo.edu", source="官网咨询", level="B"),
        Customer(name="沈听澜", company="北极星资本", industry="金融服务", city="北京", contact_person="沈听澜", phone="13000001010", email="shen@polaris.vc", source="投资生态", level="A"),
        Customer(name="韩知意", company="北宸制造", industry="智能制造", city="苏州", contact_person="韩知意", phone="13900001122", email="hanzhiyi@beichenmfg.com", source="展会", level="B"),
        Customer(name="许川", company="云舟智能", industry="人工智能", city="深圳", contact_person="许川", phone="13800002233", email="xuchuan@yunzhou.ai", source="老客户增购", level="S"),
    ]
    customer_metrics = {
        "星海装备": (860000, "active"),
        "云川医疗": (1180000, "active"),
        "北辰教育科技": (520000, "nurturing"),
        "峰值数据": (530000, "active"),
        "拓海医疗": (960000, "proposal"),
        "永酌公司": (1420000, "active"),
        "辰星物流": (420000, "nurturing"),
        "南山科技": (1680000, "active"),
        "星火教育": (360000, "closed"),
        "北极星资本": (980000, "active"),
        "北宸制造": (640000, "proposal"),
        "云舟智能": (1880000, "active"),
    }
    for customer in customers:
        customer.annual_revenue, customer.status = customer_metrics[customer.company]
    session.add_all(customers)
    session.flush()

    contacts = [
        Contact(name="李强", company="星海装备", role="数字化负责人", email="liqiang@xinghai.com", phone="13800001111", owner="李伟超", status="active"),
        Contact(name="陈敏", company="云川医疗", role="采购经理", email="chenmin@yunchuan.com", phone="13900002222", owner="王晨", status="active"),
        Contact(name="王凯", company="北辰教育科技", role="信息中心主任", email="wangkai@beichen.com", phone="13700003333", owner="李伟超", status="nurturing"),
        Contact(name="孙伊", company="峰值数据", role="CEO", email="sunyi@fengzhi.cn", phone="13600004444", owner="陈卓", status="active"),
        Contact(name="赵可", company="拓海医疗", role="运营负责人", email="zhaoke@tuohai.com", phone="13500005555", owner="赵可", status="active"),
        Contact(name="吴青", company="永酌公司", role="行政负责人", email="wuqing@yongzhuo.com", phone="13400006666", owner="刘涵", status="active"),
        Contact(name="韩澈", company="辰星物流", role="IT 经理", email="hanche@chenxing.io", phone="13300007777", owner="赵可", status="nurturing"),
        Contact(name="周宁", company="南山科技", role="增长负责人", email="zhouning@nanshan.ai", phone="13200008888", owner="李伟超", status="active"),
        Contact(name="林渡", company="星火教育", role="校区负责人", email="lindu@xinghuo.edu", phone="13100009999", owner="陈卓", status="closed"),
        Contact(name="沈听澜", company="北极星资本", role="投后运营", email="shen@polaris.vc", phone="13000001010", owner="王蕾", status="active"),
        Contact(name="韩知意", company="北宸制造", role="采购主管", email="hanzhiyi@beichenmfg.com", phone="13900001122", owner="刘涵", status="active"),
        Contact(name="许川", company="云舟智能", role="采购总监", email="xuchuan@yunzhou.ai", phone="13800002233", owner="王蕾", status="active"),
    ]
    session.add_all(contacts)
    session.flush()
    owner_by_company: dict[str, str] = {}
    for contact in contacts:
        owner_by_company.setdefault(contact.company, contact.owner)
    for customer in customers:
        customer.owner = owner_by_company.get(customer.company, customer.contact_person)
        session.add(customer)

    products = [
        Product(name="智能巡检终端", sku="AI-DEVICE-001", category="硬件", unit_price=16800, stock=80),
        Product(name="销售分析大屏授权", sku="SAAS-LIC-008", category="软件", unit_price=6800, stock=1200),
        Product(name="客户数据接入服务", sku="SERV-API-003", category="服务", unit_price=4200, stock=500),
        Product(name="移动录单套件", sku="MOBILE-KIT-011", category="硬件", unit_price=9800, stock=60),
        Product(name="AI 商机评分模块", sku="AI-COPILOT-021", category="软件", unit_price=12800, stock=300),
        Product(name="私有化部署服务", sku="SERV-DEPLOY-018", category="服务", unit_price=26000, stock=80),
        Product(name="工单协同席位", sku="SUPPORT-SEAT-006", category="软件", unit_price=1800, stock=2000),
        Product(name="客户画像增强包", sku="DATA-PROFILE-013", category="软件", unit_price=9600, stock=360),
        Product(name="销售流程咨询包", sku="CONSULT-SALES-016", category="服务", unit_price=18800, stock=60),
        Product(name="多组织权限模块", sku="AUTH-ORG-009", category="软件", unit_price=7200, stock=520),
    ]
    session.add_all(products)
    session.flush()

    leads = [
        SalesLead(title="云舟年度 CRM 升级", customer_name="云舟智能", owner="王蕾", region="华南", expected_amount=198000, stage=LeadStage.negotiation, next_action="推动采购审批并确认合同条款", due_date=today + timedelta(days=1), ai_assisted=True),
        SalesLead(title="拓海销售自动化", customer_name="拓海医疗", owner="赵可", region="华南", expected_amount=154000, stage=LeadStage.proposal, next_action="发送 ROI 测算和试点计划", due_date=today + timedelta(days=3), ai_assisted=True),
        SalesLead(title="峰值客户数据治理", customer_name="峰值数据", owner="陈卓", region="华南", expected_amount=83000, stage=LeadStage.qualified, next_action="确认数据源范围", due_date=today + timedelta(days=5), ai_assisted=False),
        SalesLead(title="永酌流程整合项目", customer_name="永酌公司", owner="刘涵", region="华南", expected_amount=126000, stage=LeadStage.negotiation, next_action="准备让步边界", due_date=today + timedelta(days=2), ai_assisted=True),
        SalesLead(title="北辰校企合作采购", customer_name="北辰教育科技", owner="李伟超", region="华南", expected_amount=120000, stage=LeadStage.proposal, next_action="提交最终报价单", due_date=today + timedelta(days=2), ai_assisted=True),
        SalesLead(title="云川智能终端补货", customer_name="云川医疗", owner="王晨", region="华东", expected_amount=86000, stage=LeadStage.negotiation, next_action="确认交付周期", due_date=today + timedelta(days=1), ai_assisted=False),
        SalesLead(title="星海工业现场改造一期", customer_name="星海装备", owner="李伟超", region="华东", expected_amount=152000, stage=LeadStage.qualified, next_action="安排现场勘查", due_date=today + timedelta(days=4), ai_assisted=True),
        SalesLead(title="辰星仓配看板", customer_name="辰星物流", owner="赵可", region="华南", expected_amount=71000, stage=LeadStage.proposal, next_action="补充 SLA 报表字段", due_date=today + timedelta(days=7), ai_assisted=False),
        SalesLead(title="南山智能增长包", customer_name="南山科技", owner="李伟超", region="华南", expected_amount=238000, stage=LeadStage.new, next_action="确认预算和决策人", due_date=today + timedelta(days=10), ai_assisted=True),
        SalesLead(title="北极星投后 CRM 标准化", customer_name="北极星资本", owner="王蕾", region="华北", expected_amount=176000, stage=LeadStage.qualified, next_action="整理投后企业模板", due_date=today + timedelta(days=8), ai_assisted=True),
        SalesLead(title="星火续费与工单协同", customer_name="星火教育", owner="陈卓", region="华中", expected_amount=62000, stage=LeadStage.new, next_action="确认续费窗口", due_date=today + timedelta(days=12), ai_assisted=False),
        SalesLead(title="北宸制造售后系统", customer_name="北宸制造", owner="刘涵", region="华东", expected_amount=64000, stage=LeadStage.proposal, next_action="发送工单协同方案", due_date=today + timedelta(days=6), ai_assisted=False),
        SalesLead(title="云舟二期客户画像", customer_name="云舟智能", owner="王蕾", region="华南", expected_amount=98000, stage=LeadStage.won, next_action="沉淀赢单复盘", due_date=today - timedelta(days=2), ai_assisted=True),
        SalesLead(title="物流移动录单试点", customer_name="辰星物流", owner="赵可", region="华南", expected_amount=45000, stage=LeadStage.lost, next_action="记录丢单原因", due_date=today - timedelta(days=5), ai_assisted=False),
        SalesLead(title="云川数据接入服务", customer_name="云川医疗", owner="李伟超", region="华东", expected_amount=58000, stage=LeadStage.qualified, next_action="补充接口清单", due_date=today + timedelta(days=9), ai_assisted=True),
    ]
    session.add_all(leads)
    session.flush()

    cases = [
        SupportCase(title="导入联系人失败", account="峰值数据", owner="徐柠", priority="hot", status="open", status_label="Open", due_date=today + timedelta(days=1)),
        SupportCase(title="移动端表格显示错位", account="拓海医疗", owner="顾川", priority="warm", status="working", status_label="Pending", due_date=today + timedelta(days=2)),
        SupportCase(title="审批流通知延迟", account="永酌公司", owner="陆远", priority="hot", status="working", status_label="Pending", due_date=today),
        SupportCase(title="权限组配置咨询", account="云舟智能", owner="徐柠", priority="cold", status="closed", status_label="Resolved", due_date=today - timedelta(days=2)),
        SupportCase(title="工单 SLA 报表校对", account="辰星物流", owner="顾川", priority="warm", status="open", status_label="Open", due_date=today + timedelta(days=4)),
        SupportCase(title="DeepSeek 话术接口超时复盘", account="南山科技", owner="李伟超", priority="hot", status="open", status_label="Open", due_date=today + timedelta(days=1)),
        SupportCase(title="订单库存扣减核对", account="北宸制造", owner="刘涵", priority="warm", status="working", status_label="Pending", due_date=today + timedelta(days=3)),
        SupportCase(title="演示数据库重置指导", account="北极星资本", owner="陈卓", priority="cold", status="closed", status_label="Resolved", due_date=today - timedelta(days=1)),
    ]
    session.add_all(cases)

    tasks = [
        TaskItem(title="回访云舟智能采购团队", description="确认六月采购窗口与预算审批节奏。", owner="王蕾", due_date="今天 18:00", priority="hot", status="today", status_label="今天"),
        TaskItem(title="补充拓海医疗实施排期", description="将实施节点同步到销售计划与商机详情。", owner="赵可", due_date="明天 10:00", priority="warm", status="week", status_label="本周"),
        TaskItem(title="整理峰值数据合同附件", description="核对法务意见并更新签署版本。", owner="陈卓", due_date="昨天 15:00", priority="hot", status="overdue", status_label="逾期"),
        TaskItem(title="检查辰星物流工单报表", description="修正筛选条件并补充导出字段。", owner="刘涵", due_date="周四 11:00", priority="cold", status="week", status_label="本周"),
        TaskItem(title="安排永酌公司需求研讨会", description="同步销售、产品和实施的关键问题。", owner="王蕾", due_date="今天 14:30", priority="warm", status="today", status_label="今天"),
        TaskItem(title="复盘 DeepSeek Copilot 生成质量", description="挑选 3 条真实商机话术作为答辩截图。", owner="李伟超", due_date="周五 17:00", priority="hot", status="week", status_label="本周"),
        TaskItem(title="更新部署文档截图", description="补充 reset-db、pytest、Copilot 接口返回截图。", owner="孙梦琪", due_date="本周日 20:00", priority="warm", status="week", status_label="本周"),
        TaskItem(title="绘制 L2C 流程图", description="使用 Draw.io 输出可放入 Word/PPT 的流程图。", owner="周博文", due_date="明天 21:00", priority="warm", status="today", status_label="今天"),
    ]
    session.add_all(tasks)

    goals = [
        SalesGoal(name="Q2 新签 ARR", period="2026 Q2", current=388000, target=520000, progress=75, note="距离季度目标还差 132K，重点依赖 3 个谈判中商机。"),
        SalesGoal(name="大客户续约率", period="2026 Q2", current=84, target=92, progress=91, note="高于历史同期，需重点盯住 2 个高风险续约客户。"),
        SalesGoal(name="线索转商机率", period="2026 Q2", current=31, target=40, progress=77, note="优化首轮跟进模板后，本月已连续两周提升。"),
        SalesGoal(name="AI 辅助订单占比", period="2026 Q2", current=58, target=70, progress=83, note="DeepSeek Copilot 接入后，优先推动高价值商机使用 AI 草稿。"),
    ]
    session.add_all(goals)
    session.flush()

    product_by_sku = {product.sku: product for product in products}
    customer_by_company = {customer.company: customer for customer in customers}

    activity_specs = [
        ("云舟智能", "王蕾", "meeting", "二期画像需求复盘", "采购和业务负责人确认希望把客户画像接入售后工单数据。", "认可二期方向", "整理数据字段清单并同步报价", "positive", 1),
        ("南山科技", "李伟超", "call", "DeepSeek Copilot 质量沟通", "客户反馈话术生成质量稳定，但希望补充审批场景模板。", "需求扩大", "补充审批流模板并约演示", "positive", 1),
        ("北辰教育科技", "李伟超", "email", "最终报价单确认", "客户收到报价单，关注移动录单套件交付时间。", "等待采购确认", "明天跟进采购审批状态", "neutral", 2),
        ("星海装备", "李伟超", "meeting", "工业现场勘查", "现场网络环境较复杂，需要私有化部署和数据接入服务联合评估。", "技术方案需细化", "安排实施顾问补充部署方案", "risk", 3),
        ("云川医疗", "王晨", "call", "终端补货交付确认", "客户希望在月底前完成终端到货和接口联调。", "交付窗口明确", "同步供应链库存并锁定交付批次", "neutral", 2),
        ("峰值数据", "陈卓", "meeting", "数据治理合同附件", "法务已返回两处修改意见，客户认可数据接入服务范围。", "合同推进", "更新附件并发起盖章流程", "positive", 4),
        ("拓海医疗", "赵可", "call", "ROI 试点计划沟通", "客户希望先做 2 周试点，看销售自动化对跟进效率的提升。", "进入试点", "发送试点里程碑和验收口径", "positive", 2),
        ("永酌公司", "刘涵", "meeting", "流程整合让步边界", "客户压缩预算，希望减少首期权限模块范围。", "价格异议", "准备两档报价并保留增购空间", "risk", 1),
        ("辰星物流", "赵可", "email", "SLA 报表字段补充", "客户补充仓配看板需要按区域、时效和异常原因拆分。", "范围清晰", "更新方案字段和实施排期", "neutral", 5),
        ("北极星资本", "王蕾", "meeting", "投后模板研讨", "客户希望把投后企业模板标准化到 CRM 客户资产页。", "方案认可", "输出模板样例并约下周评审", "positive", 6),
        ("星火教育", "陈卓", "call", "续费窗口确认", "客户预算需等校区汇总，短期不会推进增购。", "节奏放缓", "七天后回访预算进展", "negative", 7),
        ("北宸制造", "刘涵", "meeting", "售后系统方案讲解", "客户对工单协同席位感兴趣，但担心库存扣减核对问题影响上线。", "存在上线顾虑", "先关闭库存核对工单再推进合同", "risk", 2),
        ("云舟智能", "王蕾", "email", "合同条款补充", "采购要求补充服务级别和数据安全条款。", "合同待补充", "发送法务修订版", "neutral", 3),
        ("南山科技", "李伟超", "meeting", "增长包预算确认", "客户确认预算上限，要求本周提供私有化部署资源安排。", "预算明确", "整理部署资源排期", "positive", 4),
        ("星海装备", "李伟超", "call", "现场改造安全要求", "客户安全负责人要求补充离线部署和审计日志说明。", "安全审查", "补充安全方案和审计截图", "risk", 5),
        ("云川医疗", "李伟超", "email", "接口清单补充", "客户发送 HIS 接口清单，等待技术评估工作量。", "资料已收齐", "请技术评估接口改造工期", "positive", 1),
    ]
    activities = [
        CustomerActivity(
            customer_id=customer_by_company[company].id,
            customer_name=company,
            owner=owner,
            activity_type=activity_type,
            subject=subject,
            summary=summary,
            outcome=outcome,
            next_action=next_action,
            sentiment=sentiment,
            occurred_at=now - timedelta(days=days_ago),
        )
        for company, owner, activity_type, subject, summary, outcome, next_action, sentiment, days_ago in activity_specs
    ]
    session.add_all(activities)

    order_specs = [
        ("云川医疗", "李伟超", "华东", OrderStatus.confirmed, True, 0.93, today - timedelta(days=6), today + timedelta(days=6), [("AI-DEVICE-001", 2), ("SERV-API-003", 1)]),
        ("星海装备", "王晨", "华东", OrderStatus.fulfilled, False, 0.0, today - timedelta(days=15), today - timedelta(days=1), [("AI-DEVICE-001", 1)]),
        ("云舟智能", "王蕾", "华南", OrderStatus.confirmed, True, 0.88, today - timedelta(days=4), today + timedelta(days=12), [("AI-COPILOT-021", 4), ("DATA-PROFILE-013", 2)]),
        ("永酌公司", "刘涵", "华南", OrderStatus.draft, True, 0.81, today - timedelta(days=2), today + timedelta(days=16), [("SAAS-LIC-008", 5), ("AUTH-ORG-009", 3)]),
        ("北辰教育科技", "李伟超", "华南", OrderStatus.confirmed, True, 0.9, today - timedelta(days=8), today + timedelta(days=10), [("MOBILE-KIT-011", 3), ("SUPPORT-SEAT-006", 20)]),
        ("峰值数据", "陈卓", "华南", OrderStatus.fulfilled, False, 0.0, today - timedelta(days=24), today - timedelta(days=8), [("DATA-PROFILE-013", 3), ("SERV-API-003", 2)]),
        ("拓海医疗", "赵可", "华南", OrderStatus.draft, True, 0.79, today - timedelta(days=1), today + timedelta(days=20), [("SAAS-LIC-008", 8), ("AI-COPILOT-021", 2)]),
        ("辰星物流", "赵可", "华南", OrderStatus.confirmed, False, 0.0, today - timedelta(days=12), today + timedelta(days=3), [("MOBILE-KIT-011", 2), ("SUPPORT-SEAT-006", 15)]),
        ("南山科技", "李伟超", "华南", OrderStatus.draft, True, 0.86, today, today + timedelta(days=21), [("AI-COPILOT-021", 6), ("SERV-DEPLOY-018", 1)]),
        ("北极星资本", "王蕾", "华北", OrderStatus.confirmed, False, 0.0, today - timedelta(days=18), today + timedelta(days=2), [("CONSULT-SALES-016", 1), ("AUTH-ORG-009", 5)]),
        ("星火教育", "陈卓", "华中", OrderStatus.fulfilled, False, 0.0, today - timedelta(days=30), today - timedelta(days=12), [("SUPPORT-SEAT-006", 30)]),
        ("北宸制造", "刘涵", "华东", OrderStatus.confirmed, True, 0.84, today - timedelta(days=9), today + timedelta(days=9), [("AI-DEVICE-001", 2), ("CONSULT-SALES-016", 1)]),
    ]

    orders: list[SalesOrder] = []
    pending_items: list[tuple[SalesOrder, Product, int]] = []
    for company, owner, region, status, by_ai, confidence, order_date, due_date, lines in order_specs:
        order = SalesOrder(
            customer_id=customer_by_company[company].id,
            owner=owner,
            region=region,
            currency="CNY",
            status=status,
            order_date=order_date,
            due_date=due_date,
            notes="AI Copilot 演示数据：用于验证订单、库存与仪表盘联动。" if by_ai else "历史手工订单演示数据。",
            created_by_ai=by_ai,
            ai_confidence_score=confidence,
        )
        session.add(order)
        orders.append(order)
        for sku, quantity in lines:
            pending_items.append((order, product_by_sku[sku], quantity))
    session.flush()

    for order, product, quantity in pending_items:
        line_total = product.unit_price * quantity
        order.total_amount += line_total
        before_stock = product.stock
        product.stock = max(product.stock - quantity, 0)
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.unit_price,
                line_total=line_total,
            )
        )
        session.add(
            InventoryMovement(
                product_id=product.id,
                change_quantity=-quantity,
                before_stock=before_stock,
                after_stock=product.stock,
                reason=f"演示订单 #{order.id} 库存扣减",
                operator=order.owner,
                source="seed_order_deduction",
            )
        )
        session.add(product)
        session.add(order)

    order_by_company: dict[str, SalesOrder] = {}
    for order in orders:
        for company, customer in customer_by_company.items():
            if order.customer_id == customer.id:
                order_by_company[company] = order
                break
    nanshan_order = order_by_company.get("南山科技")
    beichen_order = order_by_company.get("北辰教育科技")
    if nanshan_order:
        session.add(
            OrderApprovalRequest(
                order_id=nanshan_order.id,
                owner=nanshan_order.owner,
                requester=nanshan_order.owner,
                reviewer="销售经理",
                status=OrderApprovalStatus.pending,
                reason="AI Copilot 生成的高价值订单，需要经理复核私有化部署、库存和交付排期。",
                risk_summary="订单金额超过 10 万元；AI 录单生成；包含私有化部署服务，需确认实施资源。",
                risk_level="high",
                sla_due_at=datetime.utcnow() + timedelta(hours=6),
                requested_total=nanshan_order.total_amount,
                previous_order_status=nanshan_order.status,
                target_order_status=OrderStatus.confirmed,
            )
        )
    if beichen_order:
        session.add(
            OrderApprovalRequest(
                order_id=beichen_order.id,
                owner=beichen_order.owner,
                requester=beichen_order.owner,
                reviewer="销售经理",
                status=OrderApprovalStatus.approved,
                reason="教育客户批量移动录单套件采购，需确认交付窗口。",
                risk_summary="订单包含硬件与席位组合，需要复核库存扣减和交付日期。",
                risk_level="medium",
                sla_due_at=datetime.utcnow() + timedelta(hours=24),
                requested_total=beichen_order.total_amount,
                previous_order_status=OrderStatus.draft,
                target_order_status=OrderStatus.confirmed,
                decision_comment="库存和交付窗口已核对，同意进入确认状态。",
                decided_at=datetime.utcnow(),
            )
        )

    session.commit()

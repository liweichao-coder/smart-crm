from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from .models import Customer, InventoryMovement, OrderApprovalRequest, OrderApprovalStatus, OrderItem, Product, SalesOrder


@dataclass
class ConsistencyCheck:
    id: str
    category: str
    severity: str
    status: str
    title: str
    detail: str
    entity_type: str = ""
    entity_id: int | None = None
    suggestion: str = ""


def ok_check(check_id: str, category: str, title: str, detail: str) -> ConsistencyCheck:
    return ConsistencyCheck(
        id=check_id,
        category=category,
        severity="info",
        status="ok",
        title=title,
        detail=detail,
        suggestion="无需处理。",
    )


def issue_check(
    check_id: str,
    category: str,
    severity: str,
    title: str,
    detail: str,
    *,
    entity_type: str = "",
    entity_id: int | None = None,
    suggestion: str,
) -> ConsistencyCheck:
    return ConsistencyCheck(
        id=check_id,
        category=category,
        severity=severity,
        status="issue",
        title=title,
        detail=detail,
        entity_type=entity_type,
        entity_id=entity_id,
        suggestion=suggestion,
    )


def collect_consistency_checks(session: Session) -> list[ConsistencyCheck]:
    checks: list[ConsistencyCheck] = []
    customers = {customer.id: customer for customer in session.exec(select(Customer)).all()}
    products = {product.id: product for product in session.exec(select(Product)).all()}
    orders = {order.id: order for order in session.exec(select(SalesOrder)).all()}
    order_items = session.exec(select(OrderItem)).all()
    movements = session.exec(select(InventoryMovement)).all()
    approvals = session.exec(select(OrderApprovalRequest)).all()

    orphan_orders = [order for order in orders.values() if order.customer_id not in customers]
    if orphan_orders:
        checks.extend(
            issue_check(
                f"order-customer-{order.id}",
                "订单客户引用",
                "critical",
                f"订单 #{order.id} 缺少客户",
                f"订单关联 customer_id={order.customer_id}，但客户表中不存在该记录。",
                entity_type="order",
                entity_id=order.id,
                suggestion="恢复客户记录，或重新关联到有效客户后再演示订单闭环。",
            )
            for order in orphan_orders
        )
    else:
        checks.append(ok_check("order-customer-ok", "订单客户引用", "订单客户引用正常", f"{len(orders)} 张订单均关联有效客户。"))

    items_by_order: dict[int, list[OrderItem]] = defaultdict(list)
    item_reference_issues: list[ConsistencyCheck] = []
    item_math_issues: list[ConsistencyCheck] = []
    for item in order_items:
        items_by_order[item.order_id].append(item)
        if item.order_id not in orders:
            item_reference_issues.append(
                issue_check(
                    f"order-item-order-{item.id}",
                    "订单明细引用",
                    "critical",
                    f"订单明细 #{item.id} 缺少订单",
                    f"订单明细关联 order_id={item.order_id}，但订单表中不存在该记录。",
                    entity_type="order_item",
                    entity_id=item.id,
                    suggestion="删除孤儿明细或恢复关联订单。",
                )
            )
        if item.product_id not in products:
            item_reference_issues.append(
                issue_check(
                    f"order-item-product-{item.id}",
                    "订单明细引用",
                    "critical",
                    f"订单明细 #{item.id} 缺少商品",
                    f"订单明细关联 product_id={item.product_id}，但商品表中不存在该记录。",
                    entity_type="order_item",
                    entity_id=item.id,
                    suggestion="恢复商品目录记录，或替换为有效商品。",
                )
            )
        expected_line_total = item.quantity * item.unit_price
        if abs(item.line_total - expected_line_total) > 0.01:
            item_math_issues.append(
                issue_check(
                    f"order-item-total-{item.id}",
                    "订单明细金额",
                    "warning",
                    f"订单明细 #{item.id} 小计不一致",
                    f"当前小计 {item.line_total:.2f}，按数量和单价应为 {expected_line_total:.2f}。",
                    entity_type="order_item",
                    entity_id=item.id,
                    suggestion="重新保存订单明细，使行金额按数量和单价重算。",
                )
            )
    checks.extend(item_reference_issues or [ok_check("order-item-references-ok", "订单明细引用", "订单明细引用正常", f"{len(order_items)} 条明细均关联有效订单和商品。")])
    checks.extend(item_math_issues or [ok_check("order-item-totals-ok", "订单明细金额", "订单明细金额正常", f"{len(order_items)} 条明细的小计均与数量和单价一致。")])

    order_total_issues: list[ConsistencyCheck] = []
    for order in orders.values():
        expected_total = sum(item.line_total for item in items_by_order.get(order.id or 0, []))
        if abs(order.total_amount - expected_total) > 0.01:
            order_total_issues.append(
                issue_check(
                    f"order-total-{order.id}",
                    "订单金额合计",
                    "warning",
                    f"订单 #{order.id} 金额不一致",
                    f"订单 total_amount={order.total_amount:.2f}，按明细合计应为 {expected_total:.2f}。",
                    entity_type="order",
                    entity_id=order.id,
                    suggestion="重新保存订单或运行订单明细重算流程。",
                )
            )
    checks.extend(order_total_issues or [ok_check("order-totals-ok", "订单金额合计", "订单金额合计正常", f"{len(orders)} 张订单金额均与明细合计一致。")])

    movement_issues: list[ConsistencyCheck] = []
    for movement in movements:
        if movement.product_id not in products:
            movement_issues.append(
                issue_check(
                    f"inventory-product-{movement.id}",
                    "库存流水",
                    "critical",
                    f"库存流水 #{movement.id} 缺少商品",
                    f"流水关联 product_id={movement.product_id}，但商品表中不存在该记录。",
                    entity_type="inventory_movement",
                    entity_id=movement.id,
                    suggestion="恢复商品目录记录，或删除无效库存流水。",
                )
            )
        expected_after_stock = movement.before_stock + movement.change_quantity
        if movement.after_stock != expected_after_stock:
            movement_issues.append(
                issue_check(
                    f"inventory-balance-{movement.id}",
                    "库存流水",
                    "warning",
                    f"库存流水 #{movement.id} 前后库存不一致",
                    f"before_stock + change_quantity = {expected_after_stock}，记录 after_stock={movement.after_stock}。",
                    entity_type="inventory_movement",
                    entity_id=movement.id,
                    suggestion="复核补货或扣减记录，必要时重建库存流水。",
                )
            )
    checks.extend(movement_issues or [ok_check("inventory-movements-ok", "库存流水", "库存流水正常", f"{len(movements)} 条库存流水均通过商品引用和前后库存校验。")])

    negative_products = [product for product in products.values() if product.stock < 0]
    if negative_products:
        checks.extend(
            issue_check(
                f"product-stock-{product.id}",
                "商品库存",
                "critical",
                f"商品 #{product.id} 库存为负数",
                f"{product.name} 当前库存 {product.stock}，不符合库存非负约束。",
                entity_type="product",
                entity_id=product.id,
                suggestion="补正商品库存，并检查是否存在超卖订单。",
            )
            for product in negative_products
        )
    else:
        checks.append(ok_check("product-stock-ok", "商品库存", "商品库存正常", f"{len(products)} 个商品库存均为非负数。"))

    approval_issues: list[ConsistencyCheck] = []
    for approval in approvals:
        order = orders.get(approval.order_id)
        if not order:
            approval_issues.append(
                issue_check(
                    f"approval-order-{approval.id}",
                    "订单审批",
                    "critical",
                    f"审批 #{approval.id} 缺少订单",
                    f"审批关联 order_id={approval.order_id}，但订单表中不存在该记录。",
                    entity_type="order_approval",
                    entity_id=approval.id,
                    suggestion="删除孤儿审批记录或恢复关联订单。",
                )
            )
            continue
        if approval.status == OrderApprovalStatus.pending and order.status == approval.target_order_status:
            approval_issues.append(
                issue_check(
                    f"approval-status-{approval.id}",
                    "订单审批",
                    "warning",
                    f"审批 #{approval.id} 已无待推进状态",
                    f"关联订单已处于目标状态 {approval.target_order_status.value}，但审批仍为 pending。",
                    entity_type="order_approval",
                    entity_id=approval.id,
                    suggestion="处理或关闭该审批记录，避免重复审批。",
                )
            )
        if approval.status == OrderApprovalStatus.pending and not approval.sla_due_at:
            approval_issues.append(
                issue_check(
                    f"approval-sla-{approval.id}",
                    "订单审批",
                    "warning",
                    f"审批 #{approval.id} 缺少 SLA",
                    "待审批记录未设置 sla_due_at，通知中心无法计算剩余时间。",
                    entity_type="order_approval",
                    entity_id=approval.id,
                    suggestion="重新提交审批或运行轻量迁移补齐 SLA 字段。",
                )
            )
    checks.extend(approval_issues or [ok_check("order-approvals-ok", "订单审批", "订单审批引用正常", f"{len(approvals)} 条审批记录均通过订单引用和待办状态校验。")])
    return checks


def summarize_consistency_checks(checks: list[ConsistencyCheck]) -> dict[str, int | str]:
    issue_count = sum(1 for check in checks if check.status == "issue")
    critical_count = sum(1 for check in checks if check.status == "issue" and check.severity == "critical")
    warning_count = sum(1 for check in checks if check.status == "issue" and check.severity == "warning")
    ok_count = sum(1 for check in checks if check.status == "ok")
    return {
        "overall_status": "fail" if critical_count else "warning" if warning_count else "ok",
        "total_checks": len(checks),
        "issue_count": issue_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "ok_count": ok_count,
    }


def build_consistency_payload(session: Session) -> dict:
    checks = collect_consistency_checks(session)
    summary = summarize_consistency_checks(checks)
    return {
        **summary,
        "generated_at": datetime.utcnow(),
        "checks": [check.__dict__ for check in checks],
    }

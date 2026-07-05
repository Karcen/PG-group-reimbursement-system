"""
API v1 主路由
将所有子路由聚合到 /api/v1 前缀下。
新增模块时只需在此处 include_router 即可。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    approvals,
    audit_logs,
    auth,
    dashboard,
    invoices,
    notifications,
    payment_records,
    projects,
    reimbursements,
    system,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(projects.router, prefix="/projects", tags=["经费项目"])
api_router.include_router(reimbursements.router, prefix="/reimbursements", tags=["报销申请"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["发票管理"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["审批"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知中心"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["审计日志"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["统计面板"])
api_router.include_router(system.router, prefix="/system", tags=["系统设置"])
# 付款凭证（金额超阈值时强制附上转账截图）
api_router.include_router(payment_records.router, prefix="/payment-records", tags=["付款凭证"])

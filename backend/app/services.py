from __future__ import annotations

from datetime import date

from fastapi import UploadFile

from .schemas import VisionExtractItem, VisionExtractResponse


class VisionExtractionService:
    """Local demo extractor with deterministic sample output."""

    async def extract(self, file: UploadFile) -> VisionExtractResponse:
        raw_name = (file.filename or "sample").lower()
        name_hint = "陈敏" if "income" in raw_name else "李强"
        company_hint = "云川医疗" if "income" in raw_name else "星海装备"

        sample_items = [
            VisionExtractItem(product_name="智能巡检终端", quantity=2, unit_price=16800),
            VisionExtractItem(product_name="客户数据接入服务", quantity=1, unit_price=4200),
        ]
        if "deal" in raw_name:
            sample_items = [
                VisionExtractItem(product_name="移动录单套件", quantity=1, unit_price=9800),
                VisionExtractItem(product_name="销售分析大屏授权", quantity=3, unit_price=6800),
            ]

        total = sum(item.quantity * item.unit_price for item in sample_items)
        confidence = 0.91 if "income" in raw_name or "deal" in raw_name else 0.82
        return VisionExtractResponse(
            customer_name=name_hint,
            company=company_hint,
            confidence=confidence,
            summary=f"识别到 {len(sample_items)} 个条目，预估总金额 {total:.0f} 元。",
            items=sample_items,
            suggested_notes=f"AI 于 {date.today().isoformat()} 从图片中提取客户与商品信息，建议人工复核数量与单价。",
        )

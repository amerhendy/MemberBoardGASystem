# -*- coding: utf-8 -*-
"""
evaluation_service.py
خدمة التقييم - Evaluation Service
تطبّق صيغة "الأيام النشطة" و"نسبة التقييم" الموحّدة، وتبني تقرير مالي مجمّع
لكل عضو خلال فترة محددة، لأي من الفئتين (Board/Assembly) أو كليهما.
"""
from datetime import date, datetime


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def active_days(period_start, period_end, member_start, member_end=None) -> int:
    """
    Active Days = MAX(0, MIN(period_end, member_end) - MAX(period_start, member_start) + 1)
    إذا member_end فارغ (لسه نشط)، تُستخدم period_end كنهاية فعلية.
    """
    period_start = _parse_date(period_start)
    period_end = _parse_date(period_end)
    member_start = _parse_date(member_start)
    effective_end = _parse_date(member_end) if member_end else period_end

    start = max(period_start, member_start)
    end = min(period_end, effective_end)
    return max(0, (end - start).days + 1)


def evaluation_percent(period_start, period_end, member_start, member_end=None) -> float:
    period_start_d = _parse_date(period_start)
    period_end_d = _parse_date(period_end)
    total_days = (period_end_d - period_start_d).days + 1
    if total_days <= 0:
        return 0.0
    days = active_days(period_start, period_end, member_start, member_end)
    return round(days / total_days * 100, 2)


class EvaluationService:
    def __init__(self, db, member_service):
        self.db = db
        self.member_service = member_service

    def evaluation_report(self, period_start, period_end, member_type=None):
        """
        تقرير الأيام النشطة والتقييم لكل عضو ضمن الفترة.
        member_type=None => Board و Assembly معًا.
        """
        members = self.member_service.list_members(member_type=member_type)
        report = []
        for m in members:
            # نتجاهل الأعضاء الذين لا تتقاطع فترة عضويتهم مع الفترة المطلوبة إطلاقًا
            m_start = _parse_date(m["start_date"])
            m_end = _parse_date(m["end_date"]) if m["end_date"] else None
            p_start = _parse_date(period_start)
            p_end = _parse_date(period_end)
            if m_start > p_end or (m_end and m_end < p_start):
                continue

            days = active_days(period_start, period_end, m["start_date"], m["end_date"])
            pct = evaluation_percent(period_start, period_end, m["start_date"], m["end_date"])
            report.append({
                "member_id": m["id"],
                "full_name": m["full_name"],
                "member_type": m["member_type"],
                "start_date": m["start_date"],
                "end_date": m["end_date"],
                "active_days": days,
                "evaluation_percent": pct,
            })
        report.sort(key=lambda r: r["evaluation_percent"], reverse=True)
        return report

    def financial_report(self, period_start, period_end, member_type=None):
        """
        تقرير الصرف المالي لكل عضو خلال الفترة (بناءً على attendance_financials
        المرتبطة بجلسات ضمن نطاق التاريخ وفئة العضوية).
        """
        query = """
            SELECT m.id as member_id, m.full_name, m.member_type,
                   COUNT(af.id) as sessions_count,
                   SUM(CASE WHEN af.attended = 1 THEN 1 ELSE 0 END) as attended_count,
                   COALESCE(SUM(af.amount_paid), 0) as total_paid
            FROM members m
            LEFT JOIN attendance_financials af ON af.member_id = m.id
            LEFT JOIN meetings mt ON mt.id = af.meeting_id
                AND mt.meeting_date BETWEEN ? AND ?
            WHERE 1=1
        """
        params = [period_start, period_end]
        if member_type:
            query += " AND m.member_type = ?"
            params.append(member_type)
        query += " GROUP BY m.id ORDER BY total_paid DESC"

        rows = self.db.execute(query, params, fetchall=True)
        return [dict(r) for r in rows]

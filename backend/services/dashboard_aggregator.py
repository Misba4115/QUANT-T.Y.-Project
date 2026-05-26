"""
Dashboard Aggregator Service
Aggregates all user financial data and computes dashboard metrics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from models.models import (
    User, BankingAccount, EquityHolding, MutualFundHolding,
    ETFHolding, CryptoHolding, Goal, BankTransaction
)


class DashboardAggregator:
    """Aggregates user financial data to compute dashboard metrics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate(self, user_id: UUID) -> dict:
        """
        Aggregate all user data and compute dashboard metrics
        Returns dictionary with net_worth, asset_allocation, etc.
        """
        # Fetch all user holdings and accounts
        user = await self.db.get(User, user_id)
        if not user:
            return self._empty_dashboard()

        # Calculate totals
        banking_total = await self._get_banking_total(user_id)
        equity_data = await self._get_equity_data(user_id)
        mf_data = await self._get_mutual_fund_data(user_id)
        etf_data = await self._get_etf_data(user_id)
        crypto_data = await self._get_crypto_data(user_id)
        cashflow_data = await self._get_cashflow_data(user_id)

        # Calculate net worth
        net_worth = (
            float(banking_total) +
            equity_data['total_value'] +
            mf_data['total_value'] +
            etf_data['total_value'] +
            crypto_data['total_value']
        )

        # Build asset allocation
        asset_allocation = self._build_asset_allocation(
            banking_total, equity_data, mf_data, etf_data, crypto_data
        )

        # Get top holdings
        all_holdings = []
        all_holdings.extend(equity_data['holdings'])
        all_holdings.extend(mf_data['holdings'])
        all_holdings.extend(etf_data['holdings'])
        all_holdings.extend(crypto_data['holdings'])
        
        top_holdings = sorted(
            all_holdings,
            key=lambda x: x['current_value'],
            reverse=True
        )[:5]

        # Generate portfolio history (simulated 12-month growth)
        portfolio_history = self._generate_portfolio_history(net_worth)

        # Calculate tax saved (80C limit)
        tax_saved = await self._calculate_tax_saved(user_id)
        tax_limit = 150000  # 80C limit in INR

        # Generate alerts
        alerts = self._generate_alerts(
            net_worth, cashflow_data, user.risk_profile
        )

        # Determine risk level
        risk_level = self._determine_risk_level(user.risk_profile)

        # Net worth growth (simulated as 5% annual)
        net_worth_growth = (net_worth * 0.05 / 12) if net_worth > 0 else 0

        return {
            "net_worth": round(net_worth, 2),
            "net_worth_growth": round(net_worth_growth, 2),
            "risk_level": risk_level,
            "monthly_income": float(user.monthly_income or 0),
            "monthly_expenses": float(user.monthly_expenses or 0),
            "surplus": max(0, float((user.monthly_income or 0) - (user.monthly_expenses or 0))),
            "tax_saved": round(tax_saved, 2),
            "tax_limit": tax_limit,
            "portfolio_history": portfolio_history,
            "asset_allocation": asset_allocation,
            "top_holdings": top_holdings,
            "alerts": alerts
        }

    async def _get_banking_total(self, user_id: UUID) -> float:
        """Get total balance across all banking accounts"""
        result = await self.db.execute(
            select(func.sum(BankingAccount.current_balance))
            .where(BankingAccount.user_id == user_id)
        )
        total = result.scalar() or 0
        return float(total)

    async def _get_equity_data(self, user_id: UUID):
        """Get equity holdings and total value"""
        result = await self.db.execute(
            select(EquityHolding).where(EquityHolding.user_id == user_id)
        )
        holdings = result.scalars().all()
        
        holdings_list = []
        total_value = 0.0
        for h in holdings:
            value = float((h.current_value or 0))
            total_value += value
            holdings_list.append({
                "instrument": f"{h.symbol}",
                "type": "Equity",
                "quantity": float(h.quantity),
                "current_value": round(value, 2),
                "profit_loss_percent": self._calculate_profit_loss_percent(h),
            })
        
        return {"holdings": holdings_list, "total_value": total_value}

    async def _get_mutual_fund_data(self, user_id: UUID):
        """Get mutual fund holdings and total value"""
        result = await self.db.execute(
            select(MutualFundHolding).where(MutualFundHolding.user_id == user_id)
        )
        holdings = result.scalars().all()
        
        holdings_list = []
        total_value = 0.0
        for h in holdings:
            value = float((h.current_value or 0))
            total_value += value
            holdings_list.append({
                "instrument": h.name,
                "type": "Mutual Fund",
                "quantity": float(h.units),
                "current_value": round(value, 2),
                "profit_loss_percent": self._calculate_profit_loss_percent_mf(h),
            })
        
        return {"holdings": holdings_list, "total_value": total_value}

    async def _get_etf_data(self, user_id: UUID):
        """Get ETF holdings and total value"""
        result = await self.db.execute(
            select(ETFHolding).where(ETFHolding.user_id == user_id)
        )
        holdings = result.scalars().all()
        
        holdings_list = []
        total_value = 0.0
        for h in holdings:
            value = float((h.current_value or 0))
            total_value += value
            holdings_list.append({
                "instrument": f"{h.symbol}",
                "type": "ETF",
                "quantity": float(h.quantity),
                "current_value": round(value, 2),
                "profit_loss_percent": self._calculate_profit_loss_percent(h),
            })
        
        return {"holdings": holdings_list, "total_value": total_value}

    async def _get_crypto_data(self, user_id: UUID):
        """Get crypto holdings and total value"""
        result = await self.db.execute(
            select(CryptoHolding).where(CryptoHolding.user_id == user_id)
        )
        holdings = result.scalars().all()
        
        holdings_list = []
        total_value = 0.0
        for h in holdings:
            value = float((h.current_value or 0))
            total_value += value
            holdings_list.append({
                "instrument": f"{h.symbol}",
                "type": "Crypto",
                "quantity": float(h.quantity),
                "current_value": round(value, 2),
                "profit_loss_percent": self._calculate_profit_loss_percent(h),
            })
        
        return {"holdings": holdings_list, "total_value": total_value}

    async def _get_cashflow_data(self, user_id: UUID):
        """Get cashflow data (income/expenses) from transactions"""
        # Get transactions from last month
        last_month = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(
            select(
                func.sum(BankTransaction.amount).filter(BankTransaction.tx_type == "credit"),
                func.sum(BankTransaction.amount).filter(BankTransaction.tx_type == "debit")
            ).where(
                (BankTransaction.user_id == user_id) &
                (BankTransaction.tx_date >= last_month.date())
            )
        )
        income, expenses = result.first()
        return {
            "income": float(income or 0),
            "expenses": float(expenses or 0),
        }

    async def _calculate_tax_saved(self, user_id: UUID) -> float:
        """
        Calculate total tax saved through 80C investments
        (Simplified: assume 30% return on equity/MF investments)
        """
        result = await self.db.execute(
            select(func.sum(EquityHolding.current_value))
            .where(EquityHolding.user_id == user_id)
        )
        equity_value = float(result.scalar() or 0)
        
        result = await self.db.execute(
            select(func.sum(MutualFundHolding.current_value))
            .where(MutualFundHolding.user_id == user_id)
        )
        mf_value = float(result.scalar() or 0)
        
        # Simplified tax calculation: 30% of investments
        tax_saved = (equity_value + mf_value) * 0.30 * 0.15  # 15% tax rate
        return min(tax_saved, 50000)  # Cap at typical 80C ceiling

    def _build_asset_allocation(self, banking, equity_data, mf_data, etf_data, crypto_data):
        """Build asset allocation breakdown"""
        total = (
            banking +
            equity_data['total_value'] +
            mf_data['total_value'] +
            etf_data['total_value'] +
            crypto_data['total_value']
        )
        
        if total == 0:
            return []
        
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
        allocations = [
            ("Cash", banking, colors[0]),
            ("Equities", equity_data['total_value'], colors[1]),
            ("Mutual Funds", mf_data['total_value'], colors[2]),
            ("ETFs", etf_data['total_value'], colors[3]),
            ("Crypto", crypto_data['total_value'], colors[4]),
        ]
        
        return [
            {
                "name": name,
                "value": round((value / total) * 100, 2),
                "color": color
            }
            for name, value, color in allocations
            if value > 0
        ]

    def _generate_portfolio_history(self, current_net_worth, months=12):
        """Generate simulated 12-month portfolio value history"""
        history = []
        base_value = current_net_worth * 0.8  # Start from 80% of current
        
        for i in range(months):
            # Simulate 5% annual growth with some volatility
            growth = base_value * (1 + (0.05 / 12)) * (0.95 + (i % 3) * 0.02)
            date = datetime.utcnow() - timedelta(days=(months - i) * 30)
            
            history.append({
                "month": date.strftime("%b %Y"),
                "value": round(growth, 2)
            })
        
        return history

    def _generate_alerts(self, net_worth: float, cashflow_data: dict, risk_profile: str = "moderate"):
        """Generate dashboard alerts based on portfolio state"""
        alerts = []
        
        if net_worth == 0:
            alerts.append({
                "id": "1",
                "type": "info",
                "message": "Connect your accounts or insert data to see insights.",
                "icon": "lightbulb"
            })
        elif net_worth < 100000:
            alerts.append({
                "id": "2",
                "type": "info",
                "message": "Your net worth is below ₹1,00,000. Start with small investments.",
                "icon": "lightbulb"
            })
        
        if cashflow_data['expenses'] > cashflow_data['income']:
            alerts.append({
                "id": "3",
                "type": "warning",
                "message": f"Expenses exceed income by ₹{abs(cashflow_data['expenses'] - cashflow_data['income']):,.0f}",
                "icon": "alert-triangle"
            })
        elif cashflow_data['income'] > 0 and (cashflow_data['expenses'] / cashflow_data['income']) > 0.9:
            alerts.append({
                "id": "4",
                "type": "warning",
                "message": "High expense ratio. Consider reducing discretionary spending.",
                "icon": "alert-triangle"
            })
        
        if (cashflow_data['income'] - cashflow_data['expenses']) > 50000:
            alerts.append({
                "id": "5",
                "type": "opportunity",
                "message": "Strong monthly surplus! Consider increasing investment contributions.",
                "icon": "bar-chart-3"
            })
        
        return alerts

    def _determine_risk_level(self, risk_profile: str = None) -> str:
        """Map user risk profile to dashboard risk level"""
        profile_map = {
            "conservative": "Low",
            "moderate": "Medium",
            "aggressive": "High",
        }
        return profile_map.get(risk_profile or "moderate", "Medium")

    def _calculate_profit_loss_percent(self, holding) -> float:
        """Calculate profit/loss percentage for equity-like holdings"""
        if holding.avg_price and holding.avg_price > 0:
            current_price = float(holding.current_price or holding.avg_price)
            return round(((current_price - float(holding.avg_price)) / float(holding.avg_price)) * 100, 2)
        return 0.0

    def _calculate_profit_loss_percent_mf(self, holding) -> float:
        """Calculate profit/loss percentage for mutual funds"""
        if holding.avg_nav and holding.avg_nav > 0:
            current_nav = float(holding.current_nav or holding.avg_nav)
            return round(((current_nav - float(holding.avg_nav)) / float(holding.avg_nav)) * 100, 2)
        return 0.0

    def _empty_dashboard(self) -> dict:
        """Return empty dashboard structure"""
        return {
            "net_worth": 0,
            "net_worth_growth": 0,
            "risk_level": "Low",
            "monthly_income": 0,
            "monthly_expenses": 0,
            "surplus": 0,
            "tax_saved": 0,
            "tax_limit": 150000,
            "portfolio_history": [],
            "asset_allocation": [],
            "top_holdings": [],
            "alerts": [{
                "id": "1",
                "type": "info",
                "message": "Connect your accounts or insert data to see your insights.",
                "icon": "lightbulb"
            }]
        }

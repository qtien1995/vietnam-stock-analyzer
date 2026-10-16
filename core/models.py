"""
Canonical Data Models for Vietnam Stock Analyzer
Single Source of Truth (SSOT) schema for all quantitative engines and presentation layers.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    STALE = "STALE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID = "INVALID"


class RecommendationAction(str, Enum):
    STRONG_BUY = "MUA MẠNH (STRONG BUY)"
    TEST_BUY = "MUA THĂM DÒ (TEST BUY)"
    WATCHLIST = "THEO DÕI (WATCHLIST)"
    AVOID = "BÁN / TRÁNH XA (AVOID)"
    NO_VALID_SETUP = "CHƯA CÓ ĐIỂM MUA HỢP LỆ (NO SETUP)"


class ConfidenceLevel(str, Enum):
    HIGH = "CAO"
    MEDIUM = "VỪA"
    LOW = "THẤP"


class ProvenanceSource(str, Enum):
    SSI_REALTIME = "SSI_REALTIME"
    DNSE_CANDLES = "DNSE_CANDLES"
    VNSTOCK_VCI = "VNSTOCK_VCI"
    LOCAL_CACHE = "LOCAL_CACHE"
    REFERENCE_BENCHMARK = "REFERENCE_BENCHMARK"
    STATIC_FALLBACK = "STATIC_FALLBACK"


# -------------------------------------------------------------
# 1. Market & Quote Model
# -------------------------------------------------------------
class MarketQuote(BaseModel):
    symbol: str
    company_name: str
    exchange: str = "HOSE"
    price_limit_pct: float = 7.0
    price: float = 0.0
    ref_price: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: float = 0.0
    value: float = 0.0
    foreign_net_vol: float = 0.0
    trading_date: str = ""
    source: str = "SSI_REALTIME"


# -------------------------------------------------------------
# 2. Fundamental Analysis Models
# -------------------------------------------------------------
class FinancialRatios(BaseModel):
    pe: Optional[float] = None
    pe_status: str = "VALID"
    pb: Optional[float] = None
    pb_status: str = "VALID"
    peg: Optional[float] = None
    peg_status: str = "VALID"
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    liabilities_to_equity: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    profit_growth_yoy: Optional[float] = None
    eps: Optional[float] = None
    bvps: Optional[float] = None
    tbvps: Optional[float] = None
    ncavps: Optional[float] = None
    net_cash_per_share: Optional[float] = None
    issue_share: Optional[float] = None
    market_cap: Optional[float] = None
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash: Optional[float] = None
    receivables: Optional[float] = None
    inventories: Optional[float] = None
    total_debt: Optional[float] = None
    owners_equity: Optional[float] = None
    working_capital: Optional[float] = None
    ttm_revenue: Optional[float] = None
    ttm_profit: Optional[float] = None
    ebit_ttm: Optional[float] = None
    dupont: Optional[Dict[str, Any]] = None


class CashFlowAnalysis(BaseModel):
    cfo_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None
    fcf_ttm: Optional[float] = None
    cfi_ttm: Optional[float] = None
    cff_ttm: Optional[float] = None
    cfo_latest_q: Optional[float] = None
    quality_grade: str = "B"
    quality_verdict: str = "LÀNH MẠNH"
    quality_desc: str = ""
    earnings_quality_ratio: Optional[float] = None
    altman_z: Optional[float] = None
    z_zone: str = "SAFE"
    z_verdict: str = "AN TOÀN"
    z_desc: str = ""
    red_flags: List[str] = Field(default_factory=list)
    quarterly_cash_flows: List[Dict[str, Any]] = Field(default_factory=list)


class PiotroskiFScore(BaseModel):
    score: int = 0
    max_score: int = 9
    variant: str = "STANDARD"  # "STANDARD" or "MODIFIED_STATIC"
    details: Dict[str, Any] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)


class ValuationAssessment(BaseModel):
    fair_price: float = 0.0
    margin_of_safety_pct: float = 0.0
    value_status: str = "ĐỊNH GIÁ HỢP LÝ"
    valuation_warning: str = ""
    valuation_scenario: Dict[str, Any] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)


class BusinessSegment(BaseModel):
    name: str
    rev_share_pct: float = 0.0
    gross_profit_share_pct: float = 0.0
    gross_margin_pct: float = 0.0
    role: str = ""
    highlights: str = ""
    service_description: str = ""


class BusinessSegmentsProfile(BaseModel):
    has_detailed_segments: bool = False
    source: str = "UNVERIFIED"
    business_model_summary: str = ""
    segments: List[BusinessSegment] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)


class GovernanceAssessment(BaseModel):
    g_score: int = 60
    g_rating: str = "ĐẠT CHUẨN"
    integrity_verdict: str = ""
    shell_risk_desc: str = ""
    leadership_analysis: str = ""
    ownership: Dict[str, Any] = Field(default_factory=dict)
    leadership: Dict[str, Any] = Field(default_factory=dict)
    subsidiary_web: Dict[str, Any] = Field(default_factory=dict)


class MacroAndSectorAssessment(BaseModel):
    sector_key: str = "GENERAL"
    sector_name: str = "Doanh nghiệp Tổng hợp"
    cycle_phase: str = "Bình thường"
    tailwind_score: float = 70.0
    sentiment: str = "TRUNG TÍNH"
    dalio_verdict: str = ""
    marks_verdict: str = ""
    macro_drivers: List[str] = Field(default_factory=list)
    key_metrics_to_watch: List[str] = Field(default_factory=list)
    commodity_sensitivity: Dict[str, Any] = Field(default_factory=dict)
    global_commodities: Dict[str, Any] = Field(default_factory=dict)
    sector_wave: Dict[str, Any] = Field(default_factory=dict)


class FundamentalAnalysis(BaseModel):
    sector: str = "GENERAL"
    fa_total_score: int = 50
    data_quality_status: DataQualityStatus = DataQualityStatus.VALID
    latest_quarter: str = ""
    ratios: FinancialRatios = Field(default_factory=FinancialRatios)
    cash_flow: CashFlowAnalysis = Field(default_factory=CashFlowAnalysis)
    f_score: PiotroskiFScore = Field(default_factory=PiotroskiFScore)
    buffett_valuation: ValuationAssessment = Field(default_factory=ValuationAssessment)
    lynch_growth: Dict[str, Any] = Field(default_factory=dict)
    asset_valuation: Dict[str, Any] = Field(default_factory=dict)
    growth_quality: Dict[str, Any] = Field(default_factory=dict)
    dupont: Dict[str, Any] = Field(default_factory=dict)
    roic: Optional[float] = None
    segments: BusinessSegmentsProfile = Field(default_factory=BusinessSegmentsProfile)
    governance: GovernanceAssessment = Field(default_factory=GovernanceAssessment)
    macro: MacroAndSectorAssessment = Field(default_factory=MacroAndSectorAssessment)
    valuation_warning: str = ""


# -------------------------------------------------------------
# 3. Technical Analysis Models
# -------------------------------------------------------------
class TechnicalIndicators(BaseModel):
    close: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    sma200: float = 0.0
    rsi14: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    atr14: float = 0.0
    sup_20d: float = 0.0
    res_20d: float = 0.0
    high_52w: float = 0.0
    low_52w: float = 0.0
    rs_rating: int = 50
    vol_ma20: float = 0.0
    vol_ratio: float = 1.0


class TechnicalAnalysis(BaseModel):
    ta_total_score: int = 50
    indicators: TechnicalIndicators = Field(default_factory=TechnicalIndicators)
    oneil: Dict[str, Any] = Field(default_factory=dict)
    vsa: Dict[str, Any] = Field(default_factory=dict)
    advanced_ta: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------------------------------------
# 4. Risk & Trade Setup Models
# -------------------------------------------------------------
class TradeSetup(BaseModel):
    has_valid_setup: bool = False
    setup_status: str = "NO_VALID_SETUP"
    action: str = "THEO DÕI (WATCHLIST)"
    action_color: str = "#f59e0b"
    action_summary: str = ""
    confidence: str = "VỪA"
    consensus_score: int = 50
    current_price: float = 0.0
    buy_zone: str = "CHƯA CÓ ĐIỂM MUA HỢP LỆ"
    stop_loss: float = 0.0
    stop_loss_pct: float = 0.0
    take_profit_1: float = 0.0
    take_profit_1_pct: float = 0.0
    take_profit_2: float = 0.0
    take_profit_2_pct: float = 0.0
    take_profit_3: float = 0.0
    take_profit_3_pct: float = 0.0
    risk_reward_ratio: float = 0.0
    max_position_size_pct: float = 0.0
    invalidation_conditions: List[str] = Field(default_factory=list)
    exchange: str = "HOSE"
    price_limit_pct: float = 7.0
    fair_price: float = 0.0
    value_status: str = ""
    value_warning: str = ""
    value_buy_zone: str = ""
    premium_discount_pct: float = 0.0
    valuation_gap_explanation: str = ""
    swing_buy_zone: str = ""
    swing_strategy_note: str = ""
    in_downtrend: bool = False
    heavy_foreign_sell: bool = False
    fa_score: int = 50
    ta_score: int = 50


# -------------------------------------------------------------
# 5. Timing Prediction Model
# -------------------------------------------------------------
class TimingPrediction(BaseModel):
    setup_quality_score: int = 50
    timing_state: str = "TÍCH LŨY THEO DÕI"
    timing_verdict: str = "TÍCH LŨY THEO DÕI"
    timing_color: str = "#38bdf8"
    active_buy_pct: float = 50.0
    active_sell_pct: float = 50.0
    order_pressure_verdict: str = "CÂN BẰNG CUNG CẦU"
    foreign_verdict: str = "Trung lập"
    trigger_pivot_price: float = 0.0
    dist_pivot_pct: float = 0.0
    failure_trigger_level: float = 0.0
    dist_failure_pct: float = 0.0
    surge_scenario: Dict[str, Any] = Field(default_factory=dict)
    crash_scenario: Dict[str, Any] = Field(default_factory=dict)
    smart_money_pulse: Dict[str, Any] = Field(default_factory=dict)
    catalysts: List[Dict[str, Any]] = Field(default_factory=list)


# -------------------------------------------------------------
# 6. Investment Council Model
# -------------------------------------------------------------
class CouncilMember(BaseModel):
    name: str
    role_title: str
    badge: str
    stance: str
    stance_color: str
    score: int
    core_thesis: str
    arguments: List[str] = Field(default_factory=list)
    invalidation: str = ""


class InvestmentCouncilResult(BaseModel):
    council_report: str = ""
    members: List[CouncilMember] = Field(default_factory=list)
    voting_summary: Dict[str, Any] = Field(default_factory=dict)
    clash_of_perspectives: List[Dict[str, Any]] = Field(default_factory=list)


# -------------------------------------------------------------
# 7. CANONICAL ANALYSIS RESULT (Root SSOT)
# -------------------------------------------------------------
class AnalysisResult(BaseModel):
    # Metadata & Schema Versioning
    schema_version: str = "2.0.0"
    symbol: str
    company_name: str
    exchange: str = "HOSE"
    price_limit_pct: float = 7.0
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    market_data_as_of: str = ""
    latest_financial_quarter: str = ""
    data_quality_status: DataQualityStatus = DataQualityStatus.VALID
    data_warnings: List[str] = Field(default_factory=list)

    # Core Components
    quote: MarketQuote
    fa: FundamentalAnalysis
    ta: TechnicalAnalysis
    trade_setup: TradeSetup
    timing: TimingPrediction
    council: InvestmentCouncilResult
    insider_whale: Optional[Dict[str, Any]] = None

    # Report Artifact Paths
    html_report_path: Optional[str] = None
    markdown_report_path: Optional[str] = None

    @classmethod
    def from_components(
        cls,
        symbol: str,
        quote: Dict[str, Any],
        fa_result: Dict[str, Any],
        ta_result: Dict[str, Any],
        trade_setup: Dict[str, Any],
        timing_result: Optional[Dict[str, Any]] = None,
        council_result: Optional[Dict[str, Any]] = None,
        insider_whale_result: Optional[Dict[str, Any]] = None,
        html_report_path: Optional[str] = None
    ) -> "AnalysisResult":
        """Factory method xây dựng canonical AnalysisResult từ output của các engine."""
        if timing_result is None:
            timing_result = {}
        if council_result is None:
            council_result = {}
        if insider_whale_result is None:
            insider_whale_result = {}


        quote_clean = {
            "symbol": symbol.upper().strip(),
            "company_name": quote.get("company_name", symbol),
            "exchange": quote.get("exchange", "HOSE"),
            "price_limit_pct": float(quote.get("price_limit_pct", 7.0)),
            "price": float(quote.get("price", 0.0)),
            "ref_price": float(quote.get("ref_price", quote.get("price", 0.0))),
            "open_price": float(quote.get("open", quote.get("open_price", 0.0))),
            "high_price": float(quote.get("high", quote.get("high_price", 0.0))),
            "low_price": float(quote.get("low", quote.get("low_price", 0.0))),
            "change": float(quote.get("change", 0.0)),
            "change_pct": float(quote.get("change_pct", 0.0)),
            "volume": float(quote.get("volume", 0.0)),
            "value": float(quote.get("value", 0.0)),
            "foreign_net_vol": float(quote.get("foreign_net_vol", 0.0)),
            "trading_date": str(quote.get("trading_date", "")),
            "source": str(quote.get("source", "SSI_REALTIME"))
        }

        # Sub-models FA
        ratios_dict = fa_result.get("ratios", {})
        cf_dict = fa_result.get("cash_flow", {})
        buffett_dict = fa_result.get("buffett", {})
        seg_dict = fa_result.get("segments", {})
        gov_dict = fa_result.get("governance", {})
        macro_dict = fa_result.get("macro", {})

        f_score_obj = PiotroskiFScore(
            score=int(fa_result.get("f_score", 0)),
            breakdown=fa_result.get("f_score_breakdown", fa_result.get("f_score_details", [])),
            method=fa_result.get("f_score_meta", {}).get("method", "MODIFIED_STATIC") if isinstance(fa_result.get("f_score_meta"), dict) else "MODIFIED_STATIC"
        )

        fa_obj = FundamentalAnalysis(
            sector=fa_result.get("sector", "GENERAL"),
            fa_total_score=int(fa_result.get("fa_total_score", 50)),
            latest_quarter=str(fa_result.get("latest_quarter", "")),
            ratios=FinancialRatios(**{k: v for k, v in ratios_dict.items() if k in FinancialRatios.model_fields}),
            cash_flow=CashFlowAnalysis(**{k: v for k, v in cf_dict.items() if k in CashFlowAnalysis.model_fields}),
            f_score=f_score_obj,
            buffett_valuation=ValuationAssessment(**{k: v for k, v in buffett_dict.items() if k in ValuationAssessment.model_fields}),
            lynch_growth=fa_result.get("lynch", {}),
            asset_valuation=fa_result.get("asset_valuation", {}),
            growth_quality=fa_result.get("growth_quality", {}),
            dupont=fa_result.get("dupont", {}),
            roic=fa_result.get("roic"),
            segments=BusinessSegmentsProfile(**{k: v for k, v in seg_dict.items() if k in BusinessSegmentsProfile.model_fields}),
            governance=GovernanceAssessment(**{k: v for k, v in gov_dict.items() if k in GovernanceAssessment.model_fields}),
            macro=MacroAndSectorAssessment(**{k: v for k, v in macro_dict.items() if k in MacroAndSectorAssessment.model_fields}),
            valuation_warning=str(fa_result.get("valuation_warning", ""))
        )

        # Sub-models TA
        ind_dict = ta_result.get("indicators", {})
        ta_obj = TechnicalAnalysis(
            ta_total_score=int(ta_result.get("ta_total_score", 50)),
            indicators=TechnicalIndicators(**{k: v for k, v in ind_dict.items() if k in TechnicalIndicators.model_fields}),
            oneil=ta_result.get("oneil", {}),
            vsa=ta_result.get("vsa", {}),
            advanced_ta=ta_result.get("advanced_ta", {})
        )

        # Sub-model Trade Setup
        trade_obj = TradeSetup(**{k: v for k, v in trade_setup.items() if k in TradeSetup.model_fields})

        # Sub-model Timing
        timing_obj = TimingPrediction(**{k: v for k, v in timing_result.items() if k in TimingPrediction.model_fields})

        # Sub-model Council
        raw_members = council_result.get("members", [])
        c_members = []
        for rm in raw_members:
            if isinstance(rm, dict):
                c_members.append(CouncilMember(**{k: v for k, v in rm.items() if k in CouncilMember.model_fields}))

        council_obj = InvestmentCouncilResult(
            council_report=council_result.get("council_report", ""),
            members=c_members,
            voting_summary=council_result.get("voting_summary", {}),
            clash_of_perspectives=council_result.get("clash_of_perspectives", [])
        )

        return cls(
            symbol=symbol.upper().strip(),
            company_name=quote_clean["company_name"],
            exchange=quote_clean["exchange"],
            price_limit_pct=quote_clean["price_limit_pct"],
            quote=MarketQuote(**quote_clean),
            fa=fa_obj,
            ta=ta_obj,
            trade_setup=trade_obj,
            timing=timing_obj,
            council=council_obj,
            insider_whale=insider_whale_result if insider_whale_result else None,
            html_report_path=html_report_path
        )

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Adapter xuất ngược sang dict cấu trúc v1 để bảo đảm tương thích tuyệt đối."""
        return {
            "symbol": self.symbol,
            "quote": self.quote.model_dump(),
            "current_price": self.quote.price,
            "fa_result": {
                "sector": self.fa.sector,
                "fa_total_score": self.fa.fa_total_score,
                "latest_quarter": self.fa.latest_quarter,
                "data_quality_status": self.fa.data_quality_status.value,
                "f_score": self.fa.f_score.score,
                "piotroski_details": self.fa.f_score.details,
                "ratios": self.fa.ratios.model_dump(),
                "cash_flow": self.fa.cash_flow.model_dump(),
                "buffett": self.fa.buffett_valuation.model_dump(),
                "lynch": self.fa.lynch_growth,
                "asset_valuation": self.fa.asset_valuation,
                "growth_quality": self.fa.growth_quality,
                "dupont": self.fa.dupont,
                "roic": self.fa.roic,
                "segments": self.fa.segments.model_dump(),
                "governance": self.fa.governance.model_dump(),
                "macro": self.fa.macro.model_dump(),
                "valuation_warning": self.fa.valuation_warning,
            },
            "ta_result": {
                "ta_total_score": self.ta.ta_total_score,
                "indicators": self.ta.indicators.model_dump(),
                "oneil": self.ta.oneil,
                "vsa": self.ta.vsa,
                "advanced_ta": self.ta.advanced_ta,
            },
            "trade_setup": self.trade_setup.model_dump(),
            "timing_result": self.timing.model_dump(),
            "insider_whale": self.insider_whale,
            "council_result": {
                "council_report": self.council.council_report,
                "members": [m.model_dump() for m in self.council.members],
                "voting_summary": self.council.voting_summary,
                "clash_of_perspectives": self.council.clash_of_perspectives,
            },
            "html_path": self.html_report_path
        }


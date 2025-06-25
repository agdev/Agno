"""
Financial Modeling Prep API Tools

This module implements the FinancialModelingPrepTools class that provides
integration with the Financial Modeling Prep API for fetching financial data.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from agno.tools.toolkit import Toolkit


class FinancialModelingPrepTools(Toolkit):
    """
    Tools for interacting with the Financial Modeling Prep API

    This toolkit provides methods to fetch various types of financial data
    including income statements, company financials, stock prices, and symbol search.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="financial_modeling_prep")

        # Get API key from parameter, environment, or session state
        self.api_key = api_key or os.getenv("FINANCIAL_MODELING_PREP_API_KEY")

        # If still no API key, try to get from session state (requires streamlit)
        if not self.api_key:
            try:
                import streamlit as st

                self.api_key = st.session_state.get("fmp_api_key")
            except ImportError:
                pass  # Streamlit not available, that's OK

        self.base_url = "https://financialmodelingprep.com/api/v3"

        if not self.api_key:
            raise ValueError(
                "Financial Modeling Prep API key is required. "
                "Please set FINANCIAL_MODELING_PREP_API_KEY environment variable "
                "or provide api_key parameter, or enter it in the UI."
            )

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Make HTTP request to Financial Modeling Prep API

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            List or Dict containing API response data

        Raises:
            Exception: If API request fails
        """
        if params is None:
            params = {}

        params["apikey"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Financial Modeling Prep API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")

    def search_symbol(self, query: str) -> Dict[str, Any]:
        """
        Search for stock symbols by company name or partial ticker

        Args:
            query: Company name or partial ticker symbol to search for

        Returns:
            Dict containing search results with symbol, name, and exchange info
        """
        try:
            # First try direct symbol lookup
            if len(query) <= 5 and query.isalpha():
                symbol = query.upper()
                # Validate symbol exists by fetching basic profile
                profile_data = self._make_request(f"profile/{symbol}")
                if (
                    profile_data
                    and isinstance(profile_data, list)
                    and len(profile_data) > 0
                ):
                    company = profile_data[0]
                    return {
                        "symbol": symbol,
                        "name": company.get("companyName", "Unknown"),
                        "exchange": company.get("exchangeShortName", "Unknown"),
                        "found": True,
                    }

            # Search by company name
            search_data = self._make_request("search", {"query": query, "limit": 5})

            if search_data and isinstance(search_data, list) and len(search_data) > 0:
                # Return the first (most relevant) result
                result = search_data[0]
                return {
                    "symbol": result.get("symbol", "UNKNOWN"),
                    "name": result.get("name", "Unknown"),
                    "exchange": result.get("exchangeShortName", "Unknown"),
                    "found": True,
                }
            else:
                return {
                    "symbol": "UNKNOWN",
                    "name": "Not Found",
                    "exchange": "N/A",
                    "found": False,
                    "error": f"No symbols found for query: {query}",
                }
        except Exception as e:
            return {
                "symbol": "UNKNOWN",
                "name": "Error",
                "exchange": "N/A",
                "found": False,
                "error": str(e),
            }

    def get_income_statement(
        self, symbol: str, period: str = "annual", limit: int = 1
    ) -> Dict[str, Any]:
        """
        Get income statement data for a company

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve (default: 1)

        Returns:
            Dict containing income statement data
        """
        try:
            symbol = symbol.upper()
            endpoint = f"income-statement/{symbol}"
            params = {"period": period, "limit": limit}

            data = self._make_request(endpoint, params)

            if not data or not isinstance(data, list) or len(data) == 0:
                return {
                    "symbol": symbol,
                    "error": f"No income statement data found for {symbol}",
                    "success": False,
                }

            # Process the most recent income statement
            income_statement = data[0]

            return {
                "symbol": symbol,
                "date": income_statement.get("date", "Unknown"),
                "period": income_statement.get("period", period),
                "revenue": income_statement.get("revenue", 0),
                "gross_profit": income_statement.get("grossProfit", 0),
                "operating_income": income_statement.get("operatingIncome", 0),
                "net_income": income_statement.get("netIncome", 0),
                "eps": income_statement.get("eps", 0),
                "gross_profit_ratio": income_statement.get("grossProfitRatio", 0),
                "operating_income_ratio": income_statement.get(
                    "operatingIncomeRatio", 0
                ),
                "net_income_ratio": income_statement.get("netIncomeRatio", 0),
                "research_and_development": income_statement.get(
                    "researchAndDevelopmentExpenses", 0
                ),
                "total_operating_expenses": income_statement.get(
                    "totalOperatingExpenses", 0
                ),
                "success": True,
                "raw_data": income_statement,
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch income statement for {symbol}: {str(e)}",
                "success": False,
            }

    def get_company_financials(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive company financial metrics and ratios

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict containing company financial metrics
        """
        try:
            symbol = symbol.upper()

            # Get key financial metrics
            metrics_data = self._make_request(f"key-metrics/{symbol}", {"limit": 1})

            # Get financial ratios
            ratios_data = self._make_request(f"ratios/{symbol}", {"limit": 1})

            # Get company profile for basic info
            profile_data = self._make_request(f"profile/{symbol}")

            if (
                not metrics_data
                or not isinstance(metrics_data, list)
                or len(metrics_data) == 0
            ):
                return {
                    "symbol": symbol,
                    "error": f"No financial data found for {symbol}",
                    "success": False,
                }

            metrics = (
                metrics_data[0]
                if isinstance(metrics_data, list) and metrics_data
                else {}
            )
            ratios = (
                ratios_data[0] if isinstance(ratios_data, list) and ratios_data else {}
            )
            profile = (
                profile_data[0]
                if isinstance(profile_data, list) and profile_data
                else {}
            )

            return {
                "symbol": symbol,
                "company_name": profile.get("companyName", "Unknown"),
                "market_cap": profile.get("mktCap", 0),
                "beta": profile.get("beta", 0),
                "pe_ratio": metrics.get("peRatio", 0),
                "price_to_book": ratios.get("priceToBookRatio", 0),
                "price_to_sales": ratios.get("priceToSalesRatio", 0),
                "debt_to_equity": ratios.get("debtEquityRatio", 0),
                "current_ratio": ratios.get("currentRatio", 0),
                "quick_ratio": ratios.get("quickRatio", 0),
                "roe": ratios.get("returnOnEquity", 0),
                "roa": ratios.get("returnOnAssets", 0),
                "revenue_growth": metrics.get("revenueGrowth", 0),
                "gross_margin": ratios.get("grossProfitMargin", 0),
                "operating_margin": ratios.get("operatingProfitMargin", 0),
                "net_margin": ratios.get("netProfitMargin", 0),
                "enterprise_value": metrics.get("enterpriseValue", 0),
                "working_capital": metrics.get("workingCapital", 0),
                "date": metrics.get("date", "Unknown"),
                "success": True,
                "raw_metrics": metrics,
                "raw_ratios": ratios,
                "raw_profile": profile,
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch company financials for {symbol}: {str(e)}",
                "success": False,
            }

    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price and trading information

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict containing current stock price data
        """
        try:
            symbol = symbol.upper()

            # Get real-time quote
            quote_data = self._make_request(f"quote/{symbol}")

            # Get historical price for trend analysis (last 5 days)
            historical_data = self._make_request(
                f"historical-price-full/{symbol}", {"timeseries": 5}
            )

            if (
                not quote_data
                or not isinstance(quote_data, list)
                or len(quote_data) == 0
            ):
                return {
                    "symbol": symbol,
                    "error": f"No price data found for {symbol}",
                    "success": False,
                }

            quote = quote_data[0]

            # Calculate basic metrics
            previous_close = quote.get("previousClose", 0)
            current_price = quote.get("price", 0)

            # Enhanced analytics using historical data
            trend_analysis = self._analyze_price_trend(historical_data, current_price)
            volatility_metrics = self._calculate_volatility(historical_data)

            return {
                "symbol": symbol,
                "name": quote.get("name", "Unknown"),
                "price": current_price,
                "change": quote.get("change", 0),
                "change_percent": quote.get("changesPercentage", 0),
                "previous_close": previous_close,
                "open": quote.get("open", 0),
                "high": quote.get("dayHigh", 0),
                "low": quote.get("dayLow", 0),
                "volume": quote.get("volume", 0),
                "avg_volume": quote.get("avgVolume", 0),
                "market_cap": quote.get("marketCap", 0),
                "pe_ratio": quote.get("pe", 0),
                "eps": quote.get("eps", 0),
                "fifty_two_week_high": quote.get("yearHigh", 0),
                "fifty_two_week_low": quote.get("yearLow", 0),
                "exchange": quote.get("exchange", "Unknown"),
                "timestamp": quote.get("timestamp", int(datetime.now().timestamp())),
                # Enhanced analytics from historical data
                "trend_direction": trend_analysis.get("direction", "neutral"),
                "trend_strength": trend_analysis.get("strength", 0),
                "five_day_change_percent": trend_analysis.get(
                    "five_day_change_percent", 0
                ),
                "price_volatility": volatility_metrics.get("volatility", 0),
                "volume_trend": volatility_metrics.get("volume_trend", "stable"),
                "success": True,
                "raw_data": quote,
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch stock price for {symbol}: {str(e)}",
                "success": False,
            }

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get basic company profile information

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict containing company profile data
        """
        try:
            symbol = symbol.upper()
            profile_data = self._make_request(f"profile/{symbol}")

            if (
                not profile_data
                or not isinstance(profile_data, list)
                or len(profile_data) == 0
            ):
                return {
                    "symbol": symbol,
                    "error": f"No profile data found for {symbol}",
                    "success": False,
                }

            profile = profile_data[0]

            return {
                "symbol": symbol,
                "company_name": profile.get("companyName", "Unknown"),
                "description": profile.get("description", "No description available"),
                "industry": profile.get("industry", "Unknown"),
                "sector": profile.get("sector", "Unknown"),
                "website": profile.get("website", ""),
                "ceo": profile.get("ceo", "Unknown"),
                "employees": profile.get("fullTimeEmployees", 0),
                "country": profile.get("country", "Unknown"),
                "exchange": profile.get("exchangeShortName", "Unknown"),
                "currency": profile.get("currency", "USD"),
                "success": True,
                "raw_data": profile,
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch company profile for {symbol}: {str(e)}",
                "success": False,
            }

    def _analyze_price_trend(
        self,
        historical_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Analyze price trend from historical data

        Args:
            historical_data: Historical price data from API
            current_price: Current stock price

        Returns:
            Dict containing trend analysis
        """
        try:
            # Handle case where historical data is not available or not in expected format
            if not historical_data or not isinstance(historical_data, dict):
                return {
                    "direction": "neutral",
                    "strength": 0,
                    "five_day_change_percent": 0,
                }

            # Extract historical prices from the nested structure
            historical_prices = historical_data.get("historical", [])
            if not historical_prices or len(historical_prices) < 2:
                return {
                    "direction": "neutral",
                    "strength": 0,
                    "five_day_change_percent": 0,
                }

            # Get prices (most recent first in FMP API)
            prices = [
                float(day.get("close", 0))
                for day in historical_prices[:5]
                if day.get("close")
            ]
            if len(prices) < 2:
                return {
                    "direction": "neutral",
                    "strength": 0,
                    "five_day_change_percent": 0,
                }

            # Calculate 5-day change
            oldest_price = prices[-1]  # 5 days ago
            five_day_change_percent = (
                ((current_price - oldest_price) / oldest_price * 100)
                if oldest_price > 0
                else 0
            )

            # Determine trend direction and strength
            if len(prices) >= 3:
                # Count upward vs downward movements
                up_days = sum(
                    1 for i in range(len(prices) - 1) if prices[i] > prices[i + 1]
                )
                total_days = len(prices) - 1

                if up_days / total_days >= 0.6:
                    direction = "bullish"
                    strength = min(up_days / total_days, 1.0)
                elif up_days / total_days <= 0.4:
                    direction = "bearish"
                    strength = min((total_days - up_days) / total_days, 1.0)
                else:
                    direction = "neutral"
                    strength = 0.5
            else:
                # Simple comparison for limited data
                if five_day_change_percent > 2:
                    direction = "bullish"
                    strength = min(abs(five_day_change_percent) / 10, 1.0)
                elif five_day_change_percent < -2:
                    direction = "bearish"
                    strength = min(abs(five_day_change_percent) / 10, 1.0)
                else:
                    direction = "neutral"
                    strength = 0.5

            return {
                "direction": direction,
                "strength": round(strength, 2),
                "five_day_change_percent": round(five_day_change_percent, 2),
            }

        except Exception:
            return {"direction": "neutral", "strength": 0, "five_day_change_percent": 0}

    def _calculate_volatility(
        self, historical_data: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate volatility metrics from historical data

        Args:
            historical_data: Historical price data from API

        Returns:
            Dict containing volatility metrics
        """
        try:
            # Handle case where historical data is not available
            if not historical_data or not isinstance(historical_data, dict):
                return {"volatility": 0, "volume_trend": "stable"}

            historical_prices = historical_data.get("historical", [])
            if not historical_prices or len(historical_prices) < 3:
                return {"volatility": 0, "volume_trend": "stable"}

            # Calculate price volatility (standard deviation of daily returns)
            prices = [
                float(day.get("close", 0))
                for day in historical_prices[:5]
                if day.get("close")
            ]
            volumes = [
                int(day.get("volume", 0))
                for day in historical_prices[:5]
                if day.get("volume")
            ]

            if len(prices) >= 3:
                # Calculate daily returns
                returns = []
                for i in range(len(prices) - 1):
                    if prices[i + 1] > 0:
                        daily_return = (prices[i] - prices[i + 1]) / prices[i + 1]
                        returns.append(daily_return)

                # Calculate volatility (standard deviation)
                if returns:
                    mean_return = sum(returns) / len(returns)
                    variance = sum((r - mean_return) ** 2 for r in returns) / len(
                        returns
                    )
                    volatility = (variance**0.5) * 100  # Convert to percentage
                else:
                    volatility = 0
            else:
                volatility = 0

            # Analyze volume trend
            volume_trend = "stable"
            if len(volumes) >= 3:
                recent_avg = sum(volumes[:2]) / 2 if len(volumes) >= 2 else volumes[0]
                older_avg = (
                    sum(volumes[2:]) / len(volumes[2:])
                    if len(volumes) > 2
                    else recent_avg
                )

                if recent_avg > older_avg * 1.2:
                    volume_trend = "increasing"
                elif recent_avg < older_avg * 0.8:
                    volume_trend = "decreasing"
                else:
                    volume_trend = "stable"

            return {"volatility": round(volatility, 2), "volume_trend": volume_trend}

        except Exception:
            return {"volatility": 0, "volume_trend": "stable"}

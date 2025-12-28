#!/usr/bin/env python3
"""
Advanced Analytics Module (Premium Feature)

Provides advanced analytics, insights, and recommendations beyond basic power monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta

from .premium import get_premium_features


class AdvancedAnalytics:
    """Advanced analytics engine (premium feature)."""
    
    def __init__(self):
        self.premium = get_premium_features()
        if not self.premium.advanced_analytics_enabled():
            raise PermissionError("Advanced Analytics is a premium feature. Upgrade to access.")
    
    def analyze_power_trends(self, csv_file: Path, window_hours: int = 24) -> Dict:
        """Analyze power consumption trends over time."""
        df = pd.read_csv(csv_file)
        
        # Convert timestamp to datetime if needed
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        # Calculate rolling statistics
        window = f"{window_hours}H"
        rolling_mean = df['ane_power_mw'].rolling(window=window).mean()
        rolling_std = df['ane_power_mw'].rolling(window=window).std()
        
        # Detect anomalies (3 sigma rule)
        mean_power = df['ane_power_mw'].mean()
        std_power = df['ane_power_mw'].std()
        anomalies = df[abs(df['ane_power_mw'] - mean_power) > 3 * std_power]
        
        # Predict future power consumption (simple linear trend)
        if len(df) > 10:
            x = np.arange(len(df))
            y = df['ane_power_mw'].values
            trend = np.polyfit(x, y, 1)
            predicted_next = np.polyval(trend, len(df))
        else:
            predicted_next = mean_power
        
        return {
            "trend_analysis": {
                "mean_power_mw": mean_power,
                "std_power_mw": std_power,
                "min_power_mw": df['ane_power_mw'].min(),
                "max_power_mw": df['ane_power_mw'].max(),
                "rolling_mean_mw": rolling_mean.iloc[-1] if len(rolling_mean) > 0 else mean_power,
                "rolling_std_mw": rolling_std.iloc[-1] if len(rolling_std) > 0 else std_power,
            },
            "anomaly_detection": {
                "anomaly_count": len(anomalies),
                "anomaly_percent": (len(anomalies) / len(df)) * 100,
                "anomalies": anomalies.to_dict('records') if len(anomalies) > 0 else []
            },
            "prediction": {
                "predicted_next_power_mw": predicted_next,
                "confidence": "medium" if len(df) > 50 else "low"
            }
        }
    
    def generate_optimization_recommendations(self, analysis_data: Dict) -> List[Dict]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Check for high power consumption
        if analysis_data.get("mean_power_mw", 0) > 2000:
            recommendations.append({
                "priority": "high",
                "category": "power_consumption",
                "title": "High Power Consumption Detected",
                "description": f"Average power consumption is {analysis_data['mean_power_mw']:.0f} mW, which is above optimal range.",
                "action": "Consider optimizing inference batch size or model quantization.",
                "potential_savings": "20-30% power reduction"
            })
        
        # Check for anomalies
        anomaly_count = analysis_data.get("anomaly_count", 0)
        if anomaly_count > 10:
            recommendations.append({
                "priority": "medium",
                "category": "stability",
                "title": "Power Anomalies Detected",
                "description": f"{anomaly_count} power anomalies detected, indicating unstable power consumption.",
                "action": "Investigate background processes or thermal throttling.",
                "potential_savings": "10-15% stability improvement"
            })
        
        # Check for burst patterns
        if analysis_data.get("max_power_mw", 0) / analysis_data.get("mean_power_mw", 1) > 2.0:
            recommendations.append({
                "priority": "medium",
                "category": "burst_optimization",
                "title": "High Burst Power Detected",
                "description": "Power consumption shows high burst patterns, indicating inefficient power management.",
                "action": "Consider implementing burst limiting or thermal throttling controls.",
                "potential_savings": "15-25% average power reduction"
            })
        
        return recommendations
    
    def compare_profiles(self, profile1: Dict, profile2: Dict) -> Dict:
        """Compare two power profiles and provide insights."""
        comparison = {
            "power_difference_mw": profile2.get("mean_power_mw", 0) - profile1.get("mean_power_mw", 0),
            "power_difference_percent": ((profile2.get("mean_power_mw", 0) - profile1.get("mean_power_mw", 0)) / profile1.get("mean_power_mw", 1)) * 100,
            "efficiency_improvement": profile1.get("mean_power_mw", 0) / profile2.get("mean_power_mw", 1) if profile2.get("mean_power_mw", 0) > 0 else 0,
            "recommendation": None
        }
        
        if comparison["power_difference_percent"] < -10:
            comparison["recommendation"] = f"Profile 2 is {abs(comparison['power_difference_percent']):.1f}% more efficient. Consider adopting Profile 2's configuration."
        elif comparison["power_difference_percent"] > 10:
            comparison["recommendation"] = f"Profile 1 is {comparison['power_difference_percent']:.1f}% more efficient. Consider keeping Profile 1's configuration."
        else:
            comparison["recommendation"] = "Both profiles have similar power consumption. Choose based on other factors (latency, accuracy, etc.)."
        
        return comparison
    
    def generate_report(self, csv_file: Path, output_file: Optional[Path] = None) -> Dict:
        """Generate comprehensive analytics report."""
        trends = self.analyze_power_trends(csv_file)
        recommendations = self.generate_optimization_recommendations(trends["trend_analysis"])
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "data_file": str(csv_file),
            "trend_analysis": trends,
            "recommendations": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "high_priority": len([r for r in recommendations if r["priority"] == "high"]),
                "medium_priority": len([r for r in recommendations if r["priority"] == "medium"]),
                "estimated_savings": "20-30% power reduction potential"
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report


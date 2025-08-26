# ChurnGuard Statistical Analysis Service
# Epic 4 - Advanced Analytics & AI Insights

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import scipy.stats as stats
from scipy import signal
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import logging

logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

class SeasonalityType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NONE = "none"

@dataclass
class StatisticalSummary:
    """Statistical summary of a dataset"""
    count: int
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float
    skewness: float
    kurtosis: float
    
@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    direction: TrendDirection
    slope: float
    r_squared: float
    p_value: float
    confidence_interval: Tuple[float, float]
    trend_strength: float
    
@dataclass
class SeasonalityAnalysis:
    """Seasonality analysis results"""
    seasonality_type: SeasonalityType
    seasonal_strength: float
    period: int
    seasonal_components: List[float]
    residuals: List[float]

@dataclass
class AnomalyDetectionResult:
    """Anomaly detection results"""
    anomalies: List[Dict[str, Any]]
    anomaly_scores: List[float]
    threshold: float
    method: str
    summary: Dict[str, Any]

class StatisticalAnalysisService:
    """
    Advanced statistical analysis service for ChurnGuard analytics
    
    Provides:
    - Descriptive statistics and distribution analysis
    - Trend detection and forecasting
    - Seasonality analysis
    - Anomaly detection using multiple algorithms
    - Correlation and causality analysis
    - Customer segmentation using clustering
    - A/B testing statistical significance
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def descriptive_statistics(self, data: List[float]) -> StatisticalSummary:
        """
        Calculate comprehensive descriptive statistics
        
        Args:
            data: List of numeric values
            
        Returns:
            StatisticalSummary with comprehensive stats
        """
        if not data:
            return StatisticalSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        arr = np.array(data)
        
        return StatisticalSummary(
            count=len(arr),
            mean=float(np.mean(arr)),
            std=float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
            min=float(np.min(arr)),
            max=float(np.max(arr)),
            median=float(np.median(arr)),
            q25=float(np.percentile(arr, 25)),
            q75=float(np.percentile(arr, 75)),
            skewness=float(stats.skew(arr)),
            kurtosis=float(stats.kurtosis(arr))
        )
    
    def trend_analysis(self, timestamps: List[datetime], values: List[float],
                      confidence_level: float = 0.95) -> TrendAnalysis:
        """
        Analyze trends in time-series data using linear regression
        
        Args:
            timestamps: List of datetime objects
            values: Corresponding numeric values
            confidence_level: Confidence level for intervals
            
        Returns:
            TrendAnalysis with trend direction, strength, and statistics
        """
        if len(timestamps) != len(values) or len(values) < 3:
            return TrendAnalysis(
                TrendDirection.STABLE, 0.0, 0.0, 1.0, (0.0, 0.0), 0.0
            )
        
        # Convert timestamps to numeric values (days since first timestamp)
        time_numeric = [(t - timestamps[0]).total_seconds() / 86400 for t in timestamps]
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)
        
        # Calculate confidence interval for slope
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, len(values) - 2)
        ci_lower = slope - t_critical * std_err
        ci_upper = slope + t_critical * std_err
        
        # Determine trend direction
        if p_value > 0.05:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for high volatility
        residuals = np.array(values) - (slope * np.array(time_numeric) + intercept)
        volatility = np.std(residuals) / np.mean(np.abs(values)) if np.mean(np.abs(values)) > 0 else 0
        
        if volatility > 0.5:  # High volatility threshold
            direction = TrendDirection.VOLATILE
        
        # Calculate trend strength (0-1 scale)
        trend_strength = min(abs(r_value), 1.0)
        
        return TrendAnalysis(
            direction=direction,
            slope=slope,
            r_squared=r_value**2,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            trend_strength=trend_strength
        )
    
    def seasonality_analysis(self, timestamps: List[datetime], values: List[float],
                           period_hints: List[int] = None) -> SeasonalityAnalysis:
        """
        Detect and analyze seasonality patterns in time-series data
        
        Args:
            timestamps: List of datetime objects
            values: Corresponding numeric values  
            period_hints: Optional list of periods to test (in data points)
            
        Returns:
            SeasonalityAnalysis with detected seasonality information
        """
        if len(values) < 14:  # Need minimum data for seasonality detection
            return SeasonalityAnalysis(
                SeasonalityType.NONE, 0.0, 0, [], values
            )
        
        # Default period hints based on typical patterns
        if period_hints is None:
            # Estimate data frequency
            time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 
                         for i in range(min(10, len(timestamps)-1))]
            avg_hours_between_points = np.mean(time_diffs)
            
            if avg_hours_between_points <= 1:  # Hourly or sub-hourly data
                period_hints = [24, 168]  # Daily (24h), Weekly (168h)
            elif avg_hours_between_points <= 24:  # Daily data
                period_hints = [7, 30]  # Weekly, Monthly
            else:
                period_hints = [4, 12]  # Quarterly, Yearly (for weekly/monthly data)
        
        best_period = 0
        best_strength = 0.0
        best_components = []
        
        # Test different periods for seasonality
        for period in period_hints:
            if period >= len(values):
                continue
                
            # Calculate autocorrelation at this lag
            autocorr = self._calculate_autocorrelation(values, period)
            
            if autocorr > best_strength:
                best_strength = autocorr
                best_period = period
                best_components = self._extract_seasonal_components(values, period)
        
        # Determine seasonality type based on period and data frequency
        seasonality_type = self._determine_seasonality_type(best_period, timestamps)
        
        # Calculate residuals after removing seasonal component
        if best_components:
            # Repeat seasonal pattern to match data length
            full_seasonal = (best_components * (len(values) // len(best_components) + 1))[:len(values)]
            residuals = [values[i] - full_seasonal[i] for i in range(len(values))]
        else:
            residuals = values.copy()
        
        return SeasonalityAnalysis(
            seasonality_type=seasonality_type,
            seasonal_strength=best_strength,
            period=best_period,
            seasonal_components=best_components,
            residuals=residuals
        )
    
    def anomaly_detection(self, values: List[float], 
                         method: str = 'zscore',
                         sensitivity: float = 2.0,
                         window_size: int = 10) -> AnomalyDetectionResult:
        """
        Detect anomalies in data using multiple statistical methods
        
        Args:
            values: Numeric data values
            method: Detection method ('zscore', 'iqr', 'isolation_forest', 'dbscan')
            sensitivity: Sensitivity parameter (lower = more sensitive)
            window_size: Window size for rolling statistics
            
        Returns:
            AnomalyDetectionResult with detected anomalies
        """
        if len(values) < window_size:
            return AnomalyDetectionResult([], [], 0.0, method, {})
        
        anomalies = []
        anomaly_scores = []
        
        if method == 'zscore':
            anomalies, anomaly_scores, threshold = self._zscore_anomalies(
                values, sensitivity, window_size
            )
        elif method == 'iqr':
            anomalies, anomaly_scores, threshold = self._iqr_anomalies(
                values, sensitivity
            )
        elif method == 'isolation_forest':
            anomalies, anomaly_scores, threshold = self._isolation_forest_anomalies(
                values, sensitivity
            )
        elif method == 'statistical':
            anomalies, anomaly_scores, threshold = self._statistical_anomalies(
                values, sensitivity, window_size
            )
        else:
            raise ValueError(f"Unsupported anomaly detection method: {method}")
        
        summary = {
            'total_anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / len(values),
            'method': method,
            'threshold': threshold,
            'avg_anomaly_score': np.mean(anomaly_scores) if anomaly_scores else 0.0
        }
        
        return AnomalyDetectionResult(
            anomalies=anomalies,
            anomaly_scores=anomaly_scores,
            threshold=threshold,
            method=method,
            summary=summary
        )
    
    def correlation_analysis(self, data_dict: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix between multiple variables
        
        Args:
            data_dict: Dictionary of variable names to value lists
            
        Returns:
            Correlation matrix as nested dictionary
        """
        if len(data_dict) < 2:
            return {}
        
        # Convert to DataFrame for easier correlation calculation
        df = pd.DataFrame(data_dict)
        
        # Handle missing values
        df = df.fillna(df.mean())
        
        # Calculate Pearson correlation
        corr_matrix = df.corr()
        
        # Convert to nested dictionary format
        result = {}
        for var1 in corr_matrix.columns:
            result[var1] = {}
            for var2 in corr_matrix.columns:
                result[var1][var2] = float(corr_matrix.loc[var1, var2])
        
        return result
    
    def customer_segmentation(self, features: List[Dict[str, float]], 
                            n_clusters: int = None,
                            method: str = 'kmeans') -> Dict[str, Any]:
        """
        Perform customer segmentation using clustering algorithms
        
        Args:
            features: List of feature dictionaries for each customer
            n_clusters: Number of clusters (auto-determined if None)
            method: Clustering method ('kmeans', 'dbscan')
            
        Returns:
            Segmentation results with cluster assignments and characteristics
        """
        if not features:
            return {'clusters': [], 'assignments': [], 'method': method}
        
        # Convert features to matrix
        feature_names = list(features[0].keys())
        feature_matrix = np.array([[f.get(name, 0.0) for name in feature_names] 
                                  for f in features])
        
        # Standardize features
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        if method == 'kmeans':
            # Auto-determine optimal number of clusters if not specified
            if n_clusters is None:
                n_clusters = self._optimal_clusters_kmeans(scaled_features)
            
            clustering = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_assignments = clustering.fit_predict(scaled_features)
            cluster_centers = clustering.cluster_centers_
            
        elif method == 'dbscan':
            # Use DBSCAN for density-based clustering
            eps = self._estimate_dbscan_eps(scaled_features)
            clustering = DBSCAN(eps=eps, min_samples=5)
            cluster_assignments = clustering.fit_predict(scaled_features)
            n_clusters = len(set(cluster_assignments)) - (1 if -1 in cluster_assignments else 0)
            cluster_centers = None
            
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
        
        # Analyze cluster characteristics
        cluster_stats = self._analyze_cluster_characteristics(
            feature_matrix, cluster_assignments, feature_names
        )
        
        # Calculate silhouette score for cluster quality
        if len(set(cluster_assignments)) > 1:
            silhouette_avg = silhouette_score(scaled_features, cluster_assignments)
        else:
            silhouette_avg = 0.0
        
        return {
            'n_clusters': n_clusters,
            'assignments': cluster_assignments.tolist(),
            'cluster_centers': cluster_centers.tolist() if cluster_centers is not None else None,
            'cluster_characteristics': cluster_stats,
            'silhouette_score': silhouette_avg,
            'method': method,
            'feature_names': feature_names
        }
    
    def ab_test_analysis(self, control_group: List[float], 
                        treatment_group: List[float],
                        confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        Perform statistical analysis of A/B test results
        
        Args:
            control_group: Values from control group
            treatment_group: Values from treatment group  
            confidence_level: Confidence level for statistical tests
            
        Returns:
            A/B test analysis results including significance and effect size
        """
        if not control_group or not treatment_group:
            return {'error': 'Both groups must have data'}
        
        control_stats = self.descriptive_statistics(control_group)
        treatment_stats = self.descriptive_statistics(treatment_group)
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(control_group, treatment_group)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(control_group) - 1) * control_stats.std**2 + 
                             (len(treatment_group) - 1) * treatment_stats.std**2) / 
                            (len(control_group) + len(treatment_group) - 2))
        
        cohens_d = (treatment_stats.mean - control_stats.mean) / pooled_std if pooled_std > 0 else 0
        
        # Calculate confidence interval for difference
        alpha = 1 - confidence_level
        se_diff = np.sqrt(control_stats.std**2/len(control_group) + 
                         treatment_stats.std**2/len(treatment_group))
        
        df = len(control_group) + len(treatment_group) - 2
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        mean_diff = treatment_stats.mean - control_stats.mean
        ci_lower = mean_diff - t_critical * se_diff
        ci_upper = mean_diff + t_critical * se_diff
        
        # Determine statistical significance
        is_significant = p_value < (1 - confidence_level)
        
        # Calculate relative lift
        relative_lift = (mean_diff / control_stats.mean * 100) if control_stats.mean != 0 else 0
        
        return {
            'control_stats': control_stats,
            'treatment_stats': treatment_stats,
            'mean_difference': mean_diff,
            'relative_lift_percent': relative_lift,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'cohens_d': cohens_d,
            'confidence_interval': (ci_lower, ci_upper),
            'confidence_level': confidence_level,
            'sample_sizes': {
                'control': len(control_group),
                'treatment': len(treatment_group)
            }
        }
    
    # Private helper methods
    def _calculate_autocorrelation(self, values: List[float], lag: int) -> float:
        """Calculate autocorrelation at specified lag"""
        if lag >= len(values):
            return 0.0
        
        # Use numpy's correlate function
        autocorr = np.correlate(values[lag:], values[:-lag], mode='valid')
        norm_factor = np.sqrt(np.sum(np.square(values[lag:])) * np.sum(np.square(values[:-lag])))
        
        return float(autocorr[0] / norm_factor) if norm_factor > 0 else 0.0
    
    def _extract_seasonal_components(self, values: List[float], period: int) -> List[float]:
        """Extract seasonal components for given period"""
        seasonal_sums = [0.0] * period
        seasonal_counts = [0] * period
        
        for i, value in enumerate(values):
            season_idx = i % period
            seasonal_sums[season_idx] += value
            seasonal_counts[season_idx] += 1
        
        # Calculate average for each seasonal component
        seasonal_components = [
            seasonal_sums[i] / seasonal_counts[i] if seasonal_counts[i] > 0 else 0.0
            for i in range(period)
        ]
        
        return seasonal_components
    
    def _determine_seasonality_type(self, period: int, timestamps: List[datetime]) -> SeasonalityType:
        """Determine seasonality type based on period and data frequency"""
        if period == 0:
            return SeasonalityType.NONE
        
        # Estimate data frequency
        if len(timestamps) > 1:
            avg_interval = (timestamps[-1] - timestamps[0]).total_seconds() / (len(timestamps) - 1)
            
            if period * avg_interval <= 86400 * 1.5:  # ~Daily
                return SeasonalityType.DAILY
            elif period * avg_interval <= 604800 * 1.5:  # ~Weekly  
                return SeasonalityType.WEEKLY
            elif period * avg_interval <= 2628000 * 1.5:  # ~Monthly
                return SeasonalityType.MONTHLY
            else:
                return SeasonalityType.YEARLY
        
        return SeasonalityType.NONE
    
    def _zscore_anomalies(self, values: List[float], sensitivity: float, 
                         window_size: int) -> Tuple[List[Dict], List[float], float]:
        """Detect anomalies using rolling Z-score"""
        anomalies = []
        anomaly_scores = []
        threshold = sensitivity
        
        for i in range(window_size, len(values)):
            window = values[max(0, i-window_size):i]
            mean = np.mean(window)
            std = np.std(window)
            
            if std > 0:
                z_score = abs(values[i] - mean) / std
                anomaly_scores.append(z_score)
                
                if z_score > sensitivity:
                    anomalies.append({
                        'index': i,
                        'value': values[i],
                        'expected': mean,
                        'z_score': z_score,
                        'type': 'zscore'
                    })
            else:
                anomaly_scores.append(0.0)
        
        return anomalies, anomaly_scores, threshold
    
    def _iqr_anomalies(self, values: List[float], 
                      sensitivity: float) -> Tuple[List[Dict], List[float], float]:
        """Detect anomalies using Interquartile Range method"""
        q25, q75 = np.percentile(values, [25, 75])
        iqr = q75 - q25
        threshold = sensitivity * iqr
        
        lower_bound = q25 - threshold
        upper_bound = q75 + threshold
        
        anomalies = []
        anomaly_scores = []
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'type': 'iqr'
                })
                anomaly_scores.append(min(abs(value - lower_bound), abs(value - upper_bound)) / iqr)
            else:
                anomaly_scores.append(0.0)
        
        return anomalies, anomaly_scores, threshold
    
    def _statistical_anomalies(self, values: List[float], sensitivity: float,
                             window_size: int) -> Tuple[List[Dict], List[float], float]:
        """Detect anomalies using statistical methods (Grubbs' test)"""
        anomalies = []
        anomaly_scores = []
        threshold = sensitivity
        
        # Use modified Z-score for robust anomaly detection
        median = np.median(values)
        mad = np.median([abs(x - median) for x in values])
        
        for i, value in enumerate(values):
            if mad > 0:
                modified_z_score = 0.6745 * (value - median) / mad
                anomaly_scores.append(abs(modified_z_score))
                
                if abs(modified_z_score) > sensitivity:
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'median': median,
                        'modified_z_score': modified_z_score,
                        'type': 'statistical'
                    })
            else:
                anomaly_scores.append(0.0)
        
        return anomalies, anomaly_scores, threshold
    
    def _optimal_clusters_kmeans(self, features: np.ndarray, max_clusters: int = 10) -> int:
        """Determine optimal number of clusters using elbow method"""
        if len(features) < 4:
            return min(2, len(features))
        
        max_k = min(max_clusters, len(features) - 1)
        inertias = []
        
        for k in range(1, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(features)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point
        if len(inertias) < 3:
            return 2
        
        # Calculate rate of change
        rates = [(inertias[i-1] - inertias[i]) / inertias[i-1] for i in range(1, len(inertias))]
        
        # Find the point where rate of change starts decreasing significantly
        for i in range(1, len(rates)):
            if rates[i] < rates[i-1] * 0.8:  # 80% threshold
                return i + 1
        
        return min(3, max_k)  # Default fallback
    
    def _estimate_dbscan_eps(self, features: np.ndarray) -> float:
        """Estimate optimal eps parameter for DBSCAN"""
        if len(features) < 5:
            return 0.5
        
        # Calculate k-distance (k=4 as rule of thumb)
        k = min(4, len(features) - 1)
        
        from sklearn.neighbors import NearestNeighbors
        neighbors = NearestNeighbors(n_neighbors=k)
        neighbors_fit = neighbors.fit(features)
        distances, indices = neighbors_fit.kneighbors(features)
        
        # Sort distances and find elbow
        distances = np.sort(distances[:, k-1], axis=0)
        
        # Use knee point detection - simplified approach
        # Find point with maximum curvature
        n_points = len(distances)
        if n_points < 10:
            return float(np.mean(distances))
        
        # Take point at 90th percentile as conservative estimate
        return float(np.percentile(distances, 90))
    
    def _analyze_cluster_characteristics(self, features: np.ndarray, 
                                       assignments: np.ndarray, 
                                       feature_names: List[str]) -> Dict[str, Dict[str, float]]:
        """Analyze characteristics of each cluster"""
        cluster_stats = {}
        
        for cluster_id in set(assignments):
            if cluster_id == -1:  # DBSCAN noise points
                continue
                
            cluster_mask = assignments == cluster_id
            cluster_features = features[cluster_mask]
            
            stats_dict = {}
            for i, feature_name in enumerate(feature_names):
                feature_values = cluster_features[:, i]
                stats_dict[feature_name] = {
                    'mean': float(np.mean(feature_values)),
                    'std': float(np.std(feature_values)),
                    'min': float(np.min(feature_values)),
                    'max': float(np.max(feature_values)),
                    'size': int(np.sum(cluster_mask))
                }
            
            cluster_stats[f'cluster_{cluster_id}'] = stats_dict
        
        return cluster_stats

# Global statistical analysis service instance
stats_service = StatisticalAnalysisService()

def get_stats_service() -> StatisticalAnalysisService:
    """Get the global statistical analysis service instance"""
    return stats_service
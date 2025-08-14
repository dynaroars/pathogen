# Reporting and visualization utilities
# Generates graphs and reports for PathGen fuzzing campaigns showing resource usage patterns

import json
import os
import time
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_pdf import PdfPages
    import seaborn as sns
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

class ResourceType(Enum):
    """Types of resources that can be measured - focused on instruction count"""
    INSTRUCTION_COUNT = "instruction_count"

@dataclass
class ResourceMeasurement:
    """Single resource measurement for an input"""
    input_data: str
    input_size: int
    resource_values: Dict[ResourceType, float]
    iteration: int
    timestamp: float
    execution_success: bool
    input_hash: str

@dataclass
class CampaignReport:
    """Complete report for a fuzzing campaign"""
    campaign_id: str
    start_time: float
    end_time: float
    total_iterations: int
    target_program: str
    resource_metrics: List[ResourceType]
    measurements: List[ResourceMeasurement]
    best_inputs: List[Tuple[str, Dict[ResourceType, float]]]
    summary_stats: Dict[str, Any]
    convergence_analysis: Dict[str, Any]

class InputSizeAnalyzer:
    """Analyzes input sizes for different input types"""
    
    @staticmethod
    def calculate_size(input_data: str, input_method: str = "stdin") -> int:
        """Calculate the logical size of an input"""
        if input_method == "args":
            # For command line args, count the number of arguments
            return len(input_data.split())
        elif input_method == "file":
            # For file inputs, use byte length
            return len(input_data.encode('utf-8'))
        else:
            # For stdin and other methods, use character length
            return len(input_data)
    
    @staticmethod
    def categorize_size(size: int) -> str:
        """Categorize input size into ranges"""
        if size == 0:
            return "empty"
        elif size <= 10:
            return "tiny"
        elif size <= 100:
            return "small"
        elif size <= 1000:
            return "medium"
        elif size <= 10000:
            return "large"
        else:
            return "huge"

class ResourceTracker:
    """Tracks resource usage across fuzzing iterations"""
    
    def __init__(self, resource_types: List[ResourceType]):
        self.resource_types = resource_types
        self.measurements: List[ResourceMeasurement] = []
        self.iteration_counter = 0
    
    def add_measurement(self, input_data: str, execution_result, input_method: str = "stdin"):
        """Add a new resource measurement"""
        input_size = InputSizeAnalyzer.calculate_size(input_data, input_method)
        
        # Extract resource values from execution result
        resource_values = {}
        for resource_type in self.resource_types:
            if resource_type == ResourceType.INSTRUCTION_COUNT:
                resource_values[resource_type] = float(getattr(execution_result, 'instruction_count', 0))
            else:
                # No other resource types supported
                resource_values[resource_type] = 0.0
        
        measurement = ResourceMeasurement(
            input_data=input_data,
            input_size=input_size,
            resource_values=resource_values,
            iteration=self.iteration_counter,
            timestamp=time.time(),
            execution_success=getattr(execution_result, 'success', False),
            input_hash=str(hash(input_data))
        )
        
        self.measurements.append(measurement)
        self.iteration_counter += 1
        
        return measurement
    
    def get_measurements_by_resource(self, resource_type: ResourceType) -> List[Tuple[int, float]]:
        """Get (input_size, resource_value) pairs for a specific resource"""
        return [(m.input_size, m.resource_values.get(resource_type, 0)) 
                for m in self.measurements if m.execution_success]
    
    def get_iteration_progress(self, resource_type: ResourceType) -> List[Tuple[int, float]]:
        """Get (iteration, max_resource_value) pairs showing progress over time"""
        progress = []
        max_so_far = 0
        
        for measurement in self.measurements:
            if measurement.execution_success:
                current_value = measurement.resource_values.get(resource_type, 0)
                max_so_far = max(max_so_far, current_value)
            progress.append((measurement.iteration, max_so_far))
            
        return progress

class ReportGenerator:
    """Generates visual reports and graphs for fuzzing campaigns"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not PLOTTING_AVAILABLE:
            print("Warning: matplotlib/seaborn not available. Install with: pip install matplotlib seaborn")
    
    def generate_campaign_report(self, 
                                campaign_data: Dict[str, Any], 
                                resource_tracker: ResourceTracker,
                                target_name: str = "unknown") -> str:
        """Generate a complete campaign report with graphs"""
        
        if not PLOTTING_AVAILABLE:
            return self._generate_text_report(campaign_data, resource_tracker, target_name)
        
        campaign_id = f"pathogen_{target_name}_{int(time.time())}"
        report_path = self.output_dir / f"{campaign_id}_report.pdf"
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8' if hasattr(plt.style, 'available') and 'seaborn-v0_8' in plt.style.available else 'default')
        
        with PdfPages(report_path) as pdf:
            # Title page
            self._create_title_page(pdf, campaign_data, target_name, campaign_id)
            
            # Resource usage graphs for each resource type
            for resource_type in resource_tracker.resource_types:
                self._create_resource_graphs(pdf, resource_tracker, resource_type, target_name)
            
            # Summary statistics page
            self._create_summary_page(pdf, campaign_data, resource_tracker)
            
            # Input analysis page
            self._create_input_analysis_page(pdf, resource_tracker)
        
        # Also generate JSON report
        json_path = self.output_dir / f"{campaign_id}_data.json"
        self._generate_json_report(campaign_data, resource_tracker, json_path)
        
        return str(report_path)
    
    def _create_title_page(self, pdf, campaign_data: Dict[str, Any], target_name: str, campaign_id: str):
        """Create the report title page"""
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.9, 'PathoGen Fuzzing Report', 
                ha='center', va='center', fontsize=24, fontweight='bold')
        
        # Campaign information
        info_text = f"""
Campaign ID: {campaign_id}
Target Program: {target_name}
Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
Total Iterations: {campaign_data.get('total_iterations', 'N/A')}
Total Time: {campaign_data.get('total_time', 0):.2f} seconds
Convergence: {'Yes' if campaign_data.get('convergence_iteration', -1) > 0 else 'No'}
        """
        
        ax.text(0.5, 0.7, info_text, ha='center', va='center', fontsize=12)
        
        # Best results preview
        best_inputs = campaign_data.get('best_inputs', [])
        if best_inputs:
            best_text = "Top 3 Best Inputs Found:\n\n"
            for i, (input_data, score) in enumerate(best_inputs[:3], 1):
                preview = input_data[:50] + "..." if len(input_data) > 50 else input_data
                best_text += f"{i}. Score: {score:.0f}\n   Input: {preview}\n\n"
            
            ax.text(0.5, 0.4, best_text, ha='center', va='center', fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_resource_graphs(self, pdf, resource_tracker: ResourceTracker, 
                               resource_type: ResourceType, target_name: str):
        """Create graphs for a specific resource type"""
        # Create a figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{resource_type.value.replace("_", " ").title()} Analysis', fontsize=16, fontweight='bold')
        
        # Graph 1: Input Size vs Resource Usage (Scatter)
        size_resource_data = resource_tracker.get_measurements_by_resource(resource_type)
        if size_resource_data:
            sizes, resources = zip(*size_resource_data)
            ax1.scatter(sizes, resources, alpha=0.6, s=30)
            ax1.set_xlabel('Input Size')
            ax1.set_ylabel(f'{resource_type.value.replace("_", " ").title()}')
            ax1.set_title('Input Size vs Resource Usage')
            ax1.grid(True, alpha=0.3)
            
            # Add trend line if we have enough data
            if len(sizes) > 5:
                z = np.polyfit(sizes, resources, 1)
                p = np.poly1d(z)
                ax1.plot(sizes, p(sizes), "r--", alpha=0.8, label=f'Trend (slope: {z[0]:.2e})')
                ax1.legend()
        
        # Graph 2: Resource Progress Over Iterations
        iteration_data = resource_tracker.get_iteration_progress(resource_type)
        if iteration_data:
            iterations, max_resources = zip(*iteration_data)
            ax2.plot(iterations, max_resources, linewidth=2, marker='o', markersize=3)
            ax2.set_xlabel('Iteration')
            ax2.set_ylabel(f'Best {resource_type.value.replace("_", " ").title()} So Far')
            ax2.set_title('Resource Discovery Progress')
            ax2.grid(True, alpha=0.3)
            
            # Highlight convergence if it occurred
            if len(max_resources) > 10:
                # Find where improvement stops
                last_improvement = max_resources.index(max(max_resources))
                if last_improvement < len(max_resources) - 5:
                    ax2.axvline(x=last_improvement, color='red', linestyle='--', 
                               label=f'Convergence at iteration {last_improvement}')
                    ax2.legend()
        
        # Graph 3: Resource Distribution Histogram
        if size_resource_data:
            _, resources = zip(*size_resource_data)
            ax3.hist(resources, bins=min(20, len(resources)//2), alpha=0.7, edgecolor='black')
            ax3.set_xlabel(f'{resource_type.value.replace("_", " ").title()}')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Resource Usage Distribution')
            ax3.grid(True, alpha=0.3)
            
            # Add statistics
            mean_resource = statistics.mean(resources)
            median_resource = statistics.median(resources)
            ax3.axvline(mean_resource, color='red', linestyle='--', label=f'Mean: {mean_resource:.0f}')
            ax3.axvline(median_resource, color='green', linestyle='--', label=f'Median: {median_resource:.0f}')
            ax3.legend()
        
        # Graph 4: Input Size Categories Analysis
        size_categories = {}
        for measurement in resource_tracker.measurements:
            if measurement.execution_success:
                category = InputSizeAnalyzer.categorize_size(measurement.input_size)
                resource_value = measurement.resource_values.get(resource_type, 0)
                if category not in size_categories:
                    size_categories[category] = []
                size_categories[category].append(resource_value)
        
        if size_categories:
            categories = list(size_categories.keys())
            means = [statistics.mean(size_categories[cat]) for cat in categories]
            
            bars = ax4.bar(categories, means, alpha=0.7)
            ax4.set_xlabel('Input Size Category')
            ax4.set_ylabel(f'Average {resource_type.value.replace("_", " ").title()}')
            ax4.set_title('Resource Usage by Input Size Category')
            ax4.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, mean_val in zip(bars, means):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{mean_val:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_summary_page(self, pdf, campaign_data: Dict[str, Any], resource_tracker: ResourceTracker):
        """Create a summary statistics page"""
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        # Calculate summary statistics
        total_measurements = len(resource_tracker.measurements)
        successful_measurements = len([m for m in resource_tracker.measurements if m.execution_success])
        success_rate = (successful_measurements / total_measurements) * 100 if total_measurements > 0 else 0
        
        # Resource statistics for each type
        resource_stats = {}
        for resource_type in resource_tracker.resource_types:
            values = [m.resource_values.get(resource_type, 0) 
                     for m in resource_tracker.measurements if m.execution_success]
            if values:
                resource_stats[resource_type.value] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0
                }
        
        # Input size statistics
        input_sizes = [m.input_size for m in resource_tracker.measurements if m.execution_success]
        size_stats = {}
        if input_sizes:
            size_stats = {
                'min': min(input_sizes),
                'max': max(input_sizes),
                'mean': statistics.mean(input_sizes),
                'median': statistics.median(input_sizes)
            }
        
        # Create summary text
        summary_text = f"""
CAMPAIGN SUMMARY STATISTICS

Execution Statistics:
• Total Executions: {total_measurements}
• Successful Executions: {successful_measurements}
• Success Rate: {success_rate:.1f}%
• Total Runtime: {campaign_data.get('total_time', 0):.2f} seconds

Input Size Statistics:
"""
        
        if size_stats:
            summary_text += f"""• Minimum Size: {size_stats['min']}
• Maximum Size: {size_stats['max']}
• Average Size: {size_stats['mean']:.1f}
• Median Size: {size_stats['median']:.1f}

"""
        
        summary_text += "Resource Usage Statistics:\n"
        for resource_name, stats in resource_stats.items():
            resource_title = resource_name.replace('_', ' ').title()
            summary_text += f"""
{resource_title}:
• Minimum: {stats['min']:.2f}
• Maximum: {stats['max']:.2f}
• Average: {stats['mean']:.2f}
• Median: {stats['median']:.2f}
• Std Deviation: {stats['std']:.2f}
"""
        
        ax.text(0.05, 0.95, summary_text, ha='left', va='top', fontsize=10, 
               transform=ax.transAxes, fontfamily='monospace')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_input_analysis_page(self, pdf, resource_tracker: ResourceTracker):
        """Create input analysis page showing best inputs"""
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        # Get top inputs for the primary resource type
        primary_resource = resource_tracker.resource_types[0] if resource_tracker.resource_types else None
        if not primary_resource:
            return
        
        # Sort measurements by primary resource
        successful_measurements = [m for m in resource_tracker.measurements if m.execution_success]
        top_measurements = sorted(successful_measurements, 
                                key=lambda m: m.resource_values.get(primary_resource, 0), 
                                reverse=True)[:10]
        
        analysis_text = f"TOP 10 INPUTS BY {primary_resource.value.replace('_', ' ').upper()}\n"
        analysis_text += "=" * 60 + "\n\n"
        
        for i, measurement in enumerate(top_measurements, 1):
            resource_value = measurement.resource_values.get(primary_resource, 0)
            input_preview = measurement.input_data[:80] + "..." if len(measurement.input_data) > 80 else measurement.input_data
            
            analysis_text += f"{i}. Score: {resource_value:.0f} | Size: {measurement.input_size} | Iteration: {measurement.iteration}\n"
            analysis_text += f"   Input: {repr(input_preview)}\n\n"
        
        # Add input size analysis
        size_distribution = {}
        for measurement in successful_measurements:
            category = InputSizeAnalyzer.categorize_size(measurement.input_size)
            if category not in size_distribution:
                size_distribution[category] = 0
            size_distribution[category] += 1
        
        analysis_text += "\nINPUT SIZE DISTRIBUTION\n"
        analysis_text += "=" * 30 + "\n"
        for category, count in sorted(size_distribution.items()):
            percentage = (count / len(successful_measurements)) * 100
            analysis_text += f"{category.capitalize():>8}: {count:>3} ({percentage:>5.1f}%)\n"
        
        ax.text(0.05, 0.95, analysis_text, ha='left', va='top', fontsize=9, 
               transform=ax.transAxes, fontfamily='monospace')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _generate_json_report(self, campaign_data: Dict[str, Any], 
                             resource_tracker: ResourceTracker, json_path: Path):
        """Generate a JSON report with all data"""
        
        # Convert measurements to serializable format
        measurements_data = []
        for measurement in resource_tracker.measurements:
            measurement_dict = {
                'input_data': measurement.input_data,
                'input_size': measurement.input_size,
                'resource_values': {rt.value: val for rt, val in measurement.resource_values.items()},
                'iteration': measurement.iteration,
                'timestamp': measurement.timestamp,
                'execution_success': measurement.execution_success,
                'input_hash': measurement.input_hash
            }
            measurements_data.append(measurement_dict)
        
        # Create complete report data
        report_data = {
            'campaign_info': campaign_data,
            'resource_types': [rt.value for rt in resource_tracker.resource_types],
            'measurements': measurements_data,
            'summary_statistics': self._calculate_summary_stats(resource_tracker),
            'generation_metadata': {
                'report_generated_at': time.time(),
                'pathogen_version': '0.1.0',
                'total_measurements': len(resource_tracker.measurements)
            }
        }
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def _calculate_summary_stats(self, resource_tracker: ResourceTracker) -> Dict[str, Any]:
        """Calculate summary statistics for the report"""
        stats = {}
        
        for resource_type in resource_tracker.resource_types:
            values = [m.resource_values.get(resource_type, 0) 
                     for m in resource_tracker.measurements if m.execution_success]
            
            if values:
                stats[resource_type.value] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'percentile_90': sorted(values)[int(0.9 * len(values))] if len(values) > 10 else max(values),
                    'percentile_95': sorted(values)[int(0.95 * len(values))] if len(values) > 20 else max(values)
                }
        
        return stats
    
    def _generate_text_report(self, campaign_data: Dict[str, Any], 
                             resource_tracker: ResourceTracker, target_name: str) -> str:
        """Generate a text-based report when plotting is not available"""
        
        campaign_id = f"pathogen_{target_name}_{int(time.time())}"
        report_path = self.output_dir / f"{campaign_id}_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("PATHOGEN FUZZING CAMPAIGN REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Campaign ID: {campaign_id}\n")
            f.write(f"Target: {target_name}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Iterations: {campaign_data.get('total_iterations', 'N/A')}\n")
            f.write(f"Total Time: {campaign_data.get('total_time', 0):.2f} seconds\n\n")
            
            # Summary statistics
            stats = self._calculate_summary_stats(resource_tracker)
            f.write("RESOURCE USAGE STATISTICS\n")
            f.write("-" * 30 + "\n")
            
            for resource_type, resource_stats in stats.items():
                f.write(f"\n{resource_type.replace('_', ' ').title()}:\n")
                f.write(f"  Count: {resource_stats['count']}\n")
                f.write(f"  Min: {resource_stats['min']:.2f}\n")
                f.write(f"  Max: {resource_stats['max']:.2f}\n")
                f.write(f"  Mean: {resource_stats['mean']:.2f}\n")
                f.write(f"  Median: {resource_stats['median']:.2f}\n")
                f.write(f"  Std Dev: {resource_stats['std']:.2f}\n")
            
            # Top inputs
            f.write(f"\n\nTOP 10 INPUTS\n")
            f.write("-" * 20 + "\n")
            
            primary_resource = resource_tracker.resource_types[0] if resource_tracker.resource_types else None
            if primary_resource:
                successful_measurements = [m for m in resource_tracker.measurements if m.execution_success]
                top_measurements = sorted(successful_measurements, 
                                        key=lambda m: m.resource_values.get(primary_resource, 0), 
                                        reverse=True)[:10]
                
                for i, measurement in enumerate(top_measurements, 1):
                    resource_value = measurement.resource_values.get(primary_resource, 0)
                    f.write(f"\n{i}. Score: {resource_value:.0f} | Size: {measurement.input_size}\n")
                    f.write(f"   Input: {repr(measurement.input_data[:100])}\n")
        
        return str(report_path)
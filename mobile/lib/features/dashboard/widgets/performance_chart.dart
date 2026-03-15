import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../../../data/models/metric_model.dart';
import 'package:intl/intl.dart';

class PerformanceChart extends StatelessWidget {
  final List<Metric> metrics;

  const PerformanceChart({super.key, required this.metrics});

  @override
  Widget build(BuildContext context) {
    if (metrics.isEmpty) {
      return const SizedBox(
        height: 200,
        child: Center(
          child: Text('No data available', style: TextStyle(color: Colors.white54)),
        ),
      );
    }

    // Take last 30 days for performance trends (CTL/ATL are long-term)
    final recentMetrics = metrics.length > 30 ? metrics.sublist(metrics.length - 30) : metrics;
    
    return Container(
      height: 320,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A).withOpacity(0.4), // Slate 900
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Fitness & Fatigue',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _buildLegendItem("CTL (Fitness)", Colors.blueAccent),
              const SizedBox(width: 12),
              _buildLegendItem("ATL (Fatigue)", Colors.pinkAccent),
              const SizedBox(width: 12),
              _buildLegendItem("TSB (Form)", Colors.greenAccent),
            ],
          ),
          const SizedBox(height: 24),
          Expanded(
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(
                      color: Colors.white.withOpacity(0.05),
                      strokeWidth: 1,
                      dashArray: [5, 5], 
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  show: true,
                  rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 32,
                      interval: 5, // Show fewer labels
                      getTitlesWidget: (value, meta) {
                         int index = value.toInt();
                        if (index >= 0 && index < recentMetrics.length) {
                          try {
                            final date = DateTime.parse(recentMetrics[index].date);
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(
                                DateFormat('d.M').format(date), 
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.5),
                                  fontSize: 10,
                                ),
                              ),
                            );
                          } catch (e) {
                            return const Text('');
                          }
                        }
                        return const Text('');
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 45,
                      interval: null,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          value.toInt().toString(),
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 10,
                          ),
                        );
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                minX: 0,
                maxX: (recentMetrics.length - 1).toDouble(),
                lineBarsData: [
                  // CTL (Fitness) - Blue
                  LineChartBarData(
                    spots: recentMetrics.asMap().entries.map((e) {
                      return FlSpot(e.key.toDouble(), e.value.ctl);
                    }).toList(),
                    isCurved: true,
                    color: Colors.blueAccent,
                    barWidth: 2,
                    isStrokeCapRound: true,
                    dotData: FlDotData(show: false),
                  ),
                  // ATL (Fatigue) - Pink
                  LineChartBarData(
                    spots: recentMetrics.asMap().entries.map((e) {
                      return FlSpot(e.key.toDouble(), e.value.atl);
                    }).toList(),
                    isCurved: true,
                    color: Colors.pinkAccent,
                    barWidth: 2,
                    isStrokeCapRound: true,
                    dotData: FlDotData(show: false),
                  ),
                   // TSB (Form) - Green (Visualized as a line here, though Bar/Area might be better, sticking to line for simplicity in LineChart)
                   // Ideally TSB should be bars, but mixing charts in fl_chart is tricky. Let's use a dashed line or different style.
                   LineChartBarData(
                    spots: recentMetrics.asMap().entries.map((e) {
                      return FlSpot(e.key.toDouble(), e.value.tsb);
                    }).toList(),
                    isCurved: true,
                    color: Colors.greenAccent,
                    barWidth: 2,
                    dashArray: [5, 5],
                    isStrokeCapRound: true,
                    dotData: FlDotData(show: false),
                  ),
                ],
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    tooltipBgColor: Colors.blueGrey.shade900,
                    getTooltipItems: (touchedSpots) {
                      return touchedSpots.map((spot) {
                        return LineTooltipItem(
                          '${spot.y.toInt()}',
                          TextStyle(
                            color: spot.bar.color, // Match line color
                            fontWeight: FontWeight.bold,
                          ),
                        );
                      }).toList();
                    },
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 10)),
      ],
    );
  }
}

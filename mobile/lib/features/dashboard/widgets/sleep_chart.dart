import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../../../data/models/metric_model.dart';
import 'package:intl/intl.dart';

class SleepChart extends StatelessWidget {
  final List<Metric> metrics;

  const SleepChart({super.key, required this.metrics});

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
    
    // Take last 7 days or less
    final recentMetrics = metrics.length > 7 ? metrics.sublist(metrics.length - 7) : metrics;

    return Container(
      height: 280,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
             const Color(0xFF1E293B).withOpacity(0.6), // Slate 800
             const Color(0xFF0F172A).withOpacity(0.6), // Slate 900
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
         boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
               Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.indigoAccent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.nightlight_round, color: Colors.indigoAccent, size: 18),
              ),
              const SizedBox(width: 12),
              const Text(
                'Sleep Duration (Hours)',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          Expanded(
            child: BarChart(
              BarChartData(
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
                      getTitlesWidget: (value, meta) {
                        int index = value.toInt();
                        if (index >= 0 && index < recentMetrics.length) {
                           try {
                            final date = DateTime.parse(recentMetrics[index].date);
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(
                                DateFormat('E').format(date).substring(0, 1), // M, T, W
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.5),
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
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
                      reservedSize: 35,
                      interval: 2, // Show every 2 hours
                      getTitlesWidget: (value, meta) {
                        return Text(
                          value.toInt().toString(),
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 11,
                          ),
                        );
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                barGroups: recentMetrics.asMap().entries.map((e) {
                  // sleepMin is in minutes, convert to hours
                  final hours = e.value.sleepMin / 60.0;
                  return BarChartGroupData(
                    x: e.key,
                    barRods: [
                      BarChartRodData(
                        toY: hours,
                        gradient: const LinearGradient(
                           colors: [Colors.indigoAccent, Colors.purpleAccent],
                           begin: Alignment.bottomCenter,
                           end: Alignment.topCenter,
                        ),
                        width: 12,
                        borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(6),
                          topRight: Radius.circular(6),
                        ),
                        backDrawRodData: BackgroundBarChartRodData(
                          show: true,
                          toY: 10, // Max scale roughly
                          color: Colors.white.withOpacity(0.05),
                        ),
                      ),
                    ],
                  );
                }).toList(),
                 barTouchData: BarTouchData(
                   touchTooltipData: BarTouchTooltipData(
                     tooltipPadding: const EdgeInsets.all(8),
                     tooltipBorder: BorderSide(color: Colors.white.withOpacity(0.1)),
                     getTooltipItem: (group, groupIndex, rod, rodIndex) {
                       return BarTooltipItem(
                         '${rod.toY.toStringAsFixed(1)} h',
                         const TextStyle(
                           color: Colors.indigoAccent,
                           fontWeight: FontWeight.bold,
                           fontSize: 14,
                         ),
                       );
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
}

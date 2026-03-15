import 'package:flutter/material.dart';
import '../../data/models/metric_model.dart';
import '../../core/services/api_service.dart';
import '../dashboard/widgets/readiness_chart.dart';
import '../dashboard/widgets/sleep_chart.dart';
import '../dashboard/widgets/load_chart.dart';
import '../dashboard/widgets/performance_chart.dart';

class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({super.key});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  String? _error;
  List<Metric> _history = [];
  Map<String, dynamic>? _weeklyStats;
  Map<String, dynamic>? _mlMetrics;
  Map<String, dynamic>? _refreshStatus;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final metrics = await _apiService.fetchMetricsHistory();
      final weeklyStats = await _apiService.fetchWeeklyStats();
      final mlMetrics = await _apiService.fetchAiModelMetrics();
      final refreshStatus = await _apiService.fetchRefreshStatus();
      
      if (mounted) {
        setState(() {
          _history = metrics;
          _weeklyStats = weeklyStats;
          _mlMetrics = mlMetrics;
          _refreshStatus = refreshStatus;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Error: $_error', style: const TextStyle(color: Colors.red)),
            ElevatedButton(onPressed: _fetchData, child: const Text('Retry')),
          ],
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF020617), // Slate 950
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Analysis',
               style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
             const Text(
              'Deep dive into your recovery and training trends.',
               style: TextStyle(
                fontSize: 14,
                color: Colors.white54,
              ),
            ),
            const SizedBox(height: 24),
            
            // Weekly Stats Summary
            if (_weeklyStats != null) ...[
               Container(
                 padding: const EdgeInsets.all(16),
                 decoration: BoxDecoration(
                   color: const Color(0xFF0F172A),
                   borderRadius: BorderRadius.circular(16),
                   border: Border.all(color: Colors.white10),
                 ),
                 child: Row(
                   mainAxisAlignment: MainAxisAlignment.spaceAround,
                   children: [
                     _buildStatItem("Load", "${_weeklyStats!['current_load']?.toInt() ?? 0}", Colors.orangeAccent),
                     _buildStatItem("Duration", "${((_weeklyStats!['duration_minutes'] ?? 0) / 60).toStringAsFixed(1)}h", Colors.blueAccent),
                     _buildStatItem("Planned", "${_weeklyStats!['planned_load']?.toInt() ?? 0}", Colors.greenAccent),
                   ],
                 ),
               ),
               const SizedBox(height: 24),
            ],

            const Text(
              'Readiness & Recovery',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            ReadinessChart(metrics: _history),
            const SizedBox(height: 24),

            const Text(
              'Sleep Quality',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            SleepChart(metrics: _history),
            const SizedBox(height: 24),

            const Text(
              'Performance (CTL/ATL/TSB)',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            PerformanceChart(metrics: _history),
            const SizedBox(height: 24),

            // ML Metrics Summary
            if (_mlMetrics != null) ...[
              const Text(
                'ML Model Health',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                 padding: const EdgeInsets.all(16),
                 decoration: BoxDecoration(
                   color: const Color(0xFF0F172A),
                   borderRadius: BorderRadius.circular(16),
                   border: Border.all(color: Colors.indigoAccent.withOpacity(0.5)),
                 ),
                 child: Column(
                   crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (_refreshStatus != null && _refreshStatus!['status'] == 'in_progress') ...[
                        Row(
                          children: [
                            const SizedBox(
                              width: 12,
                              height: 12,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.indigoAccent),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Päivitetään: ${_refreshStatus!['message'] ?? 'Koulutetaan mallia...'}',
                              style: const TextStyle(color: Colors.indigoAccent, fontSize: 12, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                      ],
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                       children: [
                         const Text('Accuracy (R² Score)', style: TextStyle(color: Colors.white70)),
                         Container(
                           padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                           decoration: BoxDecoration(
                             color: ((_mlMetrics!['r2'] ?? 0) >= 0.8) ? Colors.greenAccent.withOpacity(0.2) : Colors.yellowAccent.withOpacity(0.2),
                             borderRadius: BorderRadius.circular(8),
                             border: Border.all(color: ((_mlMetrics!['r2'] ?? 0) >= 0.8) ? Colors.greenAccent : Colors.yellowAccent),
                           ),
                             child: Text(
                               (_refreshStatus != null && _refreshStatus!['status'] == 'in_progress')
                                   ? 'Training...'
                                   : '${((_mlMetrics!['r2'] ?? 0).clamp(0, 1.0) * 100).toStringAsFixed(0)}%',
                               style: TextStyle(
                                 fontWeight: FontWeight.bold,
                                 color: ((_mlMetrics!['r2'] ?? 0) >= 0.8) ? Colors.greenAccent : Colors.yellowAccent,
                               ),
                             ),
                         ),
                       ],
                     ),
                     const SizedBox(height: 12),
                     ClipRRect(
                       borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: ((_mlMetrics!['r2'] ?? 0) as num).toDouble().clamp(0.0, 1.0),
                          backgroundColor: Colors.white10,
                          color: ((_mlMetrics!['r2'] ?? 0) >= 0.8) ? Colors.greenAccent : Colors.yellowAccent,
                          minHeight: 8,
                        ),
                     ),
                     const SizedBox(height: 16),
                     Row(
                       mainAxisAlignment: MainAxisAlignment.spaceBetween,
                       children: [
                         Column(
                           crossAxisAlignment: CrossAxisAlignment.start,
                           children: [
                             const Text('MAE Error', style: TextStyle(color: Colors.white54, fontSize: 12)),
                             Text('${((_mlMetrics!['mae'] ?? 0.0) as num).toStringAsFixed(2)} pts', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                           ],
                         ),
                         Column(
                           crossAxisAlignment: CrossAxisAlignment.end,
                           children: [
                             const Text('Last Trained', style: TextStyle(color: Colors.white54, fontSize: 12)),
                             Text('${_mlMetrics!['last_trained'] ?? 'Unknown'}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                           ],
                         ),
                       ],
                     ),
                   ],
                 ),
               ),
               const SizedBox(height: 24),
            ],

            const Text(
              'Training Load',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            LoadChart(metrics: _history),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)),
      ],
    );
  }
}

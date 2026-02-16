import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../../data/models/metric_model.dart';
import '../../data/models/goal_model.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'widgets/readiness_chart.dart';
import 'widgets/sleep_chart.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  String? _error;
  
  // Data
  Metric? _latestMetric;
  List<Metric> _history = [];
  List<Goal> _goals = [];
  Map<String, dynamic>? _nextWorkout;
  Map<String, dynamic>? _aiInsight;
  Map<String, dynamic>? _weeklyStats;

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
      final goals = await _apiService.fetchGoals();
      final nextWorkout = await _apiService.fetchNextWorkout();
      final aiInsight = await _apiService.fetchAIInsight();
      final weeklyStats = await _apiService.fetchWeeklyStats();

      if (mounted) {
        setState(() {
          // Get the most recent metric
          if (metrics.isNotEmpty) {
             _latestMetric = metrics.last; 
             _history = metrics;
          }
          _goals = goals;
          _nextWorkout = nextWorkout;
          _aiInsight = aiInsight;
          _weeklyStats = weeklyStats;
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

  // ... (build method remains mostly same until _buildWorkoutCard call)

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $_error', style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchData,
                child: const Text('Retry'),
              )
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF020617), // Slate 950
      appBar: AppBar(
        title: const Text('Dashboard'),
        backgroundColor: const Color(0xFF020617),
        elevation: 0,
        automaticallyImplyLeading: false, 
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.blueAccent),
            onPressed: _fetchData,
          ),
          IconButton(
            icon: const Icon(Icons.person, color: Colors.white70),
            onPressed: () {
              // Navigate to Settings
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Greeting Header
            Text(
              'Hello, ${FirebaseAuth.instance.currentUser?.displayName ?? "User"}',
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const Text(
              'Welcome back',
              style: TextStyle(
                fontSize: 14,
                color: Colors.white54,
              ),
            ),
            const SizedBox(height: 24),

            // AI Insight Card
            if (_aiInsight != null) ...[
              _buildAIInsightCard(),
              const SizedBox(height: 24),
            ],

            // Stats Grid (2x2)
            GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              childAspectRatio: 1.3,
              children: [
                _buildStatCard(
                  title: 'Readiness',
                  value: '${_latestMetric?.readiness ?? '--'}%',
                  subtitle: 'Body Battery',
                  icon: Icons.battery_charging_full,
                  color: Colors.greenAccent,
                ),
                _buildStatCard(
                  title: 'Weekly Load',
                  value: '${_weeklyStats?['current_load']?.round() ?? '--'}',
                  subtitle: 'Planned: ${_weeklyStats?['planned_load']?.round() ?? '--'}',
                  icon: Icons.local_fire_department,
                  color: Colors.blueAccent,
                ),
                _buildStatCard(
                  title: 'Next Workout',
                  value: _nextWorkout?['content']?['activity'] ?? 'Rest',
                  subtitle: _nextWorkout?['date'] ?? 'No plan',
                  icon: Icons.calendar_today,
                  color: Colors.purpleAccent,
                ),
                _buildStatCard(
                  title: 'Active Goals',
                  value: '${_goals.length}',
                  subtitle: 'Targets',
                  icon: Icons.flag,
                  color: Colors.orangeAccent,
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Performance Analytics Section (Charts)
            const Text(
              'Performance Analytics',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            if (_history.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A).withOpacity(0.5), // Slate 900/50
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white.withOpacity(0.1)),
                ),
                child: Column(
                  children: [
                    const Align(alignment: Alignment.centerLeft, child: Text("Readiness Trend", style: TextStyle(color: Colors.white70, fontSize: 14))),
                    const SizedBox(height: 16),
                    ReadinessChart(metrics: _history),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                 padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A).withOpacity(0.5),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white.withOpacity(0.1)),
                ),
                child: Column(
                  children: [
                    const Align(alignment: Alignment.centerLeft, child: Text("Sleep Duration", style: TextStyle(color: Colors.white70, fontSize: 14))),
                    const SizedBox(height: 16),
                    SleepChart(metrics: _history),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],

            // Goals Section
            const Text(
              'Your Active Goals',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            if (_goals.isEmpty)
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                    color: const Color(0xFF0F172A).withOpacity(0.3),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white10, style: BorderStyle.solid)
                ),
                child: const Center(child: Text('No active goals', style: TextStyle(color: Colors.white54))),
              )
            else
              ..._goals.map((goal) => _buildGoalCard(goal)),

            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        selectedItemColor: Colors.blueAccent,
        unselectedItemColor: Colors.white54,
        backgroundColor: const Color(0xFF0F172A), // Slate 900
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard_rounded),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_month_rounded),
            label: 'Calendar',
          ),
           BottomNavigationBarItem(
            icon: Icon(Icons.insights_rounded),
            label: 'Analysis',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }

  // ... (Keep _buildMetricCard and _buildGoalCard as is, assume they are there or see context)

  Widget _buildStatCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A).withOpacity(0.5), // Slate 900
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 8),
              Text(
                title.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white54,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          Column(
             crossAxisAlignment: CrossAxisAlignment.start,
             children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Colors.white38,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
             ],
          )
        ],
      ),
    );
  }

  Widget _buildAIInsightCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.indigo.shade900, Colors.purple.shade900],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.indigo.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ]
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
           Container(
             padding: const EdgeInsets.all(8),
             decoration: BoxDecoration(
               color: Colors.white.withOpacity(0.1),
               borderRadius: BorderRadius.circular(12),
             ),
             child: const Icon(Icons.auto_awesome, color: Colors.amberAccent, size: 24),
           ),
           const SizedBox(width: 16),
           Expanded(
             child: Column(
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 const Text(
                   "AI COACH INSIGHT",
                   style: TextStyle(
                     color: Colors.indigoAccent,
                     fontSize: 10,
                     fontWeight: FontWeight.bold,
                     letterSpacing: 1.2,
                   ),
                 ),
                 const SizedBox(height: 4),
                 Text(
                   _aiInsight?['insight'] ?? "Analyzing your data...",
                   style: const TextStyle(
                     color: Colors.white,
                     fontSize: 14,
                     height: 1.4,
                     fontStyle: FontStyle.italic,
                   ),
                 )
               ],
             ),
           )
        ],
      ),
    );
  }

  Widget _buildGoalCard(Goal goal) {
     return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A).withOpacity(0.5), // Slate 900
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                   Icon(goal.targetUnit == 'km' ? Icons.directions_run : Icons.flag, size: 16, color: Colors.blueAccent),
                   const SizedBox(width: 8),
                   Text(
                    '${goal.activityType}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
              Text(
                '${goal.progressPercentage}%',
                style: const TextStyle(
                  color: Colors.blueAccent,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: goal.progressPercentage / 100,
            backgroundColor: Colors.white10,
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.blueAccent),
            borderRadius: BorderRadius.circular(4),
            minHeight: 6,
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
               Text(
                '${goal.currentValue} / ${goal.targetValue} ${goal.targetUnit}',
                style: const TextStyle(color: Colors.white54, fontSize: 12),
              ),
              Text(
                 '${goal.daysLeft} days left',
                 style: const TextStyle(color: Colors.white54, fontSize: 12),
              )
            ],
          )
        ],
      ),
    );
  }



}

import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../../data/models/metric_model.dart';
import '../../data/models/goal_model.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'widgets/readiness_chart.dart';
import 'widgets/sleep_chart.dart';
import '../calendar/calendar_screen.dart';
import '../analysis/analysis_screen.dart';
import '../chat/chat_screen.dart';
import '../profile/profile_screen.dart';
import '../goals/goal_form_sheet.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  String? _error;
  bool _garminConnected = true; // Optimistic default to avoid flash
  
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
    _fetchGarminStatus();
  }

  Future<void> _fetchGarminStatus() async {
    try {
      final status = await _apiService.getGarminStatus();
      if (mounted) setState(() => _garminConnected = status?['connected'] == true);
    } catch (_) {}
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

  int _selectedIndex = 0;
  
  // No longer static list, handled in build method via switch or if/else
  // int _selectedIndex = 0; // Already defined above

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

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
               setState(() {
                 _selectedIndex = 4; // Switch to Profile tab
               });
            },
          ),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        selectedItemColor: Colors.indigoAccent,
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
            icon: Icon(Icons.chat_bubble_rounded),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    switch (_selectedIndex) {
      case 0:
        return _buildDashboardContent();
      case 1:
        return const CalendarScreen();
      case 2:
        return const AnalysisScreen();
      case 3:
        return const ChatScreen();
      case 4:
        return const ProfileScreen();
      default:
        return _buildDashboardContent();
    }
  }

  Widget _buildDashboardContent() {
    return SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Greeting Header
            Text(
              'Hello, ${_getDisplayName()}',
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

            // Garmin connection banner
            if (!_garminConnected)
              GestureDetector(
                onTap: () => setState(() => _selectedIndex = 3),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.orangeAccent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orangeAccent.withOpacity(0.4)),
                  ),
                  child: Row(children: [
                    const Icon(Icons.watch_outlined, color: Colors.orangeAccent, size: 20),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Connect your Garmin to sync workouts',
                        style: TextStyle(color: Colors.orangeAccent, fontSize: 13),
                      ),
                    ),
                    const Icon(Icons.arrow_forward_ios, color: Colors.orangeAccent, size: 14),
                  ]),
                ),
              ),

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
              ReadinessChart(metrics: _history),
              const SizedBox(height: 16),
              SleepChart(metrics: _history),
              const SizedBox(height: 24),
            ],

            // Goals Section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Your Active Goals',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                TextButton.icon(
                  onPressed: () => _openGoalForm(),
                  icon: const Icon(Icons.add, color: Colors.blueAccent, size: 18),
                  label: const Text('Add', style: TextStyle(color: Colors.blueAccent)),
                ),
              ],
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
                child: Column(
                  children: [
                    const Icon(Icons.flag_outlined, color: Colors.white24, size: 36),
                    const SizedBox(height: 8),
                    const Text('No active goals', style: TextStyle(color: Colors.white54)),
                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () => _openGoalForm(),
                      child: const Text('+ Create your first goal', style: TextStyle(color: Colors.blueAccent)),
                    )
                  ],
                ),
              )
            else
              ..._goals.map((goal) => _buildGoalCard(goal)),

            const SizedBox(height: 24),
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

  void _openGoalForm({Goal? existingGoal}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => GoalFormSheet(
        existingGoal: existingGoal,
        onSuccess: _fetchData,
      ),
    );
  }

  Future<void> _deleteGoal(Goal goal) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text('Delete Goal', style: TextStyle(color: Colors.white)),
        content: Text(
          'Delete "${goal.activityType}" goal? This cannot be undone.',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Delete', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      try {
        await _apiService.deleteGoal(goal.id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Goal deleted'), backgroundColor: Colors.green),
          );
          _fetchData();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Widget _buildGoalCard(Goal goal) {
    final isRace = goal.periodType == 'race';
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A).withOpacity(0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isRace ? Colors.purple.withOpacity(0.3) : Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    isRace ? Icons.flag : (goal.targetUnit == 'km' ? Icons.directions_run : Icons.fitness_center),
                    size: 16,
                    color: isRace ? Colors.purpleAccent : Colors.blueAccent,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    goal.activityType,
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  if (isRace) ...[const SizedBox(width: 6), Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(color: Colors.purple.withOpacity(0.2), borderRadius: BorderRadius.circular(4)),
                    child: const Text('RACE', style: TextStyle(color: Colors.purpleAccent, fontSize: 9, fontWeight: FontWeight.bold)),
                  )],
                ],
              ),
              // Edit / Delete icons
              Row(
                children: [
                  if (!isRace)
                    Text('${goal.progressPercentage}%',
                        style: const TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: () => _openGoalForm(existingGoal: goal),
                    child: const Icon(Icons.edit_outlined, size: 18, color: Colors.white38),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: () => _deleteGoal(goal),
                    child: const Icon(Icons.delete_outline, size: 18, color: Colors.redAccent),
                  ),
                ],
              ),
            ],
          ),
          if (isRace && goal.daysRemaining != null) ...[
            const SizedBox(height: 8),
            Center(
              child: RichText(
                text: TextSpan(children: [
                  TextSpan(
                    text: '${(goal.daysRemaining! / 7).floor()}',
                    style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                  const TextSpan(text: ' w  ', style: TextStyle(color: Colors.white54, fontSize: 14)),
                  TextSpan(
                    text: '${goal.daysRemaining! % 7}',
                    style: const TextStyle(color: Colors.white70, fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const TextSpan(text: ' d to start line', style: TextStyle(color: Colors.white38, fontSize: 12)),
                ]),
              ),
            ),
          ] else ...[
            const SizedBox(height: 12),
            LinearProgressIndicator(
              value: goal.progressPercentage / 100,
              backgroundColor: Colors.white10,
              valueColor: AlwaysStoppedAnimation<Color>(
                goal.progressPercentage >= 100 ? Colors.greenAccent : Colors.blueAccent,
              ),
              borderRadius: BorderRadius.circular(4),
              minHeight: 6,
            ),
          ],
          const SizedBox(height: 8),
          if (isRace)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Race distance: ${goal.targetValue} ${goal.targetUnit}',
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
                Text(
                  goal.targetDate ?? '',
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            )
          else
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
                ),
              ],
            ),
        ],
      ),
    );
  }

  String _getDisplayName() {
    final user = FirebaseAuth.instance.currentUser;
    String name = "User";

    if (user?.displayName != null && user!.displayName!.isNotEmpty) {
      name = user.displayName!;
    } else if (user?.email != null && user!.email!.isNotEmpty) {
      name = user.email!.split('@')[0];
    }

    if (name.isNotEmpty) {
      return name[0].toUpperCase() + name.substring(1);
    }
    return name;
  }
}

// DashboardContent class removed as it was a temporary stub.
// The logic is now in _buildDashboardContent method within _DashboardScreenState.
// To keep _widgetOptions happy, we need a widget that wraps _buildDashboardContent.
// However, _buildDashboardContent is an instance method, so we can't use it in a static list easily.
// Let's refactor: _widgetOptions should be a getter or build method switch.


import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:intl/intl.dart';
import '../../core/services/api_service.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  final ApiService _apiService = ApiService();

  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;
  List<Map<String, dynamic>> _workouts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _selectedDay = _focusedDay;
    _fetchWorkouts();
  }

  Future<void> _fetchWorkouts() async {
    setState(() => _loading = true);
    try {
      // Fetch scheduled workouts from backend
      final history = await _apiService.fetchWorkoutHistory();
      final next = await _apiService.fetchNextWorkout();

      final List<Map<String, dynamic>> all = [];

      // Add workout history
      for (final w in history) {
        if (w['date'] != null) {
          all.add({
            'date': DateTime.tryParse(w['date'].toString()) ?? DateTime.now(),
            'name': w['workout_type'] ?? w['type'] ?? 'Workout',
            'duration': w['duration_minutes'] ?? w['planned_duration'] ?? 0,
            'type': w['workout_type'] ?? w['type'] ?? 'Training',
            'raw': w,
            'source': 'history',
          });
        }
      }

      // Add next workout if present
      if (next != null && next['date'] != null) {
        all.add({
          'date': DateTime.tryParse(next['date'].toString()) ?? DateTime.now(),
          'name': next['workout_type'] ?? next['type'] ?? 'Next Workout',
          'duration': next['duration_minutes'] ?? next['planned_duration'] ?? 0,
          'type': next['workout_type'] ?? next['type'] ?? 'Training',
          'raw': next,
          'source': 'next',
        });
      }

      if (mounted) setState(() => _workouts = all);
    } catch (e) {
      debugPrint('Calendar fetch error: $e');
    }
    if (mounted) setState(() => _loading = false);
  }

  List<Map<String, dynamic>> _getEventsForDay(DateTime day) {
    return _workouts.where((w) => isSameDay(w['date'] as DateTime, day)).toList();
  }

  Future<void> _sendToGarmin(Map<String, dynamic> workout) async {
    final date = workout['date'] as DateTime;
    final dateStr = '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';

    try {
      await _apiService.uploadWorkoutToGarmin(workout['raw'] as Map<String, dynamic>, dateStr);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Workout sent & scheduled on Garmin Calendar!'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ Garmin upload failed: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedWorkouts = _selectedDay != null ? _getEventsForDay(_selectedDay!) : <Map<String, dynamic>>[];

    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: const Color(0xFF020617),
        title: const Text('Training Calendar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white54),
            onPressed: _fetchWorkouts,
          ),
        ],
      ),
      body: Column(
        children: [
          // Calendar
          TableCalendar(
            firstDay: DateTime.now().subtract(const Duration(days: 90)),
            lastDay: DateTime.now().add(const Duration(days: 180)),
            focusedDay: _focusedDay,
            selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
            onDaySelected: (selected, focused) {
              setState(() {
                _selectedDay = selected;
                _focusedDay = focused;
              });
            },
            eventLoader: _getEventsForDay,
            calendarFormat: CalendarFormat.month,
            calendarStyle: CalendarStyle(
              outsideDaysVisible: false,
              defaultTextStyle: const TextStyle(color: Colors.white70),
              weekendTextStyle: const TextStyle(color: Colors.white54),
              selectedDecoration: const BoxDecoration(
                color: Colors.blueAccent,
                shape: BoxShape.circle,
              ),
              todayDecoration: BoxDecoration(
                color: Colors.blueAccent.withOpacity(0.3),
                shape: BoxShape.circle,
              ),
              markerDecoration: const BoxDecoration(
                color: Colors.greenAccent,
                shape: BoxShape.circle,
              ),
            ),
            headerStyle: const HeaderStyle(
              formatButtonVisible: false,
              titleCentered: true,
              titleTextStyle: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              leftChevronIcon: Icon(Icons.chevron_left, color: Colors.white54),
              rightChevronIcon: Icon(Icons.chevron_right, color: Colors.white54),
            ),
            daysOfWeekStyle: const DaysOfWeekStyle(
              weekdayStyle: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold),
              weekendStyle: TextStyle(color: Colors.white24, fontWeight: FontWeight.bold),
            ),
          ),

          const SizedBox(height: 8),
          const Divider(color: Colors.white10),

          // Workout list for selected day
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Colors.blueAccent))
                : selectedWorkouts.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.event_available, color: Colors.white24, size: 48),
                            const SizedBox(height: 12),
                            Text(
                              _selectedDay != null
                                  ? 'No workouts on ${DateFormat('MMM d').format(_selectedDay!)}'
                                  : 'Select a day',
                              style: const TextStyle(color: Colors.white38, fontSize: 14),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: selectedWorkouts.length,
                        itemBuilder: (context, index) {
                          final w = selectedWorkouts[index];
                          final isNext = w['source'] == 'next';
                          return Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0F172A),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: isNext ? Colors.blueAccent.withOpacity(0.4) : Colors.white10,
                              ),
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
                                          _workoutIcon(w['type'] as String),
                                          color: isNext ? Colors.blueAccent : Colors.white54,
                                          size: 20,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          w['name'] as String,
                                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                                        ),
                                        if (isNext) ...[
                                          const SizedBox(width: 8),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: Colors.blueAccent.withOpacity(0.2),
                                              borderRadius: BorderRadius.circular(4),
                                            ),
                                            child: const Text('NEXT', style: TextStyle(color: Colors.blueAccent, fontSize: 9, fontWeight: FontWeight.bold)),
                                          ),
                                        ],
                                      ],
                                    ),
                                    if (w['duration'] != null && (w['duration'] as num) > 0)
                                      Text(
                                        '${w['duration']} min',
                                        style: const TextStyle(color: Colors.white54, fontSize: 12),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                // Send to Garmin button
                                SizedBox(
                                  width: double.infinity,
                                  child: OutlinedButton.icon(
                                    onPressed: () => _sendToGarmin(w),
                                    icon: const Icon(Icons.watch, size: 16, color: Colors.tealAccent),
                                    label: const Text(
                                      'Send to Garmin',
                                      style: TextStyle(color: Colors.tealAccent, fontSize: 13),
                                    ),
                                    style: OutlinedButton.styleFrom(
                                      side: BorderSide(color: Colors.tealAccent.withOpacity(0.4)),
                                      padding: const EdgeInsets.symmetric(vertical: 10),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  IconData _workoutIcon(String type) {
    switch (type.toLowerCase()) {
      case 'running':
      case 'run':
        return Icons.directions_run;
      case 'cycling':
      case 'bike':
        return Icons.directions_bike;
      case 'swimming':
      case 'swim':
        return Icons.pool;
      case 'gym':
      case 'strength':
        return Icons.fitness_center;
      default:
        return Icons.sports;
    }
  }
}

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

  void _showWorkoutDetails(Map<String, dynamic> workout) {
    if (workout['source'] != 'next' && workout['source'] != 'history') return;
    final isPending = workout['raw']['status'] == 'PENDING';
    final workoutId = workout['raw']['id'] ?? workout['raw']['_id']; // Depending on how backend returns it
    
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F172A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                workout['name'] as String,
                style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (workout['raw']['description'] != null)
                Text(
                  workout['raw']['description'].toString(),
                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                ),
              const SizedBox(height: 20),
              
              if (workoutId != null) ...[
                // Siirto = Päivämäärän vaihto
                ListTile(
                  leading: const Icon(Icons.calendar_month, color: Colors.blueAccent),
                  title: const Text('Reschedule Workout', style: TextStyle(color: Colors.white)),
                  onTap: () async {
                    Navigator.pop(context); // Sulje bottom sheet
                    final newDate = await showDatePicker(
                      context: context,
                      initialDate: workout['date'] as DateTime,
                      firstDate: DateTime.now().subtract(const Duration(days: 7)),
                      lastDate: DateTime.now().add(const Duration(days: 90)),
                      builder: (context, child) {
                        return Theme(
                          data: ThemeData.dark().copyWith(
                            colorScheme: const ColorScheme.dark(
                              primary: Colors.blueAccent,
                              onPrimary: Colors.white,
                              surface: Color(0xFF0F172A),
                            ),
                          ),
                          child: child!,
                        );
                      },
                    );
                    
                    if (newDate != null) {
                      final dateStr = '${newDate.year}-${newDate.month.toString().padLeft(2, '0')}-${newDate.day.toString().padLeft(2, '0')}';
                      try {
                        await _apiService.updateWorkoutDate(workoutId.toString(), dateStr);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Workout rescheduled'), backgroundColor: Colors.green));
                          _fetchWorkouts();
                        }
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Colors.red));
                        }
                      }
                    }
                  },
                ),
                // Poisto
                ListTile(
                  leading: const Icon(Icons.delete_outline, color: Colors.redAccent),
                  title: const Text('Delete Workout', style: TextStyle(color: Colors.redAccent)),
                  onTap: () async {
                    Navigator.pop(context);
                    final confirm = await showDialog<bool>(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        backgroundColor: const Color(0xFF0F172A),
                        title: const Text('Delete Workout', style: TextStyle(color: Colors.white)),
                        content: const Text('Are you sure you want to delete this workout?', style: TextStyle(color: Colors.white70)),
                        actions: [
                          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
                          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete', style: TextStyle(color: Colors.redAccent))),
                        ],
                      ),
                    );
                    
                    if (confirm == true) {
                      try {
                        await _apiService.deleteWorkout(workoutId.toString());
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Workout deleted'), backgroundColor: Colors.green));
                          _fetchWorkouts();
                        }
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Colors.red));
                        }
                      }
                    }
                  },
                ),
              ],
              const SizedBox(height: 20),
            ],
          ),
        );
      },
    );
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
            icon: const Icon(Icons.auto_awesome, color: Colors.blueAccent),
            tooltip: 'Generate AI Plan',
            onPressed: () async {
              final days = await showDialog<int>(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: const Color(0xFF0F172A),
                  title: const Row(
                    children: [
                      Icon(Icons.auto_awesome, color: Colors.blueAccent),
                      SizedBox(width: 8),
                      Text('Generate AI Plan', style: TextStyle(color: Colors.white)),
                    ],
                  ),
                  content: const Text('How many days of training should the AI generate? (1-7)', style: TextStyle(color: Colors.white70)),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, 3), child: const Text('3 Days', style: TextStyle(color: Colors.blueAccent))),
                    TextButton(onPressed: () => Navigator.pop(ctx, 5), child: const Text('5 Days', style: TextStyle(color: Colors.blueAccent))),
                    TextButton(onPressed: () => Navigator.pop(ctx, 7), child: const Text('7 Days', style: TextStyle(color: Colors.blueAccent))),
                  ],
                ),
              );
              
              if (days != null) {
                setState(() => _loading = true);
                try {
                  await _apiService.generateAiPlan(days);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('AI Plan Generated!'), backgroundColor: Colors.green));
                    _fetchWorkouts(); // Load new generated workouts
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Colors.red));
                  }
                } finally {
                  if (mounted) setState(() => _loading = false);
                }
              }
            },
          ),
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
                          return GestureDetector(
                            onTap: () => _showWorkoutDetails(w),
                            child: Container(
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
                                          if (w['raw']?['execution_score'] != null) ...[
                                            const SizedBox(width: 8),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: ((w['raw']['execution_score'] as num) >= 80)
                                                    ? Colors.greenAccent.withOpacity(0.2)
                                                    : ((w['raw']['execution_score'] as num) >= 50)
                                                        ? Colors.orangeAccent.withOpacity(0.2)
                                                        : Colors.redAccent.withOpacity(0.2),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Row(
                                                children: [
                                                  Icon(
                                                    ((w['raw']['execution_score'] as num) >= 80) ? Icons.check_circle : Icons.error_outline,
                                                    size: 10,
                                                    color: ((w['raw']['execution_score'] as num) >= 80)
                                                        ? Colors.greenAccent
                                                        : ((w['raw']['execution_score'] as num) >= 50)
                                                            ? Colors.orangeAccent
                                                            : Colors.redAccent,
                                                  ),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    'Score: ${w['raw']['execution_score']}%',
                                                    style: TextStyle(
                                                      color: ((w['raw']['execution_score'] as num) >= 80)
                                                          ? Colors.greenAccent
                                                          : ((w['raw']['execution_score'] as num) >= 50)
                                                              ? Colors.orangeAccent
                                                              : Colors.redAccent,
                                                      fontSize: 9,
                                                      fontWeight: FontWeight.bold,
                                                    ),
                                                  ),
                                                ],
                                              ),
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

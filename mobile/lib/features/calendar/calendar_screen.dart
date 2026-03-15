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

  CalendarFormat _calendarFormat = CalendarFormat.month;
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
    if (!mounted) return;
    setState(() => _loading = true);
    try {
      // Fetch scheduled workouts from backend
      final history = await _apiService.fetchWorkoutHistory();
      final upcoming = await _apiService.fetchUpcomingWorkouts();
      final next = await _apiService.fetchNextWorkout();

      final List<Map<String, dynamic>> all = [];
      final Map<String, Map<String, dynamic>> dedupMap = {};

      // Helper to add/update workout with prioritization
      void addOrUpdate(Map<String, dynamic> workout) {
        final id = workout['raw']['id']?.toString() ?? workout['raw']['activity_id']?.toString() ??'${workout['date']}_${workout['name']}';
        final existing = dedupMap[id];
        
        // Prioritize 'DONE' status over 'PENDING' for same ID
        if (existing == null || workout['raw']['status'] == 'DONE') {
           dedupMap[id] = workout;
        }
      }

      // Add workout history
      for (final w in history) {
        if (w['date'] != null) {
          addOrUpdate({
            'date': _normalizeDate(DateTime.tryParse(w['date'].toString()) ?? DateTime.now()),
            'name': w['workout_type'] ?? w['type'] ?? w['activity'] ?? 'Workout',
            'duration': w['duration_minutes'] ?? w['duration_min'] ?? w['planned_duration'] ?? 0,
            'type': w['workout_type'] ?? w['type'] ?? w['activity'] ?? 'Training',
            'raw': w,
            'source': 'history',
          });
        }
      }

      // Add upcoming workouts
      for (final w in upcoming) {
        if (w['date'] != null) {
          addOrUpdate({
            'date': _normalizeDate(DateTime.tryParse(w['date'].toString()) ?? DateTime.now()),
            'name': w['activity'] ?? w['workout_type'] ?? w['type'] ?? 'Planned Workout',
            'duration': w['duration_min'] ?? w['duration_minutes'] ?? w['planned_duration'] ?? 0,
            'type': w['activity'] ?? w['workout_type'] ?? w['type'] ?? 'Training',
            'raw': w,
            'source': 'upcoming',
          });
        }
      }

      // Add next workout if present (as a fallback or override)
      if (next != null && next['date'] != null) {
        final content = next['content'] ?? next;
        final normalizedDate = _normalizeDate(DateTime.tryParse(next['date'].toString()) ?? DateTime.now());
        
        addOrUpdate({
          'date': normalizedDate,
          'name': content['activity'] ?? content['workout_type'] ?? content['type'] ?? 'Next Workout',
          'duration': content['duration_min'] ?? content['duration_minutes'] ?? content['planned_duration'] ?? 0,
          'type': content['activity'] ?? content['workout_type'] ?? content['type'] ?? 'Training',
          'raw': next,
          'source': 'next',
        });
      }

      if (mounted) {
        final sortedList = dedupMap.values.toList();
        sortedList.sort((a, b) => (a['date'] as DateTime).compareTo(b['date'] as DateTime));
        setState(() => _workouts = sortedList);
      }
    } catch (e) {
      debugPrint('Calendar fetch error: $e');
    }
    if (mounted) setState(() => _loading = false);
  }

  DateTime _normalizeDate(DateTime date) {
    return DateTime(date.year, date.month, date.day);
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
    if (workout['source'] != 'next' && workout['source'] != 'history' && workout['source'] != 'upcoming') return;
    final workoutId = workout['raw']['id'] ?? workout['raw']['_id']; 
    
    // Unpack content if it's nested (next workout style) or direct (upcoming style)
    final Map<String, dynamic> raw = workout['raw'];
    final Map<String, dynamic> content = raw['content'] ?? raw;
    
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F172A),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(context).size.height * 0.85,
          ),
          child: SingleChildScrollView(
            child: Padding(
              padding: EdgeInsets.only(
                top: 20, 
                left: 20, 
                right: 20, 
                bottom: MediaQuery.of(context).viewInsets.bottom + 20
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                workout['name'] as String,
                style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (content['description'] != null && content['description'].toString().isNotEmpty)
                Text(
                  content['description'].toString(),
                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                ),
              
              if (content['structure'] != null && content['structure'].toString().isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text('STRUCTURE:', style: TextStyle(color: Colors.indigoAccent, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
                const SizedBox(height: 4),
                Text(content['structure'].toString(), style: const TextStyle(color: Colors.white, fontSize: 14)),
              ],

              if (content['details'] != null && content['details'] is List && (content['details'] as List).isNotEmpty) ...[
                const SizedBox(height: 20),
                const Text('VAIHEET:', style: TextStyle(color: Colors.blueAccent, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
                const SizedBox(height: 8),
                ...(content['details'] as List).map((step) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(color: Colors.blueAccent, fontSize: 16)),
                      Expanded(child: Text(step.toString(), style: const TextStyle(color: Colors.white, fontSize: 14))),
                    ],
                  ),
                )),
              ],
              
              if (content['tips'] != null && content['tips'].toString().isNotEmpty) ...[
                const SizedBox(height: 20),
                const Text('VINKKI:', style: TextStyle(color: Colors.amberAccent, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.amberAccent.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.amberAccent.withOpacity(0.2)),
                  ),
                  child: Text(
                    content['tips'].toString(),
                    style: const TextStyle(color: Colors.white70, fontSize: 14, fontStyle: FontStyle.italic),
                  ),
                ),
              ],
              const SizedBox(height: 32),
              
              if (workoutId != null) ...[
                ListTile(
                  leading: const Icon(Icons.calendar_month, color: Colors.blueAccent),
                  title: const Text('Reschedule Workout', style: TextStyle(color: Colors.white)),
                  onTap: () async {
                    Navigator.pop(context); 
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
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _openAiPlanDialog() async {
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
          _fetchWorkouts(); 
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Colors.red));
        }
      } finally {
        if (mounted) setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedWorkouts = _selectedDay != null ? _getEventsForDay(_selectedDay!) : <Map<String, dynamic>>[];

    return Container(
      color: const Color(0xFF020617),
      child: CustomScrollView(
        slivers: [
          // Actions Row (AI Plan & Refresh)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton.icon(
                    onPressed: _openAiPlanDialog,
                    icon: const Icon(Icons.auto_awesome, color: Colors.blueAccent, size: 18),
                    label: const Text('Generate AI Plan', style: TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh, color: Colors.white54),
                    onPressed: _fetchWorkouts,
                  ),
                ],
              ),
            ),
          ),

          // Calendar
          SliverToBoxAdapter(
            child: TableCalendar(
              firstDay: DateTime.now().subtract(const Duration(days: 90)),
              lastDay: DateTime.now().add(const Duration(days: 180)),
              focusedDay: _focusedDay,
              selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
              calendarFormat: _calendarFormat,
              onFormatChanged: (format) {
                setState(() {
                  _calendarFormat = format;
                });
              },
              onDaySelected: (selected, focused) {
                setState(() {
                  _selectedDay = selected;
                  _focusedDay = focused;
                });
              },
              eventLoader: _getEventsForDay,
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
                markerSize: 5,
                markersMaxCount: 4,
              ),
              headerStyle: const HeaderStyle(
                formatButtonVisible: true,
                formatButtonTextStyle: TextStyle(color: Colors.blueAccent, fontSize: 13),
                formatButtonDecoration: BoxDecoration(
                  border: Border.fromBorderSide(BorderSide(color: Colors.blueAccent)),
                  borderRadius: BorderRadius.all(Radius.circular(12.0)),
                ),
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
          ),

          // Selection Header
          if (_selectedDay != null)
            SliverToBoxAdapter(
              child: Column(
                children: [
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    child: Row(
                      children: [
                        const Icon(Icons.fitness_center, color: Colors.white54, size: 16),
                        const SizedBox(width: 8),
                        Text(
                          DateFormat('EEEE, MMM d').format(_selectedDay!),
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        const Spacer(),
                        Text(
                          '${selectedWorkouts.length} Workouts',
                          style: const TextStyle(color: Colors.white54, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  const Divider(color: Colors.white10),
                ],
              ),
            ),

          // Loading Indicator
          if (_loading)
            const SliverFillRemaining(
              hasScrollBody: false,
              child: Center(child: CircularProgressIndicator(color: Colors.blueAccent)),
            )
          // Empty State
          else if (selectedWorkouts.isEmpty)
            SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
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
              ),
            )
          // Workout list for selected day
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100), // Extra bottom padding for FAB
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final w = selectedWorkouts[index];
                    final isNext = w['source'] == 'next';
                    final description = w['raw']?['description']?.toString();
                    
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
                                Expanded(
                                  child: Row(
                                    children: [
                                      Icon(
                                        _workoutIcon(w['type'] as String),
                                        color: isNext ? Colors.blueAccent : Colors.white54,
                                        size: 20,
                                      ),
                                      const SizedBox(width: 8),
                                      Flexible(
                                        child: Text(
                                          w['name'] as String,
                                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                                          overflow: TextOverflow.ellipsis,
                                        ),
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
                                ),
                                if (w['duration'] != null && (w['duration'] as num) > 0)
                                  Text(
                                    '${w['duration']} min',
                                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                                  ),
                              ],
                            ),

                            if (description != null && description.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Text(
                                description,
                                style: const TextStyle(color: Colors.white70, fontSize: 13),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ] else if (w['raw']?['content']?['structure_summary'] != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                w['raw']['content']['structure_summary'].toString(),
                                style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],

                            if (w['raw']?['execution_score'] != null) ...[
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: ((w['raw']['execution_score'] as num) >= 80)
                                      ? Colors.greenAccent.withOpacity(0.1)
                                      : ((w['raw']['execution_score'] as num) >= 50)
                                          ? Colors.orangeAccent.withOpacity(0.1)
                                          : Colors.redAccent.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      ((w['raw']['execution_score'] as num) >= 80) ? Icons.check_circle : Icons.error_outline,
                                      size: 14,
                                      color: ((w['raw']['execution_score'] as num) >= 80)
                                          ? Colors.greenAccent
                                          : ((w['raw']['execution_score'] as num) >= 50)
                                              ? Colors.orangeAccent
                                              : Colors.redAccent,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'Execution: ${w['raw']['execution_score']}%',
                                      style: TextStyle(
                                        color: ((w['raw']['execution_score'] as num) >= 80)
                                            ? Colors.greenAccent
                                            : ((w['raw']['execution_score'] as num) >= 50)
                                                ? Colors.orangeAccent
                                                : Colors.redAccent,
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],

                            const SizedBox(height: 16),
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
                  childCount: selectedWorkouts.length,
                ),
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
      case 'juoksu':
        return Icons.directions_run;
      case 'cycling':
      case 'bike':
      case 'pyöräily':
        return Icons.directions_bike;
      case 'swimming':
      case 'swim':
      case 'uinti':
        return Icons.pool;
      case 'gym':
      case 'strength':
      case 'kuntosali':
      case 'voimaharjoittelu':
        return Icons.fitness_center;
      case 'walking':
      case 'kävely':
        return Icons.directions_walk;
      default:
        return Icons.sports;
    }
  }
}

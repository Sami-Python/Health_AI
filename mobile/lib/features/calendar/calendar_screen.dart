import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import 'package:intl/intl.dart';

import 'package:table_calendar/table_calendar.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  String? _error;
  List<dynamic> _workouts = [];
  
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  @override
  void initState() {
    super.initState();
    _selectedDay = _focusedDay;
    _fetchUpcomingWorkouts(); 
  }

  Future<void> _fetchUpcomingWorkouts() async {
     setState(() {
       _isLoading = false;
       // Mock data for visual verification until API is ready
       _workouts = [
         {'date': DateTime.now().add(const Duration(days: 1)), 'activity': 'Running', 'title': 'Base Run', 'duration': '45 min'},
         {'date': DateTime.now().add(const Duration(days: 2)), 'activity': 'Cycling', 'title': 'Recovery Ride', 'duration': '60 min'},
         {'date': DateTime.now().add(const Duration(days: 4)), 'activity': 'Gym', 'title': 'Strength', 'duration': '45 min'},
         {'date': DateTime.now(), 'activity': 'Gym', 'title': 'Strength', 'duration': '45 min'},
       ];
     });
  }

  List<dynamic> _getEventsForDay(DateTime day) {
    // Simple event loader based on date match
    return _workouts.where((workout) {
      final workoutDate = workout['date'] as DateTime;
      return isSameDay(workoutDate, day);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Training Schedule', style: TextStyle(color: Colors.white)),
        automaticallyImplyLeading: false,
      ),
      body: Column(
        children: [
          _buildCalendar(),
          const SizedBox(height: 16),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   const Text(
                    "Upcoming Workouts",
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Expanded(child: _buildWorkoutList()),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCalendar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: TableCalendar(
        firstDay: DateTime.utc(2023, 1, 1),
        lastDay: DateTime.utc(2030, 12, 31),
        focusedDay: _focusedDay,
        selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
        onDaySelected: (selectedDay, focusedDay) {
          setState(() {
            _selectedDay = selectedDay;
            _focusedDay = focusedDay;
          });
        },
        eventLoader: _getEventsForDay,
        calendarStyle: CalendarStyle(
          defaultTextStyle: const TextStyle(color: Colors.white),
          weekendTextStyle: const TextStyle(color: Colors.white54),
          outsideTextStyle: TextStyle(color: Colors.white.withOpacity(0.2)),
          todayDecoration: BoxDecoration(
            color: Colors.blueAccent.withOpacity(0.3),
            shape: BoxShape.circle,
          ),
          selectedDecoration: const BoxDecoration(
            color: Colors.blueAccent,
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
          titleTextStyle: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          leftChevronIcon: Icon(Icons.chevron_left, color: Colors.white),
          rightChevronIcon: Icon(Icons.chevron_right, color: Colors.white),
        ),
        daysOfWeekStyle: const DaysOfWeekStyle(
          weekdayStyle: TextStyle(color: Colors.white54),
          weekendStyle: TextStyle(color: Colors.white54),
        ),
      ),
    );
  }

  Widget _buildWorkoutList() {
    // Optionally filter by selected day, but user requested "Upcoming workouts" to remain at bottom.
    // For now, showing all upcoming. If user wants filtering, we can change this list source.
    // Based on "Seuraavat treenuit voi jättää alimmaiseksi noin, miten ne nytkin näkyy",
    // keeping the full list seems correct, or maybe highlighting selected? 
    // Let's keep the full list for now as requested.
    
    return ListView.builder(
        itemCount: _workouts.length,
        itemBuilder: (context, index) {
          final workout = _workouts[index];
          final date = workout['date'] as DateTime;
          return Card(
            color: const Color(0xFF0F172A),
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.white.withOpacity(0.1))),
            child: ListTile(
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blueAccent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  workout['activity'] == 'Running' ? Icons.directions_run : Icons.fitness_center,
                  color: Colors.blueAccent,
                ),
              ),
              title: Text(
                workout['title'],
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
              subtitle: Text(
                '${DateFormat('EEEE, MMM d').format(date)} • ${workout['duration']}',
                style: const TextStyle(color: Colors.white54),
              ),
              trailing: const Icon(Icons.chevron_right, color: Colors.white24),
            ),
          );
        },
      );
  }
}

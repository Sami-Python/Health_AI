import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';

class ManualWorkoutFormSheet extends StatefulWidget {
  final VoidCallback onSuccess;

  const ManualWorkoutFormSheet({super.key, required this.onSuccess});

  @override
  State<ManualWorkoutFormSheet> createState() => _ManualWorkoutFormSheetState();
}

class _ManualWorkoutFormSheetState extends State<ManualWorkoutFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _apiService = ApiService();

  bool _isLoading = false;
  DateTime _selectedDate = DateTime.now();
  String _activityType = 'Running';
  String _durationMin = '';
  String _distanceKm = '';
  int _rpe = 5; // Default RPE
  String _notes = '';

  final List<String> _activities = [
    'Running',
    'Cycling',
    'Swimming',
    'Strength',
    'Walking',
    'Other'
  ];

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: Colors.blueAccent,
              onPrimary: Colors.white,
              surface: Color(0xFF0F172A),
              onSurface: Colors.white,
            ),
            dialogBackgroundColor: const Color(0xFF0F172A),
          ),
          child: child!,
        );
      },
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() => _isLoading = true);

    try {
      final workoutData = {
        'date': _selectedDate.toIso8601String().split('T')[0],
        'activity': _activityType,
        'duration_min': int.parse(_durationMin),
        'rpe': _rpe,
        'notes': _notes,
      };

      if (_distanceKm.isNotEmpty) {
        workoutData['distance_km'] = double.parse(_distanceKm);
      }

      await _apiService.logManualWorkout(workoutData);

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Workout logged successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onSuccess();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final keyboardSpace = MediaQuery.of(context).viewInsets.bottom;
    
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A), // Slate 900
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        border: Border.all(color: Colors.white10),
      ),
      padding: EdgeInsets.fromLTRB(24, 24, 24, 24 + keyboardSpace),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Log Manual Workout',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _selectDate(context),
                      icon: const Icon(Icons.calendar_today, size: 18, color: Colors.blueAccent),
                      label: Text(
                        '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
                        style: const TextStyle(color: Colors.white),
                      ),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: const BorderSide(color: Colors.white24),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _activityType,
                dropdownColor: const Color(0xFF1E293B),
                decoration: InputDecoration(
                  labelText: 'Activity Type',
                  labelStyle: const TextStyle(color: Colors.white54),
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
                style: const TextStyle(color: Colors.white),
                items: _activities.map((String activity) {
                  return DropdownMenuItem<String>(
                    value: activity,
                    child: Text(activity),
                  );
                }).toList(),
                onChanged: (String? newValue) {
                  setState(() {
                    _activityType = newValue!;
                  });
                },
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      initialValue: _durationMin,
                      keyboardType: TextInputType.number,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        labelText: 'Duration (min)',
                        labelStyle: const TextStyle(color: Colors.white54),
                        filled: true,
                        fillColor: Colors.white.withOpacity(0.05),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) return 'Required';
                        if (int.tryParse(value) == null) return 'Invalid number';
                        return null;
                      },
                      onSaved: (value) => _durationMin = value!,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextFormField(
                      initialValue: _distanceKm,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        labelText: 'Distance (km, opt)',
                        labelStyle: const TextStyle(color: Colors.white54),
                        filled: true,
                        fillColor: Colors.white.withOpacity(0.05),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      ),
                      validator: (value) {
                        if (value != null && value.isNotEmpty && double.tryParse(value) == null) {
                          return 'Invalid number';
                        }
                        return null;
                      },
                      onSaved: (value) => _distanceKm = value ?? '',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('RPE (Perceived Exertion)', style: TextStyle(color: Colors.white54)),
                      Text('$_rpe / 10', style: const TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Slider(
                    value: _rpe.toDouble(),
                    min: 1,
                    max: 10,
                    divisions: 9,
                    activeColor: Colors.blueAccent,
                    inactiveColor: Colors.white24,
                    onChanged: (double value) {
                      setState(() {
                        _rpe = value.toInt();
                      });
                    },
                  ),
                ],
              ),
              const SizedBox(height: 16),
              TextFormField(
                initialValue: _notes,
                style: const TextStyle(color: Colors.white),
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: 'Notes (optional)',
                  labelStyle: const TextStyle(color: Colors.white54),
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
                onSaved: (value) => _notes = value ?? '',
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text(
                        'Save Workout',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

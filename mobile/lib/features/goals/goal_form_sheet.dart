import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../../data/models/goal_model.dart';

/// A modal bottom sheet for creating or editing a goal.
/// Pass [existingGoal] to enter edit mode.
class GoalFormSheet extends StatefulWidget {
  final Goal? existingGoal;
  final VoidCallback onSuccess;

  const GoalFormSheet({super.key, this.existingGoal, required this.onSuccess});

  @override
  State<GoalFormSheet> createState() => _GoalFormSheetState();
}

class _GoalFormSheetState extends State<GoalFormSheet> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  // Form fields
  String _activityType = 'Running';
  String _periodType = 'weekly';
  String _targetUnit = 'km';
  String _frequency = 'Weekly';
  final TextEditingController _targetValueCtrl = TextEditingController();
  final TextEditingController _descriptionCtrl = TextEditingController();
  final TextEditingController _targetDateCtrl = TextEditingController();

  final List<String> _activities = ['Running', 'Cycling', 'Swimming', 'Gym', 'Skiing'];
  final List<String> _units = ['km', 'min', 'hours', 'times', 'kcal'];

  bool get _isEditMode => widget.existingGoal != null;

  @override
  void initState() {
    super.initState();
    if (_isEditMode) {
      final g = widget.existingGoal!;
      // Clamp to known values to prevent DropdownButton RangeError
      _activityType = _activities.contains(g.activityType) ? g.activityType : _activities.first;
      _periodType = ['weekly', 'monthly', 'target_date', 'race'].contains(g.periodType) ? g.periodType : 'weekly';
      _targetUnit = _units.contains(g.targetUnit) ? g.targetUnit : _units.first;
      _frequency = g.frequency ?? 'Weekly';
      _targetValueCtrl.text = g.targetValue.toString();
      _descriptionCtrl.text = g.description ?? '';
      _targetDateCtrl.text = g.targetDate ?? '';
    }
  }


  @override
  void dispose() {
    _targetValueCtrl.dispose();
    _descriptionCtrl.dispose();
    _targetDateCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final value = double.tryParse(_targetValueCtrl.text.trim());
    if (value == null || value <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a valid target value'), backgroundColor: Colors.red),
      );
      return;
    }

    final bool needsDate = _periodType == 'target_date' || _periodType == 'race';
    if (needsDate && _targetDateCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a target date'), backgroundColor: Colors.red),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final data = {
        'activity_type': _activityType,
        'target_value': value,
        'target_unit': _targetUnit,
        'period_type': _periodType,
        'frequency': needsDate ? null : _frequency,
        'target_date': needsDate ? _targetDateCtrl.text.trim() : null,
        'description': _descriptionCtrl.text.trim(),
      };

      if (_isEditMode) {
        await _apiService.updateGoal(widget.existingGoal!.id, data);
      } else {
        await _apiService.createGoal(data);
      }

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_isEditMode ? 'Goal updated!' : 'Goal created!'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onSuccess();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 30)),
      firstDate: DateTime.now(),
      lastDate: DateTime(2030),
      builder: (context, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: const ColorScheme.dark(primary: Colors.blueAccent),
        ),
        child: child!,
      ),
    );
    if (picked != null) {
      setState(() {
        _targetDateCtrl.text =
            '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool needsDate = _periodType == 'target_date' || _periodType == 'race';

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F172A),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(20, 16, 20, MediaQuery.of(context).viewInsets.bottom + 20),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Title
            Text(
              _isEditMode ? 'Edit Goal' : 'Create New Goal',
              style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),

            // Activity Type
            _label('Activity'),
            _dropdown(
              value: _activityType,
              items: _activities,
              onChanged: (v) => setState(() => _activityType = v!),
            ),
            const SizedBox(height: 16),

            // Goal Type selector
            _label('Goal Type'),
            Row(
              children: [
                _typeButton('Recurring', 'weekly'),
                const SizedBox(width: 8),
                _typeButton('Target Date', 'target_date'),
                const SizedBox(width: 8),
                _typeButton('Race 🏁', 'race', activeColor: Colors.purpleAccent),
              ],
            ),
            const SizedBox(height: 16),

            // Frequency or Date picker
            if (!needsDate) ...[
              _label('Frequency'),
              _dropdown(
                value: _frequency,
                items: const ['Weekly', 'Monthly'],
                onChanged: (v) => setState(() => _frequency = v!),
              ),
            ] else ...[
              _label(_periodType == 'race' ? 'Race Date' : 'Target Date'),
              GestureDetector(
                onTap: _pickDate,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.calendar_today, color: Colors.white54, size: 18),
                      const SizedBox(width: 10),
                      Text(
                        _targetDateCtrl.text.isEmpty ? 'Select date...' : _targetDateCtrl.text,
                        style: TextStyle(
                          color: _targetDateCtrl.text.isEmpty ? Colors.white38 : Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: 16),

            // Target Value + Unit
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _label('Target Value'),
                      _textField(_targetValueCtrl, 'e.g. 30', TextInputType.number),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _label('Unit'),
                      _dropdown(
                        value: _targetUnit,
                        items: _units,
                        onChanged: (v) => setState(() => _targetUnit = v!),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Description
            _label('Description (optional)'),
            _textField(_descriptionCtrl, 'e.g. Prepare for marathon', TextInputType.text),
            const SizedBox(height: 24),

            // Submit button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(
                        _isEditMode ? 'Update Goal' : 'Create Goal',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text.toUpperCase(),
            style: const TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
      );

  Widget _textField(TextEditingController ctrl, String hint, TextInputType type) => TextField(
        controller: ctrl,
        keyboardType: type,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.white24),
          filled: true,
          fillColor: const Color(0xFF1E293B),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        ),
      );

  Widget _dropdown({required String value, required List<String> items, required ValueChanged<String?> onChanged}) =>
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(10),
        ),
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          underline: const SizedBox(),
          dropdownColor: const Color(0xFF1E293B),
          style: const TextStyle(color: Colors.white),
          items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
          onChanged: onChanged,
        ),
      );

  Widget _typeButton(String label, String type, {Color activeColor = Colors.blueAccent}) => Expanded(
        child: GestureDetector(
          onTap: () => setState(() => _periodType = type),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: _periodType == type ? activeColor.withOpacity(0.15) : const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: _periodType == type ? activeColor : Colors.white12),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: _periodType == type ? activeColor : Colors.white54,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      );
}

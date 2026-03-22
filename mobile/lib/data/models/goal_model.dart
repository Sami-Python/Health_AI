class Goal {
  final String id;
  final String activityType;
  final double targetValue;
  final String targetUnit;
  final String periodType;
  final String status;
  final double currentValue;
  final int progressPercentage;
  final double remaining;
  final int daysLeft;
  final String? description;
  final String? frequency;
  final String? targetDate;
  final int? daysRemaining;

  Goal({
    required this.id,
    required this.activityType,
    required this.targetValue,
    required this.targetUnit,
    required this.periodType,
    required this.status,
    required this.currentValue,
    required this.progressPercentage,
    required this.remaining,
    required this.daysLeft,
    this.description,
    this.frequency,
    this.targetDate,
    this.daysRemaining,
  });

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id'] ?? '',
      activityType: json['activity_type'] ?? '',
      targetValue: (json['target_value'] ?? 0).toDouble(),
      targetUnit: json['target_unit'] ?? '',
      periodType: json['period_type'] ?? '',
      status: json['status'] ?? 'UNKNOWN',
      currentValue: (json['current_value'] ?? 0).toDouble(),
      progressPercentage: json['progress_percentage'] ?? 0,
      remaining: (json['remaining'] ?? 0).toDouble(),
      daysLeft: json['days_left'] ?? 0,
      description: json['description'],
      frequency: json['frequency'],
      targetDate: json['target_date'],
      daysRemaining: json['days_remaining'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'activity_type': activityType,
      'target_value': targetValue,
      'target_unit': targetUnit,
      'period_type': periodType,
      'description': description,
      'frequency': frequency,
      'target_date': targetDate,
    };
  }
}

class Metric {
  final String date;
  final double ctl;
  final double atl;
  final double tsb;
  final int load;
  final int readiness;
  final int sleepMin;

  Metric({
    required this.date,
    required this.ctl,
    required this.atl,
    required this.tsb,
    required this.load,
    required this.readiness,
    required this.sleepMin,
  });

  factory Metric.fromJson(Map<String, dynamic> json) {
    return Metric(
      date: json['date'] ?? '',
      ctl: (json['ctl'] ?? 0).toDouble(),
      atl: (json['atl'] ?? 0).toDouble(),
      tsb: (json['tsb'] ?? 0).toDouble(),
      load: (json['load'] ?? 0),
      readiness: (json['readiness'] ?? 0),
      sleepMin: (json['sleep_min'] ?? 0),
    );
  }

  // Alias for compatibility with Charts
  int get workoutLoad => load;
}

import 'package:flutter/material.dart';

class GamificationCard extends StatelessWidget {
  final Map<String, dynamic>? data;

  const GamificationCard({super.key, this.data});

  @override
  Widget build(BuildContext context) {
    if (data == null) return const SizedBox.shrink();

    final int score = data?['consistency_score'] ?? 0;
    final int streak = data?['streak'] ?? 0;
    final List<dynamic> badges = data?['badges'] ?? [];

    Color getProgressColor(int s) {
      if (s >= 95) return Colors.amber;
      if (s >= 80) return Colors.blueAccent;
      if (s >= 60) return Colors.teal;
      return Colors.grey;
    }

    Color getBadgeColor(String level) {
      switch (level) {
        case 'gold': return Colors.amber;
        case 'silver': return Colors.grey.shade400;
        case 'bronze': return Colors.orange.shade300;
        case 'special': return Colors.deepOrangeAccent;
        default: return Colors.blueGrey;
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16.0),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A), // Slate 900
        borderRadius: BorderRadius.circular(16.0),
        border: Border.all(color: const Color(0xFF1E293B)), // Slate 800
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            spreadRadius: 1,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Circular Progress
                SizedBox(
                  width: 70,
                  height: 70,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      CircularProgressIndicator(
                        value: score / 100,
                        backgroundColor: const Color(0xFF1E293B),
                        color: getProgressColor(score),
                        strokeWidth: 6,
                      ),
                      Text(
                        '$score%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                
                // Details
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'CONSISTENCY',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        '14-Day Average',
                        style: TextStyle(color: Colors.white54, fontSize: 11),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF334155)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.local_fire_department,
                              color: streak >= 3 ? Colors.deepOrange : Colors.grey,
                              size: 14,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '$streak Day Streak',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            // Badges Section
            if (badges.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Divider(color: Color(0xFF1E293B)),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.emoji_events, color: Colors.teal, size: 16),
                  const SizedBox(width: 6),
                  const Text(
                    'Unlocked Badges',
                    style: TextStyle(
                      color: Colors.white70,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    '${badges.length} Total',
                    style: const TextStyle(color: Colors.white54, fontSize: 11),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: badges.map((badge) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: getBadgeColor(badge['level'] ?? ''),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          badge['icon'] ?? '',
                          style: const TextStyle(fontSize: 14),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          badge['name'] ?? '',
                          style: const TextStyle(
                            color: Colors.black87,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import '../../data/models/metric_model.dart';
import '../../data/models/goal_model.dart';

class ApiService {
  // Use physical device PC IP over WiFi
  static const String baseUrl = 'http://192.168.1.130:8000';

  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<Map<String, String>> _getHeaders() async {
    final user = _auth.currentUser;
    if (user == null) throw Exception('User not logged in');
    final token = await user.getIdToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // ─── Metrics ────────────────────────────────────────────────
  Future<List<Metric>> fetchMetricsHistory() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/metrics/history'), headers: headers);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((json) => Metric.fromJson(json)).toList();
    }
    throw Exception('Failed to load metrics: ${response.statusCode}');
  }

  // ─── Goals ──────────────────────────────────────────────────
  Future<List<Goal>> fetchGoals() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/goals'), headers: headers);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((json) => Goal.fromJson(json)).toList();
    }
    throw Exception('Failed to load goals: ${response.statusCode}');
  }

  Future<void> createGoal(Map<String, dynamic> goalData) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/goals'),
      headers: headers,
      body: json.encode(goalData),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('Failed to create goal: ${response.statusCode}');
    }
  }

  Future<void> updateGoal(String goalId, Map<String, dynamic> goalData) async {
    final headers = await _getHeaders();
    final response = await http.put(
      Uri.parse('$baseUrl/goals/$goalId'),
      headers: headers,
      body: json.encode(goalData),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to update goal: ${response.statusCode}');
    }
  }

  Future<void> deleteGoal(String goalId) async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/goals/$goalId'),
      headers: headers,
    );
    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete goal: ${response.statusCode}');
    }
  }

  // ─── Workouts ───────────────────────────────────────────────
  Future<Map<String, dynamic>?> fetchNextWorkout() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/workouts/next'), headers: headers);
    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      if (data is Map<String, dynamic> && data.isNotEmpty) return data;
      return null;
    }
    return null;
  }

  Future<List<dynamic>> fetchWorkoutHistory() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/workouts/history'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as List<dynamic>;
    }
    return [];
  }

  Future<void> logManualWorkout(Map<String, dynamic> workoutData) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/workouts/manual'),
      headers: headers,
      body: json.encode(workoutData),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('Failed to log workout: ${response.statusCode}');
    }
  }

  Future<void> deleteWorkout(String workoutId) async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/workouts/$workoutId'),
      headers: headers,
    );
    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete workout: ${response.statusCode}');
    }
  }

  Future<void> updateWorkoutDate(String workoutId, String newDate) async {
    final headers = await _getHeaders();
    final response = await http.patch(
      Uri.parse('$baseUrl/workouts/$workoutId'),
      headers: headers,
      body: json.encode({'date': newDate}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to update workout date: ${response.statusCode}');
    }
  }

  Future<void> uploadWorkoutToGarmin(Map<String, dynamic> workout, String date) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/workouts/upload'),
      headers: headers,
      body: json.encode({'workout': workout, 'date': date}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to upload to Garmin: ${response.statusCode}');
    }
  }

  Future<Map<String, dynamic>?> fetchWeeklyStats() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/workouts/weekly-status'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    return null;
  }

  // ─── AI ─────────────────────────────────────────────────────
  Future<Map<String, dynamic>?> fetchAIInsight() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/ai/insight'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    return null;
  }

  Future<Map<String, dynamic>?> fetchAiModelMetrics() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/ai/model-metrics'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    return null;
  }

  Future<Map<String, dynamic>> generateAiPlan(int days) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/plans/generate'),
      headers: headers,
      body: json.encode({'days': days}),
    );
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    if (response.statusCode == 429) {
      throw Exception('Daily AI generation limit reached.');
    }
    throw Exception('Failed to generate AI plan: ${response.statusCode}');
  }

  Future<String> sendChatMessage(
    String message,
    List<Map<String, String>> history,
  ) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/ai/chat'),
      headers: headers,
      body: json.encode({
        'message': message,
        'history': history.take(10).toList(), // Limit context size
      }),
    );
    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return data['reply'] as String? ?? 'No response';
    }
    if (response.statusCode == 429) {
      throw Exception('Rate limit reached. Please wait a moment.');
    }
    throw Exception('Chat failed: ${response.statusCode}');
  }

  // ─── User Profile ────────────────────────────────────────────
  Future<Map<String, dynamic>?> getUserProfile() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/profile'), headers: headers);

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    return null;
  }

  Future<void> saveUserProfile(Map<String, dynamic> profileData) async {
    final headers = await _getHeaders();
    final response = await http.put(
      Uri.parse('$baseUrl/profile'),
      headers: headers,
      body: json.encode(profileData),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save profile: ${response.statusCode}');
    }
  }

  // ─── Garmin ─────────────────────────────────────────────────
  Future<Map<String, dynamic>?> getGarminStatus() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/garmin/status'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    return null;
  }

  Future<void> saveGarminCredentials(String username, String password) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/garmin/credentials'),
      headers: headers,
      body: json.encode({'username': username, 'password': password}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save Garmin credentials: ${response.statusCode}');
    }
  }

  Future<void> deleteGarminCredentials() async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/garmin/credentials'),
      headers: headers,
    );
    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete Garmin credentials: ${response.statusCode}');
    }
  }

  // ─── Settings / GDPR ────────────────────────────────────────
  Future<Map<String, dynamic>?> exportUserData() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/user/export'), headers: headers);
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    throw Exception('Failed to export data: ${response.statusCode}');
  }

  Future<void> deleteAccount() async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/account'),
      headers: headers,
    );
    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete account: ${response.statusCode}');
    }
  }

  Future<void> sendFeedback(String message, String category) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/feedback'),
      headers: headers,
      body: json.encode({'message': message, 'category': category}),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('Failed to send feedback: ${response.statusCode}');
    }
  }
}

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import '../../data/models/metric_model.dart';
import '../../data/models/goal_model.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator to access localhost
  // Use localhost for iOS Simulator
  // static const String baseUrl = 'http://10.0.2.2:8000';
  static const String baseUrl = 'http://10.0.2.2:8000'; 

  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<Map<String, String>> _getHeaders() async {
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('User not logged in');
    }
    final token = await user.getIdToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  Future<List<Metric>> fetchMetricsHistory() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/metrics/history'), headers: headers);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((json) => Metric.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load metrics: ${response.statusCode}');
    }
  }

  Future<List<Goal>> fetchGoals() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/goals'), headers: headers);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((json) => Goal.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load goals: ${response.statusCode}');
    }
  }

  Future<Map<String, dynamic>?> fetchNextWorkout() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/workouts/next'), headers: headers);

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      if (data is Map<String, dynamic> && data.isNotEmpty) {
        return data;
      }
      return null;
    } else {
      // Allow 404 or empty returns as null
      print('Fetch next workout failed: ${response.statusCode}');
      return null;
    }
  }

  Future<Map<String, dynamic>?> fetchAIInsight() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/ai/insight'), headers: headers);

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    } else {
      print('Fetch AI insight failed: ${response.statusCode}');
      return null;
    }
  }

  Future<Map<String, dynamic>?> fetchWeeklyStats() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/workouts/weekly-status'), headers: headers);

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    } else {
      print('Fetch weekly stats failed: ${response.statusCode}');
      return null;
    }
  }
}

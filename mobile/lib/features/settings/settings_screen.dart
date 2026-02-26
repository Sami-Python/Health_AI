import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../core/services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final ApiService _apiService = ApiService();

  bool _exportLoading = false;
  bool _deleteLoading = false;

  // Feedback form
  final _feedbackCtrl = TextEditingController();
  String _feedbackCategory = 'General';
  bool _feedbackLoading = false;

  @override
  void dispose() {
    _feedbackCtrl.dispose();
    super.dispose();
  }

  Future<void> _exportData() async {
    setState(() => _exportLoading = true);
    try {
      final data = await _apiService.exportUserData();
      if (mounted && data != null) {
        showDialog(
          context: context,
          builder: (_) => AlertDialog(
            backgroundColor: const Color(0xFF0F172A),
            title: const Text('Your Data', style: TextStyle(color: Colors.white)),
            content: SingleChildScrollView(
              child: Text(
                data.entries.map((e) => '${e.key}: ${e.value}').join('\n'),
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close', style: TextStyle(color: Colors.blueAccent)),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e'), backgroundColor: Colors.red),
        );
      }
    }
    if (mounted) setState(() => _exportLoading = false);
  }

  Future<void> _deleteAccount() async {
    // Step 1: first confirmation
    final step1 = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text('Delete Account', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This will permanently delete your account and all data. This cannot be undone.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Continue', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
    if (step1 != true) return;

    // Step 2: final confirmation
    final step2 = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E0000),
        title: const Row(children: [
          Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
          SizedBox(width: 8),
          Text('Are you sure?', style: TextStyle(color: Colors.white)),
        ]),
        content: const Text(
          'Your account, training data, and Garmin connection will be permanently deleted.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete Everything', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (step2 != true) return;

    setState(() => _deleteLoading = true);
    try {
      await _apiService.deleteAccount();
      await FirebaseAuth.instance.signOut();
      await GoogleSignIn().signOut();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
        setState(() => _deleteLoading = false);
      }
    }
  }

  Future<void> _sendFeedback() async {
    if (_feedbackCtrl.text.trim().isEmpty) return;
    setState(() => _feedbackLoading = true);
    try {
      await _apiService.sendFeedback(_feedbackCtrl.text.trim(), _feedbackCategory);
      if (mounted) {
        _feedbackCtrl.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Feedback sent – thank you! 🙏'), backgroundColor: Colors.green),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
    if (mounted) setState(() => _feedbackLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: const Color(0xFF020617),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Settings', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Feedback ─────────────────────────────────────────
            _sectionTitle('Send Feedback'),
            const SizedBox(height: 4),
            const Text('Help us improve the app', style: TextStyle(color: Colors.white38, fontSize: 12)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(color: const Color(0xFF0F172A), borderRadius: BorderRadius.circular(10)),
              child: DropdownButton<String>(
                value: _feedbackCategory,
                isExpanded: true,
                underline: const SizedBox(),
                dropdownColor: const Color(0xFF0F172A),
                style: const TextStyle(color: Colors.white),
                items: ['General', 'Bug Report', 'Feature Request', 'Data Issue']
                    .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                    .toList(),
                onChanged: (v) => setState(() => _feedbackCategory = v!),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _feedbackCtrl,
              maxLines: 4,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Describe your feedback...',
                hintStyle: const TextStyle(color: Colors.white24),
                filled: true,
                fillColor: const Color(0xFF0F172A),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.all(14),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _feedbackLoading ? null : _sendFeedback,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _feedbackLoading
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Send Feedback', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 32),

            // ── Privacy & Data (GDPR) ────────────────────────────
            _sectionTitle('Privacy & Data'),
            const SizedBox(height: 4),
            const Text('GDPR – Your rights over your data', style: TextStyle(color: Colors.white38, fontSize: 12)),
            const SizedBox(height: 16),

            // Export data
            _settingsTile(
              icon: Icons.download_outlined,
              iconColor: Colors.blueAccent,
              title: 'Export My Data',
              subtitle: 'Download all your data as JSON',
              trailing: _exportLoading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blueAccent))
                  : const Icon(Icons.chevron_right, color: Colors.white38),
              onTap: _exportLoading ? null : _exportData,
            ),
            const SizedBox(height: 12),

            // Delete account
            _settingsTile(
              icon: Icons.delete_forever_outlined,
              iconColor: Colors.redAccent,
              title: 'Delete Account',
              subtitle: 'Permanently delete your account and all data',
              trailing: _deleteLoading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.redAccent))
                  : const Icon(Icons.chevron_right, color: Colors.white38),
              onTap: _deleteLoading ? null : _deleteAccount,
              isDestructive: true,
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String text) => Text(
        text,
        style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold),
      );

  Widget _settingsTile({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required Widget trailing,
    VoidCallback? onTap,
    bool isDestructive = false,
  }) =>
      GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isDestructive ? Colors.redAccent.withOpacity(0.2) : Colors.white10),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconColor, size: 20),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: TextStyle(color: isDestructive ? Colors.redAccent : Colors.white, fontWeight: FontWeight.w600)),
                    Text(subtitle, style: const TextStyle(color: Colors.white38, fontSize: 12)),
                  ],
                ),
              ),
              trailing,
            ],
          ),
        ),
      );
}

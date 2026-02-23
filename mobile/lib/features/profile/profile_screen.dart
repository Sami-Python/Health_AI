import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../../core/services/api_service.dart';
import '../settings/settings_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _apiService = ApiService();
  final User? _user = FirebaseAuth.instance.currentUser;

  // Profile form state
  final _ageCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  final _heightCtrl = TextEditingController();
  String _gender = 'Male';
  bool _profileLoading = false;
  bool _profileSaving = false;

  // Garmin state
  final _garminUserCtrl = TextEditingController();
  final _garminPassCtrl = TextEditingController();
  bool _garminConnected = false;
  bool _garminLoading = false;
  bool _garminSaving = false;
  bool _garminPassVisible = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadGarminStatus();
  }

  @override
  void dispose() {
    _ageCtrl.dispose();
    _weightCtrl.dispose();
    _heightCtrl.dispose();
    _garminUserCtrl.dispose();
    _garminPassCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    setState(() => _profileLoading = true);
    try {
      final data = await _apiService.getUserProfile();
      if (data != null && mounted) {
        setState(() {
          _ageCtrl.text = (data['age'] ?? '').toString();
          _weightCtrl.text = (data['weight_kg'] ?? '').toString();
          _heightCtrl.text = (data['height_cm'] ?? '').toString();
          _gender = data['gender'] ?? 'Male';
        });
      }
    } catch (_) {}
    if (mounted) setState(() => _profileLoading = false);
  }

  Future<void> _saveProfile() async {
    setState(() => _profileSaving = true);
    try {
      await _apiService.saveUserProfile({
        'age': int.tryParse(_ageCtrl.text.trim()),
        'weight_kg': double.tryParse(_weightCtrl.text.trim()),
        'height_cm': double.tryParse(_heightCtrl.text.trim()),
        'gender': _gender,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile saved!'), backgroundColor: Colors.green),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
    if (mounted) setState(() => _profileSaving = false);
  }

  Future<void> _loadGarminStatus() async {
    setState(() => _garminLoading = true);
    try {
      final status = await _apiService.getGarminStatus();
      if (mounted) {
        setState(() => _garminConnected = status?['connected'] == true);
      }
    } catch (_) {}
    if (mounted) setState(() => _garminLoading = false);
  }

  Future<void> _saveGarminCredentials() async {
    final user = _garminUserCtrl.text.trim();
    final pass = _garminPassCtrl.text.trim();
    if (user.isEmpty || pass.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter username and password'), backgroundColor: Colors.orange),
      );
      return;
    }
    setState(() => _garminSaving = true);
    try {
      await _apiService.saveGarminCredentials(user, pass);
      if (mounted) {
        setState(() {
          _garminConnected = true;
          _garminPassCtrl.clear();
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Garmin connected! ✅'), backgroundColor: Colors.green),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    }
    if (mounted) setState(() => _garminSaving = false);
  }

  Future<void> _disconnectGarmin() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text('Disconnect Garmin', style: TextStyle(color: Colors.white)),
        content: const Text('Remove Garmin credentials?', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Disconnect', style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
    if (confirmed == true) {
      try {
        await _apiService.deleteGarminCredentials();
        if (mounted) setState(() => _garminConnected = false);
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _signOut() async {
    try {
      await FirebaseAuth.instance.signOut();
      await GoogleSignIn().signOut();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error signing out: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayName = (_user?.displayName?.isNotEmpty == true
            ? _user!.displayName!
            : _user?.email?.split('@').first)
        ?.trim() ?? 'User';

    final email = _user?.email ?? '';

    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: const Color(0xFF020617),
        title: const Text('Profile', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Colors.white54),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen())),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // User header
            Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: Colors.blueAccent.withOpacity(0.2),
                  backgroundImage: _user?.photoURL != null ? NetworkImage(_user!.photoURL!) : null,
                  child: _user?.photoURL == null
                      ? Text(displayName.isNotEmpty ? displayName[0].toUpperCase() : '?', style: const TextStyle(color: Colors.blueAccent, fontSize: 24, fontWeight: FontWeight.bold))
                      : null,

                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(displayName, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                      Text(email, style: const TextStyle(color: Colors.white54, fontSize: 13)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 28),

            // ── Physical Profile ─────────────────────────────────
            _sectionTitle('Physical Profile'),
            const SizedBox(height: 12),
            if (_profileLoading)
              const Center(child: CircularProgressIndicator(color: Colors.blueAccent))
            else ...[
              Row(
                children: [
                  Expanded(child: _inputField('Age', _ageCtrl, 'years', TextInputType.number)),
                  const SizedBox(width: 12),
                  Expanded(child: _inputField('Weight', _weightCtrl, 'kg', TextInputType.number)),
                  const SizedBox(width: 12),
                  Expanded(child: _inputField('Height', _heightCtrl, 'cm', TextInputType.number)),
                ],
              ),
              const SizedBox(height: 12),
              _label('Gender'),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(color: const Color(0xFF0F172A), borderRadius: BorderRadius.circular(10)),
                child: DropdownButton<String>(
                  value: _gender,
                  isExpanded: true,
                  underline: const SizedBox(),
                  dropdownColor: const Color(0xFF0F172A),
                  style: const TextStyle(color: Colors.white),
                  items: ['Male', 'Female', 'Other']
                      .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                      .toList(),
                  onChanged: (v) => setState(() => _gender = v!),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _profileSaving ? null : _saveProfile,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _profileSaving
                      ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Save Profile', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
            const SizedBox(height: 28),

            // ── Garmin Connection ────────────────────────────────
            _sectionTitle('Garmin Connection'),
            const SizedBox(height: 12),
            if (_garminLoading)
              const Center(child: CircularProgressIndicator(color: Colors.greenAccent))
            else if (_garminConnected)
              _garminConnectedCard()
            else
              _garminForm(),
            const SizedBox(height: 28),

            // ── Account ──────────────────────────────────────────
            _sectionTitle('Account'),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _signOut,
              icon: const Icon(Icons.logout, color: Colors.redAccent),
              label: const Text('Sign Out', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Colors.redAccent),
                padding: const EdgeInsets.symmetric(vertical: 14),
                minimumSize: const Size(double.infinity, 0),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _garminConnectedCard() => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.green.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.green.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline, color: Colors.greenAccent, size: 28),
            const SizedBox(width: 12),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Garmin Connected', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  Text('Your workouts sync automatically', style: TextStyle(color: Colors.white54, fontSize: 12)),
                ],
              ),
            ),
            TextButton(
              onPressed: _disconnectGarmin,
              child: const Text('Disconnect', style: TextStyle(color: Colors.redAccent, fontSize: 12)),
            ),
          ],
        ),
      );

  Widget _garminForm() => Column(
        children: [
          _inputField('Garmin Username / Email', _garminUserCtrl, 'garmin@email.com', TextInputType.emailAddress),
          const SizedBox(height: 12),
          TextField(
            controller: _garminPassCtrl,
            obscureText: !_garminPassVisible,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              labelText: 'Garmin Password',
              labelStyle: const TextStyle(color: Colors.white38),
              filled: true,
              fillColor: const Color(0xFF0F172A),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              suffixIcon: IconButton(
                icon: Icon(_garminPassVisible ? Icons.visibility_off : Icons.visibility, color: Colors.white38),
                onPressed: () => setState(() => _garminPassVisible = !_garminPassVisible),
              ),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _garminSaving ? null : _saveGarminCredentials,
              icon: const Icon(Icons.link, color: Colors.white),
              label: _garminSaving
                  ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Connect Garmin', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.tealAccent.shade700,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
        ],
      );

  Widget _sectionTitle(String text) => Text(
        text,
        style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold),
      );

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6, top: 4),
        child: Text(text.toUpperCase(),
            style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
      );

  Widget _inputField(String label, TextEditingController ctrl, String hint, TextInputType type) => TextField(
        controller: ctrl,
        keyboardType: type,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white38, fontSize: 12),
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.white24),
          filled: true,
          fillColor: const Color(0xFF0F172A),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        ),
      );
}

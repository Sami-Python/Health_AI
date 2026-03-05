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

  // Garmin section
  bool _garminConnected = false;
  String? _garminUsername;
  bool _garminStatusLoading = true;
  bool _garminConnecting = false;
  bool _garminDisconnecting = false;

  @override
  void initState() {
    super.initState();
    _loadGarminStatus();
  }

  @override
  void dispose() {
    _feedbackCtrl.dispose();
    super.dispose();
  }

  // ── Garmin ─────────────────────────────────────────────────────

  Future<void> _loadGarminStatus() async {
    try {
      final status = await _apiService.getGarminStatus();
      if (mounted) {
        setState(() {
          _garminConnected = status?['connected'] == true;
          _garminUsername = status?['username'] as String?;
          _garminStatusLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _garminStatusLoading = false);
    }
  }

  Future<void> _connectGarmin() async {
    final emailCtrl = TextEditingController();
    final passCtrl = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Row(children: [
          Icon(Icons.watch_outlined, color: Color(0xFF6366F1)),
          SizedBox(width: 8),
          Text('Yhdistä Garmin', style: TextStyle(color: Colors.white)),
        ]),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Kirjaudu Garmin Connect -tilillesi. Salasana salataan AES-256:lla ennen tallennusta.',
              style: TextStyle(color: Colors.white60, fontSize: 12),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: emailCtrl,
              keyboardType: TextInputType.emailAddress,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('Garmin-sähköposti'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: passCtrl,
              obscureText: true,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('Salasana'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Peruuta', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF6366F1)),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Yhdistä', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final email = emailCtrl.text.trim();
    final password = passCtrl.text;
    if (email.isEmpty || password.isEmpty) return;

    setState(() => _garminConnecting = true);
    try {
      final result = await _apiService.connectGarmin(email, password);
      final status = result['status'] as String?;

      if (status == 'connected') {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Garmin yhdistetty!'),
              backgroundColor: Colors.green,
            ),
          );
          await _loadGarminStatus();
        }
      } else if (status == 'mfa_required') {
        final sessionId = result['session_id'] as String;
        if (mounted) await _showMfaDialog(sessionId);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Yhdistäminen epäonnistui: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _garminConnecting = false);
    }
  }

  Future<void> _showMfaDialog(String sessionId) async {
    final codeCtrl = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Row(children: [
          Icon(Icons.security_outlined, color: Color(0xFFF59E0B)),
          SizedBox(width: 8),
          Text('Kaksivaiheinen tunnistus', style: TextStyle(color: Colors.white)),
        ]),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Garmin lähetti vahvistuskoodin sähköpostiisi tai tekstiviestillä. Syötä se alle.',
              style: TextStyle(color: Colors.white60, fontSize: 12),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: codeCtrl,
              keyboardType: TextInputType.number,
              style: const TextStyle(color: Colors.white, letterSpacing: 4, fontSize: 20),
              textAlign: TextAlign.center,
              maxLength: 8,
              decoration: _inputDecoration('123456').copyWith(counterText: ''),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Peruuta', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFF59E0B)),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Vahvista', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final code = codeCtrl.text.trim();
    if (code.isEmpty) return;

    setState(() => _garminConnecting = true);
    try {
      await _apiService.submitGarminMfa(sessionId, code);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Garmin yhdistetty 2FA:n kautta!'),
            backgroundColor: Colors.green,
          ),
        );
        await _loadGarminStatus();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Koodi virheellinen tai vanhentunut: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _garminConnecting = false);
    }
  }

  Future<void> _disconnectGarmin() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text('Katkaise Garmin-yhteys', style: TextStyle(color: Colors.white)),
        content: const Text(
          'Tämä poistaa tallennetut Garmin-tunnukset ja OAuth-tokenit.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Peruuta', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Katkaise', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _garminDisconnecting = true);
    try {
      await _apiService.deleteGarminCredentials();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Garmin-yhteys katkaistu'), backgroundColor: Colors.orange),
        );
        await _loadGarminStatus();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Virhe: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _garminDisconnecting = false);
    }
  }

  // ── GDPR ───────────────────────────────────────────────────────

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

  // ── Build ───────────────────────────────────────────────────────

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
        title: const Text('Asetukset', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // ── Garmin Connect ────────────────────────────────────
            _sectionTitle('Garmin Connect'),
            const SizedBox(height: 4),
            const Text('Synkronoi harjoittelutiedot automaattisesti', style: TextStyle(color: Colors.white38, fontSize: 12)),
            const SizedBox(height: 12),
            _garminStatusLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF6366F1)))
                : _garminConnected
                    ? _garminConnectedTile()
                    : _garminDisconnectedTile(),
            const SizedBox(height: 32),

            // ── Feedback ──────────────────────────────────────────
            _sectionTitle('Lähetä palautetta'),
            const SizedBox(height: 4),
            const Text('Auta meitä parantamaan sovellusta', style: TextStyle(color: Colors.white38, fontSize: 12)),
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
                hintText: 'Kuvaile palautteesi...',
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
                    : const Text('Lähetä palaute', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 32),

            // ── Privacy & Data (GDPR) ─────────────────────────────
            _sectionTitle('Yksityisyys & Data'),
            const SizedBox(height: 4),
            const Text('GDPR – Oikeutesi tietoihisi', style: TextStyle(color: Colors.white38, fontSize: 12)),
            const SizedBox(height: 16),

            _settingsTile(
              icon: Icons.download_outlined,
              iconColor: Colors.blueAccent,
              title: 'Vie omat tietoni',
              subtitle: 'Lataa kaikki tietosi JSON-muodossa',
              trailing: _exportLoading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.blueAccent))
                  : const Icon(Icons.chevron_right, color: Colors.white38),
              onTap: _exportLoading ? null : _exportData,
            ),
            const SizedBox(height: 12),

            _settingsTile(
              icon: Icons.delete_forever_outlined,
              iconColor: Colors.redAccent,
              title: 'Poista tili',
              subtitle: 'Poista tilisi ja kaikki tietosi pysyvästi',
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

  // ── Garmin sub-widgets ──────────────────────────────────────────

  Widget _garminConnectedTile() => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.greenAccent.withOpacity(0.25)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.watch_outlined, color: Colors.greenAccent, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Yhdistetty ✅', style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.w600)),
                  if (_garminUsername != null)
                    Text(_garminUsername!, style: const TextStyle(color: Colors.white38, fontSize: 12)),
                ],
              ),
            ),
            _garminDisconnecting
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.redAccent))
                : TextButton(
                    onPressed: _disconnectGarmin,
                    style: TextButton.styleFrom(foregroundColor: Colors.redAccent),
                    child: const Text('Katkaise'),
                  ),
          ],
        ),
      );

  Widget _garminDisconnectedTile() => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF6366F1).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.watch_outlined, color: Color(0xFF6366F1), size: 20),
            ),
            const SizedBox(width: 14),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Ei yhdistetty', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                  Text('Yhdistä Garmin-tilisi synkronointia varten', style: TextStyle(color: Colors.white38, fontSize: 12)),
                ],
              ),
            ),
            _garminConnecting
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF6366F1)))
                : ElevatedButton(
                    onPressed: _connectGarmin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF6366F1),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text('Yhdistä', style: TextStyle(color: Colors.white, fontSize: 13)),
                  ),
          ],
        ),
      );

  // ── Shared helpers ──────────────────────────────────────────────

  InputDecoration _inputDecoration(String hint) => InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Colors.white30),
        filled: true,
        fillColor: const Color(0xFF1E293B),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      );

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

import 'package:flutter/material.dart';

class HeartbeatLogo extends StatelessWidget {
  final double size;

  const HeartbeatLogo({super.key, this.size = 100});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // The Heart Background
          Icon(
            Icons.favorite_border_rounded,
            size: size,
            color: const Color(0xFFBB86FC).withOpacity(0.8), // Light purple/blueish
          ),
          // The Red Heartbeat Line
          SizedBox(
            width: size * 1.2, // Slightly wider to go across
            height: size * 0.6,
            child: CustomPaint(
              painter: _HeartbeatPainter(),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeartbeatPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.redAccent // Requested red color
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final path = Path();
    final w = size.width;
    final h = size.height;
    final midY = h / 2;

    // Draw the ECG waveform
    path.moveTo(0, midY);
    path.lineTo(w * 0.2, midY); // Flat start
    path.lineTo(w * 0.3, midY - h * 0.3); // P wave (small up)
    path.lineTo(w * 0.35, midY + h * 0.1); // slight down
    path.lineTo(w * 0.4, midY - h * 0.8); // R wave (big up)
    path.lineTo(w * 0.45, midY + h * 0.8); // S wave (big down)
    path.lineTo(w * 0.5, midY); // back to baseline
    path.lineTo(w * 0.6, midY - h * 0.4); // T wave (medium up)
    path.lineTo(w * 0.7, midY); // back to baseline
    path.lineTo(w, midY); // Flat end

    // Add a glow effect (optional, implies neon look from user image)
    final shadowPaint = Paint()
      ..color = Colors.red.withOpacity(0.5)
      ..strokeWidth = 6.0
      ..style = PaintingStyle.stroke
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);

    canvas.drawPath(path, shadowPaint);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

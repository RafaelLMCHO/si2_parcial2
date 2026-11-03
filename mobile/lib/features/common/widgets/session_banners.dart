import 'package:flutter/material.dart';

import '../../../core/session/session_controller.dart';

class SessionBanners extends StatelessWidget {
  const SessionBanners({super.key, required this.session});

  final SessionController session;

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[];

    if (!session.isOnline) {
      children.add(
        const _Banner(
          icon: Icons.cloud_off,
          text: 'Sin conexion. Puede consultar los datos guardados; las escrituras estan deshabilitadas.',
          background: Color(0xFFFFFBEB),
          border: Color(0xFFFDE68A),
          foreground: Color(0xFF92400E),
        ),
      );
    }

    if (session.isSessionExpired) {
      children.add(
        const _Banner(
          icon: Icons.lock_clock,
          text: 'La sesion local expiro. Reconectese para renovarla; mientras tanto no puede guardar cambios.',
          background: Color(0xFFFFFBEB),
          border: Color(0xFFFDE68A),
          foreground: Color(0xFF92400E),
        ),
      );
    }

    if (session.notice != null) {
      children.add(
        _Banner(
          icon: Icons.info_outline,
          text: session.notice!,
          background: const Color(0xFFFFFBEB),
          border: const Color(0xFFFDE68A),
          foreground: const Color(0xFF92400E),
        ),
      );
    }

    if (session.error != null) {
      children.add(
        _Banner(
          icon: Icons.error_outline,
          text: session.error!,
          background: const Color(0xFFFEF2F2),
          border: const Color(0xFFFECACA),
          foreground: const Color(0xFFB91C1C),
        ),
      );
    }

    if (session.message != null) {
      children.add(
        _Banner(
          icon: Icons.check_circle_outline,
          text: session.message!,
          background: const Color(0xFFF0FDF4),
          border: const Color(0xFFBBF7D0),
          foreground: const Color(0xFF166534),
        ),
      );
    }

    if (children.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        children: [
          for (final child in children)
            Padding(padding: const EdgeInsets.only(bottom: 8), child: child),
        ],
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({
    required this.icon,
    required this.text,
    required this.background,
    required this.border,
    required this.foreground,
  });

  final IconData icon;
  final String text;
  final Color background;
  final Color border;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: background,
        border: Border.all(color: border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: foreground),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(color: foreground, height: 1.4, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

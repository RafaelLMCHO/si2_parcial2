import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'auditoria_controller.dart';

class AuditoriaScreen extends StatefulWidget {
  final ApiClient apiClient;

  const AuditoriaScreen({super.key, required this.apiClient});

  @override
  State<AuditoriaScreen> createState() => _AuditoriaScreenState();
}

class _AuditoriaScreenState extends State<AuditoriaScreen> {
  late final AuditoriaController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AuditoriaController(widget.apiClient);
    _controller.cargarLogs();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Logs de Auditoría (CU-05)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarLogs(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.logs.isEmpty
                      ? const Center(child: Text('No hay registros de auditoría.'))
                      : ListView.separated(
                          itemCount: _controller.logs.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final log = _controller.logs[index];
                            final actor =
                                log['usuario_email'] ??
                                log['actor_tipo'] ??
                                log['usuario_id'] ??
                                'Sistema';
                            final ip = log['ip'] ?? log['ip_origen'] ?? '-';
                            final fecha =
                                log['created_at'] ?? log['ocurrido_en'] ?? '-';
                            final modulo = log['modulo'] ?? log['entidad'] ?? '';
                            return ListTile(
                              leading: const CircleAvatar(
                                child: Icon(Icons.security, size: 20),
                              ),
                              title: Text(log['accion']?.toString() ?? 'Acción'),
                              subtitle: Text(
                                'Actor: $actor\nIP: $ip | Fecha: $fecha',
                              ),
                              trailing: Text(
                                modulo.toString(),
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}


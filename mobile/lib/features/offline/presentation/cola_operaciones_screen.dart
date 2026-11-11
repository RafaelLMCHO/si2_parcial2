import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../../controller/cu30_cola_operaciones_offline_controller.dart';
import '../../../controller/cu31_sincronizar_operaciones_controller.dart';

class ColaOperacionesScreen extends StatefulWidget {
  final ApiClient apiClient;
  final LocalDatabase database;
  final SessionController? session;

  const ColaOperacionesScreen({
    super.key,
    required this.apiClient,
    required this.database,
    this.session,
  });

  @override
  State<ColaOperacionesScreen> createState() => _ColaOperacionesScreenState();
}

class _ColaOperacionesScreenState extends State<ColaOperacionesScreen> {
  late final CU30ColaOperacionesOfflineController _colaCtrl;
  late final CU31SincronizarOperacionesController _syncCtrl;

  @override
  void initState() {
    super.initState();
    _colaCtrl = CU30ColaOperacionesOfflineController(widget.database);
    _syncCtrl = CU31SincronizarOperacionesController(widget.apiClient, widget.database);
    _colaCtrl.cargarCola();
  }

  @override
  void dispose() {
    _colaCtrl.dispose();
    _syncCtrl.dispose();
    super.dispose();
  }

  Future<void> _sincronizar() async {
    final ok = await _syncCtrl.sincronizarLote();
    await _colaCtrl.cargarCola();
    await widget.session?.refreshPendingOperations();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ok
              ? 'Sincronización completada: ${_syncCtrl.confirmados} confirmadas, ${_syncCtrl.conflictos} conflictos.'
              : 'Error o corte de red. Operaciones preservadas en cola.'),
        ),
      );
    }
  }

  Color _badgeColor(String estado) {
    switch (estado) {
      case 'confirmada':
        return Colors.green;
      case 'en_conflicto':
        return Colors.red;
      case 'enviada':
        return Colors.blue;
      default:
        return Colors.orange;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_colaCtrl, _syncCtrl]),
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Cola Outbox y Sincronización (CU-30 y CU-31)'),
            actions: [
              IconButton(icon: const Icon(Icons.refresh), onPressed: _colaCtrl.cargarCola),
            ],
          ),
          body: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.indigo.shade50,
                child: Row(
                  children: [
                    const Icon(Icons.sync_alt, color: Colors.indigo),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Total operaciones en cola local: ${_colaCtrl.operaciones.length}',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: _syncCtrl.loading ? null : _sincronizar,
                      icon: const Icon(Icons.cloud_upload),
                      label: const Text('Sincronizar Lote (RNF05)'),
                    ),
                  ],
                ),
              ),
              if (_syncCtrl.error != null)
                Container(
                  padding: const EdgeInsets.all(8),
                  color: Colors.red.shade100,
                  width: double.infinity,
                  child: Text(_syncCtrl.error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                ),
              Expanded(
                child: _colaCtrl.operaciones.isEmpty
                    ? const Center(child: Text('Todas las operaciones están sincronizadas con el servidor central.'))
                    : ListView.separated(
                        itemCount: _colaCtrl.operaciones.length,
                        separatorBuilder: (_, _) => const Divider(height: 1),
                        itemBuilder: (_, idx) {
                          final op = _colaCtrl.operaciones[idx];
                          final estado = op['estado'] ?? 'pendiente';
                          return ListTile(
                            leading: CircleAvatar(
                              backgroundColor: _badgeColor(estado).withValues(alpha: 0.2),
                              child: Icon(Icons.receipt, color: _badgeColor(estado)),
                            ),
                            title: Text('${op['tipo']} • UUID: ${op['id']}'),
                            subtitle: Text('Fecha local: ${op['creada_en']}'),
                            trailing: Chip(
                              label: Text(estado.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white)),
                              backgroundColor: _badgeColor(estado),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}


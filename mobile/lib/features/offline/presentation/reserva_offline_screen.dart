import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../controller/cu26_registrar_reserva_offline_controller.dart';
import '../../../controller/cu27_bloquear_stock_soft_lock_controller.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/local_database.dart';

class ReservaOfflineScreen extends StatefulWidget {
  final LocalDatabase database;
  final ApiClient? apiClient;
  final String? initialSucursalId;
  final String? initialVarianteId;

  const ReservaOfflineScreen({
    super.key,
    required this.database,
    this.apiClient,
    this.initialSucursalId,
    this.initialVarianteId,
  });

  @override
  State<ReservaOfflineScreen> createState() => _ReservaOfflineScreenState();
}

class _ReservaOfflineScreenState extends State<ReservaOfflineScreen> {
  late final CU26RegistrarReservaOfflineController _controller;
  late final CU27BloquearStockSoftLockController _lockCtrl;
  late final TextEditingController _sucursalCtrl;
  late final TextEditingController _varianteCtrl;
  bool _probador = true;
  bool _aplicarSoftLock = true;

  @override
  void initState() {
    super.initState();
    _sucursalCtrl = TextEditingController(
      text: widget.initialSucursalId?.isNotEmpty == true
          ? widget.initialSucursalId
          : '11111111-1111-1111-1111-111111111101',
    );
    _varianteCtrl = TextEditingController(
      text: widget.initialVarianteId?.isNotEmpty == true
          ? widget.initialVarianteId
          : '22222222-2222-2222-2222-222222222201',
    );
    _controller = CU26RegistrarReservaOfflineController(widget.database);
    _lockCtrl = CU27BloquearStockSoftLockController(
      widget.database,
      apiClient: widget.apiClient,
    )..cargarBloqueosActivos();
  }

  @override
  void dispose() {
    _controller.dispose();
    _lockCtrl.dispose();
    _sucursalCtrl.dispose();
    _varianteCtrl.dispose();
    super.dispose();
  }

  Future<void> _guardarReserva() async {
    final sucursalId = _sucursalCtrl.text.trim();
    final varianteId = _varianteCtrl.text.trim();
    if (_aplicarSoftLock && sucursalId.isNotEmpty && varianteId.isNotEmpty) {
      await _lockCtrl.bloquearStock(
        varianteId: varianteId,
        sucursalId: sucursalId,
        cantidad: 1,
        ttlMinutos: 45,
      );
    }
    await _controller.registrarReservaOffline(
      sucursalId: sucursalId,
      fechaVisita: DateTime.now().add(const Duration(days: 1)),
      probador: _probador,
      items: [
        {'variante_id': varianteId, 'cantidad': 1},
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_controller, _lockCtrl]),
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Reserva Offline (CU-26)'),
            actions: [
              IconButton(
                tooltip: 'Bloqueos activos (${_lockCtrl.bloqueos.length})',
                icon: const Icon(Icons.lock_clock),
                onPressed: () => context.push('/offline/bloqueos'),
              ),
            ],
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Card(
                  color: Colors.amber,
                  child: Padding(
                    padding: EdgeInsets.all(12.0),
                    child: Text(
                      'Modo Desconectado: La reserva se registrará en la cola local con UUID v4 y se confirmará al volver la red.',
                      style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _sucursalCtrl,
                  decoration: const InputDecoration(labelText: 'Sucursal ID', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _varianteCtrl,
                  decoration: const InputDecoration(labelText: 'Variante ID', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  title: const Text('Apartar Probador'),
                  value: _probador,
                  onChanged: (val) => setState(() => _probador = val),
                ),
                SwitchListTile(
                  title: const Text('Aplicar Soft-Lock temporal de 45 min (CU-27)'),
                  subtitle: Text('${_lockCtrl.bloqueos.length} bloqueos activos'),
                  value: _aplicarSoftLock,
                  onChanged: (val) => setState(() => _aplicarSoftLock = val),
                ),
                TextButton.icon(
                  onPressed: () => context.push('/offline/bloqueos'),
                  icon: const Icon(Icons.lock_clock),
                  label: Text('Ver bloqueos activos (${_lockCtrl.bloqueos.length})'),
                ),
                const SizedBox(height: 8),
                if (_controller.reservaUuid != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8)),
                    child: Text('Reserva registrada en cola local:\nUUID: ${_controller.reservaUuid}', style: TextStyle(color: Colors.green.shade900, fontWeight: FontWeight.bold)),
                  ),
                const Spacer(),
                ElevatedButton(
                  onPressed: _controller.loading ? null : _guardarReserva,
                  child: const Text('Guardar Reserva en Cola Local'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}


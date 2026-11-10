import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../controller/cu27_bloquear_stock_soft_lock_controller.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/local_database.dart';

class BloqueosActivosScreen extends StatefulWidget {
  final LocalDatabase database;
  final ApiClient? apiClient;

  const BloqueosActivosScreen({
    super.key,
    required this.database,
    this.apiClient,
  });

  @override
  State<BloqueosActivosScreen> createState() => _BloqueosActivosScreenState();
}

class _BloqueosActivosScreenState extends State<BloqueosActivosScreen> {
  late final CU27BloquearStockSoftLockController _controller;
  final _sucursalCtrl = TextEditingController(
    text: '11111111-1111-1111-1111-111111111101',
  );
  final _varianteCtrl = TextEditingController(
    text: '22222222-2222-2222-2222-222222222201',
  );
  final _cantidadCtrl = TextEditingController(text: '1');
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _controller = CU27BloquearStockSoftLockController(
      widget.database,
      apiClient: widget.apiClient,
    );
    _controller.cargarBloqueosActivos();
    _timer = Timer.periodic(
      const Duration(seconds: 1),
      (_) => _controller.refrescarTtlVisual(),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    _sucursalCtrl.dispose();
    _varianteCtrl.dispose();
    _cantidadCtrl.dispose();
    super.dispose();
  }

  String _formatTtl(int segs) {
    final s = segs < 0 ? 0 : segs;
    final mins = (s ~/ 60).toString().padLeft(2, '0');
    final rem = (s % 60).toString().padLeft(2, '0');
    return '$mins:$rem';
  }

  Future<void> _crearBloqueo() async {
    final sucursalId = _sucursalCtrl.text.trim();
    final varianteId = _varianteCtrl.text.trim();
    final cantidad = int.tryParse(_cantidadCtrl.text.trim()) ?? 1;
    if (sucursalId.isEmpty || varianteId.isEmpty || cantidad < 1) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Complete sucursal, variante y cantidad.')),
      );
      return;
    }

    final ok = await _controller.bloquearStock(
      varianteId: varianteId,
      sucursalId: sucursalId,
      cantidad: cantidad,
      ttlMinutos: 45,
    );
    if (!mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Soft-Lock aplicado con TTL de 45 min.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Bloqueos Activos (CU-27)'),
            actions: [
              IconButton(
                tooltip: 'Actualizar',
                icon: const Icon(Icons.refresh),
                onPressed: _controller.loading
                    ? null
                    : () => _controller.cargarBloqueosActivos(),
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                color: Colors.amber.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        'Aplicar Soft-Lock Temporal (45 min)',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _sucursalCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Sucursal ID',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _varianteCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Variante ID',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _cantidadCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Cantidad',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                      const SizedBox(height: 10),
                      FilledButton.icon(
                        onPressed: _controller.loading ? null : _crearBloqueo,
                        icon: const Icon(Icons.lock_clock),
                        label: const Text('Bloquear Stock (45 min)'),
                      ),
                    ],
                  ),
                ),
              ),
              if (_controller.error != null) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(10),
                  color: Colors.red.shade50,
                  child: Text(
                    _controller.error!,
                    style: TextStyle(color: Colors.red.shade800),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              Text(
                'Soft-Locks Activos (${_controller.bloqueos.length})',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              if (_controller.loading && _controller.bloqueos.isEmpty)
                const Center(child: CircularProgressIndicator())
              else if (_controller.bloqueos.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Center(
                      child: Text('No hay bloqueos de stock activos.'),
                    ),
                  ),
                )
              else
                ..._controller.bloqueos.map((b) {
                  final id = b['id']?.toString() ?? '';
                  final varianteId = b['variante_id']?.toString() ?? '';
                  final sucursalId = b['sucursal_id']?.toString() ?? '';
                  final prenda = b['prenda_nombre']?.toString() ?? varianteId;
                  final sucursal = b['sucursal_nombre']?.toString() ?? sucursalId;
                  final ttl = (b['ttl_restante_segundos'] as num?)?.toInt() ?? 0;
                  final urgent = ttl < 300;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Text(
                                  prenda,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              Chip(
                                label: Text(
                                  _formatTtl(ttl),
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: urgent
                                        ? Colors.red.shade900
                                        : Colors.amber.shade900,
                                  ),
                                ),
                                backgroundColor: urgent
                                    ? Colors.red.shade50
                                    : Colors.amber.shade50,
                              ),
                            ],
                          ),
                          Text('Sucursal: $sucursal | Cant: ${b['cantidad']}'),
                          Text(
                            'Origen: ${b['origen'] ?? 'local'} • ID: $id',
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              OutlinedButton(
                                onPressed: () =>
                                    _controller.liberarBloqueoPorId(id),
                                child: const Text('Liberar'),
                              ),
                              const SizedBox(width: 8),
                              FilledButton.tonal(
                                onPressed: () {
                                  final uri = Uri(
                                    path: '/offline/reserva',
                                    queryParameters: {
                                      'sucursal_id': sucursalId,
                                      'variante_id': varianteId,
                                    },
                                  );
                                  context.push(uri.toString());
                                },
                                child: const Text('Usar en Reserva'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                }),
            ],
          ),
        );
      },
    );
  }
}


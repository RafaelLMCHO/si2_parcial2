import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../controller/cu32_resolver_conflictos_controller.dart';

class ConflictosScreen extends StatefulWidget {
  final ApiClient apiClient;

  const ConflictosScreen({super.key, required this.apiClient});

  @override
  State<ConflictosScreen> createState() => _ConflictosScreenState();
}

class _ConflictosScreenState extends State<ConflictosScreen> {
  late final CU32ResolverConflictosController _controller;

  @override
  void initState() {
    super.initState();
    _controller = CU32ResolverConflictosController(widget.apiClient);
    _controller.cargarConflictos();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _resolver(String id, String decision) async {
    final ok = await _controller.resolverConflicto(
      operacionId: id,
      decision: decision,
      motivo: 'Resolución manual por encargado en tienda',
    );
    if (ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Conflicto $id resuelto con política: $decision')),
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
            title: const Text('Bandeja de Conflictos FIFO (CU-32)'),
            actions: [
              IconButton(icon: const Icon(Icons.refresh), onPressed: _controller.cargarConflictos),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.conflictos.isEmpty
                  ? const Center(child: Text('No hay conflictos de sincronización pendientes.'))
                  : ListView.separated(
                      padding: const EdgeInsets.all(12),
                      itemCount: _controller.conflictos.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 12),
                      itemBuilder: (_, idx) {
                        final c = _controller.conflictos[idx];
                        return Card(
                          elevation: 2,
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('Op: ${c['id']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                                    const Chip(label: Text('EN CONFLICTO', style: TextStyle(color: Colors.white, fontSize: 10)), backgroundColor: Colors.red),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text('Tipo: ${c['tipo']} | Sucursal: ${c['sucursal_nombre'] ?? c['sucursal_id']}'),
                                Text('Causa: ${c['ultimo_error'] ?? 'Stock central insuficiente'}', style: const TextStyle(color: Colors.red)),
                                const SizedBox(height: 12),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    OutlinedButton(
                                      onPressed: () => _resolver(c['id'].toString(), 'rechazar'),
                                      child: const Text('Anular Venta'),
                                    ),
                                    const SizedBox(width: 8),
                                    ElevatedButton(
                                      onPressed: () => _resolver(c['id'].toString(), 'ajustar'),
                                      child: const Text('Ajustar Stock (FIFO)'),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        );
      },
    );
  }
}


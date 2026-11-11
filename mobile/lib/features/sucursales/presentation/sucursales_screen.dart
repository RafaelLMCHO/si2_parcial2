import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'sucursales_controller.dart';

class SucursalesScreen extends StatefulWidget {
  final ApiClient apiClient;

  const SucursalesScreen({super.key, required this.apiClient});

  @override
  State<SucursalesScreen> createState() => _SucursalesScreenState();
}

class _SucursalesScreenState extends State<SucursalesScreen> {
  late final SucursalesController _controller;

  @override
  void initState() {
    super.initState();
    _controller = SucursalesController(widget.apiClient);
    _controller.cargarSucursales();
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
            title: const Text('Gestión de Sucursales (CU-11)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarSucursales(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Error: ${_controller.error}',
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 12),
                            OutlinedButton.icon(
                              onPressed: () => _controller.cargarSucursales(),
                              icon: const Icon(Icons.refresh),
                              label: const Text('Reintentar'),
                            ),
                          ],
                        ),
                      ),
                    )
                  : _controller.sucursales.isEmpty
                      ? const Center(child: Text('No hay sucursales registradas.'))
                      : Column(
                          children: [
                            if (_controller.limitePlan != null)
                              Container(
                                width: double.infinity,
                                margin: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.indigo.shade50,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Colors.indigo.shade100),
                                ),
                                child: Text(
                                  'Sucursales activas: ${_controller.activas} de ${_controller.limitePlan} permitidas por el plan (Total: ${_controller.total})',
                                  style: TextStyle(
                                    color: Colors.indigo.shade900,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            Expanded(
                              child: ListView.separated(
                                itemCount: _controller.sucursales.length,
                                separatorBuilder: (_, _) => const Divider(height: 1),
                                itemBuilder: (context, index) {
                                  final suc = _controller.sucursales[index];
                                  final isActiva = suc['estado'] == 'activa' ||
                                      suc['activo'] == true;
                                  final esMatriz = suc['es_matriz'] == true;
                                  final ciudad = suc['ciudad_nombre']?.toString();
                                  final dir = suc['direccion'] ?? 'Sin dirección';
                                  final ubicacion = ciudad != null && ciudad.isNotEmpty
                                      ? '$ciudad • $dir'
                                      : dir;
                                  return ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: esMatriz
                                          ? Colors.indigo.shade100
                                          : null,
                                      child: Icon(
                                        esMatriz ? Icons.star : Icons.store,
                                      ),
                                    ),
                                    title: Text(
                                      esMatriz
                                          ? '${suc['nombre'] ?? 'Sucursal'} (Matriz)'
                                          : (suc['nombre'] ?? 'Sucursal'),
                                    ),
                                    subtitle: Text(
                                      '$ubicacion\nTel: ${suc['telefono'] ?? '-'}',
                                    ),
                                    isThreeLine: true,
                                    trailing: Chip(
                                      label: Text(isActiva ? 'Abierta' : 'Cerrada'),
                                      backgroundColor: isActiva
                                          ? Colors.green.shade50
                                          : Colors.grey.shade200,
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

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
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.sucursales.isEmpty
                      ? const Center(child: Text('No hay sucursales registradas.'))
                      : ListView.separated(
                          itemCount: _controller.sucursales.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final suc = _controller.sucursales[index];
                            return ListTile(
                              leading: const CircleAvatar(
                                child: Icon(Icons.store),
                              ),
                              title: Text(suc['nombre'] ?? 'Sucursal'),
                              subtitle: Text(
                                '${suc['direccion'] ?? 'Sin dirección'}\nTel: ${suc['telefono'] ?? '-'}',
                              ),
                              trailing: Chip(
                                label: Text(suc['activo'] == true ? 'Abierta' : 'Cerrada'),
                                backgroundColor: suc['activo'] == true ? Colors.green.shade50 : Colors.grey.shade200,
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}


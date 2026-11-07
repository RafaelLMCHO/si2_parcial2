import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'proveedores_controller.dart';

class ProveedoresScreen extends StatefulWidget {
  final ApiClient apiClient;

  const ProveedoresScreen({super.key, required this.apiClient});

  @override
  State<ProveedoresScreen> createState() => _ProveedoresScreenState();
}

class _ProveedoresScreenState extends State<ProveedoresScreen> {
  late final ProveedoresController _controller;

  @override
  void initState() {
    super.initState();
    _controller = ProveedoresController(widget.apiClient);
    _controller.cargarProveedores();
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
            title: const Text('Gestión de Proveedores (CU-15)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarProveedores(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.proveedores.isEmpty
                      ? const Center(child: Text('No hay proveedores registrados.'))
                      : ListView.separated(
                          itemCount: _controller.proveedores.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final prov = _controller.proveedores[index];
                            return ListTile(
                              leading: const CircleAvatar(
                                child: Icon(Icons.local_shipping),
                              ),
                              title: Text(prov['nombre'] ?? 'Proveedor'),
                              subtitle: Text(
                                'Contacto: ${prov['contacto_nombre'] ?? '-'}\nTel: ${prov['telefono'] ?? '-'} | Email: ${prov['email'] ?? '-'}',
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}


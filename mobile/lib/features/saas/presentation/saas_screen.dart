import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'saas_controller.dart';

class SaasScreen extends StatefulWidget {
  final ApiClient apiClient;

  const SaasScreen({super.key, required this.apiClient});

  @override
  State<SaasScreen> createState() => _SaasScreenState();
}

class _SaasScreenState extends State<SaasScreen> {
  late final SaasController _controller;

  @override
  void initState() {
    super.initState();
    _controller = SaasController(widget.apiClient);
    _controller.cargarEmpresas();
    _controller.cargarPlanes();
    _controller.cargarMetricas();
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
            title: const Text('Administración SaaS (CU-06 a CU-09)'),
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Card(
                          color: Colors.indigo.shade50,
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Métricas Globales (CU-09)',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                const SizedBox(height: 8),
                                Text('Total Inquilinos: ${_controller.empresas.length}'),
                                Text('Total Planes Activos: ${_controller.planes.length}'),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        const Text('Empresas Registradas', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        ..._controller.empresas.map((e) => ListTile(
                          leading: const Icon(Icons.business),
                          title: Text(e['nombre'] ?? 'Empresa'),
                          subtitle: Text('Slug: ${e['slug']} | Estado: ${e['estado']}'),
                        )),
                      ],
                    ),
        );
      },
    );
  }
}


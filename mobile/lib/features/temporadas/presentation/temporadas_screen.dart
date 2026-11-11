import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'temporadas_controller.dart';

class TemporadasScreen extends StatefulWidget {
  final ApiClient apiClient;

  const TemporadasScreen({super.key, required this.apiClient});

  @override
  State<TemporadasScreen> createState() => _TemporadasScreenState();
}

class _TemporadasScreenState extends State<TemporadasScreen> {
  late final TemporadasController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TemporadasController(widget.apiClient);
    _controller.cargarTemporadas();
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
            title: const Text('Temporadas y Colecciones (CU-16)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarTemporadas(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
              : _controller.temporadas.isEmpty && _controller.colecciones.isEmpty
                  ? const Center(
                      child: Text('No hay temporadas ni colecciones registradas.'),
                    )
                  : ListView(
                      padding: const EdgeInsets.all(12),
                      children: [
                        if (_controller.temporadas.isNotEmpty) ...[
                          const Padding(
                            padding: EdgeInsets.fromLTRB(4, 4, 4, 8),
                            child: Text(
                              'Temporadas',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          ..._controller.temporadas.map((temp) {
                            final inicio = temp['fecha_inicio']?.toString() ?? '-';
                            final fin = temp['fecha_fin']?.toString() ?? '-';
                            return Card(
                              margin: const EdgeInsets.only(bottom: 8),
                              child: ListTile(
                                leading: const CircleAvatar(
                                  child: Icon(Icons.calendar_today),
                                ),
                                title: Text(temp['nombre']?.toString() ?? 'Temporada'),
                                subtitle: Text('Vigencia: $inicio a $fin'),
                              ),
                            );
                          }),
                          const SizedBox(height: 12),
                        ],
                        if (_controller.colecciones.isNotEmpty) ...[
                          const Padding(
                            padding: EdgeInsets.fromLTRB(4, 4, 4, 8),
                            child: Text(
                              'Colecciones',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          ..._controller.colecciones.map((col) {
                            final anio = col['anio']?.toString() ?? '-';
                            return Card(
                              margin: const EdgeInsets.only(bottom: 8),
                              child: ListTile(
                                leading: const CircleAvatar(
                                  child: Icon(Icons.collections_bookmark),
                                ),
                                title: Text(col['nombre']?.toString() ?? 'Colección'),
                                subtitle: Text('Año: $anio'),
                              ),
                            );
                          }),
                        ],
                      ],
                    ),
        );
      },
    );
  }
}


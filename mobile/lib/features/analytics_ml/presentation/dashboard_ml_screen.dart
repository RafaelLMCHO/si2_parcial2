import 'package:flutter/material.dart';
import '../../../controller/cu35_dashboard_analitico_ml_controller.dart';
import '../../../core/session/session_controller.dart';

class DashboardMlScreen extends StatefulWidget {
  final SessionController session;

  const DashboardMlScreen({super.key, required this.session});

  @override
  State<DashboardMlScreen> createState() => _DashboardMlScreenState();
}

class _DashboardMlScreenState extends State<DashboardMlScreen> {
  late final CU35DashboardAnaliticoMlController _controller;

  @override
  void initState() {
    super.initState();
    _controller = CU35DashboardAnaliticoMlController.fromSession(widget.session);
    _controller.consultarDashboardMl();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-35: Dashboard Analítico ML'),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.consultarDashboardMl(),
          ),
        ],
      ),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          if (_controller.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          final dash = _controller.dashboardMl;
          if (dash == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_controller.error != null) ...[
                      Text(
                        _controller.error!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: Colors.red),
                      ),
                      const SizedBox(height: 12),
                    ],
                    ElevatedButton.icon(
                      onPressed: () => _controller.consultarDashboardMl(),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Cargar Dashboard ML'),
                    ),
                  ],
                ),
              ),
            );
          }

          final rawDemanda = dash['prediccion_demanda'];
          final demanda = rawDemanda is Map
              ? Map<String, dynamic>.from(rawDemanda)
              : const <String, dynamic>{};
          final predicciones = (demanda['predicciones'] as List<dynamic>?) ?? [];
          final rawSeg = dash['segmentacion_clientes'];
          final seg = rawSeg is Map
              ? Map<String, dynamic>.from(rawSeg)
              : const <String, dynamic>{};
          final segmentos = (seg['segmentos'] as List<dynamic>?) ?? [];
          final sintesis = dash['sintesis_ejecutiva']?.toString() ?? '';

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Banner Síntesis Narrativa TTS
              Card(
                color: Colors.indigo.shade900,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.volume_up, color: Colors.amber),
                          SizedBox(width: 8),
                          Text(
                            'Síntesis Ejecutiva por Voz (TTS)',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(
                        sintesis,
                        style: const TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),
              // Sección Supervisada: Demanda
              const Text(
                '1. Predicción de Demanda Futura (Supervisado)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              ...predicciones.whereType<Map>().map((p) {
                final map = Map<String, dynamic>.from(p);
                return Card(
                  child: ListTile(
                    title: Text(
                      map['categoria_nombre']?.toString() ?? 'Categoría',
                    ),
                    subtitle: Text(
                      'Período: ${map['periodo']} | Tendencia: ${map['tendencia']}',
                    ),
                    trailing: Text(
                      '${map['demanda_estimada']} un.',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.indigo,
                        fontSize: 16,
                      ),
                    ),
                  ),
                );
              }),

              const SizedBox(height: 20),
              // Sección No Supervisada: Segmentación
              const Text(
                '2. Segmentación K-Means de Clientes (No Supervisado)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              ...segmentos.whereType<Map>().map((s) {
                final map = Map<String, dynamic>.from(s);
                return Card(
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
                                map['nombre']?.toString() ?? 'Segmento',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                            Chip(
                              label: Text('${map['porcentaje_base']}% base'),
                              backgroundColor: Colors.green.shade50,
                            ),
                          ],
                        ),
                        Text(
                          map['descripcion']?.toString() ?? '',
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Estrategia: ${map['estrategia_recomendada'] ?? ''}',
                          style: const TextStyle(fontSize: 11, color: Colors.indigo),
                        ),
                      ],
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }
}

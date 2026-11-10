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
  late CU35DashboardAnaliticoMlController _controller;

  @override
  void initState() {
    super.initState();
    _controller = CU35DashboardAnaliticoMlController.fromSession(widget.session);
    _controller.consultarDashboardMl();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-35: Dashboard Analítico ML'),
        actions: [
          IconButton(
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
              child: ElevatedButton(
                onPressed: () => _controller.consultarDashboardMl(),
                child: const Text('Cargar Dashboard ML'),
              ),
            );
          }

          final demanda = dash['prediccion_demanda'] as Map<String, dynamic>? ?? {};
          final predicciones = (demanda['predicciones'] as List<dynamic>?) ?? [];
          final seg = dash['segmentacion_clientes'] as Map<String, dynamic>? ?? {};
          final segmentos = (seg['segmentos'] as List<dynamic>?) ?? [];
          final sintesis = dash['sintesis_ejecutiva'] as String? ?? '';

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
                      Row(
                        children: const [
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
              ...predicciones.map((p) {
                final map = p as Map<String, dynamic>;
                return Card(
                  child: ListTile(
                    title: Text(map['categoria_nombre'] ?? 'Categoría'),
                    subtitle: Text('Período: ${map['periodo']} | Tendencia: ${map['tendencia']}'),
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
              ...segmentos.map((s) {
                final map = s as Map<String, dynamic>;
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              map['nombre'] ?? 'Segmento',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            Chip(
                              label: Text('${map['porcentaje_base']}% base'),
                              backgroundColor: Colors.green.shade50,
                            ),
                          ],
                        ),
                        Text(
                          map['descripcion'] ?? '',
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


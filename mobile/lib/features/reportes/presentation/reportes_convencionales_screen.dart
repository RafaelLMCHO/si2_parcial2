import 'package:flutter/material.dart';
import '../../../controller/cu33_reportes_convencionales_controller.dart';
import '../../../core/session/session_controller.dart';

class ReportesConvencionalesScreen extends StatefulWidget {
  final SessionController session;

  const ReportesConvencionalesScreen({super.key, required this.session});

  @override
  State<ReportesConvencionalesScreen> createState() =>
      _ReportesConvencionalesScreenState();
}

class _ReportesConvencionalesScreenState
    extends State<ReportesConvencionalesScreen>
    with SingleTickerProviderStateMixin {
  late final CU33ReportesConvencionalesController _controller;
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _controller =
        CU33ReportesConvencionalesController.fromSession(widget.session);
    _tabController = TabController(length: 3, vsync: this);
    _controller.obtenerDashboard();
  }

  @override
  void dispose() {
    _controller.dispose();
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-33: Reportes Convencionales'),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.obtenerDashboard(),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Resumen'),
            Tab(text: 'Rotación'),
            Tab(text: 'Top Prendas'),
          ],
        ),
      ),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          if (_controller.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          final dash = _controller.dashboard;
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
                      onPressed: () => _controller.obtenerDashboard(),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Cargar Dashboard'),
                    ),
                  ],
                ),
              ),
            );
          }

          final rawKpis = dash['kpis'];
          final kpis = rawKpis is Map
              ? Map<String, dynamic>.from(rawKpis)
              : const <String, dynamic>{};
          final topPrendas = (dash['top_prendas'] as List<dynamic>?) ?? [];
          final rawRotacion = dash['rotacion_resumen'];
          final rotacion = rawRotacion is Map
              ? Map<String, dynamic>.from(rawRotacion)
              : const <String, dynamic>{};
          final sucursales = (dash['ventas_por_sucursal'] as List<dynamic>?) ?? [];

          return TabBarView(
            controller: _tabController,
            children: [
              // Tab 1: Resumen y KPIs
              RefreshIndicator(
                onRefresh: () => _controller.obtenerDashboard(),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: _buildKpiCard(
                            'Ventas Hoy',
                            'Bs. ${kpis['ventas_hoy'] ?? 0}',
                            Colors.indigo,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildKpiCard(
                            'Ventas Mes',
                            'Bs. ${kpis['ventas_mes'] ?? 0}',
                            Colors.green,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: _buildKpiCard(
                            'Stock Total',
                            '${kpis['stock_total_unidades'] ?? 0} un.',
                            Colors.blue,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildKpiCard(
                            'Reservas Activas',
                            '${kpis['reservas_activas'] ?? 0}',
                            Colors.orange,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Ventas por Sucursal',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 8),
                    ...sucursales.whereType<Map>().map((s) {
                      final map = Map<String, dynamic>.from(s);
                      return Card(
                        child: ListTile(
                          title: Text(
                            map['sucursal_nombre']?.toString() ?? 'Sucursal',
                          ),
                          subtitle: Text('${map['operaciones'] ?? 0} operaciones'),
                          trailing: Text(
                            'Bs. ${map['total_ventas'] ?? 0}',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.green,
                            ),
                          ),
                        ),
                      );
                    }),
                  ],
                ),
              ),

              // Tab 2: Rotación
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    color: Colors.amber.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          const Icon(Icons.warning_amber, color: Colors.amber),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Prendas con stock crítico: ${rotacion['stock_critico'] ?? 0}',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),

              // Tab 3: Top Prendas
              ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: topPrendas.length,
                itemBuilder: (context, idx) {
                  final raw = topPrendas[idx];
                  if (raw is! Map) return const SizedBox.shrink();
                  final tp = Map<String, dynamic>.from(raw);
                  return Card(
                    child: ListTile(
                      leading: CircleAvatar(
                        child: Text('${tp['ranking'] ?? (idx + 1)}'),
                      ),
                      title: Text(tp['nombre']?.toString() ?? 'Prenda'),
                      subtitle: Text(
                        '${tp['categoria'] ?? ''} - ${tp['cantidad_vendida'] ?? 0} vendidas',
                      ),
                      trailing: Text(
                        'Bs. ${tp['total_ingresos'] ?? 0}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.green,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildKpiCard(String label, String value, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

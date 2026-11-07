import 'package:flutter/material.dart';
import '../../../controller/cu34_reporte_generativo_ia_controller.dart';
import '../../../core/session/session_controller.dart';

class ReporteIaScreen extends StatefulWidget {
  final SessionController session;

  const ReporteIaScreen({super.key, required this.session});

  @override
  State<ReporteIaScreen> createState() => _ReporteIaScreenState();
}

class _ReporteIaScreenState extends State<ReporteIaScreen> {
  late CU34ReporteGenerativoIaController _controller;
  final TextEditingController _promptController = TextEditingController();

  final List<String> _whitelistChips = [
    'Mostrame las ventas de septiembre agrupadas por sucursal',
    '¿Cuáles fueron los diez productos más vendidos?',
    'Generá un gráfico de ventas por semana',
    'Rotación y stock crítico por categoría',
  ];

  @override
  void initState() {
    super.initState();
    _controller = CU34ReporteGenerativoIaController.fromSession(widget.session);
  }

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  void _enviarConsulta(String prompt) {
    if (prompt.trim().isEmpty) return;
    _promptController.text = prompt;
    _controller.solicitarReporteIa(prompt: prompt);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CU-34: Reporte IA Generativo'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Seguridad Whitelist (BR-08)'),
                  content: const Text(
                    'Este módulo utiliza un motor LLM restringido a una lista blanca de consultas seguras sobre datos reales, con aislamiento estricto por empresa_id.',
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Entendido'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          final reporte = _controller.reporte;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Barra de Entrada
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Pregunta a la IA sobre tu negocio',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: _promptController,
                        decoration: InputDecoration(
                          hintText: 'Ej: Ventas de septiembre por sucursal...',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          suffixIcon: IconButton(
                            icon: const Icon(Icons.send, color: Colors.purple),
                            onPressed: () => _enviarConsulta(_promptController.text),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Consultas Frecuentes (Whitelist):',
                        style: TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: _whitelistChips.map((chip) {
                          return ActionChip(
                            label: Text(chip, style: const TextStyle(fontSize: 10)),
                            backgroundColor: Colors.purple.shade50,
                            onPressed: () => _enviarConsulta(chip),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),

              if (_controller.isLoading) ...[
                const SizedBox(height: 32),
                const Center(child: CircularProgressIndicator()),
                const SizedBox(height: 12),
                const Center(
                  child: Text(
                    'Interpretando consulta y consultando datos reales...',
                    style: TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),
              ],

              if (_controller.error != null) ...[
                const SizedBox(height: 16),
                Card(
                  color: Colors.red.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      _controller.error!,
                      style: const TextStyle(color: Colors.red, fontSize: 12),
                    ),
                  ),
                ),
              ],

              if (reporte != null && !_controller.isLoading) ...[
                const SizedBox(height: 16),
                // Tarjeta de Resumen Ejecutivo
                Card(
                  color: Colors.purple.shade900,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          reporte['titulo'] ?? 'Reporte IA',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          reporte['resumen_ejecutivo'] ?? '',
                          style: const TextStyle(color: Colors.white70, fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),
                // Filas de Datos
                const Text(
                  'Datos Generados:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ...((reporte['filas'] as List<dynamic>?) ?? []).map((f) {
                  final map = f as Map<String, dynamic>;
                  final keys = map.keys.toList();
                  final titleKey = keys.isNotEmpty ? keys[0] : '';
                  final valKey = keys.length > 1 ? keys[1] : '';

                  return Card(
                    child: ListTile(
                      title: Text('${map[titleKey]}'),
                      trailing: Text(
                        '${map[valKey]}',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  );
                }),
              ],
            ],
          );
        },
      ),
    );
  }
}


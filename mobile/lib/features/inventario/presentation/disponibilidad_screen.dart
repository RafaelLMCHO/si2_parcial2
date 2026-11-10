import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/local_database.dart';
import '../data/inventario_models.dart';

class DisponibilidadScreen extends StatefulWidget {
  final String prendaId;
  final String prendaNombre;
  final ApiClient apiClient;
  final LocalDatabase localDb;

  const DisponibilidadScreen({
    super.key,
    required this.prendaId,
    required this.prendaNombre,
    required this.apiClient,
    required this.localDb,
  });

  @override
  State<DisponibilidadScreen> createState() => _DisponibilidadScreenState();
}

class _DisponibilidadScreenState extends State<DisponibilidadScreen> {
  DisponibilidadPrenda? _datos;
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargarDisponibilidad();
  }

  Future<void> _cargarDisponibilidad() async {
    setState(() {
      _cargando = true;
      _error = null;
    });

    if (widget.prendaId.trim().isEmpty) {
      setState(() {
        _cargando = false;
        _error = 'Seleccione una prenda del catalogo para consultar su disponibilidad por tienda.';
        _datos = null;
      });
      return;
    }

    try {
      final dynamic response = await widget.apiClient.get(
        '/inventario/prendas/${widget.prendaId}/disponibilidad',
      );
      final datos = DisponibilidadPrenda.fromJson(
        Map<String, dynamic>.from(response as Map),
      );
      if (!mounted) return;
      setState(() {
        _datos = datos;
        _cargando = false;
      });
    } catch (e) {
      // Fallback a SQLite local (CU-18)
      final locales = await widget.localDb.listarExistenciasLocales();
      final actualizadoEn = locales.isNotEmpty
          ? (locales.first['actualizado_en']?.toString() ?? DateTime.now().toIso8601String())
          : DateTime.now().toIso8601String();
      if (!mounted) return;
      setState(() {
        _error = 'No se pudo contactar al servidor; usando respaldo local ($e).';
        _datos = DisponibilidadPrenda(
          prendaId: widget.prendaId,
          agotadoEnTodas: locales.isEmpty,
          actualizadoEn: actualizadoEn,
          sucursales: [],
          esLocal: true,
        );
        _cargando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Disponibilidad: ${widget.prendaNombre}'),
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _cargarDisponibilidad,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(10),
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        border: Border.all(color: Colors.red.shade200),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        _error!,
                        style: TextStyle(color: Colors.red.shade800, fontSize: 12),
                      ),
                    ),
                  ],
                  // Alerta Offline con texto exacto de la especificación CU-18
                  if (_datos?.esLocal == true) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        border: Border.all(color: Colors.amber.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '⚠️ Stock local: las existencias mostradas corresponden al último balance descargado y pueden haber variado',
                            style: TextStyle(
                              color: Colors.brown,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                          if (_datos?.actualizadoEn != null)
                            Text(
                              'Último balance: ${_datos!.actualizadoEn.split('T').first}',
                              style: TextStyle(color: Colors.brown.shade400, fontSize: 11),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Agotado en todas las tiendas físicas (Flujo 4.a)
                  if (_datos?.agotadoEnTodas == true) ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        border: Border.all(color: Colors.red.shade200),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Center(
                        child: Text(
                          'Agotado en todas las tiendas físicas',
                          style: TextStyle(
                            color: Colors.red,
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                      ),
                    ),
                  ] else if (_datos != null && _datos!.sucursales.isNotEmpty) ...[
                    ..._datos!.sucursales.map((suc) => Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  suc.nombre,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                Text(
                                  '📍 ${suc.ciudad} - ${suc.direccion}',
                                  style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                                ),
                                const Divider(),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 4,
                                  children: suc.variantes.map((v) {
                                    final tieneStock = v.stockDisponible > 0;
                                    return Chip(
                                      backgroundColor: tieneStock ? Colors.green.shade50 : Colors.grey.shade100,
                                      side: BorderSide(color: tieneStock ? Colors.green.shade300 : Colors.grey.shade300),
                                      label: Text(
                                        '${v.talla}/${v.color}: ${v.stockDisponible} disp.',
                                        style: TextStyle(
                                          color: tieneStock ? Colors.green.shade900 : Colors.grey.shade600,
                                          fontSize: 12,
                                        ),
                                      ),
                                    );
                                  }).toList(),
                                )
                              ],
                            ),
                          ),
                        )),
                  ] else ...[
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: Text('No hay datos de existencias físicas disponibles.'),
                      ),
                    ),
                  ]
                ],
              ),
            ),
    );
  }
}


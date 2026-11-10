import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';

class ReservasScreen extends StatefulWidget {
  final ApiClient apiClient;
  final bool esEncargado;

  const ReservasScreen({
    super.key,
    required this.apiClient,
    this.esEncargado = false,
  });

  @override
  State<ReservasScreen> createState() => _ReservasScreenState();
}

class _ReservasScreenState extends State<ReservasScreen> {
  List<dynamic> _reservas = [];
  bool _cargando = true;
  String? _mensaje;

  @override
  void initState() {
    super.initState();
    _cargarReservas();
  }

  Future<void> _cargarReservas() async {
    setState(() {
      _cargando = true;
      _mensaje = null;
    });
    try {
      final endpoint = widget.esEncargado ? '/reservas/por-preparar' : '/reservas/mis-reservas';
      final res = await widget.apiClient.get(endpoint);
      if (!mounted) return;
      setState(() {
        _reservas = (res['items'] as List<dynamic>? ?? []);
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _mensaje = 'Error al cargar reservas: $e';
      });
    }
  }

  Future<void> _cancelarReserva(String reservaId) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancelar Reserva'),
        content: const Text('¿Desea cancelar esta reserva? El stock se devolverá de inmediato.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('No')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sí, cancelar')),
        ],
      ),
    );

    if (confirmar != true) return;

    try {
      await widget.apiClient.post('/reservas/$reservaId/cancelar', {});
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reserva cancelada con éxito')),
      );
      _cargarReservas();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al cancelar: $e')),
      );
    }
  }

  Future<void> _prepararReserva(String reservaId) async {
    final probadorCtrl = TextEditingController(text: 'Probador 1');
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Preparar Reserva en Tienda'),
        content: TextField(
          controller: probadorCtrl,
          decoration: const InputDecoration(labelText: 'Probador Asignado'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Confirmar')),
        ],
      ),
    );

    if (confirmar != true) return;

    try {
      await widget.apiClient.post('/reservas/$reservaId/preparar', {
        'probador': probadorCtrl.text.trim(),
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reserva preparada. Cliente notificado.')),
      );
      _cargarReservas();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al preparar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.esEncargado ? 'Reservas por Preparar' : 'Mis Reservas'),
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _mensaje != null
              ? Center(child: Text(_mensaje!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _cargarReservas,
                  child: _reservas.isEmpty
                      ? const Center(child: Text('No hay reservas activas.'))
                      : ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _reservas.length,
                          itemBuilder: (ctx, index) {
                            final r = _reservas[index];
                            final items = (r['items'] as List<dynamic>? ?? []);
                            final estado = r['estado'] ?? 'pendiente';

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              child: Padding(
                                padding: const EdgeInsets.all(14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      r['codigo'] ?? '',
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                    ),
                                    Chip(
                                      label: Text(estado, style: const TextStyle(fontSize: 11)),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text('Visita: ${r['fecha_visita'] ?? ''}'),
                                if (r['probador'] != null)
                                  Text('Probador: ${r['probador']}', style: const TextStyle(color: Colors.blue)),
                                const Divider(),
                                ...items.map((it) => Text('• ${it['prenda_nombre']} (${it['talla']}/${it['color']}) x${it['cantidad']}')),
                                const SizedBox(height: 10),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        if (estado == 'pendiente_preparacion' && !widget.esEncargado)
                                          OutlinedButton(
                                            onPressed: () => _cancelarReserva(r['id']),
                                            style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                                            child: const Text('Cancelar'),
                                          ),
                                        if (widget.esEncargado && estado == 'pendiente_preparacion')
                                          ElevatedButton(
                                            onPressed: () => _prepararReserva(r['id']),
                                            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                            child: const Text('✓ Preparada'),
                                          ),
                                      ],
                                    )
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                  ),
    );
  }
}


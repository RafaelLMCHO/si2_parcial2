import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'pagos_controller.dart';

class PagosScreen extends StatefulWidget {
  final ApiClient apiClient;
  final String? ventaId;

  const PagosScreen({super.key, required this.apiClient, this.ventaId});

  @override
  State<PagosScreen> createState() => _PagosScreenState();
}

class _PagosScreenState extends State<PagosScreen> {
  late final PagosController _controller;
  final TextEditingController _ventaIdCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _controller = PagosController(widget.apiClient);
    if (widget.ventaId != null) {
      _ventaIdCtrl.text = widget.ventaId!;
      _crearIntencion();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _ventaIdCtrl.dispose();
    super.dispose();
  }

  Future<void> _crearIntencion() async {
    final vId = _ventaIdCtrl.text.trim();
    if (vId.isEmpty) return;
    await _controller.crearIntencionPago(ventaId: vId);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Pasarela de Pagos (CU-24)'),
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: _ventaIdCtrl,
                  decoration: const InputDecoration(
                    labelText: 'ID de Venta / Orden',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _controller.loading ? null : _crearIntencion,
                  icon: const Icon(Icons.payment),
                  label: const Text('Generar Intención de Pago'),
                ),
                const SizedBox(height: 20),
                if (_controller.loading)
                  const Center(child: CircularProgressIndicator())
                else if (_controller.error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Text(
                      _controller.error!,
                      style: TextStyle(color: Colors.red.shade800),
                    ),
                  )
                else if (_controller.pagoActual != null)
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Estado: ${_controller.pagoActual!['estado'] ?? 'creado'}',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          Text('ID Pago: ${_controller.pagoActual!['id'] ?? _controller.pagoActual!['payment_intent_id']}'),
                          const SizedBox(height: 4),
                          Text('Monto: BOB ${_controller.pagoActual!['monto']}'),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                            onPressed: () {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Pago confirmado con Stripe')),
                              );
                            },
                            child: const Text('Confirmar Pago con Tarjeta'),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}


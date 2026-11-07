import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';

class CheckoutScreen extends StatefulWidget {
  final ApiClient apiClient;

  const CheckoutScreen({super.key, required this.apiClient});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  Map<String, dynamic>? _carrito;
  bool _cargando = true;
  String _tipoEntrega = 'envio';
  bool _procesandoPago = false;

  @override
  void initState() {
    super.initState();
    _cargarCarrito();
  }

  Future<void> _cargarCarrito() async {
    setState(() => _cargando = true);
    try {
      final res = await widget.apiClient.get('/carrito');
      setState(() {
        _carrito = res;
        _cargando = false;
      });
    } catch (e) {
      setState(() => _cargando = false);
    }
  }

  Future<void> _realizarCompra() async {
    setState(() => _procesandoPago = true);
    try {
      // 1. Crear orden
      final orden = await widget.apiClient.post('/checkout/ordenes', {
        'tipo_entrega': _tipoEntrega,
        'sucursal_id': '11111111-1111-1111-1111-111111111101',
      });

      // 2. Crear intención en Stripe (CU-24)
      final ventaId = orden['venta_id'];
      await widget.apiClient.post('/pagos/intencion', {'venta_id': ventaId});

      setState(() => _procesandoPago = false);
      if (!mounted) return;

      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('¡Pago Exitoso!'),
          content: Text('Orden N° ${orden['numero']} confirmada y regularizada en inventario.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                _cargarCarrito();
              },
              child: const Text('Aceptar'),
            ),
          ],
        ),
      );
    } catch (e) {
      setState(() => _procesandoPago = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Fallo en la compra: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = (_carrito?['items'] as List<dynamic>? ?? []);
    final total = _carrito?['total'] ?? 0.0;

    return Scaffold(
      appBar: AppBar(title: const Text('Carrito y Checkout')),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : items.isEmpty
              ? const Center(child: Text('El carrito de compras está vacío.'))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    ...items.map((it) => Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: ListTile(
                            title: Text(it['prenda_nombre'] ?? ''),
                            subtitle: Text('${it['talla']}/${it['color']} • Cant: ${it['cantidad']}'),
                            trailing: Text('${it['subtotal']} BOB', style: const TextStyle(fontWeight: FontWeight.bold)),
                          ),
                        )),
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Opciones de Entrega', style: TextStyle(fontWeight: FontWeight.bold)),
                            RadioListTile<String>(
                              title: const Text('Envío a domicilio (+20 BOB)'),
                              value: 'envio',
                              groupValue: _tipoEntrega,
                              onChanged: (val) => setState(() => _tipoEntrega = val!),
                            ),
                            RadioListTile<String>(
                              title: const Text('Recojo en sucursal física (Gratis)'),
                              value: 'recojo',
                              groupValue: _tipoEntrega,
                              onChanged: (val) => setState(() => _tipoEntrega = val!),
                            ),
                            const Divider(),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.between,
                              children: [
                                const Text('Total Estimado:', style: TextStyle(fontSize: 16)),
                                Text(
                                  '${_tipoEntrega == 'envio' ? total + 20 : total} BOB',
                                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.blue),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _procesandoPago ? null : _realizarCompra,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        backgroundColor: Colors.blue.shade700,
                      ),
                      child: _procesandoPago
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('PAGAR CON TARJETA (STRIPE SANDBOX)', style: TextStyle(fontSize: 15, color: Colors.white)),
                    ),
                  ],
                ),
    );
  }
}


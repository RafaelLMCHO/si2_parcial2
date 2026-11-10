import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';

class PosScreen extends StatefulWidget {
  final ApiClient apiClient;

  const PosScreen({super.key, required this.apiClient});

  @override
  State<PosScreen> createState() => _PosScreenState();
}

class _PosScreenState extends State<PosScreen> {
  final TextEditingController _barcodeCtrl = TextEditingController();
  final TextEditingController _montoCtrl = TextEditingController();
  final List<Map<String, dynamic>> _lineas = [];
  String _metodoPago = 'efectivo';
  double _montoRecibido = 0;
  bool _procesando = false;

  double get _total {
    double subtotal = 0;
    for (var l in _lineas) {
      subtotal += (l['precio_unitario'] as double) * (l['cantidad'] as int);
    }
    return subtotal * 1.13; // IVA 13%
  }

  double get _cambio => _montoRecibido - _total;

  Future<void> _escanearCodigo() async {
    final codigo = _barcodeCtrl.text.trim();
    if (codigo.isEmpty) return;

    try {
      final res = await widget.apiClient.get('/pos/variantes/barcode/$codigo');
      setState(() {
        final existing = _lineas.indexWhere((l) => l['variante_id'] == res['variante_id']);
        if (existing >= 0) {
          _lineas[existing]['cantidad'] = (_lineas[existing]['cantidad'] as int) + 1;
        } else {
          _lineas.add({
            'variante_id': res['variante_id'],
            'sku': res['sku'],
            'prenda_nombre': res['prenda_nombre'],
            'talla': res['talla'],
            'color': res['color'],
            'precio_unitario': (res['precio_venta'] as num).toDouble(),
            'cantidad': 1,
          });
        }
        _barcodeCtrl.clear();
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Artículo no encontrado: $e')),
      );
    }
  }

  Future<void> _cobrarVenta() async {
    setState(() => _procesando = true);
    final idempotencyKey = DateTime.now().millisecondsSinceEpoch.toString();

    try {
      final res = await widget.apiClient.post('/pos/ventas', {
        'idempotency_key': idempotencyKey,
        'items': _lineas.map((l) => {
              'variante_id': l['variante_id'],
              'cantidad': l['cantidad'],
            }).toList(),
        'cliente': {'tipo': 'consumidor_final'},
        'pago': {
          'metodo': _metodoPago,
          'monto_recibido': _metodoPago == 'efectivo' ? _montoRecibido : null,
        },
      });

      setState(() {
        _procesando = false;
        _lineas.clear();
        _montoCtrl.clear();
        _montoRecibido = 0;
      });

      if (!mounted) return;
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('¡Venta Registrada!'),
          content: Text(
            'Venta N° ${res['numero']} asentada correctamente.\nCambio: ${res['cambio']} BOB',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Aceptar')),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _procesando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al cobrar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Punto de Venta POS Móvil')),
      body: Column(
        children: [
          // Barra de escaneo / entrada
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _barcodeCtrl,
                    decoration: const InputDecoration(
                      hintText: 'Código de barras o SKU...',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 12),
                    ),
                    onSubmitted: (_) => _escanearCodigo(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _escanearCodigo,
                  icon: const Icon(Icons.qr_code_scanner),
                ),
              ],
            ),
          ),

          // Lista de prendas en venta
          Expanded(
            child: _lineas.isEmpty
                ? const Center(child: Text('Escanee prendas para añadir a la venta.'))
                : ListView.builder(
                    itemCount: _lineas.length,
                    itemBuilder: (ctx, i) {
                      final item = _lineas[i];
                      return ListTile(
                        title: Text('${item['prenda_nombre']} (${item['talla']}/${item['color']})'),
                        subtitle: Text('${item['precio_unitario']} BOB x ${item['cantidad']}'),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.remove_circle_outline),
                              onPressed: () {
                                setState(() {
                                  if ((item['cantidad'] as int) > 1) {
                                    item['cantidad'] = (item['cantidad'] as int) - 1;
                                  } else {
                                    _lineas.removeAt(i);
                                  }
                                });
                              },
                            ),
                            Text('${item['cantidad']}'),
                            IconButton(
                              icon: const Icon(Icons.add_circle_outline),
                              onPressed: () {
                                setState(() {
                                  item['cantidad'] = (item['cantidad'] as int) + 1;
                                });
                              },
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),

          // Total y Cobro
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              border: Border(top: BorderSide(color: Colors.grey.shade300)),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('TOTAL (IVA Inc.):', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    Text(
                      '${_total.toStringAsFixed(2)} BOB',
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.green),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    ChoiceChip(
                      label: const Text('Efectivo'),
                      selected: _metodoPago == 'efectivo',
                      onSelected: (_) => setState(() => _metodoPago = 'efectivo'),
                    ),
                    const SizedBox(width: 6),
                    ChoiceChip(
                      label: const Text('Tarjeta'),
                      selected: _metodoPago == 'tarjeta',
                      onSelected: (_) => setState(() => _metodoPago = 'tarjeta'),
                    ),
                    const SizedBox(width: 6),
                    ChoiceChip(
                      label: const Text('QR'),
                      selected: _metodoPago == 'qr',
                      onSelected: (_) => setState(() => _metodoPago = 'qr'),
                    ),
                  ],
                ),
                if (_metodoPago == 'efectivo') ...[
                  const SizedBox(height: 8),
                  TextField(
                    controller: _montoCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Monto Recibido',
                      suffixText: _cambio >= 0
                          ? 'Cambio: ${_cambio.toStringAsFixed(2)} BOB'
                          : 'Falta: ${(-_cambio).toStringAsFixed(2)} BOB',
                      suffixStyle: TextStyle(
                        color: _cambio >= 0 ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    onChanged: (val) {
                      setState(() {
                        _montoRecibido = double.tryParse(val) ?? 0;
                      });
                    },
                  ),
                ],
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: (_lineas.isEmpty || (_metodoPago == 'efectivo' && _cambio < 0) || _procesando)
                        ? null
                        : _cobrarVenta,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green.shade700),
                    child: _procesando
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text('COBRAR EN CAJA', style: TextStyle(fontSize: 16, color: Colors.white)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


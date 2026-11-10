import 'package:flutter/material.dart';
import '../../../core/storage/local_database.dart';
import '../../../controller/cu27_bloquear_stock_soft_lock_controller.dart';
import '../../../controller/cu28_venta_contado_offline_controller.dart';

class VentaOfflineScreen extends StatefulWidget {
  final LocalDatabase database;
  final String usuarioId;

  const VentaOfflineScreen({
    super.key,
    required this.database,
    this.usuarioId = 'cajero-01',
  });

  @override
  State<VentaOfflineScreen> createState() => _VentaOfflineScreenState();
}

class _VentaOfflineScreenState extends State<VentaOfflineScreen> {
  late final CU27BloquearStockSoftLockController _lockCtrl;
  late final CU28VentaContadoOfflineController _ventaCtrl;

  final TextEditingController _clienteCtrl = TextEditingController(text: 'Consumidor Final');
  final TextEditingController _nitCtrl = TextEditingController(text: '0');
  final List<Map<String, dynamic>> _lineas = [];
  String _metodoPago = 'efectivo';

  @override
  void initState() {
    super.initState();
    _lockCtrl = CU27BloquearStockSoftLockController(widget.database);
    _ventaCtrl = CU28VentaContadoOfflineController(widget.database);

    // Ítem inicial de prueba
    _lineas.add({
      'variante_id': '22222222-2222-2222-2222-222222222201',
      'sku': 'CAMISA-L',
      'prenda_nombre': 'Camisa de Lino',
      'talla': 'L',
      'color': 'Blanco',
      'cantidad': 1,
      'precio_unitario': 180.0,
    });
  }

  @override
  void dispose() {
    _lockCtrl.dispose();
    _ventaCtrl.dispose();
    _clienteCtrl.dispose();
    _nitCtrl.dispose();
    super.dispose();
  }

  double get _total => _lineas.fold(0.0, (acc, item) => acc + (item['cantidad'] as int) * (item['precio_unitario'] as double));

  Future<void> _confirmarVentaOffline() async {
    // 1. Aplicar Soft-Lock con TTL 45 min (CU-27)
    for (var l in _lineas) {
      await _lockCtrl.bloquearStock(
        varianteId: l['variante_id'],
        sucursalId: '11111111-1111-1111-1111-111111111101',
        cantidad: l['cantidad'],
        ttlMinutos: 45,
      );
    }

    // 2. Registrar venta de contado en outbox (CU-28)
    final res = await _ventaCtrl.registrarVentaOffline(
      sucursalId: '11111111-1111-1111-1111-111111111101',
      usuarioId: widget.usuarioId,
      clienteNombre: _clienteCtrl.text,
      clienteDocumento: _nitCtrl.text,
      lineas: _lineas,
      total: _total,
      metodoPago: _metodoPago,
    );

    if (res != null && mounted) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Comprobante Preliminar Emitido'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                color: Colors.amber.shade100,
                child: const Text(
                  'VENTA EN MODO OFFLINE - PENDIENTE DE SINCRONIZACIÓN',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
              const SizedBox(height: 12),
              Text('UUID: ${res['uuid']}'),
              Text('Cliente: ${res['cliente_nombre']}'),
              Text('Total: BOB ${res['total']}'),
              Text('Forma de Pago: ${res['forma_pago']}'),
              const SizedBox(height: 8),
              const Text('Stock local bloqueado con TTL de 45 minutos (CU-27).'),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Aceptar')),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Venta Offline (CU-27 y CU-28)'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: Colors.amber.shade50, border: Border.all(color: Colors.amber)),
              child: const Row(
                children: [
                  Icon(Icons.wifi_off, color: Colors.amber),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text('Contingencia Offline: Solo cobros en efectivo (Sección 7.2) con ticket preliminar (BR-11).', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _clienteCtrl,
              decoration: const InputDecoration(labelText: 'Cliente / Razón Social', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _nitCtrl,
              decoration: const InputDecoration(labelText: 'NIT / CI', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _metodoPago,
              decoration: const InputDecoration(labelText: 'Forma de Pago', border: OutlineInputBorder()),
              items: const [
                DropdownMenuItem(value: 'efectivo', child: Text('Efectivo / Contado (Permitido)')),
                DropdownMenuItem(value: 'tarjeta', child: Text('Tarjeta / Electrónico (Bloqueado offline)')),
              ],
              onChanged: (val) => setState(() => _metodoPago = val ?? 'efectivo'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _lineas.length,
                itemBuilder: (_, idx) {
                  final it = _lineas[idx];
                  return ListTile(
                    title: Text('${it['prenda_nombre']} (${it['talla']}/${it['color']})'),
                    subtitle: Text('SKU: ${it['sku']} • Cant: ${it['cantidad']}'),
                    trailing: Text('BOB ${it['precio_unitario'] * it['cantidad']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  );
                },
              ),
            ),
            if (_ventaCtrl.error != null)
              Text(_ventaCtrl.error!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total a Cobrar:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                Text('BOB $_total', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.indigo)),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: _confirmarVentaOffline,
                icon: const Icon(Icons.receipt_long),
                label: const Text('Confirmar Venta Offline e Imprimir Ticket'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


import 'dart:convert';
import 'package:flutter/material.dart';
import '../../../core/storage/local_database.dart';
import '../../../controller/cu29_validar_qr_cambio_offline_controller.dart';

class CambioQrScreen extends StatefulWidget {
  final LocalDatabase database;

  const CambioQrScreen({super.key, required this.database});

  @override
  State<CambioQrScreen> createState() => _CambioQrScreenState();
}

class _CambioQrScreenState extends State<CambioQrScreen> {
  late final CU29ValidarQrCambioOfflineController _controller;
  final TextEditingController _qrInputCtrl = TextEditingController();
  final TextEditingController _motivoCtrl = TextEditingController(text: 'Cambio por talla incorrecta');

  @override
  void initState() {
    super.initState();
    _controller = CU29ValidarQrCambioOfflineController(widget.database);

    // QR demo válido de ejemplo
    final demoQr = {
      'uuid': 'demo-ticket-1234',
      'fecha_hora_local': DateTime.now().subtract(const Duration(days: 5)).toIso8601String(),
      'total': 180.0,
      'usuario_id': 'cajero-01',
      'cliente_nombre': 'Juan Perez'
    };
    _qrInputCtrl.text = jsonEncode(demoQr);
  }

  @override
  void dispose() {
    _controller.dispose();
    _qrInputCtrl.dispose();
    _motivoCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Validar QR y Cambio Offline (CU-29)'),
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: ListView(
              children: [
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: Text(
                      'Validación criptográfica de comprobante y límite de 30 días para cambios de prenda (Regla BR-10).',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _qrInputCtrl,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Contenido del Código QR Escaneado',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: () => _controller.escanearYValidarQr(_qrInputCtrl.text),
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Validar Autenticidad y Plazo (BR-10)'),
                ),
                const SizedBox(height: 16),
                if (_controller.error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
                    child: Text(_controller.error!, style: TextStyle(color: Colors.red.shade800, fontWeight: FontWeight.bold)),
                  ),
                if (_controller.ticketValidado != null) ...[
                  Card(
                    color: Colors.green.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Comprobante Válido (Dentro de Plazo 30 días)', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                          Text('UUID: ${_controller.ticketValidado!['uuid']}'),
                          Text('Cliente: ${_controller.ticketValidado!['cliente_nombre']}'),
                          Text('Monto: BOB ${_controller.ticketValidado!['total']}'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _motivoCtrl,
                    decoration: const InputDecoration(labelText: 'Motivo del Cambio', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo),
                    onPressed: () {
                      _controller.procesarCambioOffline(
                        sucursalId: '11111111-1111-1111-1111-111111111101',
                        varianteDevueltaId: '22222222-2222-2222-2222-222222222201',
                        varianteNuevaId: '22222222-2222-2222-2222-222222222202',
                        motivo: _motivoCtrl.text,
                      );
                    },
                    child: const Text('Confirmar Cambio y Emitir Nota Preliminar'),
                  ),
                ],
                if (_controller.notaCambio != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    color: Colors.blue.shade50,
                    child: Text(
                      'Nota de Cambio generada en cola local:\nUUID: ${_controller.notaCambio!['uuid']}',
                      style: TextStyle(color: Colors.blue.shade900, fontWeight: FontWeight.bold),
                    ),
                  )
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}


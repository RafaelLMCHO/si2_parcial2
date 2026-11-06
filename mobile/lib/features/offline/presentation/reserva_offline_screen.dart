import 'package:flutter/material.dart';
import '../../../core/storage/local_database.dart';
import '../../../controller/cu26_registrar_reserva_offline_controller.dart';

class ReservaOfflineScreen extends StatefulWidget {
  final LocalDatabase database;

  const ReservaOfflineScreen({super.key, required this.database});

  @override
  State<ReservaOfflineScreen> createState() => _ReservaOfflineScreenState();
}

class _ReservaOfflineScreenState extends State<ReservaOfflineScreen> {
  late final CU26RegistrarReservaOfflineController _controller;
  final TextEditingController _sucursalCtrl = TextEditingController(text: '11111111-1111-1111-1111-111111111101');
  final TextEditingController _varianteCtrl = TextEditingController(text: '22222222-2222-2222-2222-222222222201');
  bool _probador = true;

  @override
  void initState() {
    super.initState();
    _controller = CU26RegistrarReservaOfflineController(widget.database);
  }

  @override
  void dispose() {
    _controller.dispose();
    _sucursalCtrl.dispose();
    _varianteCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Reserva Offline (CU-26)'),
          ),
          body: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Card(
                  color: Colors.amber,
                  child: Padding(
                    padding: EdgeInsets.all(12.0),
                    child: Text(
                      'Modo Desconectado: La reserva se registrará en la cola local con UUID v4 y se confirmará al volver la red.',
                      style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _sucursalCtrl,
                  decoration: const InputDecoration(labelText: 'Sucursal ID', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _varianteCtrl,
                  decoration: const InputDecoration(labelText: 'Variante ID', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  title: const Text('Apartar Probador'),
                  value: _probador,
                  onChanged: (val) => setState(() => _probador = val),
                ),
                const SizedBox(height: 16),
                if (_controller.reservaUuid != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8)),
                    child: Text('Reserva registrada en cola local:\nUUID: ${_controller.reservaUuid}', style: TextStyle(color: Colors.green.shade900, fontWeight: FontWeight.bold)),
                  ),
                const Spacer(),
                ElevatedButton(
                  onPressed: _controller.loading ? null : () {
                    _controller.registrarReservaOffline(
                      sucursalId: _sucursalCtrl.text,
                      fechaVisita: DateTime.now().add(const Duration(days: 1)),
                      probador: _probador,
                      items: [{'variante_id': _varianteCtrl.text, 'cantidad': 1}],
                    );
                  },
                  child: const Text('Guardar Reserva en Cola Local'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

